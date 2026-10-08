from account_types import (
    InvestmentAccount,
    PremiumAccount,
    SavingsAccount,
)
from models import InsufficientFundsError


def main():
    print("The 2nd day task")
    savings_account1 = SavingsAccount(
        owner="Alex",
        balance=10000,
        currency="RUB",
        min_balance=2000,
        monthly_interest_rate=0.01,
    )

    savings_account2 = SavingsAccount(
        owner="Maria",
        balance=5000,
        currency="USD",
        min_balance=1000,
        monthly_interest_rate=0.02,
    )

    savings_account1.withdraw(2000)
    savings_account1.apply_monthly_interest()

    print(savings_account1)
    print(savings_account2)

    try:
        savings_account2.withdraw(4500)
    except InsufficientFundsError as error:
        print(error)

    premium_account1 = PremiumAccount(
        owner="John",
        balance=5000,
        currency="EUR",
        overdraft_limit=10000,
        fixed_fee=100,
    )

    premium_account2 = PremiumAccount(
        owner="Anna",
        balance=20000,
        currency="RUB",
        overdraft_limit=50000,
        fixed_fee=200,
    )

    premium_account1.withdraw(7000)
    premium_account2.withdraw(5000)

    print(premium_account1)
    print(premium_account2)

    investment_account1 = InvestmentAccount(
        owner="David",
        balance=20000,
        currency="USD",
    )

    investment_account2 = InvestmentAccount(
        owner="Kate",
        balance=15000,
        currency="EUR",
    )

    investment_account1.invest("stocks", 5000)
    investment_account1.invest("bonds", 3000)
    investment_account1.invest("etf", 2000)

    investment_account2.invest("stocks", 4000)
    investment_account2.invest("etf", 3000)

    growth_rates = {
        "stocks": 0.10,
        "bonds": 0.04,
        "etf": 0.07,
    }

    print(investment_account1)
    print(investment_account2)

    print(
        investment_account1.project_yearly_growth(growth_rates)
    )
    print(
        investment_account2.project_yearly_growth(growth_rates)
    )


if __name__ == "__main__":
    main()