import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.append(
    str(
        Path(__file__).resolve().parents[1]
        / "src"
    )
)

from client import Client
from demo import BankDemo
from transaction import (
    Transaction,
    TransactionStatus,
    TransactionType,
)


class TestBankDemo(unittest.TestCase):
    def setUp(self):
        self.demo = BankDemo()
        self.demo.initialize()

    def test_initialization(self):
        self.assertEqual(
            len(self.demo.bank.clients),
            6,
        )

        self.assertEqual(
            len(self.demo.bank.accounts),
            12,
        )

    def test_transaction_creation(self):
        self.demo.create_transactions()

        self.assertEqual(
            len(self.demo.transactions),
            36,
        )

        self.assertEqual(
            len(self.demo.queue_log),
            36,
        )

        self.assertEqual(
            len(self.demo.queue),
            36,
        )

    def test_execute_transactions(self):
        self.demo.create_transactions()
        self.demo.execute()

        self.assertEqual(
            len(self.demo.execution_log),
            36,
        )

        self.assertEqual(
            len(self.demo.queue),
            0,
        )

        self.assertTrue(
            all(
                transaction.status
                in {
                    TransactionStatus.COMPLETED,
                    TransactionStatus.FAILED,
                }
                for transaction
                in self.demo.transactions
            )
        )

    def test_contains_failed_transactions(self):
        self.demo.create_transactions()
        self.demo.execute()

        failed = [
            transaction
            for transaction
            in self.demo.transactions
            if transaction.status
            == TransactionStatus.FAILED
        ]

        self.assertGreater(
            len(failed),
            0,
        )

    def test_contains_completed_transactions(self):
        self.demo.create_transactions()
        self.demo.execute()

        completed = [
            transaction
            for transaction
            in self.demo.transactions
            if transaction.status
            == TransactionStatus.COMPLETED
        ]

        self.assertGreater(
            len(completed),
            0,
        )

    def test_client_accounts(self):
        client = list(
            self.demo.bank.clients.values()
        )[0]

        accounts = (
            self.demo.get_client_accounts(
                client.client_id
            )
        )

        self.assertEqual(
            len(accounts),
            2,
        )

    def test_client_history(self):
        self.demo.create_transactions()
        self.demo.execute()

        client = list(
            self.demo.bank.clients.values()
        )[0]

        history = (
            self.demo.get_client_history(
                client.client_id
            )
        )

        self.assertGreater(
            len(history),
            0,
        )

    def test_suspicious_operations(self):
        self.demo.create_transactions()
        self.demo.execute()

        suspicious = (
            self.demo
            .get_suspicious_operations()
        )

        self.assertGreater(
            len(suspicious),
            0,
        )

    def test_top_three_clients(self):
        self.demo.create_transactions()
        self.demo.execute()

        ranking = (
            self.demo.get_top_clients()
        )

        self.assertEqual(
            len(ranking),
            3,
        )

        self.assertGreaterEqual(
            ranking[0][1],
            ranking[1][1],
        )

        self.assertGreaterEqual(
            ranking[1][1],
            ranking[2][1],
        )

    def test_transaction_statistics(self):
        self.demo.create_transactions()
        self.demo.execute()

        statistics = (
            self.demo
            .get_transaction_statistics()
        )

        self.assertEqual(
            statistics["total"],
            36,
        )

        self.assertEqual(
            statistics["completed"]
            + statistics["failed"]
            + statistics["cancelled"],
            36,
        )

    def test_total_balance(self):
        initial_balance = (
            self.demo.get_total_balance()
        )

        self.demo.create_transactions()
        self.demo.execute()

        final_balance = (
            self.demo.get_total_balance()
        )

        self.assertLessEqual(
            final_balance,
            initial_balance,
        )
    def test_history_is_separated_for_same_names(self):
        demo = BankDemo()

        client1 = Client(
            full_name="Alex Smith",
            age=25,
            contacts={"phone": "1"},
        )

        client2 = Client(
            full_name="Alex Smith",
            age=30,
            contacts={"phone": "2"},
        )

        demo.bank.add_client(
            client1,
            "password1",
        )

        demo.bank.add_client(
            client2,
            "password2",
        )

        account1 = demo.bank.open_account(
            client1.client_id,
            balance=1000,
        )

        account2 = demo.bank.open_account(
            client1.client_id,
            balance=1000,
        )

        demo.bank.open_account(
            client2.client_id,
            balance=1000,
        )

        transaction = Transaction(
            TransactionType.INTERNAL,
            100,
            "RUB",
            account1,
            account2,
        )

        transaction.created_at = datetime(
            2026,
            10,
            11,
            12,
            0,
        )

        demo.transactions.append(
            transaction
        )

        self.assertEqual(
            demo.get_client_history(
                client1.client_id
            ),
            [transaction],
        )

        self.assertEqual(
            demo.get_client_history(
                client2.client_id
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()