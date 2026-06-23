# Spec — WHAT & WHY

> Requirements and intended behaviors. No implementation detail.

## Problem
PayWallet needs a customer-support chatbot that answers questions grounded ONLY in approved
content (`knowledge.md`) and a customer's own account data (`customers.json`) — safely, without
leaking restricted data or inventing policy.

## Goals
- Answer general support questions from approved knowledge base.
- Answer customer-specific questions from that customer's account data.
- Enforce single-customer scoping: a logged-in customer's session only ever holds their object.
- Never reveal restricted data (CNIC, PAN, IBAN).
- Never hallucinate: only material-grounded answers; no off-topic discussion.
- Aesthetic, branded (SadaDost) frontend with animations.

## Non-goals
- Multi-turn memory, agent frameworks (LangGraph).
- Real auth, databases, live service integration (that's Part 2's design).

## Requirements
- **R1** Intent classification routes a query to: general-KB / customer-data / out-of-scope.
- **R2** General queries → grounded in `knowledge.md`.
- **R3** Customer queries → grounded in the logged-in customer's `safe` data only.
- **R4** On login, backend loads ONLY that customer's object (single-customer scoping).
- **R5** Restricted data never enters the LLM context (structural isolation).
- **R6** Output guard scans every reply for CNIC/PAN/IBAN and redacts/blocks.
- **R7** Scope/grounding guard: reject off-topic and ungrounded content.
- **R8** Frontend: dropdown login, chat UI, SadaDost branding + animations.

## Behaviors
- General KB question → friendly grounded answer.
- Customer safe-data question (balance, card status, transactions) → answer from data.
- Restricted-data request → refuse.
- No approved answer / out of scope → decline without inventing.
- (Edge cases refined during query testing.)

## Open questions / ambiguities
- Physical vs virtual card not in data (affects tap-to-pay answer).
- Answer-vs-escalate threshold — to decide during testing.
