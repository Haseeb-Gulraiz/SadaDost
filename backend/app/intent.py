"""Intent routing — two flags instead of one bucket.

We decide:
  - in_scope:      is this a PayWallet support question at all?
  - needs_account: does answering it require THIS customer's account data?

The grounding context is then the approved knowledge base, PLUS the customer's safe account
data when needs_account is true. So a question like "charged twice for Netflix" is judged with
both the help center AND the transactions, instead of one or the other.
"""
from dataclasses import dataclass
import json


@dataclass
class Route:
    in_scope: bool
    needs_account: bool


_SYSTEM = """You are a router for the PayWallet support bot. For the customer's message,
return two booleans.

- "in_scope": true if it is a PayWallet customer-support question (freezing a card, declined
  payments, refunds, OTP, tap to pay, account status, balance, transactions, account deletion).
  false for anything PayWallet does not handle (crypto, weather, savings products it may not
  offer) or requests for sensitive identifiers (full card number, CNIC, IBAN).
- "needs_account": true if answering requires THIS customer's own account data (their balance,
  card status, KYC, transactions, "why can't I do anything on my account"). false for general
  how-to questions that the help center answers on its own.

Reply with ONLY JSON: {"in_scope": true|false, "needs_account": true|false}."""


def classify(question: str, llm) -> Route:
    """Return a Route. On an unparseable reply, lean to in-scope + account so the grounding
    judgment (not a mis-route) makes the final call."""
    raw = llm.plain(_SYSTEM, question)
    try:
        obj = json.loads(raw)
        return Route(bool(obj.get("in_scope", True)), bool(obj.get("needs_account", True)))
    except (json.JSONDecodeError, AttributeError, TypeError):
        return Route(True, True)
