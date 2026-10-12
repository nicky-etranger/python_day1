import csv
import json
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from demo import BankDemo
from transaction import TransactionStatus


class ReportBuilder:
    def __init__(self, demo: BankDemo):
        if not isinstance(demo, BankDemo):
            raise ValueError("Invalid bank demo")

        self.demo = demo

    def build_client_report(self, client_id: str) -> dict:
        if client_id not in self.demo.bank.clients:
            raise ValueError("Client not found")

        client = self.demo.bank.clients[client_id]
        accounts = self.demo.get_client_accounts(client_id)
        history = self.demo.get_client_history(client_id)
        risk_profile = self.demo.risk_analyzer.get_client_risk_profile(
            client.full_name
        )

        return {
            "report_type": "client",
            "client_id": client.client_id,
            "full_name": client.full_name,
            "status": client.status.value,
            "contacts": client.contacts,
            "accounts": [
                {
                    "account_id": account.account_id,
                    "status": account.status.value,
                    "balance": account.balance,
                    "currency": account.currency.value,
                }
                for account in accounts
            ],
            "transactions": [
                {
                    "transaction_id": transaction.transaction_id,
                    "type": transaction.transaction_type.value,
                    "amount": transaction.amount,
                    "currency": transaction.currency.value,
                    "status": transaction.status.value,
                    "sender": transaction.sender.account_id,
                    "recipient": transaction.recipient.account_id,
                    "created_at": transaction.created_at,
                }
                for transaction in history
            ],
            "risk_profile": risk_profile,
        }

    def build_bank_report(self) -> dict:
        statistics = self.demo.get_transaction_statistics()

        return {
            "report_type": "bank",
            "clients_count": len(self.demo.bank.clients),
            "accounts_count": len(self.demo.bank.accounts),
            "total_balance": self.demo.get_total_balance(),
            "transaction_statistics": statistics,
            "top_clients": [
                {
                    "client_id": client.client_id,
                    "full_name": client.full_name,
                    "balance": balance,
                }
                for client, balance in self.demo.get_top_clients()
            ],
        }

    def build_risk_report(self) -> dict:
        suspicious = self.demo.get_suspicious_operations()

        clients = [
            self.demo.risk_analyzer.get_client_risk_profile(
                client.full_name
            )
            for client in self.demo.bank.clients.values()
        ]

        return {
            "report_type": "risk",
            "suspicious_operations": suspicious,
            "client_risk_profiles": clients,
        }

    def build_text_report(self, report: dict) -> str:
        lines = []

        for key, value in report.items():
            lines.append(
                f"{key}: {self._text_value(value)}"
            )

        return "\n".join(lines)

    def export_to_json(
        self,
        report: dict,
        file_path: str,
    ):
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(
                report,
                file,
                ensure_ascii=False,
                indent=2,
                default=self._json_default,
            )

    def export_to_csv(
        self,
        report: dict,
        file_path: str,
    ):
        row = {
            key: self._csv_value(value)
            for key, value in report.items()
        }

        with open(
            file_path,
            "w",
            encoding="utf-8",
            newline="",
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=row.keys(),
            )

            writer.writeheader()
            writer.writerow(row)

    def save_charts(
        self,
        output_dir: str,
        client_id: str | None = None,
    ) -> list:
        directory = Path(output_dir)
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        if client_id is None:
            client_id = next(
                iter(self.demo.bank.clients)
            )

        files = [
            self._save_status_pie(directory),
            self._save_clients_bar(directory),
            self._save_balance_line(
                directory,
                client_id,
            ),
        ]

        return files

    def _save_status_pie(
        self,
        directory: Path,
    ) -> str:
        statistics = (
            self.demo.get_transaction_statistics()
        )

        labels = [
            "Completed",
            "Failed",
            "Cancelled",
        ]

        values = [
            statistics["completed"],
            statistics["failed"],
            statistics["cancelled"],
        ]

        filtered = [
            (label, value)
            for label, value in zip(labels, values)
            if value > 0
        ]

        labels = [
            item[0]
            for item in filtered
        ]

        values = [
            item[1]
            for item in filtered
        ]

        figure, axis = plt.subplots()

        axis.pie(
            values,
            labels=labels,
            autopct="%1.1f%%",
        )

        axis.set_title(
            "Transaction statuses"
        )

        file_path = (
            directory
            / "transaction_statuses.png"
        )

        figure.savefig(
            file_path,
            bbox_inches="tight",
        )

        plt.close(figure)

        return str(file_path)

    def _save_clients_bar(
        self,
        directory: Path,
    ) -> str:
        ranking = (
            self.demo.bank.get_clients_ranking()
        )

        names = [
            client.full_name
            for client, _ in ranking
        ]

        balances = [
            float(balance)
            for _, balance in ranking
        ]

        figure, axis = plt.subplots()

        axis.bar(
            names,
            balances,
        )

        axis.set_title(
            "Client balances"
        )

        axis.set_ylabel(
            "Balance"
        )

        axis.tick_params(
            axis="x",
            rotation=45,
        )

        file_path = (
            directory
            / "client_balances.png"
        )

        figure.savefig(
            file_path,
            bbox_inches="tight",
        )

        plt.close(figure)

        return str(file_path)

    def _save_balance_line(
        self,
        directory: Path,
        client_id: str,
    ) -> str:
        accounts = self.demo.get_client_accounts(
            client_id
        )

        if not accounts:
            raise ValueError(
                "Client has no accounts"
            )

        account = accounts[0]

        transactions = sorted(
            [
                transaction
                for transaction
                in self.demo.transactions
                if (
                    transaction.status
                    == TransactionStatus.COMPLETED
                    and (
                        transaction.sender
                        is account
                        or transaction.recipient
                        is account
                    )
                )
            ],
            key=lambda transaction: (
                transaction.created_at
            ),
        )

        balances = self._reconstruct_balances(
            account,
            transactions,
        )

        figure, axis = plt.subplots()

        axis.plot(
            range(len(balances)),
            balances,
            marker="o",
        )

        axis.set_title(
            "Account balance movement"
        )

        axis.set_xlabel(
            "Operation"
        )

        axis.set_ylabel(
            f"Balance {account.currency.value}"
        )

        file_path = (
            directory
            / "balance_movement.png"
        )

        figure.savefig(
            file_path,
            bbox_inches="tight",
        )

        plt.close(figure)

        return str(file_path)

    def _reconstruct_balances(
        self,
        account,
        transactions,
    ) -> list:
        current_balance = account.balance
        reversed_balances = [
            current_balance
        ]

        for transaction in reversed(
            transactions
        ):
            if transaction.sender is account:
                current_balance += (
                    transaction.amount
                    + transaction.commission
                )

            if transaction.recipient is account:
                current_balance -= (
                    transaction.amount
                )

            reversed_balances.append(
                current_balance
            )

        return [
            float(balance)
            for balance
            in reversed(reversed_balances)
        ]

    def _text_value(self, value) -> str:
        if isinstance(value, Enum):
            return value.value

        if isinstance(value, Decimal):
            return str(value)

        if isinstance(value, datetime):
            return value.isoformat()

        if isinstance(value, list):
            return json.dumps(
                value,
                ensure_ascii=False,
                default=self._json_default,
            )

        if isinstance(value, dict):
            return json.dumps(
                value,
                ensure_ascii=False,
                default=self._json_default,
            )

        return str(value)

    def _csv_value(self, value):
        if isinstance(
            value,
            (list, dict),
        ):
            return json.dumps(
                value,
                ensure_ascii=False,
                default=self._json_default,
            )

        return self._text_value(value)

    def _json_default(self, value):
        if isinstance(value, Decimal):
            return str(value)

        if isinstance(value, Enum):
            return value.value

        if isinstance(value, datetime):
            return value.isoformat()

        raise TypeError(
            f"Unsupported value: {type(value)}"
        )