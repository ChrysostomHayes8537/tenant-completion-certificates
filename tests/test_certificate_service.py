from certificate_service import Participant, issue_certificate


class FakeClient:
    def __init__(self):
        self.calls = []

    def generate_pdf(self, markdown, request_id):
        self.calls.append((markdown, request_id))
        return {"id": "pdf-1"}


def test_certificate_requires_admin_approval():
    client = FakeClient()
    participant = Participant("tenant-1", "p-1", "Ari", "a@example.test", True, True, False)
    assert issue_certificate(participant, client) is None
    assert client.calls == []


def test_approved_participant_gets_one_certificate_request():
    client = FakeClient()
    participant = Participant("tenant-1", "p-1", "Ari", "a@example.test", True, True, True)
    assert issue_certificate(participant, client) == {"id": "pdf-1"}
    assert client.calls[0][1] == "certificate:tenant-1:p-1"
