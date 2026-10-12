from demo import BankDemo


def main():
    demo = BankDemo(
        audit_file="audit_day6.log"
    )

    demo.initialize()

    print("Bank initialized")
    print("Clients:", len(demo.bank.clients))
    print("Accounts:", len(demo.bank.accounts))

    demo.create_transactions()

    print("Transactions queued:", len(demo.queue_log))

    for entry in demo.queue_log:
        print(
            entry["transaction_id"],
            entry["status"],
        )

    demo.execute()

    print("Execution results")

    for entry in demo.execution_log:
        print(
            entry["transaction_id"],
            entry["status"],
            entry["reason"],
        )

    client = list(
        demo.bank.clients.values()
    )[0]

    print("Client accounts")
    print(client.full_name)

    for account in demo.get_client_accounts(
        client.client_id
    ):
        print(account)

    print("Client history")

    for transaction in demo.get_client_history(
        client.client_id
    ):
        print(transaction)

    print("Suspicious operations")

    for operation in (
        demo.get_suspicious_operations()
    ):
        print(
            operation["transaction_id"],
            operation["event_type"],
            operation["data"],
        )

    print("Top 3 clients")

    for position, (
        ranked_client,
        balance,
    ) in enumerate(
        demo.get_top_clients(),
        start=1,
    ):
        print(
            position,
            ranked_client.full_name,
            balance,
        )

    print("Transaction statistics")

    statistics = (
        demo.get_transaction_statistics()
    )

    print(
        "Total:",
        statistics["total"],
    )
    print(
        "Completed:",
        statistics["completed"],
    )
    print(
        "Failed:",
        statistics["failed"],
    )
    print(
        "Cancelled:",
        statistics["cancelled"],
    )

    print(
        "Total bank balance:",
        demo.get_total_balance(),
    )


if __name__ == "__main__":
    main()