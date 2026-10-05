from models import (
    AccountFrozenError,
    AccountStatus,
    BankAccount,
)


def main():
    active_account = BankAccount(
        owner="Alex",
        balance=1000,
        currency="RUB",
    )

    frozen_account = BankAccount(
        owner="Maria",
        balance=500,
        currency="USD",
        status=AccountStatus.FROZEN,
    )

    print(active_account)
    print(frozen_account)

    active_account.deposit(500)
    active_account.withdraw(200)

    print(active_account)

    try:
        frozen_account.deposit(100)
    except AccountFrozenError as error:
        print(error)

    try:
        frozen_account.withdraw(100)
    except AccountFrozenError as error:
        print(error)


if __name__ == "__main__":
    main()