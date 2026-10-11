from bank import Bank
from client import Client
from models import AccountStatus, AccountFrozenError


def main():
    bank = Bank()

    client1 = Client(
        full_name="Alex Smith",
        age=25,
        contacts={
            "phone": "+10000000001",
            "email": "alex@example.com",
        },
    )

    client2 = Client(
        full_name="Maria Brown",
        age=31,
        contacts={
            "phone": "+10000000002",
            "email": "maria@example.com",
        },
    )

    client3 = Client(
        full_name="John White",
        age=40,
        contacts={
            "phone": "+10000000003",
            "email": "john@example.com",
        },
    )

    bank.add_client(client1, "alex123")
    bank.add_client(client2, "maria123")
    bank.add_client(client3, "john123")

    account1 = bank.open_account(
        client1.client_id,
        balance=10000,
        currency="RUB",
    )

    account2 = bank.open_account(
        client1.client_id,
        balance=5000,
        currency="RUB",
    )

    account3 = bank.open_account(
        client2.client_id,
        balance=20000,
        currency="RUB",
    )

    account4 = bank.open_account(
        client3.client_id,
        balance=3000,
        currency="RUB",
    )

    print(client1)
    print(client2)
    print(client3)

    print(bank.authenticate_client(client1.client_id, "alex123"))

    print(bank.authenticate_client(client2.client_id, "wrong"))
    print(bank.authenticate_client(client2.client_id, "wrong"))
    print(bank.authenticate_client(client2.client_id, "wrong"))

    print(client2)

    bank.freeze_account(account1.account_id)

    print(account1)

    try:
        account1.withdraw(1000)
    except AccountFrozenError as error:
        print(error)

    bank.unfreeze_account(account1.account_id)

    print(account1)

    active_accounts = bank.search_accounts(
        status=AccountStatus.ACTIVE,
    )

    for account in active_accounts:
        print(account)

    print(bank.get_total_balance())

    for client, total_balance in bank.get_clients_ranking():
        print(client.full_name, total_balance)


if __name__ == "__main__":
    main()