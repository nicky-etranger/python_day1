import sys
import unittest
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from account_types import PremiumAccount
from models import AccountStatus, BankAccount
from transaction import (
    Transaction,
    TransactionStatus,
    TransactionType,
)
from transaction_processor import TransactionProcessor
from transaction_queue import TransactionQueue


class TestTransaction(unittest.TestCase):
    def setUp(self):
        self.sender = BankAccount(
            owner="Alex",
            balance=10000,
            currency="RUB",
        )

        self.recipient = BankAccount(
            owner="Maria",
            balance=1000,
            currency="RUB",
        )

    def test_create_transaction(self):
        transaction = Transaction(
            TransactionType.INTERNAL,
            1000,
            "RUB",
            self.sender,
            self.recipient,
        )

        self.assertEqual(
            transaction.amount,
            Decimal("1000"),
        )
        self.assertEqual(
            transaction.status,
            TransactionStatus.PENDING,
        )
        self.assertEqual(
            transaction.commission,
            Decimal("0"),
        )
        self.assertEqual(
            len(transaction.transaction_id),
            8,
        )

    def test_negative_amount(self):
        with self.assertRaises(ValueError):
            Transaction(
                TransactionType.INTERNAL,
                -100,
                "RUB",
                self.sender,
                self.recipient,
            )


class TestTransactionQueue(unittest.TestCase):
    def setUp(self):
        self.sender = BankAccount(
            owner="Alex",
            balance=10000,
        )

        self.recipient = BankAccount(
            owner="Maria",
            balance=1000,
        )

    def create_transaction(self, amount):
        return Transaction(
            TransactionType.INTERNAL,
            amount,
            "RUB",
            self.sender,
            self.recipient,
        )

    def test_priority(self):
        low = self.create_transaction(100)
        high = self.create_transaction(200)

        queue = TransactionQueue()

        queue.add(low, priority=1)
        queue.add(high, priority=10)

        result = queue.pop_ready()

        self.assertEqual(result, high)

    def test_delayed_transaction(self):
        transaction = self.create_transaction(100)

        queue = TransactionQueue()

        execute_at = datetime.now() + timedelta(hours=1)

        queue.add(
            transaction,
            execute_at=execute_at,
        )

        result = queue.pop_ready(
            current_time=datetime.now()
        )

        self.assertIsNone(result)

        result = queue.pop_ready(
            current_time=execute_at
        )

        self.assertEqual(
            result,
            transaction,
        )

    def test_cancel_transaction(self):
        transaction = self.create_transaction(100)

        queue = TransactionQueue()
        queue.add(transaction)

        queue.cancel(
            transaction.transaction_id
        )

        self.assertEqual(
            transaction.status,
            TransactionStatus.CANCELLED,
        )

        self.assertIsNone(
            queue.pop_ready()
        )


class TestTransactionProcessor(unittest.TestCase):
    def setUp(self):
        self.sender = BankAccount(
            owner="Alex",
            balance=10000,
            currency="RUB",
        )

        self.recipient = BankAccount(
            owner="Maria",
            balance=1000,
            currency="RUB",
        )

        self.processor = TransactionProcessor(
            exchange_rates={
                ("RUB", "USD"): 0.01,
            },
            external_fee_rate=0.01,
            max_retries=3,
        )

    def test_internal_transfer(self):
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
        self.assertEqual(
            self.sender.balance,
            Decimal("9000"),
        )
        self.assertEqual(
            self.recipient.balance,
            Decimal("2000"),
        )
        self.assertEqual(
            transaction.commission,
            Decimal("0"),
        )

    def test_external_transfer_fee(self):
        transaction = Transaction(
            TransactionType.EXTERNAL,
            1000,
            "RUB",
            self.sender,
            self.recipient,
        )

        self.processor.process(transaction)

        self.assertEqual(
            transaction.commission,
            Decimal("10.00"),
        )
        self.assertEqual(
            self.sender.balance,
            Decimal("8990.00"),
        )
        self.assertEqual(
            self.recipient.balance,
            Decimal("2000"),
        )

    def test_currency_conversion(self):
        usd_recipient = BankAccount(
            owner="John",
            balance=100,
            currency="USD",
        )

        transaction = Transaction(
            TransactionType.INTERNAL,
            1000,
            "RUB",
            self.sender,
            usd_recipient,
        )

        self.processor.process(transaction)

        self.assertEqual(
            transaction.status,
            TransactionStatus.COMPLETED,
        )
        self.assertEqual(
            usd_recipient.balance,
            Decimal("110.00"),
        )

    def test_regular_account_cannot_go_negative(self):
        transaction = Transaction(
            TransactionType.INTERNAL,
            20000,
            "RUB",
            self.sender,
            self.recipient,
        )

        self.processor.process(transaction)

        self.assertEqual(
            transaction.status,
            TransactionStatus.FAILED,
        )
        self.assertEqual(
            self.sender.balance,
            Decimal("10000"),
        )

    def test_premium_account_can_use_overdraft(self):
        premium = PremiumAccount(
            owner="Alex",
            balance=500,
            currency="RUB",
            overdraft_limit=5000,
            fixed_fee=0,
        )

        transaction = Transaction(
            TransactionType.INTERNAL,
            1000,
            "RUB",
            premium,
            self.recipient,
        )

        self.processor.process(transaction)

        self.assertEqual(
            transaction.status,
            TransactionStatus.COMPLETED,
        )
        self.assertEqual(
            premium.balance,
            Decimal("-500"),
        )

    def test_frozen_sender(self):
        self.sender.status = AccountStatus.FROZEN

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
            TransactionStatus.FAILED,
        )
        self.assertEqual(
            transaction.attempts,
            3,
        )
        self.assertEqual(
            len(transaction.errors),
            3,
        )
        self.assertEqual(
            self.sender.balance,
            Decimal("10000"),
        )

    def test_frozen_recipient(self):
        self.recipient.status = AccountStatus.FROZEN

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
            TransactionStatus.FAILED,
        )
        self.assertEqual(
            self.sender.balance,
            Decimal("10000"),
        )

    def test_process_ten_transactions(self):
        sender = BankAccount(
            owner="Alex",
            balance=100000,
            currency="RUB",
        )

        recipient = BankAccount(
            owner="Maria",
            balance=0,
            currency="RUB",
        )

        queue = TransactionQueue()

        transactions = []

        for index in range(10):
            transaction = Transaction(
                TransactionType.INTERNAL,
                1000,
                "RUB",
                sender,
                recipient,
            )

            transactions.append(transaction)

            queue.add(
                transaction,
                priority=index % 3,
            )

        processed = self.processor.process_queue(
            queue
        )

        self.assertEqual(
            len(processed),
            10,
        )

        self.assertTrue(
            all(
                transaction.status
                == TransactionStatus.COMPLETED
                for transaction in transactions
            )
        )

        self.assertEqual(
            sender.balance,
            Decimal("90000"),
        )

        self.assertEqual(
            recipient.balance,
            Decimal("10000"),
        )


if __name__ == "__main__":
    unittest.main()