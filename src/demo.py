from datetime import datetime, timedelta
from decimal import Decimal

from audit import AuditLog
from audit_reports import AuditReports
from bank import Bank
from client import Client
from models import BankAccount
from risk import RiskAnalyzer
from secure_transaction_processor import SecureTransactionProcessor
from transaction import Transaction, TransactionStatus, TransactionType
from transaction_queue import TransactionQueue


class BankDemo:
    def __init__(self, audit_file: str | None = None):
        self.bank = Bank(
            time_provider=lambda: datetime(2026, 10, 11, 12, 0)
        )

        self.audit_log = AuditLog(audit_file)

        self.risk_analyzer = RiskAnalyzer(
            large_amount_threshold=50000,
            frequent_operations_limit=3,
            frequent_operations_window_minutes=60,
        )

        self.processor = SecureTransactionProcessor(
            audit_log=self.audit_log,
            risk_analyzer=self.risk_analyzer,
            external_fee_rate=0.01,
            max_retries=3,
        )

        self.queue = TransactionQueue()
        self.transactions = []
        self.queue_log = []
        self.execution_log = []

    def initialize(self):
        clients_data = [
            (
                "Alex Smith",
                25,
                {"phone": "+10000000001"},
                "alex123",
            ),
            (
                "Maria Brown",
                31,
                {"phone": "+10000000002"},
                "maria123",
            ),
            (
                "John White",
                40,
                {"phone": "+10000000003"},
                "john123",
            ),
            (
                "Anna Green",
                28,
                {"phone": "+10000000004"},
                "anna123",
            ),
            (
                "David Black",
                36,
                {"phone": "+10000000005"},
                "david123",
            ),
            (
                "Kate Wilson",
                29,
                {"phone": "+10000000006"},
                "kate123",
            ),
        ]

        for full_name, age, contacts, password in clients_data:
            client = Client(
                full_name=full_name,
                age=age,
                contacts=contacts,
            )

            self.bank.add_client(
                client,
                password,
            )

        balances = [
            200000,
            80000,
            150000,
            60000,
            100000,
            5000,
            180000,
            70000,
            120000,
            40000,
            90000,
            30000,
        ]

        clients = list(self.bank.clients.values())

        for index, balance in enumerate(balances):
            client = clients[index // 2]

            self.bank.open_account(
                client.client_id,
                account_class=BankAccount,
                balance=balance,
                currency="RUB",
            )

    def _create_transaction(
        self,
        sender,
        recipient,
        amount,
        created_at,
        transaction_type=TransactionType.INTERNAL,
    ) -> Transaction:
        transaction = Transaction(
            transaction_type,
            amount,
            "RUB",
            sender,
            recipient,
        )

        transaction.created_at = created_at
        self.transactions.append(transaction)

        return transaction

    def create_transactions(self):
        accounts = list(self.bank.accounts.values())

        base_time = datetime(
            2026,
            10,
            11,
            6,
            0,
        )

        for index in range(24):
            sender = accounts[index % len(accounts)]
            recipient = accounts[
                (index + 3) % len(accounts)
            ]

            transaction = self._create_transaction(
                sender=sender,
                recipient=recipient,
                amount=1000 + (index % 5) * 500,
                created_at=(
                    base_time
                    + timedelta(minutes=index * 70)
                ),
            )

            self.add_to_queue(transaction)

        error_sender = accounts[5]

        for index in range(6):
            recipient = accounts[
                (index + 6) % len(accounts)
            ]

            transaction = self._create_transaction(
                sender=error_sender,
                recipient=recipient,
                amount=40000,
                created_at=(
                    base_time
                    + timedelta(
                        hours=35 + index * 2
                    )
                ),
            )

            self.add_to_queue(transaction)

        suspicious_sender = accounts[0]

        for index in range(3):
            transaction = self._create_transaction(
                sender=suspicious_sender,
                recipient=accounts[index + 7],
                amount=60000,
                created_at=datetime(
                    2026,
                    10,
                    13,
                    12 + index,
                    0,
                ),
                transaction_type=TransactionType.EXTERNAL,
            )

            self.add_to_queue(transaction)

        for index in range(3):
            transaction = self._create_transaction(
                sender=suspicious_sender,
                recipient=accounts[index + 8],
                amount=60000,
                created_at=datetime(
                    2026,
                    10,
                    14,
                    1 + index,
                    0,
                ),
                transaction_type=TransactionType.EXTERNAL,
            )

            self.add_to_queue(transaction)

    def add_to_queue(
        self,
        transaction: Transaction,
        priority: int = 0,
    ):
        self.queue.add(
            transaction,
            priority=priority,
        )

        self.queue_log.append(
            {
                "transaction_id": transaction.transaction_id,
                "status": "queued",
            }
        )

    def execute(self):
        while True:
            transaction = self.queue.pop_ready(
                current_time=datetime(
                    2026,
                    10,
                    15,
                    12,
                    0,
                )
            )

            if transaction is None:
                break

            result = self.processor.process(
                transaction
            )

            self.execution_log.append(
                {
                    "transaction_id": result.transaction_id,
                    "status": result.status.value,
                    "reason": result.rejection_reason,
                }
            )

    def get_client_accounts(
        self,
        client_id: str,
    ) -> list:
        return self.bank.search_accounts(
            client_id=client_id
        )

    def get_client_history(
        self,
        client_id: str,
    ) -> list:
        client = self.bank.clients[client_id]
        account_ids = set(client.account_numbers)

        return [
            transaction
            for transaction in self.transactions
            if (
                transaction.sender.account_id in account_ids
                or transaction.recipient.account_id in account_ids
            )
        ]

    def get_suspicious_operations(self) -> list:
        reports = AuditReports(
            self.audit_log,
            self.risk_analyzer,
        )

        return reports.get_suspicious_operations()

    def get_top_clients(self) -> list:
        return self.bank.get_clients_ranking()[:3]

    def get_transaction_statistics(self) -> dict:
        statuses = {
            TransactionStatus.PENDING: 0,
            TransactionStatus.PROCESSING: 0,
            TransactionStatus.COMPLETED: 0,
            TransactionStatus.FAILED: 0,
            TransactionStatus.CANCELLED: 0,
        }

        for transaction in self.transactions:
            statuses[transaction.status] += 1

        return {
            "total": len(self.transactions),
            "completed": statuses[
                TransactionStatus.COMPLETED
            ],
            "failed": statuses[
                TransactionStatus.FAILED
            ],
            "cancelled": statuses[
                TransactionStatus.CANCELLED
            ],
        }

    def get_total_balance(self) -> Decimal:
        return self.bank.get_total_balance()