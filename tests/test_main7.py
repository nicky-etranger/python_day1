import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(
    str(
        Path(__file__).resolve().parents[1]
        / "src"
    )
)

from demo import BankDemo
from report_builder import ReportBuilder
from decimal import Decimal

from account_types import PremiumAccount
from models import BankAccount
from transaction import (
    Transaction,
    TransactionType,
)
from transaction_processor import TransactionProcessor

class TestReportBuilder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.demo = BankDemo()
        cls.demo.initialize()
        cls.demo.create_transactions()
        cls.demo.execute()

        cls.builder = ReportBuilder(
            cls.demo
        )

        cls.client = next(
            iter(
                cls.demo.bank.clients.values()
            )
        )

    def test_client_report(self):
        report = (
            self.builder
            .build_client_report(
                self.client.client_id
            )
        )

        self.assertEqual(
            report["report_type"],
            "client",
        )

        self.assertEqual(
            report["client_id"],
            self.client.client_id,
        )

        self.assertEqual(
            len(report["accounts"]),
            2,
        )

        self.assertIn(
            "transactions",
            report,
        )

        self.assertIn(
            "risk_profile",
            report,
        )

    def test_bank_report(self):
        report = (
            self.builder
            .build_bank_report()
        )

        self.assertEqual(
            report["report_type"],
            "bank",
        )

        self.assertEqual(
            report["clients_count"],
            6,
        )

        self.assertEqual(
            report["accounts_count"],
            12,
        )

        self.assertEqual(
            report[
                "transaction_statistics"
            ]["total"],
            36,
        )

    def test_risk_report(self):
        report = (
            self.builder
            .build_risk_report()
        )

        self.assertEqual(
            report["report_type"],
            "risk",
        )

        self.assertGreater(
            len(
                report[
                    "suspicious_operations"
                ]
            ),
            0,
        )

        self.assertEqual(
            len(
                report[
                    "client_risk_profiles"
                ]
            ),
            6,
        )

    def test_text_report(self):
        report = (
            self.builder
            .build_bank_report()
        )

        text = (
            self.builder
            .build_text_report(report)
        )

        self.assertIsInstance(
            text,
            str,
        )

        self.assertIn(
            "report_type: bank",
            text,
        )

        self.assertIn(
            "clients_count: 6",
            text,
        )

    def test_export_to_json(self):
        report = (
            self.builder
            .build_bank_report()
        )

        with tempfile.TemporaryDirectory() as directory:
            file_path = (
                Path(directory)
                / "report.json"
            )

            self.builder.export_to_json(
                report,
                str(file_path),
            )

            self.assertTrue(
                file_path.exists()
            )

            with open(
                file_path,
                encoding="utf-8",
            ) as file:
                data = json.load(file)

            self.assertEqual(
                data["report_type"],
                "bank",
            )

    def test_export_to_csv(self):
        report = (
            self.builder
            .build_bank_report()
        )

        with tempfile.TemporaryDirectory() as directory:
            file_path = (
                Path(directory)
                / "report.csv"
            )

            self.builder.export_to_csv(
                report,
                str(file_path),
            )

            self.assertTrue(
                file_path.exists()
            )

            with open(
                file_path,
                encoding="utf-8",
            ) as file:
                rows = list(
                    csv.DictReader(file)
                )

            self.assertEqual(
                len(rows),
                1,
            )

            self.assertEqual(
                rows[0]["report_type"],
                "bank",
            )

    def test_save_charts(self):
        with tempfile.TemporaryDirectory() as directory:
            files = (
                self.builder
                .save_charts(
                    directory,
                    self.client.client_id,
                )
            )

            self.assertEqual(
                len(files),
                3,
            )

            for file_path in files:
                path = Path(file_path)

                self.assertTrue(
                    path.exists()
                )

                self.assertEqual(
                    path.suffix,
                    ".png",
                )

                self.assertGreater(
                    path.stat().st_size,
                    0,
                )
def test_balance_reconstruction_with_conversion(self):
    sender = BankAccount(
        owner="Alex",
        balance=10000,
        currency="RUB",
    )

    recipient = BankAccount(
        owner="Maria",
        balance=100,
        currency="USD",
    )

    processor = TransactionProcessor(
        exchange_rates={
            ("RUB", "USD"): 0.01,
        }
    )

    transaction = Transaction(
        TransactionType.INTERNAL,
        1000,
        "RUB",
        sender,
        recipient,
    )

    processor.process(transaction)

    self.assertEqual(
        transaction.debited_amount,
        Decimal("1000"),
    )

    self.assertEqual(
        transaction.credited_amount,
        Decimal("10.00"),
    )

    balances = (
        self.builder
        ._reconstruct_balances(
            recipient,
            [transaction],
        )
    )

    self.assertEqual(
        balances,
        [100.0, 110.0],
    )

    def test_balance_reconstruction_with_premium_fee(self):
        sender = PremiumAccount(
            owner="Alex",
            balance=2000,
            currency="RUB",
            fixed_fee=100,
        )

        recipient = BankAccount(
            owner="Maria",
            balance=1000,
            currency="RUB",
        )

        processor = TransactionProcessor()

        transaction = Transaction(
            TransactionType.INTERNAL,
            1000,
            "RUB",
            sender,
            recipient,
        )

        processor.process(transaction)

        self.assertEqual(
            transaction.debited_amount,
            Decimal("1100"),
        )

        balances = (
            self.builder
            ._reconstruct_balances(
                sender,
                [transaction],
            )
        )

        self.assertEqual(
            balances,
            [2000.0, 900.0],
        )


if __name__ == "__main__":
    unittest.main()