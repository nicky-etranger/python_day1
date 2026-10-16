from datetime import datetime

from audit import AuditLevel, AuditLog
from models import InvalidOperationError
from risk import RiskAnalyzer, RiskLevel
from transaction import Transaction, TransactionStatus
from transaction_processor import TransactionProcessor


class SecureTransactionProcessor(TransactionProcessor):
    def __init__(
        self,
        audit_log: AuditLog,
        risk_analyzer: RiskAnalyzer,
        exchange_rates: dict | None = None,
        external_fee_rate=0.01,
        max_retries=3,
    ):
        super().__init__(
            exchange_rates=exchange_rates,
            external_fee_rate=external_fee_rate,
            max_retries=max_retries,
        )

        self.audit_log = audit_log
        self.risk_analyzer = risk_analyzer

    def process(
        self,
        transaction: Transaction,
    ) -> Transaction:
        if transaction.status != TransactionStatus.PENDING:
            raise InvalidOperationError(
                "Transaction is not pending"
            )

        analysis = self.risk_analyzer.analyze(
            transaction
        )

        self.risk_analyzer.record(
            transaction,
            analysis,
        )

        if (
            "night_operation" in analysis["reasons"]
            or analysis["level"] == RiskLevel.HIGH
        ):
            if "night_operation" in analysis["reasons"]:
                reason = (
                    "Transaction blocked: operations are not allowed "
                    "from 00:00 to 05:00"
                )
            else:
                reason = (
                    "Transaction blocked due to high risk: "
                    + ", ".join(analysis["reasons"])
                )

            transaction.status = TransactionStatus.FAILED
            transaction.rejection_reason = reason
            transaction.errors.append(reason)
            transaction.updated_at = datetime.now()

            self.audit_log.log(
                AuditLevel.CRITICAL,
                "risk_blocked",
                reason,
                transaction_id=transaction.transaction_id,
                client=transaction.sender.owner,
                data={
                    "risk_level": analysis["level"].value,
                    "score": analysis["score"],
                    "reasons": analysis["reasons"],
                },
            )

            return transaction

        if analysis["level"] == RiskLevel.MEDIUM:
            self.audit_log.log(
                AuditLevel.WARNING,
                "risk_detected",
                "Suspicious transaction detected",
                transaction_id=transaction.transaction_id,
                client=transaction.sender.owner,
                data={
                    "risk_level": analysis["level"].value,
                    "score": analysis["score"],
                    "reasons": analysis["reasons"],
                },
            )

        result = super().process(transaction)

        if result.status == TransactionStatus.COMPLETED:
            self.audit_log.log(
                AuditLevel.INFO,
                "transaction_completed",
                "Transaction completed",
                transaction_id=result.transaction_id,
                client=result.sender.owner,
                data={
                    "risk_level": analysis["level"].value,
                },
            )
        else:
            self.audit_log.log(
                AuditLevel.ERROR,
                "transaction_failed",
                "Transaction failed",
                transaction_id=result.transaction_id,
                client=result.sender.owner,
                data={
                    "reason": result.rejection_reason,
                    "risk_level": analysis["level"].value,
                },
            )

        return result