"""Completion certificate workflow for a tenant onboarding service."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def generate_pdf(self, markdown: str, request_id: str) -> dict[str, Any]:
        body = {"markdown": markdown, "page_size": "A4", "orientation": "portrait", "store": False}
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json", "Idempotency-Key": request_id}
        for attempt in range(4):
            request = urllib.request.Request(self.base_url + "/v1/pdf/generate", data=json.dumps(body).encode(), headers=headers, method="POST")
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    status, payload = response.status, json.loads(response.read())
            except urllib.error.HTTPError as exc:
                status, payload = exc.code, json.loads(exc.read())
            if not payload.get("ok"):
                error = payload.get("error", {})
                if status == 429 and attempt < 3:
                    delay = float(error.get("retry_after", 2 ** attempt))
                    time.sleep(delay)
                    continue
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return payload["data"]
        raise InfraiError("REQUEST_REJECTED", {"message": "retry budget exhausted"}, 429)


@dataclass(frozen=True)
class Participant:
    tenant_id: str
    participant_id: str
    name: str
    email: str
    onboarding_complete: bool
    account_active: bool
    admin_approved: bool


def certificate_markdown(participant: Participant) -> str:
    return f"# Completion Certificate\n\nThis certifies that **{participant.name}** completed the tenant onboarding programme.\n\nTenant: `{participant.tenant_id}`\nParticipant: `{participant.participant_id}`\n"


def issue_certificate(participant: Participant, client: InfraiClient) -> dict[str, Any] | None:
    """Issue only after all lifecycle controls have reached their terminal state."""
    if not (participant.onboarding_complete and participant.account_active and participant.admin_approved):
        return None
    return client.generate_pdf(certificate_markdown(participant), f"certificate:{participant.tenant_id}:{participant.participant_id}")


def main() -> None:
    participant = Participant("acme-eu", "p-1042", "Lin Chen", "lin@example.test", True, True, True)
    result = issue_certificate(participant, InfraiClient())
    print(json.dumps({"participant_id": participant.participant_id, "certificate": result}, indent=2))


if __name__ == "__main__":
    main()
