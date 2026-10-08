import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from account_types import (
    InvestmentAccount,
    PremiumAccount,
    SavingsAccount,
)
from models import (
    InsufficientFundsError,
    InvalidOperationError,
)


class TestSavingsAccount(unittest.TestCase):
    def test_withdraw(self):
        account = SavingsAccount(
            owner="Alex",
            balance=10000,
            min_balance=2000,
        )

        account.withdraw(3000)

        self.assertEqual(account.balance, 7000)

    def test_minimum_balance(self):
        account = SavingsAccount(
            owner="Alex",
            balance=10000,
            min_balance=2000,
        )

        with self.assertRaises(InsufficientFundsError):
            account.withdraw(9000)

    def test_monthly_interest(self):
        account = SavingsAccount(
            owner="Alex",
            balance=10000,
            monthly_interest_rate=0.01,
        )

        interest = account.apply_monthly_interest()

        self.assertEqual(interest, Decimal("100.00"))
        self.assertEqual(account.balance, Decimal("10100.00"))

    def test_account_info(self):
        account = SavingsAccount(
            owner="Alex",
            balance=5000,
            min_balance=1000,
            monthly_interest_rate=0.01,
        )

        info = account.get_account_info()

        self.assertEqual(info["min_balance"], Decimal("1000"))
        self.assertEqual(
            info["monthly_interest_rate"],
            Decimal("0.01"),
        )


class TestPremiumAccount(unittest.TestCase):
    def test_withdraw_with_fee(self):
        account = PremiumAccount(
            owner="Alex",
            balance=5000,
            fixed_fee=100,
        )

        account.withdraw(1000)

        self.assertEqual(account.balance, 3900)

    def test_overdraft(self):
        account = PremiumAccount(
            owner="Alex",
            balance=500,
            overdraft_limit=5000,
            fixed_fee=100,
        )

        account.withdraw(1000)

        self.assertEqual(account.balance, -600)

    def test_overdraft_limit(self):
        account = PremiumAccount(
            owner="Alex",
            balance=500,
            overdraft_limit=1000,
            fixed_fee=100,
        )

        with self.assertRaises(InsufficientFundsError):
            account.withdraw(2000)

    def test_withdrawal_limit(self):
        account = PremiumAccount(
            owner="Alex",
            balance=5000,
            withdrawal_limit=1000,
        )

        with self.assertRaises(InvalidOperationError):
            account.withdraw(1500)

    def test_account_info(self):
        account = PremiumAccount(
            owner="Alex",
            withdrawal_limit=100000,
            overdraft_limit=10000,
            fixed_fee=100,
        )

        info = account.get_account_info()

        self.assertEqual(
            info["withdrawal_limit"],
            Decimal("100000"),
        )
        self.assertEqual(
            info["overdraft_limit"],
            Decimal("10000"),
        )
        self.assertEqual(
            info["fixed_fee"],
            Decimal("100"),
        )


class TestInvestmentAccount(unittest.TestCase):
    def test_invest(self):
        account = InvestmentAccount(
            owner="Alex",
            balance=10000,
        )

        account.invest("stocks", 3000)

        self.assertEqual(account.balance, 7000)
        self.assertEqual(
            account.portfolio["stocks"],
            Decimal("3000"),
        )

    def test_invalid_asset(self):
        account = InvestmentAccount(
            owner="Alex",
            balance=10000,
        )

        with self.assertRaises(InvalidOperationError):
            account.invest("crypto", 1000)

    def test_negative_investment(self):
        account = InvestmentAccount(
            owner="Alex",
            balance=10000,
        )

        with self.assertRaises(ValueError):
            account.invest("stocks", -1000)

    def test_insufficient_funds(self):
        account = InvestmentAccount(
            owner="Alex",
            balance=1000,
        )

        with self.assertRaises(InsufficientFundsError):
            account.invest("stocks", 2000)

    def test_withdraw(self):
        account = InvestmentAccount(
            owner="Alex",
            balance=5000,
        )

        account.withdraw(1000)

        self.assertEqual(account.balance, 4000)

    def test_yearly_growth(self):
        account = InvestmentAccount(
            owner="Alex",
            balance=10000,
        )

        account.invest("stocks", 5000)
        account.invest("bonds", 3000)
        account.invest("etf", 2000)

        growth_rates = {
            "stocks": 0.10,
            "bonds": 0.04,
            "etf": 0.07,
        }

        growth = account.project_yearly_growth(growth_rates)

        self.assertEqual(growth, Decimal("760.00"))

    def test_account_info(self):
        account = InvestmentAccount(
            owner="Alex",
            balance=5000,
        )

        account.invest("etf", 1000)

        info = account.get_account_info()

        self.assertEqual(
            info["portfolio"]["etf"],
            Decimal("1000"),
        )


if __name__ == "__main__":
    unittest.main()