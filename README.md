# SadaDost — PayWallet Support AI

A grounded, safe customer-support chatbot. Given a logged-in customer and a question, it
replies **only** from approved help-center content (`materials/knowledge.md`) and that
customer's **safe** account data (`materials/customers.json`) — never inventing policy and
never leaking restricted data (CNIC, card number, IBAN).

- **Backend:** FastAPI + OpenAI, with **OpenAI Guardrails** (moderation, jailbreak, PII) plus a
  deterministic PII floor.
- **Frontend:** React + Vite, SadaDost branding and animations.

See `DECISIONS.md` for the reasoning behind every meaningful choice, and `specs/` for the
spec → plan → tasks breakdown.

---

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | **3.11+** | `openai-guardrails` requires ≥3.11. This repo uses 3.12. |
| Node.js | 18+ | For the Vite frontend (developed on Node 22). |
| OpenAI API key | — | Needed for the LLM + guardrails. |

---

## 1. Backend

From the repo root:

```bash
# create the virtual environment (Python 3.12)
python3.12 -m venv venv
source venv/bin/activate

# install dependencies
pip install -r requirements.txt

# add your OpenAI key
cp .env.example .env
# then edit .env and set OPENAI_API_KEY=sk-...
```

Run the API:

```bash
source venv/bin/activate
uvicorn backend.app.main:app --port 8000 --reload
```

The API is now at `http://localhost:8000` (interactive docs at `/docs`).

### Endpoints

| Method | Path | Body | Returns |
|--------|------|------|---------|
| `GET`  | `/customers` | — | `[{ id, firstName }]` for the login dropdown |
| `POST` | `/chat` | `{ "customer_id": "cust_001", "message": "..." }` | `{ customer_id, intent, reply, pii_redacted, guardrail_blocked }` |

Quick test:

```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"cust_001","message":"how do I freeze my card?"}'
```

---

## 2. Frontend

In a second terminal:

```bash
cd frontend
npm install

# (optional) point at a non-default backend URL
cp .env.example .env        # VITE_API_URL=http://localhost:8000

npm run dev                 # http://localhost:5173
```

Open `http://localhost:5173`, pick a customer from the dropdown, and chat.
Bot replies show small chips for the detected **intent** and whether **PII was redacted**.

---

## Configuration (`.env` at repo root)

| Variable | Default | Purpose |
|----------|---------|---------|
| `OPENAI_API_KEY` | — | Required. OpenAI key for the LLM and guardrails. |
| `OPENAI_MODEL` | `gpt-4o-mini` | Chat + classification model. |
| `MATERIALS_DIR` | `./materials` | Where `knowledge.md` / `customers.json` live. |
| `GUARDRAILS_CONFIG` | `./guardrails_config.json` | OpenAI Guardrails pipeline config. |

---

## How it works (pipeline)

```
login(customer_id)  ->  load ONLY that customer (safe context; restricted kept server-side)
question
  -> intent classify (plain LLM call):  general | account | out_of_scope
  -> build grounding context:
        general      -> approved knowledge.md
        account      -> this customer's SAFE fields only
        out_of_scope -> none (polite decline, no invention)
  -> LLM phrasing through OpenAI Guardrails (moderation, jailbreak, PII)
  -> deterministic PII floor (regex + exact-match scrub)
  -> reply
```

**Safety guarantees that do not depend on the model:**
1. Restricted fields are never placed in any prompt (structural isolation).
2. Every reply is scrubbed for CNIC / IBAN / card numbers before it is returned.

---

## Project structure

```
SadaDost/
├── materials/                # given: knowledge.md, customers.json, questions.txt
├── backend/app/
│   ├── config.py             # env + paths
│   ├── data.py               # KB loader + single-customer scoping (safe/restricted split)
│   ├── intent.py             # LLM intent classification
│   ├── llm.py                # plain() + guarded() OpenAI calls
│   ├── safety.py             # deterministic PII floor
│   ├── chat.py               # orchestration pipeline
│   └── main.py               # FastAPI endpoints
├── frontend/                 # React + Vite (SadaDost UI)
├── guardrails_config.json    # OpenAI Guardrails pipeline
├── requirements.txt
├── specs/                    # spec.md, plan.md, tasks.md (SDD)
├── DECISIONS.md              # the reasoning behind every choice
└── README.md
```

---

## Tests

```bash
source venv/bin/activate
pytest
```

Tests cover the deterministic layers (scoping, safe/restricted split, PII floor) and run
**without an API key**. (Test suite is added during the query-testing pass.)

---

## Notes

- Renaming a `venv` folder breaks it (paths are hardcoded) — recreate it instead.
- If a guardrail blocks a request, the bot returns a safe refusal rather than an error.
