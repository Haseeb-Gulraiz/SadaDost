"""The deterministic PII floor — the must-NOT-do guarantee, independent of any LLM."""
from backend.app import safety


def test_scrubs_cnic():
    out, found = safety.scrub("Your CNIC is 42101-1234567-8.")
    assert "42101-1234567-8" not in out
    assert found is True


def test_scrubs_iban_and_card():
    out, found = safety.scrub("IBAN PK24PAYW0000001234567890 card 4012881234567890")
    assert "PK24PAYW0000001234567890" not in out
    assert "4012881234567890" not in out
    assert found is True


def test_exact_match_redaction_uses_customer_values():
    out, found = safety.scrub("secret = ABC123", restricted_values=["ABC123"])
    assert "ABC123" not in out
    assert found is True


def test_clean_text_is_untouched():
    text = "Your balance is PKR 3,420.10."
    out, found = safety.scrub(text)
    assert out == text
    assert found is False


def test_masked_pan_is_not_a_false_positive():
    # The data stores PANs already masked (4012 88** **** 1881); leave them alone.
    text = "Card on file: 4012 88** **** 1881"
    out, found = safety.scrub(text)
    assert out == text
    assert found is False
