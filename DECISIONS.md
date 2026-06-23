# DECISIONS

> For each meaningful choice: the decision, alternatives considered, why, and honest unknowns.

## D1 — Restricted data is never given to the LLM

**Decision (user):** The LLM is never given access to the `restricted` section of customer data.
The restricted fields (CNIC, PAN, IBAN) are kept out of the model's context entirely, so the
model cannot leak what it never received.

**Corollary:** If a future criterion *requires* the LLM to be given sensitive data, guardrails
(input/output PII filtering) must be applied around it. By default, structural isolation is the
primary protection.

**Alternatives considered:** Give the LLM all data and rely on prompt instructions to not reveal
restricted fields — rejected as unsafe (a prompt is not a guarantee).

**Why:** Structural separation is a hard guarantee; prompt-based protection is best-effort.

---

## D2 — LLM stack: basic chatbot, not an agent framework

**Decision (user):** Build a basic LLM-backed chatbot, not LangGraph/agent orchestration.

**Why:** Single-turn (customerId + question → reply), no memory, no tool-loops. Deterministic
routing + LLM phrasing covers it. LangGraph would be gold-plating.

---

## D3 — Stack & UX

- **Frontend:** React + Vite; **Backend:** FastAPI. (LLM provider: OpenAI.)
- **Login:** dropdown selector of customers; on selection the backend loads ONLY that
  customer's object (single-customer scoping — no other customer is in memory).
- **Intent classification:** LLM-based, to handle paraphrase and Roman-Urdu. Trade-off: needs an
  API key and is less deterministic than rules. (Later evolved from a single 3-way bucket into a
  two-flag router — see D6 "Dual-context routing".)
- **Branding:** SadaDost — chosen palette/tone (fintech, trust-oriented).

---

## D4 — PII security layer (3 layers)

1. **Structural (primary):** LLM context is built from `safe` fields only; `restricted` is never loaded.
2. **Output guard (defense-in-depth):** regex-scan every reply for CNIC/PAN/IBAN before display; redact/block.
3. **Scope/grounding guard:** reject off-topic and ungrounded content (anti-hallucination; PayWallet-only).

**Note:** `safe` fields (incl. `balance`, `recentTransactions`) are treated as shareable per the
data's own safe/restricted labeling.

---

## D5 — Guardrail service: OpenAI Guardrails (+ deterministic hard floor)

**Decision (user):** Use **OpenAI Guardrails** (`openai-guardrails`, official MIT package) as the
configurable guardrail layer: PII masking (preflight), moderation + jailbreak (input),
off-topic/hallucination/fact-check (output).

**Hard floor kept in our own code (not delegated to the service):**
1. Restricted fields never enter the LLM prompt (structural).
2. Deterministic regex stop for CNIC/PAN/IBAN on every output.

**Why:** Don't reinvent moderation/jailbreak/off-topic detection; but the restricted-PII guarantee
must not depend on a billable, LLM-based, non-deterministic service.

**Alternatives:** Guardrails AI (freemium, JS+Py) and NeMo Guardrails (dialog state machine) —
both heavier than needed for a single-turn bot on the OpenAI stack.

**Trade-off:** OpenAI Guardrails calls OpenAI APIs → needs the key, adds cost/latency.

---

## D6 — Answer-vs-escalate, no-answer handling, and language

**Binary grounding judgment (the brief's "answer confidently vs a human should take this").**
Every grounded answer asks the model one yes/no question: does the approved CONTEXT *fully
answer* this? If not, the bot does not guess — it acknowledges and offers a human.
The decision is first-class: the API returns `action` (answer / escalate / decline / refuse)
and `grounded` (true/false), and the UI shows the action as a chip.

- **Why binary, not a 0–100 score:** we first used a numeric self-confidence with a 90 cutoff,
  but borderline cases (the duplicate-Netflix dispute) landed right on the line and the
  self-rated number wobbled 85↔90, flipping the decision. A yes/no grounding call is stable and
  easier to defend ("we escalate when the answer isn't fully grounded" beats "below 90%").
- **Honest unknown:** the grounding judgment is still the model's; a real system would back it
  with retrieval coverage / eval data.

**Dual-context routing.** The router returns two flags — `in_scope` and `needs_account` —
instead of one bucket. In-scope questions are always grounded in the knowledge base, **plus the
customer's safe account data when needed**. So a dispute is judged with both the help center and
the actual transactions — removing the earlier variance where the same question routed to
KB-only one run and account-only the next.

**No-approved-answer → two buckets (not one):**
- *Out of scope* (crypto, weather): plainly decline, **do not** promise a human — a human rep
  can't offer it either, so that would be a false promise. (`action=decline`)
- *In scope but unresolved* (disputes, account problems): acknowledge + **offer a human**.
  (`action=escalate`)
- **Alternative considered:** always "connect to a human" — rejected as a false promise for
  out-of-scope asks. "Always say I don't know" — rejected as unhelpful for real account issues.

**Language policy:** detect the language of the customer's message and reply in the same;
if unsure, use English.
- **Why:** the earlier "reply in the same language the customer used" wording made the model
  drift to random languages (crypto → Indonesian/Romanian). The explicit "detect … else
  English" instruction fixed it. Verified.

**Resolved:** the earlier routing variance (a dispute going to KB-only one run, account-only the
next) is fixed by dual-context routing above — in-scope answers now see the account data whenever
the router flags `needs_account`, which also gives card-state awareness (e.g. frozen card) for
free on the questions that need it.

**Escalation wording:** when not grounded, the bot replies with ONE sentence that acknowledges
and suggests a human — it does NOT give a partial answer or restate account details first.

---

## D7 — Model & response handling

- **Model:** `gpt-5` (configurable via `OPENAI_MODEL`). Used for both the router and the answer.
- **Temperature:** omitted by default — gpt-5 rejects non-default `temperature`. Set
  `OPENAI_TEMPERATURE` for models that allow it. Determinism comes from the test doubles, not
  from temperature.
- **JSON mode:** the grounded answer call uses `response_format=json_object`. Without it the model
  sometimes mixed prose + JSON, which failed to parse and leaked raw JSON into the reply.
- **Two LLM calls:** router (judgment only — never reads KB/account data) then answer (reads the
  built context). Keeps routing cheap and keeps customer data out of the classifier.
