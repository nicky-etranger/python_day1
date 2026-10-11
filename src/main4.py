from account_types import PremiumAccount
from models import BankAccount
from transaction import Transaction, TransactionType
from transaction_processor import TransactionProcessor
from transaction_queue import TransactionQueue


def main():
    rub_sender = BankAccount(
        owner="Alex Smith",
        balance=100000,
        currency="RUB",
    )

    rub_recipient = BankAccount(
        owner="Maria Brown",
        balance=10000,
        currency="RUB",
    )

    usd_recipient = BankAccount(
        owner="John White",
        balance=1000,
        currency="USD",
    )

    premium_sender = PremiumAccount(
        owner="Anna Green",
        balance=1000,
        currency="RUB",
        overdraft_limit=10000,
        fixed_fee=100,
    )

    transactions = [
        Transaction(
            TransactionType.INTERNAL,
            1000,
            "RUB",
            rub_sender,
            rub_recipient,
        ),
        Transaction(
            TransactionType.EXTERNAL,
            2000,
            "RUB",
            rub_sender,
            rub_recipient,
        ),
        Transaction(
            TransactionType.INTERNAL,
            3000,
            "RUB",
            rub_sender,
            rub_recipient,
        ),
        Transaction(
            TransactionType.EXTERNAL,
            1500,
            "RUB",
            rub_sender,
            usd_recipient,
        ),
        Transaction(
            TransactionType.INTERNAL,
            500,
            "RUB",
            premium_sender,
            rub_recipient,
        ),
        Transaction(
            TransactionType.INTERNAL,
            1200,
            "RUB",
            premium_sender,
            rub_recipient,
        ),
        Transaction(
            TransactionType.INTERNAL,
            2500,
            "RUB",
            rub_sender,
            rub_recipient,
        ),
        Transaction(
            TransactionType.EXTERNAL,
            4000,
            "RUB",
            rub_sender,
            rub_recipient,
        ),
        Transaction(
            TransactionType.INTERNAL,
            3500,
            "RUB",
            rub_sender,
            rub_recipient,
        ),
        Transaction(
            TransactionType.EXTERNAL,
            1000,
            "RUB",
            rub_sender,
            usd_recipient,
        ),
    ]

    queue = TransactionQueue()

    for index, transaction in enumerate(transactions):
        queue.add(
            transaction,
            priority=index % 3,
        )

    processor = TransactionProcessor(
        exchange_rates={
            ("RUB", "USD"): 0.011,
        },
        external_fee_rate=0.01,
        max_retries=3,
    )

    processed = processor.process_queue(queue)

    for transaction in processed:
        print(transaction)


if __name__ == "__main__":
    main()