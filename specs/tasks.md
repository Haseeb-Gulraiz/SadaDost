# Tasks

> Step-by-step breakdown. Check off as completed.

## Part 1
### Backend
- [x] Project scaffold + requirements.txt (venv = Python 3.12; openai-guardrails needs >=3.11)
- [x] config.py — load env / API key
- [x] data.py — load knowledge.md; load single scoped customer (safe/restricted split)
- [x] llm.py — OpenAI wrapper via OpenAI Guardrails
- [x] intent.py — LLM intent classification (general / account / out_of_scope)
- [x] safety.py — deterministic PII floor (exact-match + regex scrub)
- [x] guardrails_config.json — Moderation + Jailbreak (input), Contains PII (output)
- [x] chat.py — orchestration pipeline
- [x] main.py — FastAPI endpoints (/customers, /chat)

### Frontend
- [x] Vite + React scaffold (builds clean)
- [x] Dropdown login (customer selector)
- [x] Chat UI + animations (Framer Motion, typing indicator, intent/PII chips)
- [x] SadaDost branding (teal/emerald palette, SVG logo, tone)

### Testing
- [x] Run questions.txt queries; refine edge-case behavior
- [x] Tests for guardrails (PII never leaks), routing, decline/escalate

## Part 2 — Governed data layer (design note + diagram)
### Framing
- [ ] State the problem: today data comes from scraping microservices' logs (brittle, ungoverned)
- [ ] Scope the data needed: balance, card status, KYC, transactions (live) + behavioural analytics

### Architecture (the diagram)
- [ ] Data ownership: which service owns each domain (balance vs card vs KYC vs txns)
- [ ] Access pattern: bot → single data-access layer → per-service APIs (not logs)
- [ ] Product-analytics tool integration for behavioural signals

### Must take a position on
- [ ] Ownership & exposure — who owns what, how each field is exposed
- [ ] Correctness/isolation — never reads wrong customer's data or a field it shouldn't see
- [ ] Resilience — service slow/down mid-answer (timeouts, fallback, partial answers)
- [ ] Data residency — for financial data
- [ ] Extensibility — how a new data signal is added later
- [ ] Scale — as services and AI use-cases multiply

### Close
- [ ] State trade-offs and what's deliberately deferred; be honest about what's unsure

## Submission
- [ ] README (how to run)
- [ ] DECISIONS.md complete
- [ ] Part 2 design note
