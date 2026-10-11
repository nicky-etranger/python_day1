from datetime import timedelta
from decimal import Decimal, InvalidOperation
from enum import Enum

from transaction import Transaction


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RiskAnalyzer:
    def __init__(
        self,
        large_amount_threshold=50000,
        frequent_operations_limit=3,
        frequent_operations_window_minutes=60,
    ):
        try:
            self.large_amount_threshold = Decimal(
                str(large_amount_threshold)
            )
        except (InvalidOperation, ValueError, TypeError):
            raise ValueError(
                "Large amount threshold must be a valid number"
            )

        if self.large_amount_threshold <= 0:
            raise ValueError(
                "Large amount threshold must be greater than zero"
            )

        if (
            not isinstance(frequent_operations_limit, int)
            or frequent_operations_limit < 1
        ):
            raise ValueError(
                "Frequent operations limit must be a positive integer"
            )

        if (
            not isinstance(
                frequent_operations_window_minutes,
                int,
            )
            or frequent_operations_window_minutes < 1
        ):
            raise ValueError(
                "Frequent operations window must be a positive integer"
            )

        self.frequent_operations_limit = (
            frequent_operations_limit
        )
        self.frequent_operations_window = timedelta(
            minutes=frequent_operations_window_minutes
        )
        self.history = []

    def analyze(self, transaction: Transaction) -> dict:
        if not isinstance(transaction, Transaction):
            raise ValueError("Invalid transaction")

        score = 0
        reasons = []

        if transaction.amount >= self.large_amount_threshold:
            score += 2
            reasons.append("large_amount")

        window_start = (
            transaction.created_at
            - self.frequent_operations_window
        )

        recent_operations = [
            record
            for record in self.history
            if record["sender_account_id"]
            == transaction.sender.account_id
            and window_start
            <= record["timestamp"]
            <= transaction.created_at
        ]

        if len(recent_operations) >= self.frequent_operations_limit:
            score += 2
            reasons.append("frequent_operations")

        known_recipient = any(
            record["sender_account_id"]
            == transaction.sender.account_id
            and record["recipient_account_id"]
            == transaction.recipient.account_id
            for record in self.history
        )

        if not known_recipient:
            score += 1
            reasons.append("new_recipient")

        if 0 <= transaction.created_at.hour < 5:
            score += 2
            reasons.append("night_operation")

        if score >= 4:
            level = RiskLevel.HIGH
        elif score >= 2:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW

        return {
            "level": level,
            "score": score,
            "reasons": reasons,
        }

    def record(
        self,
        transaction: Transaction,
        analysis: dict,
    ):
        self.history.append(
            {
                "transaction_id": transaction.transaction_id,
                "sender_account_id": transaction.sender.account_id,
                "recipient_account_id": transaction.recipient.account_id,
                "client": transaction.sender.owner,
                "timestamp": transaction.created_at,
                "risk_level": analysis["level"],
                "score": analysis["score"],
                "reasons": analysis["reasons"],
            }
        )

    def get_client_risk_profile(
        self,
        client: str,
    ) -> dict:
        records = [
            record
            for record in self.history
            if record["client"] == client
        ]

        levels = {
            RiskLevel.LOW: 0,
            RiskLevel.MEDIUM: 0,
            RiskLevel.HIGH: 0,
        }

        for record in records:
            levels[record["risk_level"]] += 1

        if levels[RiskLevel.HIGH] > 0:
            overall_risk = RiskLevel.HIGH
        elif levels[RiskLevel.MEDIUM] > 0:
            overall_risk = RiskLevel.MEDIUM
        else:
            overall_risk = RiskLevel.LOW

        return {
            "client": client,
            "risk_level": overall_risk,
            "total_operations": len(records),
            "low_risk": levels[RiskLevel.LOW],
            "medium_risk": levels[RiskLevel.MEDIUM],
            "high_risk": levels[RiskLevel.HIGH],
        }