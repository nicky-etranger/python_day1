from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from uuid import uuid4

from models import BankAccount, Currency


class TransactionType(Enum):
    INTERNAL = "internal"
    EXTERNAL = "external"


class TransactionStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Transaction:
    def __init__(
        self,
        transaction_type: TransactionType,
        amount,
        currency: Currency | str,
        sender: BankAccount,
        recipient: BankAccount,
    ):
        if not isinstance(transaction_type, TransactionType):
            raise ValueError("Invalid transaction type")

        try:
            amount = Decimal(str(amount))
        except (InvalidOperation, ValueError, TypeError):
            raise ValueError("Amount must be a valid number")
        if not amount.is_finite():
            raise ValueError("Amount must be a finite number")
        if amount <= 0:
            raise ValueError("Amount must be greater than zero")

        if isinstance(currency, str):
            try:
                currency = Currency(currency.upper())
            except ValueError:
                raise ValueError("Unsupported currency")

        if not isinstance(currency, Currency):
            raise ValueError("Unsupported currency")

        if not isinstance(sender, BankAccount):
            raise ValueError("Invalid sender")

        if not isinstance(recipient, BankAccount):
            raise ValueError("Invalid recipient")

        if sender is recipient:
            raise ValueError("Sender and recipient must be different")

        self.transaction_id = uuid4().hex[:8]
        self.transaction_type = transaction_type
        self.amount = amount
        self.currency = currency
        self.commission = Decimal("0")
        self.sender = sender
        self.recipient = recipient
        self.status = TransactionStatus.PENDING
        self.rejection_reason = None
        self.attempts = 0
        self.errors = []
        self.priority = 0
        self.scheduled_at = None
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        self.completed_at = None

    def __str__(self) -> str:
        return (
            f"Transaction {self.transaction_id} | "
            f"Type: {self.transaction_type.value} | "
            f"Amount: {self.amount:.2f} {self.currency.value} | "
            f"Commission: {self.commission:.2f} | "
            f"Status: {self.status.value}"
        )