from datetime import datetime, timedelta

from audit import AuditLog
from audit_reports import AuditReports
from models import BankAccount
from risk import RiskAnalyzer
from secure_transaction_processor import (
    SecureTransactionProcessor,
)
from transaction import Transaction, TransactionType


def main():
    audit_log = AuditLog("audit_day5.log")

    risk_analyzer = RiskAnalyzer(
        large_amount_threshold=50000,
        frequent_operations_limit=3,
        frequent_operations_window_minutes=60,
    )

    processor = SecureTransactionProcessor(
        audit_log=audit_log,
        risk_analyzer=risk_analyzer,
        external_fee_rate=0.01,
    )

    sender = BankAccount(
        owner="Alex Smith",
        balance=300000,
        currency="RUB",
    )

    recipient1 = BankAccount(
        owner="Maria Brown",
        balance=10000,
        currency="RUB",
    )

    recipient2 = BankAccount(
        owner="John White",
        balance=10000,
        currency="RUB",
    )

    normal1 = Transaction(
        TransactionType.INTERNAL,
        1000,
        "RUB",
        sender,
        recipient1,
    )

    normal2 = Transaction(
        TransactionType.INTERNAL,
        2000,
        "RUB",
        sender,
        recipient1,
    )

    large = Transaction(
        TransactionType.INTERNAL,
        60000,
        "RUB",
        sender,
        recipient1,
    )

    frequent1 = Transaction(
        TransactionType.INTERNAL,
        1000,
        "RUB",
        sender,
        recipient1,
    )

    frequent2 = Transaction(
        TransactionType.INTERNAL,
        1000,
        "RUB",
        sender,
        recipient1,
    )

    dangerous = Transaction(
        TransactionType.INTERNAL,
        70000,
        "RUB",
        sender,
        recipient2,
    )

    base_time = datetime(
        2026,
        10,
        11,
        12,
        0,
    )

    normal1.created_at = base_time
    normal2.created_at = base_time + timedelta(minutes=5)
    large.created_at = base_time + timedelta(minutes=10)
    frequent1.created_at = base_time + timedelta(minutes=15)
    frequent2.created_at = base_time + timedelta(minutes=20)

    dangerous.created_at = datetime(
        2026,
        10,
        12,
        2,
        0,
    )

    transactions = [
        normal1,
        normal2,
        large,
        frequent1,
        frequent2,
        dangerous,
    ]

    for transaction in transactions:
        processor.process(transaction)
        print(transaction)

    reports = AuditReports(
        audit_log,
        risk_analyzer,
    )

    print(
        reports.get_suspicious_operations()
    )

    print(
        reports.get_client_risk_profile(
            "Alex Smith"
        )
    )

    print(
        reports.get_error_statistics()
    )


if __name__ == "__main__":
    main()