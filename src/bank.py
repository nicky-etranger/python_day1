from datetime import datetime
from decimal import Decimal

from client import Client, ClientStatus
from models import (
    AccountStatus,
    BankAccount,
    Currency,
    InvalidOperationError,
)


class Bank:
    def __init__(self, time_provider=datetime.now):
        self.clients = {}
        self.accounts = {}
        self._credentials = {}
        self._failed_attempts = {}
        self._time_provider = time_provider

    def _get_client(self, client_id: str) -> Client:
        if client_id not in self.clients:
            raise ValueError("Client not found")

        return self.clients[client_id]

    def _get_account(self, account_id: str) -> BankAccount:
        if account_id not in self.accounts:
            raise ValueError("Account not found")

        return self.accounts[account_id]

    def _check_operation_time(self):
        current_hour = self._time_provider().hour

        if 0 <= current_hour < 5:
            raise InvalidOperationError(
                "Operations are not allowed from 00:00 to 05:00"
            )

    def add_client(self, client: Client, password: str):
        if not isinstance(client, Client):
            raise ValueError("Invalid client")

        if client.client_id in self.clients:
            raise ValueError("Client already exists")

        if not isinstance(password, str) or not password:
            raise ValueError("Password must be a non-empty string")

        self.clients[client.client_id] = client
        self._credentials[client.client_id] = password
        self._failed_attempts[client.client_id] = 0

        return client

    def open_account(
        self,
        client_id: str,
        account_class=BankAccount,
        **account_data,
    ) -> BankAccount:
        self._check_operation_time()
        client = self._get_client(client_id)

        account = account_class(
            owner=client.full_name,
            **account_data,
        )

        self.accounts[account.account_id] = account
        client.account_numbers.append(account.account_id)

        return account

    def close_account(self, account_id: str):
        self._check_operation_time()
        account = self._get_account(account_id)

        if account.status == AccountStatus.CLOSED:
            raise InvalidOperationError("Account is already closed")

        account.status = AccountStatus.CLOSED

    def freeze_account(self, account_id: str):
        self._check_operation_time()
        account = self._get_account(account_id)

        if account.status == AccountStatus.CLOSED:
            raise InvalidOperationError("Closed account cannot be frozen")

        account.status = AccountStatus.FROZEN

    def unfreeze_account(self, account_id: str):
        self._check_operation_time()
        account = self._get_account(account_id)

        if account.status == AccountStatus.CLOSED:
            raise InvalidOperationError("Closed account cannot be unfrozen")

        if account.status != AccountStatus.FROZEN:
            raise InvalidOperationError("Account is not frozen")

        account.status = AccountStatus.ACTIVE

    def authenticate_client(
        self,
        client_id: str,
        password: str,
    ) -> bool:
        client = self._get_client(client_id)

        if client.status == ClientStatus.BLOCKED:
            return False

        if self._credentials[client_id] == password:
            self._failed_attempts[client_id] = 0
            return True

        self._failed_attempts[client_id] += 1
        client.suspicious_activity = True

        if self._failed_attempts[client_id] >= 3:
            client.status = ClientStatus.BLOCKED

        return False

    def search_accounts(
        self,
        client_id: str | None = None,
        status: AccountStatus | None = None,
        currency: Currency | str | None = None,
    ) -> list:
        if isinstance(currency, str):
            currency = Currency(currency.upper())

        account_ids = None

        if client_id is not None:
            client = self._get_client(client_id)
            account_ids = set(client.account_numbers)

        result = []

        for account in self.accounts.values():
            if account_ids is not None:
                if account.account_id not in account_ids:
                    continue

            if status is not None and account.status != status:
                continue

            if currency is not None and account.currency != currency:
                continue

            result.append(account)

        return result

    def get_total_balance(self) -> Decimal:
        return sum(
            (account.balance for account in self.accounts.values()),
            Decimal("0"),
        )

    def get_clients_ranking(self) -> list:
        ranking = []

        for client in self.clients.values():
            total_balance = sum(
                (
                    self.accounts[account_id].balance
                    for account_id in client.account_numbers
                ),
                Decimal("0"),
            )

            ranking.append((client, total_balance))

        return sorted(
            ranking,
            key=lambda item: item[1],
            reverse=True,
        )