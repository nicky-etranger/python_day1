from decimal import Decimal, InvalidOperation
from uuid import uuid4


def generate_account_id() -> str:
    return uuid4().hex[:8]


def validate_amount(amount) -> Decimal:
    try:
        value = Decimal(str(amount))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("Amount must be a valid number")

    if value <= 0:
        raise ValueError("Amount must be greater than zero")

    return value