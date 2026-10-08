from decimal import Decimal, InvalidOperation

from models import (
    BankAccount,
    InsufficientFundsError,
    InvalidOperationError,
)
from utils import validate_amount


class SavingsAccount(BankAccount):
    def __init__(
        self,
        owner: str,
        balance=0,
        account_id: str | None = None,
        status=None,
        currency="RUB",
        min_balance=0,
        monthly_interest_rate=0,
    ):
        kwargs = {
            "owner": owner,
            "balance": balance,
            "account_id": account_id,
            "currency": currency,
        }

        if status is not None:
            kwargs["status"] = status

        super().__init__(**kwargs)

        try:
            self.min_balance = Decimal(str(min_balance))
            self.monthly_interest_rate = Decimal(str(monthly_interest_rate))
        except (InvalidOperation, ValueError, TypeError):
            raise ValueError("Savings account parameters must be valid numbers")

        if self.min_balance < 0:
            raise ValueError("Minimum balance cannot be negative")

        if self.monthly_interest_rate < 0:
            raise ValueError("Monthly interest rate cannot be negative")

        if self._balance < self.min_balance:
            raise ValueError("Initial balance cannot be lower than minimum balance")

    def withdraw(self, amount) -> Decimal:
        self._validate_operation_status()
        amount = validate_amount(amount)

        if self._balance - amount < self.min_balance:
            raise InsufficientFundsError("Withdrawal would violate minimum balance")

        self._balance -= amount
        return self._balance

    def apply_monthly_interest(self) -> Decimal:
        self._validate_operation_status()

        interest = self._balance * self.monthly_interest_rate
        self._balance += interest

        return interest

    def get_account_info(self) -> dict:
        info = super().get_account_info()
        info.update(
            {
                "min_balance": self.min_balance,
                "monthly_interest_rate": self.monthly_interest_rate,
            }
        )
        return info

    def __str__(self) -> str:
        last_digits = self.account_id[-4:]

        return (
            f"SavingsAccount | "
            f"Client: {self.owner} | "
            f"Account: ****{last_digits} | "
            f"Status: {self.status.value} | "
            f"Balance: {self._balance:.2f} {self.currency.value} | "
            f"Min balance: {self.min_balance:.2f} | "
            f"Monthly rate: {self.monthly_interest_rate:.2%}"
        )


class PremiumAccount(BankAccount):
    def __init__(
        self,
        owner: str,
        balance=0,
        account_id: str | None = None,
        status=None,
        currency="RUB",
        withdrawal_limit=1_000_000,
        overdraft_limit=100_000,
        fixed_fee=100,
    ):
        kwargs = {
            "owner": owner,
            "balance": balance,
            "account_id": account_id,
            "currency": currency,
        }

        if status is not None:
            kwargs["status"] = status

        super().__init__(**kwargs)

        try:
            self.withdrawal_limit = Decimal(str(withdrawal_limit))
            self.overdraft_limit = Decimal(str(overdraft_limit))
            self.fixed_fee = Decimal(str(fixed_fee))
        except (InvalidOperation, ValueError, TypeError):
            raise ValueError("Premium account parameters must be valid numbers")

        if self.withdrawal_limit <= 0:
            raise ValueError("Withdrawal limit must be greater than zero")

        if self.overdraft_limit < 0:
            raise ValueError("Overdraft limit cannot be negative")

        if self.fixed_fee < 0:
            raise ValueError("Fixed fee cannot be negative")

    def withdraw(self, amount) -> Decimal:
        self._validate_operation_status()
        amount = validate_amount(amount)

        if amount > self.withdrawal_limit:
            raise InvalidOperationError("Withdrawal limit exceeded")

        total = amount + self.fixed_fee

        if self._balance - total < -self.overdraft_limit:
            raise InsufficientFundsError("Overdraft limit exceeded")

        self._balance -= total
        return self._balance

    def get_account_info(self) -> dict:
        info = super().get_account_info()
        info.update(
            {
                "withdrawal_limit": self.withdrawal_limit,
                "overdraft_limit": self.overdraft_limit,
                "fixed_fee": self.fixed_fee,
            }
        )
        return info

    def __str__(self) -> str:
        last_digits = self.account_id[-4:]

        return (
            f"PremiumAccount | "
            f"Client: {self.owner} | "
            f"Account: ****{last_digits} | "
            f"Status: {self.status.value} | "
            f"Balance: {self._balance:.2f} {self.currency.value} | "
            f"Overdraft: {self.overdraft_limit:.2f} | "
            f"Fee: {self.fixed_fee:.2f}"
        )


class InvestmentAccount(BankAccount):
    ALLOWED_ASSETS = {"stocks", "bonds", "etf"}

    def __init__(
        self,
        owner: str,
        balance=0,
        account_id: str | None = None,
        status=None,
        currency="RUB",
    ):
        kwargs = {
            "owner": owner,
            "balance": balance,
            "account_id": account_id,
            "currency": currency,
        }

        if status is not None:
            kwargs["status"] = status

        super().__init__(**kwargs)

        self.portfolio = {
            "stocks": Decimal("0"),
            "bonds": Decimal("0"),
            "etf": Decimal("0"),
        }

    def invest(self, asset_type: str, amount) -> Decimal:
        self._validate_operation_status()

        if asset_type not in self.ALLOWED_ASSETS:
            raise InvalidOperationError("Unsupported asset type")

        amount = validate_amount(amount)

        if amount > self._balance:
            raise InsufficientFundsError("Insufficient funds")

        self._balance -= amount
        self.portfolio[asset_type] += amount

        return self.portfolio[asset_type]

    def withdraw(self, amount) -> Decimal:
        self._validate_operation_status()
        amount = validate_amount(amount)

        if amount > self._balance:
            raise InsufficientFundsError("Insufficient funds")

        self._balance -= amount
        return self._balance

    def project_yearly_growth(self, growth_rates: dict) -> Decimal:
        growth = Decimal("0")

        for asset_type, amount in self.portfolio.items():
            if asset_type not in growth_rates:
                raise InvalidOperationError(
                    f"Growth rate for {asset_type} is not provided"
                )

            try:
                rate = Decimal(str(growth_rates[asset_type]))
            except (InvalidOperation, ValueError, TypeError):
                raise ValueError("Growth rate must be a valid number")

            growth += amount * rate

        return growth

    def get_account_info(self) -> dict:
        info = super().get_account_info()
        info["portfolio"] = self.portfolio.copy()
        return info

    def __str__(self) -> str:
        last_digits = self.account_id[-4:]
        portfolio_total = sum(self.portfolio.values(), Decimal("0"))

        return (
            f"InvestmentAccount | "
            f"Client: {self.owner} | "
            f"Account: ****{last_digits} | "
            f"Status: {self.status.value} | "
            f"Balance: {self._balance:.2f} {self.currency.value} | "
            f"Portfolio: {portfolio_total:.2f} {self.currency.value}"
        )
        

