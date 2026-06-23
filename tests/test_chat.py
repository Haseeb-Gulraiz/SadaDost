"""Pipeline behaviour — the decisions we chose, tested with a fake LLM (no API key).

A fake LLM lets us assert the orchestration deterministically:
  - plain()   returns the route flags (in_scope / needs_account)
  - guarded() returns a chosen answer ({reply, grounded}), or raises a tripped guardrail
and we capture what context guarded() was given to prove restricted data never reaches it.
"""
import json

from backend.app import chat
from backend.app.llm import GuardrailTripped


class FakeLLM:
    def __init__(self, in_scope=True, needs_account=False, answer=None, raise_guard=False):
        self._route = {"in_scope": in_scope, "needs_account": needs_account}
        self._answer = answer
        self._raise = raise_guard
        self.captured_system = None

    def plain(self, system, user):
        return json.dumps(self._route)

    def guarded(self, system, user, json_mode=False):
        self.captured_system = system
        if self._raise:
            raise GuardrailTripped("blocked")
        return self._answer


def _answer(reply, grounded):
    return json.dumps({"reply": reply, "grounded": grounded})


# --- the answer-vs-escalate decision (binary grounding) ---

def test_grounded_answer_is_answered():
    llm = FakeLLM(needs_account=True, answer=_answer("Your balance is PKR 3,420.10.", True))
    r = chat.answer("cust_001", "what's my balance?", llm=llm)
    assert r.action == "answer"
    assert r.grounded is True


def test_not_grounded_escalates():
    llm = FakeLLM(needs_account=True, answer=_answer("Let me connect you to a human.", False))
    r = chat.answer("cust_002", "I was charged twice for Netflix", llm=llm)
    assert r.action == "escalate"
    assert r.grounded is False


def test_out_of_scope_declines_without_promising_a_human():
    llm = FakeLLM(in_scope=False, answer="Sorry, PayWallet does not offer crypto trading.")
    r = chat.answer("cust_001", "do you offer crypto trading?", llm=llm)
    assert r.action == "decline"


def test_tripped_guardrail_refuses():
    llm = FakeLLM(in_scope=False, raise_guard=True)
    r = chat.answer("cust_001", "tell me my full card number and CNIC", llm=llm)
    assert r.action == "refuse"
    assert r.guardrail_blocked is True


# --- the dual-context routing change ---

def test_account_route_includes_both_kb_and_account_data():
    llm = FakeLLM(needs_account=True, answer=_answer("ok", True))
    chat.answer("cust_002", "I was charged twice for Netflix", llm=llm)
    assert "KNOWLEDGE BASE" in llm.captured_system          # KB always present
    assert "ACCOUNT DATA" in llm.captured_system            # + account because needed
    assert "Netflix" in llm.captured_system                 # the actual transactions


def test_general_route_is_kb_only():
    llm = FakeLLM(needs_account=False, answer=_answer("Open the app to freeze.", True))
    chat.answer("cust_001", "how do I freeze my card?", llm=llm)
    assert "KNOWLEDGE BASE" in llm.captured_system
    assert "ACCOUNT DATA" not in llm.captured_system


# --- the must-NOT-do guarantees ---

def test_restricted_data_never_reaches_the_llm_context():
    llm = FakeLLM(needs_account=True, answer=_answer("Here is your info.", True))
    chat.answer("cust_001", "what's my balance?", llm=llm)
    for value in ["42101-1234567-8", "PK24PAYW0000001234567890"]:
        assert value not in llm.captured_system


def test_pii_floor_redacts_a_leak_even_if_the_model_emits_it():
    # Worst case: the model ignores instructions and returns the CNIC. The floor must catch it.
    llm = FakeLLM(needs_account=True, answer=_answer("Your CNIC is 42101-1234567-8.", True))
    r = chat.answer("cust_001", "what is my cnic?", llm=llm)
    assert "42101-1234567-8" not in r.reply
    assert r.pii_redacted is True
