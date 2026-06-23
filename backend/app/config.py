"""Configuration: loads environment variables and resolves paths.

Everything tunable lives here so the rest of the code stays clean.
"""
from pathlib import Path
import os

from dotenv import load_dotenv

# Load .env from the repo root (two levels up: app -> backend -> repo root).
REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5")
# Some models (e.g. gpt-5) only allow the default temperature. Leave unset to omit it;
# set OPENAI_TEMPERATURE (e.g. 0) for models that support a custom value.
_temp = os.getenv("OPENAI_TEMPERATURE", "")
OPENAI_TEMPERATURE = float(_temp) if _temp != "" else None

# Where the approved materials live (knowledge.md + customers.json).
MATERIALS_DIR = Path(os.getenv("MATERIALS_DIR", REPO_ROOT / "materials"))

# Guardrails pipeline config (OpenAI Guardrails service).
GUARDRAILS_CONFIG = Path(os.getenv("GUARDRAILS_CONFIG", REPO_ROOT / "guardrails_config.json"))


def has_api_key() -> bool:
    return bool(OPENAI_API_KEY)
