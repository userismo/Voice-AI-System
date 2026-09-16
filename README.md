# Voice AI Patient Registration

Take-home technical assessment implementation for a conversational patient-registration system.

## What it does

A caller dials a U.S. number attached to a Vapi voice assistant. The assistant naturally collects required patient demographics, handles corrections and invalid values, reads the complete record back, asks for explicit confirmation, and then calls this FastAPI service to persist the patient. The REST API can list, retrieve, create, update, and soft-delete records.

> Demo only. Do **not** use real patient data. This project is not intended to be HIPAA-compliant.

## Architecture

```text
Caller
  |
  v
Vapi U.S. phone number
  |
  v
Vapi Assistant (STT + LLM + TTS)
  |
  | function tools over HTTPS
  v
FastAPI  ----->  PostgreSQL (deployment)
  |
  +----------->  SQLite (simple local development)
```

Separation of concerns:
- **Telephony / speech:** Vapi
- **Conversation / prompt:** Vapi assistant system prompt
- **Business validation:** Pydantic + FastAPI
- **Persistence:** SQLAlchemy
- **Public service:** REST endpoints plus Vapi tool webhook

## Required endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/patients` | List active patients; filters: `last_name`, `date_of_birth`, `phone_number` |
| GET | `/patients/{id}` | Retrieve one active patient |
| POST | `/patients` | Create a patient |
| PUT | `/patients/{id}` | Partial update |
| DELETE | `/patients/{id}` | Soft delete (`deleted_at`) |

All successful REST responses use:

```json
{"data": {}, "error": null}
```

Validation errors use a matching error envelope.

## Patient validation

The API independently validates caller-controlled values instead of trusting the voice agent. It checks:
- first/last names
- DOB is a real date and not in the future
- allowed sex values
- 10-digit U.S. phone numbers
- valid email format when supplied
- valid U.S. state abbreviation
- ZIP / ZIP+4 format
- emergency phone when supplied

## Quick local setup

Requirements: Python 3.11+.

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

macOS/Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open:
- API docs: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`

SQLite is used by default and writes `patients.db`, so local records survive app restarts.

## Run tests

```bash
pytest -q
```

## Deploy the API

For a reviewable deployment, use a persistent PostgreSQL database. Railway is convenient because the app and Postgres can live in the same project; Render/Supabase/Postgres is also fine.

### Generic Docker deployment

1. Create a PostgreSQL database.
2. Deploy this repository using the included `Dockerfile`.
3. Set environment variable:

```text
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DATABASE
```

4. Confirm these work publicly:

```text
https://YOUR-DOMAIN/health
https://YOUR-DOMAIN/docs
https://YOUR-DOMAIN/patients
```

5. Run the smoke test:

```bash
python scripts/smoke_check.py https://YOUR-DOMAIN
```

## Configure Vapi

### 1. Create the assistant

In Vapi, create an assistant. Copy the full contents of `config/vapi_system_prompt.txt` into the assistant's system prompt.

A low-latency conversational model is appropriate. The exact provider/model can be changed without changing this backend.

### 2. Add the tools

Create three function/custom tools:

1. `save_patient`
2. `lookup_patient_by_phone`
3. `update_patient`

The definitions are in `config/vapi_tools.json`.

Before copying them into Vapi, replace every:

```text
https://YOUR-DOMAIN.example/vapi/tools
```

with the real deployed endpoint, for example:

```text
https://voice-patient-production.up.railway.app/vapi/tools
```

Vapi function tools send the tool request to this endpoint. The endpoint responds with the Vapi `results` format and the assistant can tell the caller whether the write succeeded.

### 3. Create the U.S. number

In the Vapi dashboard:

1. Open **Phone Numbers**.
2. Choose **Create Phone Number**.
3. Choose the available Vapi U.S. number option.
4. Enter a 3-digit U.S. area code.
5. Attach the patient-registration assistant to the number under inbound settings.
6. Save and call the number to test it.

Do not use your personal German number for the assessment.

### 4. Test the conversation

Use fictional data, for example:

```text
Jane Doe
04/15/1990
Female
415-555-1212
100 Market Street
San Francisco, CA 94105
```

Test at least:
- normal registration
- caller corrects a misspelled last name
- future DOB -> agent re-prompts
- 3-digit phone -> agent re-prompts
- caller gives fields out of order
- caller declines optional fields
- tool/database failure -> agent does not claim success
- second call -> old data still exists
- duplicate phone -> agent offers update (bonus)

## Vapi tool endpoint

Vapi sends tool calls to:

```text
POST /vapi/tools
```

Supported tools:
- `save_patient`
- `lookup_patient_by_phone`
- `update_patient`

The endpoint is deliberately defensive about incoming tool-call nesting and always validates the final payload with the same server-side schema used by the REST API.

## Observability

The service logs successful final patient payloads on save/update and logs database/tool errors. In a real healthcare deployment, logging would need stricter PHI controls; here it is included to satisfy the technical assessment's observability requirement using fictional demo data only.

## Security

- no API keys are hardcoded
- `.env` is ignored by Git
- all patient inputs are validated server-side
- SQLAlchemy parameterizes database queries
- Vapi server authentication can be added with a Vapi custom credential / bearer token for production-hardening

## Trade-offs / known limitations

- This is a take-home demo, not a HIPAA-ready application.
- Tables are auto-created at startup instead of using Alembic migrations to keep the setup small and fast.
- U.S. validation is intentionally lightweight; it does not perform carrier/address verification.
- SQLite is appropriate for local development, but a public deployment should use PostgreSQL for reliable persistence across container replacements.
- Vapi tool payload formats can evolve; the webhook parser is tolerant of common nesting, but the integration should be smoke-tested after configuring the live assistant.
- No authentication is enabled on the public CRUD endpoints for evaluator convenience. A real system would add authentication/authorization and audit controls.

## Optional features included

- duplicate lookup by phone number
- update workflow support
- soft delete
- automated validation/API tests
- Swagger/OpenAPI documentation

## Next steps

With more time:
- authenticate Vapi requests and CRUD endpoints
- add Alembic migrations
- store call transcript/summary linked to patient
- add appointment scheduling
- add a small dashboard
- add Spanish conversation mode
- add retry/idempotency protection for repeated tool calls

## Submission checklist

Before submitting:

- [ ] repository pushed to GitHub/GitLab
- [ ] API deployed and `/health` works
- [ ] persistent PostgreSQL configured
- [ ] Vapi tools point to `/vapi/tools`
- [ ] U.S. number attached to the correct assistant
- [ ] successful phone registration tested end-to-end
- [ ] saved patient visible from `GET /patients`
- [ ] second call does not erase the first patient
- [ ] README contains final phone number and API URL
- [ ] `.env` / secrets are not committed

Then send:
- repository URL
- phone number
- API base URL
- any testing notes/credentials

See `SUBMISSION_TEMPLATE.md` for a ready-to-send message.
