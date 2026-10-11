import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.append(
    str(
        Path(__file__).resolve().parents[1]
        / "src"
    )
)

from audit import AuditLevel, AuditLog
from audit_reports import AuditReports
from models import BankAccount
from risk import RiskAnalyzer, RiskLevel
from secure_transaction_processor import (
    SecureTransactionProcessor,
)
from transaction import (
    Transaction,
    TransactionStatus,
    TransactionType,
)


class TestAuditLog(unittest.TestCase):
    def test_save_to_memory(self):
        audit = AuditLog()

        audit.log(
            AuditLevel.INFO,
            "test",
            "Test event",
        )

        self.assertEqual(
            len(audit.entries),
            1,
        )

    def test_save_to_file(self):
        with tempfile.TemporaryDirectory() as directory:
            file_path = Path(directory) / "audit.log"

            audit = AuditLog(
                str(file_path)
            )

            audit.log(
                AuditLevel.ERROR,
                "test_error",
                "Test error",
            )

            content = file_path.read_text(
                encoding="utf-8"
            )

            self.assertIn(
                "test_error",
                content,
            )

    def test_filter(self):
        audit = AuditLog()

        audit.log(
            AuditLevel.INFO,
            "completed",
            "Completed",
        )

        audit.log(
            AuditLevel.ERROR,
            "failed",
            "Failed",
        )

        result = audit.filter(
            level=AuditLevel.ERROR
        )

        self.assertEqual(
            len(result),
            1,
        )

        self.assertEqual(
            result[0]["event_type"],
            "failed",
        )


class TestRiskAnalyzer(unittest.TestCase):
    def setUp(self):
        self.sender = BankAccount(
            owner="Alex",
            balance=500000,
            currency="RUB",
        )

        self.recipient = BankAccount(
            owner="Maria",
            balance=1000,
            currency="RUB",
        )

        self.analyzer = RiskAnalyzer(
            large_amount_threshold=50000,
            frequent_operations_limit=3,
            frequent_operations_window_minutes=60,
        )

    def create_transaction(
        self,
        amount=1000,
        recipient=None,
        created_at=None,
    ):
        transaction = Transaction(
            TransactionType.INTERNAL,
            amount,
            "RUB",
            self.sender,
            recipient or self.recipient,
        )

        if created_at is not None:
            transaction.created_at = created_at

        return transaction

    def test_new_recipient(self):
        transaction = self.create_transaction()

        result = self.analyzer.analyze(
            transaction
        )

        self.assertIn(
            "new_recipient",
            result["reasons"],
        )

        self.assertEqual(
            result["level"],
            RiskLevel.LOW,
        )

    def test_large_amount(self):
        transaction = self.create_transaction(
            amount=60000
        )

        result = self.analyzer.analyze(
            transaction
        )

        self.assertIn(
            "large_amount",
            result["reasons"],
        )

        self.assertEqual(
            result["level"],
            RiskLevel.MEDIUM,
        )

    def test_night_operation(self):
        transaction = self.create_transaction(
            created_at=datetime(
                2026,
                10,
                11,
                2,
                0,
            )
        )

        result = self.analyzer.analyze(
            transaction
        )

        self.assertIn(
            "night_operation",
            result["reasons"],
        )

        self.assertEqual(
            result["level"],
            RiskLevel.MEDIUM,
        )

    def test_frequent_operations(self):
        base_time = datetime(
            2026,
            10,
            11,
            12,
            0,
        )

        for index in range(3):
            transaction = self.create_transaction(
                created_at=(
                    base_time
                    + timedelta(minutes=index * 5)
                )
            )

            analysis = self.analyzer.analyze(
                transaction
            )

            self.analyzer.record(
                transaction,
                analysis,
            )

        transaction = self.create_transaction(
            created_at=(
                base_time
                + timedelta(minutes=20)
            )
        )

        result = self.analyzer.analyze(
            transaction
        )

        self.assertIn(
            "frequent_operations",
            result["reasons"],
        )

        self.assertEqual(
            result["level"],
            RiskLevel.MEDIUM,
        )


class TestSecureTransactionProcessor(unittest.TestCase):
    def setUp(self):
        self.audit = AuditLog()

        self.analyzer = RiskAnalyzer(
            large_amount_threshold=50000,
            frequent_operations_limit=3,
        )

        self.processor = SecureTransactionProcessor(
            audit_log=self.audit,
            risk_analyzer=self.analyzer,
            max_retries=3,
        )

        self.sender = BankAccount(
            owner="Alex Smith",
            balance=200000,
            currency="RUB",
        )

        self.recipient = BankAccount(
            owner="Maria Brown",
            balance=10000,
            currency="RUB",
        )

    def test_normal_transaction(self):
        transaction = Transaction(
            TransactionType.INTERNAL,
            1000,
            "RUB",
            self.sender,
            self.recipient,
        )

        self.processor.process(transaction)

        self.assertEqual(
            transaction.status,
            TransactionStatus.COMPLETED,
        )

        entries = self.audit.filter(
            event_type="transaction_completed"
        )

        self.assertEqual(
            len(entries),
            1,
        )

    def test_medium_risk_is_logged(self):
        transaction = Transaction(
            TransactionType.INTERNAL,
            60000,
            "RUB",
            self.sender,
            self.recipient,
        )

        self.processor.process(transaction)

        entries = self.audit.filter(
            event_type="risk_detected"
        )

        self.assertEqual(
            len(entries),
            1,
        )

        self.assertEqual(
            transaction.status,
            TransactionStatus.COMPLETED,
        )

    def test_high_risk_is_blocked(self):
        new_recipient = BankAccount(
            owner="John White",
            balance=1000,
            currency="RUB",
        )

        transaction = Transaction(
            TransactionType.INTERNAL,
            60000,
            "RUB",
            self.sender,
            new_recipient,
        )

        transaction.created_at = datetime(
            2026,
            10,
            11,
            2,
            0,
        )

        sender_balance = self.sender.balance
        recipient_balance = new_recipient.balance

        self.processor.process(transaction)

        self.assertEqual(
            transaction.status,
            TransactionStatus.FAILED,
        )

        self.assertEqual(
            self.sender.balance,
            sender_balance,
        )

        self.assertEqual(
            new_recipient.balance,
            recipient_balance,
        )

        entries = self.audit.filter(
            event_type="risk_blocked"
        )

        self.assertEqual(
            len(entries),
            1,
        )

    def test_transaction_error_is_logged(self):
        sender = BankAccount(
            owner="Alex Smith",
            balance=100,
            currency="RUB",
        )

        transaction = Transaction(
            TransactionType.INTERNAL,
            1000,
            "RUB",
            sender,
            self.recipient,
        )

        self.processor.process(transaction)

        entries = self.audit.filter(
            event_type="transaction_failed"
        )

        self.assertEqual(
            len(entries),
            1,
        )

        self.assertEqual(
            transaction.status,
            TransactionStatus.FAILED,
        )


class TestAuditReports(unittest.TestCase):
    def setUp(self):
        self.audit = AuditLog()
        self.analyzer = RiskAnalyzer()

        self.reports = AuditReports(
            self.audit,
            self.analyzer,
        )

    def test_suspicious_operations_report(self):
        self.audit.log(
            AuditLevel.WARNING,
            "risk_detected",
            "Suspicious transaction",
        )

        self.audit.log(
            AuditLevel.CRITICAL,
            "risk_blocked",
            "Blocked transaction",
        )

        result = (
            self.reports
            .get_suspicious_operations()
        )

        self.assertEqual(
            len(result),
            2,
        )

    def test_client_risk_profile(self):
        sender = BankAccount(
            owner="Alex Smith",
            balance=100000,
        )

        recipient = BankAccount(
            owner="Maria",
            balance=1000,
        )

        transaction = Transaction(
            TransactionType.INTERNAL,
            60000,
            "RUB",
            sender,
            recipient,
        )

        analysis = self.analyzer.analyze(
            transaction
        )

        self.analyzer.record(
            transaction,
            analysis,
        )

        profile = (
            self.reports
            .get_client_risk_profile(
                "Alex Smith"
            )
        )

        self.assertEqual(
            profile["total_operations"],
            1,
        )

        self.assertEqual(
            profile["medium_risk"],
            1,
        )

    def test_error_statistics(self):
        self.audit.log(
            AuditLevel.ERROR,
            "transaction_failed",
            "Transaction failed",
            data={
                "reason": "Insufficient funds"
            },
        )

        self.audit.log(
            AuditLevel.CRITICAL,
            "risk_blocked",
            "Transaction blocked",
        )

        statistics = (
            self.reports
            .get_error_statistics()
        )

        self.assertEqual(
            statistics["transaction_errors"],
            1,
        )

        self.assertEqual(
            statistics["blocked_operations"],
            1,
        )

        self.assertEqual(
            statistics["total_errors"],
            2,
        )


if __name__ == "__main__":
    unittest.main()