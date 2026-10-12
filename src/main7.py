from pathlib import Path

from demo import BankDemo
from report_builder import ReportBuilder


def main():
    demo = BankDemo()
    demo.initialize()
    demo.create_transactions()
    demo.execute()

    builder = ReportBuilder(demo)

    output_dir = Path(
        "reports_day7"
    )

    output_dir.mkdir(
        exist_ok=True
    )

    client = next(
        iter(demo.bank.clients.values())
    )

    client_report = (
        builder.build_client_report(
            client.client_id
        )
    )

    bank_report = (
        builder.build_bank_report()
    )

    risk_report = (
        builder.build_risk_report()
    )

    print("Client report")
    print(
        builder.build_text_report(
            client_report
        )
    )

    print("Bank report")
    print(
        builder.build_text_report(
            bank_report
        )
    )

    print("Risk report")
    print(
        builder.build_text_report(
            risk_report
        )
    )

    builder.export_to_json(
        client_report,
        str(
            output_dir
            / "client_report.json"
        ),
    )

    builder.export_to_csv(
        client_report,
        str(
            output_dir
            / "client_report.csv"
        ),
    )

    builder.export_to_json(
        bank_report,
        str(
            output_dir
            / "bank_report.json"
        ),
    )

    builder.export_to_csv(
        bank_report,
        str(
            output_dir
            / "bank_report.csv"
        ),
    )

    builder.export_to_json(
        risk_report,
        str(
            output_dir
            / "risk_report.json"
        ),
    )

    builder.export_to_csv(
        risk_report,
        str(
            output_dir
            / "risk_report.csv"
        ),
    )

    chart_files = builder.save_charts(
        str(output_dir),
        client.client_id,
    )

    for file_path in chart_files:
        print(file_path)


if __name__ == "__main__":
    main()