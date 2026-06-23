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

## Part 2
- [ ] Governed data layer design note + diagram

## Submission
- [ ] README (how to run)
- [ ] DECISIONS.md complete
- [ ] Part 2 design note
