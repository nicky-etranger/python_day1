import json
from datetime import datetime
from enum import Enum


class AuditLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLog:
    def __init__(self, file_path: str | None = None):
        self.entries = []
        self.file_path = file_path

    def log(
        self,
        level: AuditLevel,
        event_type: str,
        message: str,
        transaction_id: str | None = None,
        client: str | None = None,
        data: dict | None = None,
    ) -> dict:
        if not isinstance(level, AuditLevel):
            raise ValueError("Invalid audit level")

        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level.value,
            "event_type": event_type,
            "message": message,
            "transaction_id": transaction_id,
            "client": client,
            "data": data or {},
        }

        self.entries.append(entry)

        if self.file_path is not None:
            with open(self.file_path, "a", encoding="utf-8") as file:
                file.write(
                    json.dumps(
                        entry,
                        ensure_ascii=False,
                    )
                    + "\n"
                )

        return entry

    def filter(
        self,
        level: AuditLevel | None = None,
        event_type: str | None = None,
        transaction_id: str | None = None,
        client: str | None = None,
    ) -> list:
        result = []

        for entry in self.entries:
            if level is not None and entry["level"] != level.value:
                continue

            if (
                event_type is not None
                and entry["event_type"] != event_type
            ):
                continue

            if (
                transaction_id is not None
                and entry["transaction_id"] != transaction_id
            ):
                continue

            if client is not None and entry["client"] != client:
                continue

            result.append(entry)

        return result