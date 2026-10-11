from collections import Counter

from audit import AuditLog
from risk import RiskAnalyzer


class AuditReports:
    def __init__(
        self,
        audit_log: AuditLog,
        risk_analyzer: RiskAnalyzer,
    ):
        self.audit_log = audit_log
        self.risk_analyzer = risk_analyzer

    def get_suspicious_operations(self) -> list:
        return [
            entry
            for entry in self.audit_log.entries
            if entry["event_type"]
            in {"risk_detected", "risk_blocked"}
        ]

    def get_client_risk_profile(
        self,
        client: str,
    ) -> dict:
        return self.risk_analyzer.get_client_risk_profile(
            client
        )

    def get_error_statistics(self) -> dict:
        errors = self.audit_log.filter(
            event_type="transaction_failed"
        )

        blocked = self.audit_log.filter(
            event_type="risk_blocked"
        )

        reasons = Counter()

        for entry in errors:
            reason = entry["data"].get("reason")

            if reason is not None:
                reasons[reason] += 1

        return {
            "transaction_errors": len(errors),
            "blocked_operations": len(blocked),
            "total_errors": len(errors) + len(blocked),
            "reasons": dict(reasons),
        }