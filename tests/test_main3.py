import sys
import unittest
from datetime import datetime
from decimal import Decimal
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from bank import Bank
from client import Client, ClientStatus
from models import (
    AccountFrozenError,
    AccountStatus,
    InvalidOperationError,
)


class TestClient(unittest.TestCase):
    def test_create_client(self):
        client = Client(
            full_name="Alex Smith",
            age=25,
            contacts={"phone": "+10000000001"},
        )

        self.assertEqual(client.full_name, "Alex Smith")
        self.assertEqual(client.status, ClientStatus.ACTIVE)
        self.assertEqual(client.account_numbers, [])
        self.assertEqual(len(client.client_id), 8)

    def test_client_must_be_adult(self):
        with self.assertRaises(ValueError):
            Client(
                full_name="Alex Smith",
                age=17,
                contacts={"phone": "+10000000001"},
            )


class TestBank(unittest.TestCase):
    def setUp(self):
        self.bank = Bank(
            time_provider=lambda: datetime(2026, 10, 8, 12, 0)
        )

        self.client1 = Client(
            full_name="Alex Smith",
            age=25,
            contacts={"phone": "+10000000001"},
        )

        self.client2 = Client(
            full_name="Maria Brown",
            age=30,
            contacts={"phone": "+10000000002"},
        )

        self.bank.add_client(self.client1, "alex123")
        self.bank.add_client(self.client2, "maria123")

    def test_add_client(self):
        self.assertIn(
            self.client1.client_id,
            self.bank.clients,
        )

    def test_open_account(self):
        account = self.bank.open_account(
            self.client1.client_id,
            balance=10000,
            currency="RUB",
        )

        self.assertIn(
            account.account_id,
            self.bank.accounts,
        )
        self.assertIn(
            account.account_id,
            self.client1.account_numbers,
        )

    def test_close_account(self):
        account = self.bank.open_account(
            self.client1.client_id,
            balance=10000,
        )

        self.bank.close_account(account.account_id)

        self.assertEqual(
            account.status,
            AccountStatus.CLOSED,
        )

    def test_freeze_account(self):
        account = self.bank.open_account(
            self.client1.client_id,
            balance=10000,
        )

        self.bank.freeze_account(account.account_id)

        self.assertEqual(
            account.status,
            AccountStatus.FROZEN,
        )

        with self.assertRaises(AccountFrozenError):
            account.withdraw(100)

    def test_unfreeze_account(self):
        account = self.bank.open_account(
            self.client1.client_id,
            balance=10000,
        )

        self.bank.freeze_account(account.account_id)
        self.bank.unfreeze_account(account.account_id)

        self.assertEqual(
            account.status,
            AccountStatus.ACTIVE,
        )

    def test_successful_authentication(self):
        result = self.bank.authenticate_client(
            self.client1.client_id,
            "alex123",
        )

        self.assertTrue(result)

    def test_failed_authentication(self):
        result = self.bank.authenticate_client(
            self.client1.client_id,
            "wrong",
        )

        self.assertFalse(result)
        self.assertTrue(
            self.client1.suspicious_activity
        )

    def test_three_failed_attempts_block_client(self):
        self.bank.authenticate_client(
            self.client1.client_id,
            "wrong1",
        )
        self.bank.authenticate_client(
            self.client1.client_id,
            "wrong2",
        )
        self.bank.authenticate_client(
            self.client1.client_id,
            "wrong3",
        )

        self.assertEqual(
            self.client1.status,
            ClientStatus.BLOCKED,
        )

        self.assertFalse(
            self.bank.authenticate_client(
                self.client1.client_id,
                "alex123",
            )
        )

    def test_successful_login_resets_attempts(self):
        self.bank.authenticate_client(
            self.client1.client_id,
            "wrong",
        )
        self.bank.authenticate_client(
            self.client1.client_id,
            "wrong",
        )

        self.bank.authenticate_client(
            self.client1.client_id,
            "alex123",
        )

        self.bank.authenticate_client(
            self.client1.client_id,
            "wrong",
        )

        self.assertEqual(
            self.client1.status,
            ClientStatus.ACTIVE,
        )

    def test_search_accounts_by_client(self):
        account1 = self.bank.open_account(
            self.client1.client_id,
            balance=10000,
        )

        self.bank.open_account(
            self.client2.client_id,
            balance=5000,
        )

        result = self.bank.search_accounts(
            client_id=self.client1.client_id,
        )

        self.assertEqual(result, [account1])

    def test_search_accounts_by_status(self):
        account1 = self.bank.open_account(
            self.client1.client_id,
            balance=10000,
        )

        self.bank.open_account(
            self.client2.client_id,
            balance=5000,
        )

        self.bank.freeze_account(account1.account_id)

        result = self.bank.search_accounts(
            status=AccountStatus.FROZEN,
        )

        self.assertEqual(result, [account1])

    def test_get_total_balance(self):
        self.bank.open_account(
            self.client1.client_id,
            balance=10000,
        )

        self.bank.open_account(
            self.client2.client_id,
            balance=5000,
        )

        total = self.bank.get_total_balance()

        self.assertEqual(
            total,
            Decimal("15000"),
        )

    def test_clients_ranking(self):
        self.bank.open_account(
            self.client1.client_id,
            balance=5000,
        )

        self.bank.open_account(
            self.client1.client_id,
            balance=10000,
        )

        self.bank.open_account(
            self.client2.client_id,
            balance=7000,
        )

        ranking = self.bank.get_clients_ranking()

        self.assertEqual(
            ranking[0][0],
            self.client1,
        )
        self.assertEqual(
            ranking[0][1],
            Decimal("15000"),
        )
        self.assertEqual(
            ranking[1][0],
            self.client2,
        )

    def test_operations_forbidden_at_night(self):
        bank = Bank(
            time_provider=lambda: datetime(
                2026,
                10,
                8,
                2,
                30,
            )
        )

        client = Client(
            full_name="John White",
            age=25,
            contacts={"phone": "+10000000003"},
        )

        bank.add_client(client, "john123")

        with self.assertRaises(
            InvalidOperationError
        ):
            bank.open_account(
                client.client_id,
                balance=1000,
            )
    def test_duplicate_account_id(self):
        account = self.bank.open_account(
            self.client1.client_id,
            account_id="account1",
            balance=1000,
        )

        with self.assertRaises(ValueError):
            self.bank.open_account(
                self.client2.client_id,
                account_id="account1",
                balance=5000,
            )

        self.assertIs(
            self.bank.accounts["account1"],
            account,
        )

        self.assertNotIn(
            "account1",
            self.client2.account_numbers,
        )

        self.assertEqual(
            self.bank.search_accounts(
                client_id=self.client1.client_id
            ),
            [account],
        )


if __name__ == "__main__":
    unittest.main()