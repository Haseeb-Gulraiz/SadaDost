# Plan — HOW

> Architecture, stack, and technical decisions. Derived from spec.md.

## Architecture
Pipeline (single-turn):

    login(customer_id) -> load ONLY that customer (safe context)
    query -> intent classify (LLM) -> route:
       general-KB    -> ground in knowledge.md  -> LLM phrasing
       customer-data -> ground in safe fields    -> LLM phrasing
       out-of-scope  -> decline (no invention)
    -> output guard (PII regex scan) -> reply

- Restricted fields are loaded into a separate object that NEVER enters the LLM prompt.

## Stack
- Backend: FastAPI (Python), OpenAI client behind a thin wrapper, python-dotenv for keys.
- Frontend: React + Vite, animations, SadaDost branding.

## Key decisions
See DECISIONS.md (D1 restricted-isolation, D2 no-LangGraph, D3 stack/UX, D4 PII layers).

## Backend modules
- `config.py` — env/key loading.
- `data.py` — load KB; load a single scoped customer (safe vs restricted split).
- `intent.py` — LLM intent classification.
- `guardrails.py` — PII output scan; scope/grounding checks.
- `llm.py` — OpenAI wrapper.
- `chat.py` — orchestration pipeline.
- `main.py` — FastAPI endpoints (`/customers`, `/chat`).

## Trade-offs / deferred
- LLM intent needs a key + is non-deterministic (vs rules). Accepted for paraphrase/Urdu coverage.
- No DB/auth — out of scope for Part 1.
