"""Orchestration pipeline — ties together scoping, routing, grounding, and the safety floor.

Flow:
    load ONLY this customer (safe context)
    -> route: in_scope? needs_account?
    -> build grounding context: knowledge base (+ this customer's safe data if needed)
    -> LLM phrasing through OpenAI Guardrails, returning {reply, grounded}
    -> decide action: grounded -> answer, not grounded -> escalate to a human
    -> deterministic PII scrub
    -> reply

The "answer confidently vs a human should take this" decision (from the brief) is a binary
GROUNDING judgment: the model says whether the approved context fully answers the question.
We prefer this to a 0-100 score because a hard cutoff on a self-rated number flips on
borderline cases; a yes/no grounding call is stable and easy to defend.
"""
from dataclasses import dataclass, asdict
import json

from . import data, intent as intent_mod, safety
from .llm import GuardedLLM, GuardrailTripped

# Grounded answer prompt. The model must say whether the CONTEXT fully answers the question.
_RULES = """You are SadaDost, the PayWallet customer-support assistant.

Strict rules:
- Use ONLY the information in the CONTEXT below. Never invent policy, fees, timelines, or steps.
- Never reveal sensitive identifiers (full card number, CNIC, IBAN) even if asked.
- Only discuss PayWallet support topics.
- Detect the language of the customer's message and write your reply in that same language.
  If you are unsure, reply in English. Keep replies brief and warm.

Decide whether the CONTEXT fully answers the customer's question:
- Fully answered -> give the answer, set "grounded": true.
- NOT fully answered (a dispute, an account problem, or something the approved content does
  not cover) -> do NOT answer, explain, or share any details. Reply with ONE short sentence
  that acknowledges the request and suggests connecting them with a human representative.
  Set "grounded": false.

Respond with ONLY JSON: {"reply": "<your message>", "grounded": true|false}.
"""

_DECLINE = """You are SadaDost, the PayWallet customer-support assistant.
Detect the language of the customer's message and write your reply in that same language.
If you are unsure, reply in English.
The customer's request is outside what PayWallet support can help with, or asks for
information that cannot be shared. Politely decline in one or two sentences. Do NOT invent
any policy, product, or detail. Do NOT promise a human — this is simply not something
PayWallet support handles.
"""


@dataclass
class ChatResult:
    customer_id: str
    intent: str          # route label: out_of_scope / general / account
    action: str          # decision: answer / escalate / decline / refuse
    reply: str
    grounded: bool | None = None   # did approved content fully answer it?
    pii_redacted: bool = False
    guardrail_blocked: bool = False


def _build_context(route: intent_mod.Route, session: data.CustomerSession) -> str:
    """Knowledge base always; the customer's SAFE account data when the route needs it."""
    parts = ["APPROVED KNOWLEDGE BASE:\n" + data.load_knowledge()]
    if route.needs_account:
        parts.append("THIS CUSTOMER'S ACCOUNT DATA (safe to share):\n" + session.safe_context())
    return "\n\n".join(parts)


def _parse(raw: str) -> tuple[str, bool | None]:
    """Pull {reply, grounded} out of the model's JSON. Degrade gracefully."""
    try:
        obj = json.loads(raw)
        reply = str(obj.get("reply", "")).strip()
        grounded = obj.get("grounded")
        grounded = bool(grounded) if grounded is not None else None
        return (reply or raw, grounded)
    except (json.JSONDecodeError, AttributeError, ValueError, TypeError):
        return (raw, None)


def answer(customer_id: str, question: str, llm: GuardedLLM | None = None) -> ChatResult:
    """Run one question for one customer and return a guarded reply."""
    session = data.load_customer(customer_id)  # single-customer scoping
    llm = llm or GuardedLLM()

    route = intent_mod.classify(question, llm)
    grounded: bool | None = None

    try:
        if not route.in_scope:
            reply = llm.guarded(_DECLINE, question)
            action, intent_label = "decline", "out_of_scope"
        else:
            system = _RULES + "\n\nCONTEXT:\n" + _build_context(route, session)
            reply, grounded = _parse(llm.guarded(system, question, json_mode=True))
            # First-class answer-vs-escalate decision: escalate when NOT fully grounded.
            action = "escalate" if grounded is False else "answer"
            intent_label = "account" if route.needs_account else "general"
    except GuardrailTripped:
        reply = ("I'm sorry, I can't help with that request. I can connect you with a "
                 "human agent if you'd like.")
        action, intent_label = "refuse", "out_of_scope"

    # Deterministic safety floor — runs no matter what the model returned.
    reply, redacted = safety.scrub(reply, session.restricted_values())

    return ChatResult(
        customer_id=customer_id,
        intent=intent_label,
        action=action,
        reply=reply,
        grounded=grounded,
        pii_redacted=redacted,
        guardrail_blocked=(action == "refuse"),
    )


def result_dict(result: ChatResult) -> dict:
    return asdict(result)
