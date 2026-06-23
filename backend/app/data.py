"""Data loading: the approved knowledge base and per-customer account data.

Two hard rules live here:
  1. Single-customer scoping  -> load_customer() returns ONLY the requested customer.
  2. Safe vs restricted split  -> CustomerSession exposes `safe` for the LLM and keeps
     `restricted` server-side only (never handed to the model).
"""
from dataclasses import dataclass, field
from functools import lru_cache
import json

from . import config


@lru_cache(maxsize=1)
def load_knowledge() -> str:
    """Return the full approved help-center text. It is tiny, so we ground on all of it."""
    return (config.MATERIALS_DIR / "knowledge.md").read_text(encoding="utf-8")


def _load_all_customers() -> dict:
    """Internal: read the raw customers file. Never exposed directly to the app/LLM."""
    raw = json.loads((config.MATERIALS_DIR / "customers.json").read_text(encoding="utf-8"))
    return {c["id"]: c for c in raw["customers"]}


def list_customers() -> list[dict]:
    """Public, safe list for the login dropdown: id + first name only."""
    return [
        {"id": c["id"], "firstName": c["safe"]["firstName"]}
        for c in _load_all_customers().values()
    ]


@dataclass
class CustomerSession:
    """A single logged-in customer. Holds that customer's data and NOTHING else.

    - `safe`       : the only fields ever placed into the LLM context.
    - `restricted` : kept here for the deterministic output guard to scan against,
                     but NEVER added to any prompt.
    """
    customer_id: str
    safe: dict
    restricted: dict = field(repr=False)

    def safe_context(self) -> str:
        """Render the safe fields as plain text for grounding the LLM."""
        return json.dumps(self.safe, ensure_ascii=False, indent=2)

    def restricted_values(self) -> list[str]:
        """Concrete restricted values (for exact-match redaction). Strings only."""
        return [str(v) for v in self.restricted.values() if v]


def load_customer(customer_id: str) -> CustomerSession:
    """Load ONLY the given customer. Raises KeyError if unknown.

    This is the single-customer scoping guarantee: the returned session contains
    exactly one customer's object and there is no path to any other customer.
    """
    everyone = _load_all_customers()
    if customer_id not in everyone:
        raise KeyError(customer_id)
    record = everyone[customer_id]
    return CustomerSession(
        customer_id=customer_id,
        safe=record["safe"],
        restricted=record.get("restricted", {}),
    )
