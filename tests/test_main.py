import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from models import (
    AccountClosedError,
    AccountFrozenError,
    AccountStatus,
    BankAccount,
    InsufficientFundsError,
)


class TestBankAccount(unittest.TestCase):
    def test_create_active_account(self):
        account = BankAccount(
            owner="Alex",
            balance=1000,
            currency="RUB",
        )

        self.assertEqual(account.owner, "Alex")
        self.assertEqual(account.balance, 1000)
        self.assertEqual(account.status, AccountStatus.ACTIVE)
        self.assertEqual(account.currency.value, "RUB")

    def test_account_id_generated(self):
        account = BankAccount(owner="Alex")

        self.assertEqual(len(account.account_id), 8)

    def test_deposit(self):
        account = BankAccount(owner="Alex", balance=1000)

        account.deposit(500)

        self.assertEqual(account.balance, 1500)

    def test_withdraw(self):
        account = BankAccount(owner="Alex", balance=1000)

        account.withdraw(300)

        self.assertEqual(account.balance, 700)

    def test_negative_deposit(self):
        account = BankAccount(owner="Alex")

        with self.assertRaises(ValueError):
            account.deposit(-100)

    def test_negative_withdraw(self):
        account = BankAccount(owner="Alex", balance=1000)

        with self.assertRaises(ValueError):
            account.withdraw(-100)

    def test_insufficient_funds(self):
        account = BankAccount(owner="Alex", balance=100)

        with self.assertRaises(InsufficientFundsError):
            account.withdraw(200)

    def test_frozen_account_deposit(self):
        account = BankAccount(
            owner="Alex",
            status=AccountStatus.FROZEN,
        )

        with self.assertRaises(AccountFrozenError):
            account.deposit(100)

    def test_frozen_account_withdraw(self):
        account = BankAccount(
            owner="Alex",
            balance=1000,
            status=AccountStatus.FROZEN,
        )

        with self.assertRaises(AccountFrozenError):
            account.withdraw(100)

    def test_closed_account_operation(self):
        account = BankAccount(
            owner="Alex",
            status=AccountStatus.CLOSED,
        )

        with self.assertRaises(AccountClosedError):
            account.deposit(100)

    def test_negative_initial_balance(self):
        with self.assertRaises(ValueError):
            BankAccount(
                owner="Alex",
                balance=-100,
            )

    def test_invalid_currency(self):
        with self.assertRaises(ValueError):
            BankAccount(
                owner="Alex",
                currency="GBP",
            )


if __name__ == "__main__":
    unittest.main()