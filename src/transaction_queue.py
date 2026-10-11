from datetime import datetime

from transaction import Transaction, TransactionStatus


class TransactionQueue:
    def __init__(self):
        self._transactions = []

    def add(
        self,
        transaction: Transaction,
        priority: int = 0,
        execute_at: datetime | None = None,
    ):
        if not isinstance(transaction, Transaction):
            raise ValueError("Invalid transaction")

        if not isinstance(priority, int):
            raise ValueError("Priority must be an integer")

        if execute_at is not None and not isinstance(execute_at, datetime):
            raise ValueError("execute_at must be datetime")

        transaction.priority = priority
        transaction.scheduled_at = execute_at

        self._transactions.append(transaction)

    def cancel(self, transaction_id: str):
        for transaction in self._transactions:
            if transaction.transaction_id == transaction_id:
                if transaction.status != TransactionStatus.PENDING:
                    raise ValueError("Transaction cannot be cancelled")

                transaction.status = TransactionStatus.CANCELLED
                transaction.updated_at = datetime.now()
                return

        raise ValueError("Transaction not found")

    def pop_ready(
        self,
        current_time: datetime | None = None,
    ) -> Transaction | None:
        current_time = current_time or datetime.now()

        ready = [
            transaction
            for transaction in self._transactions
            if transaction.status == TransactionStatus.PENDING
            and (
                transaction.scheduled_at is None
                or transaction.scheduled_at <= current_time
            )
        ]

        if not ready:
            return None

        transaction = max(
            ready,
            key=lambda item: (
                item.priority,
                -item.created_at.timestamp(),
            ),
        )

        self._transactions.remove(transaction)
        return transaction

    def __len__(self):
        return len(self._transactions)