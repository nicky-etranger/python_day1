from enum import Enum
from uuid import uuid4


class ClientStatus(Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"


class Client:
    def __init__(
        self,
        full_name: str,
        age: int,
        contacts: dict,
        client_id: str | None = None,
        status: ClientStatus = ClientStatus.ACTIVE,
    ):
        if not isinstance(full_name, str) or not full_name.strip():
            raise ValueError("Full name must be a non-empty string")

        if not isinstance(age, int) or age < 18:
            raise ValueError("Client must be at least 18 years old")

        if not isinstance(contacts, dict):
            raise ValueError("Contacts must be a dictionary")

        if not isinstance(status, ClientStatus):
            raise ValueError("Invalid client status")

        self.full_name = full_name.strip()
        self.age = age
        self.contacts = contacts
        self.client_id = client_id or uuid4().hex[:8]
        self.status = status
        self.account_numbers = []
        self.suspicious_activity = False

    def __str__(self) -> str:
        return (
            f"Client: {self.full_name} | "
            f"ID: {self.client_id} | "
            f"Status: {self.status.value} | "
            f"Accounts: {len(self.account_numbers)}"
        )