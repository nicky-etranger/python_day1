from datetime import datetime
from decimal import Decimal, InvalidOperation

from account_types import PremiumAccount
from models import (
    AccountStatus,
    InsufficientFundsError,
    InvalidOperationError,
)
from transaction import (
    Transaction,
    TransactionStatus,
    TransactionType,
)
from transaction_queue import TransactionQueue


class TransactionProcessor:
    def __init__(
        self,
        exchange_rates: dict | None = None,
        external_fee_rate=0.01,
        max_retries=3,
    ):
        self.exchange_rates = exchange_rates or {}

        try:
            self.external_fee_rate = Decimal(
                str(external_fee_rate)
            )
        except (InvalidOperation, ValueError, TypeError):
            raise ValueError(
                "External fee rate must be a valid number"
            )

        if self.external_fee_rate < 0:
            raise ValueError(
                "External fee rate cannot be negative"
            )

        if not isinstance(max_retries, int) or max_retries < 1:
            raise ValueError(
                "Max retries must be a positive integer"
            )

        self.max_retries = max_retries

    def _get_exchange_rate(
        self,
        source_currency,
        target_currency,
    ) -> Decimal:
        if source_currency == target_currency:
            return Decimal("1")

        key = (
            source_currency.value,
            target_currency.value,
        )

        if key not in self.exchange_rates:
            raise InvalidOperationError(
                "Exchange rate is not available"
            )

        try:
            rate = Decimal(str(self.exchange_rates[key]))
        except (InvalidOperation, ValueError, TypeError):
            raise ValueError(
                "Exchange rate must be a valid number"
            )

        if rate <= 0:
            raise ValueError(
                "Exchange rate must be greater than zero"
            )

        return rate

    def _calculate_commission(
        self,
        transaction: Transaction,
    ) -> Decimal:
        if transaction.transaction_type == TransactionType.EXTERNAL:
            return transaction.amount * self.external_fee_rate

        return Decimal("0")

    def _validate_accounts(
        self,
        transaction: Transaction,
    ):
        sender = transaction.sender
        recipient = transaction.recipient

        if sender.status == AccountStatus.FROZEN:
            raise InvalidOperationError(
                "Sender account is frozen"
            )

        if recipient.status == AccountStatus.FROZEN:
            raise InvalidOperationError(
                "Recipient account is frozen"
            )

        if sender.status == AccountStatus.CLOSED:
            raise InvalidOperationError(
                "Sender account is closed"
            )

        if recipient.status == AccountStatus.CLOSED:
            raise InvalidOperationError(
                "Recipient account is closed"
            )

        if transaction.currency != sender.currency:
            raise InvalidOperationError(
                "Transaction currency must match sender currency"
            )

    def _execute(self, transaction: Transaction):
        self._validate_accounts(transaction)

        commission = self._calculate_commission(transaction)
        transaction.commission = commission

        total_debit = transaction.amount + commission

        if not isinstance(transaction.sender, PremiumAccount):
            if total_debit > transaction.sender.balance:
                raise InsufficientFundsError(
                    "Insufficient funds"
                )

        rate = self._get_exchange_rate(
            transaction.currency,
            transaction.recipient.currency,
        )

        recipient_amount = transaction.amount * rate

        transaction.sender.withdraw(total_debit)
        transaction.recipient.deposit(recipient_amount)

    def process(
        self,
        transaction: Transaction,
    ) -> Transaction:
        if transaction.status != TransactionStatus.PENDING:
            raise InvalidOperationError(
                "Transaction is not pending"
            )

        transaction.status = TransactionStatus.PROCESSING
        transaction.updated_at = datetime.now()

        for attempt in range(1, self.max_retries + 1):
            transaction.attempts = attempt

            try:
                self._execute(transaction)

                transaction.status = TransactionStatus.COMPLETED
                transaction.rejection_reason = None
                transaction.completed_at = datetime.now()
                transaction.updated_at = transaction.completed_at

                return transaction

            except Exception as error:
                transaction.errors.append(str(error))

                if attempt == self.max_retries:
                    transaction.status = TransactionStatus.FAILED
                    transaction.rejection_reason = str(error)
                    transaction.updated_at = datetime.now()

                    return transaction

        return transaction

    def process_queue(
        self,
        queue: TransactionQueue,
        current_time: datetime | None = None,
    ) -> list:
        processed = []

        while True:
            transaction = queue.pop_ready(current_time)

            if transaction is None:
                break

            processed.append(
                self.process(transaction)
            )

        return processed