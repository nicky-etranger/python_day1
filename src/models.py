from abc import ABC, abstractmethod
from decimal import Decimal
from enum import Enum

from utils import generate_account_id, validate_amount


class AccountFrozenError(Exception):
    pass


class AccountClosedError(Exception):
    pass


class InvalidOperationError(Exception):
    pass


class InsufficientFundsError(Exception):
    pass


class AccountStatus(Enum):
    ACTIVE = "active"
    FROZEN = "frozen"
    CLOSED = "closed"


class Currency(Enum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"
    KZT = "KZT"
    CNY = "CNY"


class AbstractAccount(ABC):
    def __init__(
        self,
        owner: str,
        balance=0,
        account_id: str | None = None,
        status: AccountStatus = AccountStatus.ACTIVE,
    ):
        self.account_id = account_id
        self.owner = owner
        self._balance = Decimal(str(balance))
        self.status = status

    @abstractmethod
    def deposit(self, amount):
        pass

    @abstractmethod
    def withdraw(self, amount):
        pass

    @abstractmethod
    def get_account_info(self):
        pass


class BankAccount(AbstractAccount):
    def __init__(
        self,
        owner: str,
        balance=0,
        account_id: str | None = None,
        status: AccountStatus = AccountStatus.ACTIVE,
        currency: Currency | str = Currency.RUB,
    ):
        if not isinstance(owner, str) or not owner.strip():
            raise ValueError("Owner must be a non-empty string")

        try:
            initial_balance = Decimal(str(balance))
        except Exception:
            raise ValueError("Balance must be a valid number")

        if initial_balance < 0:
            raise ValueError("Balance cannot be negative")

        if not isinstance(status, AccountStatus):
            raise ValueError("Invalid account status")

        if isinstance(currency, str):
            try:
                currency = Currency(currency.upper())
            except ValueError:
                raise ValueError("Unsupported currency")

        if not isinstance(currency, Currency):
            raise ValueError("Unsupported currency")

        if account_id is not None:
            if not isinstance(account_id, str) or not account_id.strip():
                raise ValueError("Account ID must be a non-empty string")

        super().__init__(
            owner=owner.strip(),
            balance=initial_balance,
            account_id=account_id or generate_account_id(),
            status=status,
        )

        self.currency = currency

    @property
    def balance(self) -> Decimal:
        return self._balance

    def _validate_operation_status(self):
        if self.status == AccountStatus.FROZEN:
            raise AccountFrozenError("Account is frozen")

        if self.status == AccountStatus.CLOSED:
            raise AccountClosedError("Account is closed")

        if self.status != AccountStatus.ACTIVE:
            raise InvalidOperationError("Operation is not allowed")

    def deposit(self, amount) -> Decimal:
        self._validate_operation_status()
        amount = validate_amount(amount)

        self._balance += amount
        return self._balance

    def withdraw(self, amount) -> Decimal:
        self._validate_operation_status()
        amount = validate_amount(amount)

        if amount > self._balance:
            raise InsufficientFundsError("Insufficient funds")

        self._balance -= amount
        return self._balance

    def get_account_info(self) -> dict:
        return {
            "type": self.__class__.__name__,
            "account_id": self.account_id,
            "owner": self.owner,
            "status": self.status.value,
            "balance": self._balance,
            "currency": self.currency.value,
        }

    def __str__(self) -> str:
        last_digits = self.account_id[-4:]

        return (
            f"{self.__class__.__name__} | "
            f"Client: {self.owner} | "
            f"Account: ****{last_digits} | "
            f"Status: {self.status.value} | "
            f"Balance: {self._balance:.2f} {self.currency.value}"
        )