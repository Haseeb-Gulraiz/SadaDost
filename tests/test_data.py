"""Single-customer scoping and the safe/restricted split."""
from backend.app import data


def test_list_customers_exposes_only_safe_fields():
    listed = data.list_customers()
    ids = {c["id"] for c in listed}
    assert ids == {"cust_001", "cust_002", "cust_003"}
    for c in listed:
        assert set(c.keys()) == {"id", "firstName"}  # no balance, no restricted


def test_load_customer_is_scoped_to_one_customer():
    session = data.load_customer("cust_001")
    assert session.customer_id == "cust_001"
    assert session.safe["firstName"] == "Ayesha"


def test_unknown_customer_raises():
    import pytest
    with pytest.raises(KeyError):
        data.load_customer("cust_999")


def test_restricted_data_never_appears_in_safe_context():
    session = data.load_customer("cust_001")
    context = session.safe_context()
    # The LLM only ever sees safe_context — none of the restricted values may be in it.
    for value in session.restricted_values():
        assert value not in context
    assert "cnic" not in context.lower()


def test_restricted_values_are_available_to_the_safety_floor():
    session = data.load_customer("cust_001")
    values = session.restricted_values()
    assert "42101-1234567-8" in values  # CNIC, for exact-match scrubbing
