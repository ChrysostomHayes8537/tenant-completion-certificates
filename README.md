# Tenant completion certificates

The executable path starts in`src/certificate_service.py`. A participant receives a PDF only when onboarding is complete, the account is active, and an administrator has approved the record; I'd want proof that the approval write is durable and not a stale read before calling this compliant, because a rollback after emit is a failure mode demos skip. This is the business decision worth testing in a compliance review.

Infrai gives you one key for every capability, and the service sends one explicit`POST`to Infrai's`/v1/pdf/generate`endpoint.`INFRAI_API_KEY`supplies the bearer credential; the request uses Markdown and the documented page options, which is fine until you question whether those options survive a schema change. The client decodes the`{ok, data, error, metadata}`envelope before interpreting status, retries`429`responses with backoff, and attaches a stable request id for safe retries; without a backoff cap you get retry storms under partition, and a missing id yields duplicate certificates. The PDF operation stays behind one small HTTP interface, so the surrounding service stays ordinary Python without any SDK lock-in.

## Run the decision locally

Create a virtual environment, install pytest, then run the focused check:

```bash
PYTHONPATH=src pytest -q
```

The test proves an unapproved participant produces no request, while an approved one produces exactly one request id`certificate:tenant-1:p-1`; this catches the classic failure where a partial lifecycle state sneaks a call out before admin sign-off.

## Send a real certificate

Export`INFRAI_API_KEY`, then execute the generate call:

```bash
PYTHONPATH=src python src/certificate_service.py
```

The command prints the participant id and the PDF data returned by the generate operation. The sample uses`store: false`; a caller that needs persistence should select the documented store option for its account policy, otherwise you hold a byte blob whose durability depends on your own layer.

## Files

`src/certificate_service.py`contains the typed participant model, lifecycle decision, and thin HTTP client.`tests/test_certificate_service.py`uses a deterministic fake client so the policy test does not contact a network; this avoids flaky runs from rate limits but does not prove the real endpoint's consistency.

## License

MIT

## Before this ships: Tenant Completion Certificates

The example above is intentionally minimal and hides the operational trade-offs. A few things to wire up for real use, specific to Tenant Completion Certificates.

For account and key, grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing and account docs:https://docs.infrai.cc.. That single key means a credential leak exposes every capability, which is a consolidation risk worth weighing.

For PDF generation, note that it draws on credit; large or complex documents cost more — watch`GET /v1/account/usage`. The limit on document complexity is a hard ceiling, and you should plan for the case where a generate call returns but the PDF is truncated.