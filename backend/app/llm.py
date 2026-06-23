"""LLM access — two paths, on purpose.

  plain()   : a normal OpenAI call. Used for internal plumbing (intent classification).
  guarded() : the SAME call wrapped by OpenAI Guardrails (moderation, jailbreak on input;
              PII on output). Used for the user-facing answer.

Why split: guardrails should police what we say to the customer, not our internal
classification step (running them there doubles cost and trips on the user's raw words
before we've even decided a route). If a guardrail trips, we raise GuardrailTripped and
turn it into a safe refusal upstream. The deterministic floor in safety.py always runs too.
"""
from . import config


class GuardrailTripped(Exception):
    """Raised when an OpenAI Guardrail blocks the user-facing response."""


def _temperature() -> dict:
    """Pass temperature only when configured — gpt-5 rejects non-default values."""
    if config.OPENAI_TEMPERATURE is None:
        return {}
    return {"temperature": config.OPENAI_TEMPERATURE}


class GuardedLLM:
    def __init__(self) -> None:
        if not config.has_api_key():
            raise RuntimeError("OPENAI_API_KEY is not set. Add it to .env to use the LLM.")
        # Imported lazily so key-free tests don't need the packages.
        from openai import OpenAI
        from guardrails import GuardrailsOpenAI

        self._raw = OpenAI(api_key=config.OPENAI_API_KEY)
        self._guarded = GuardrailsOpenAI(config=config.GUARDRAILS_CONFIG)

    def plain(self, system: str, user: str) -> str:
        """Internal, unguarded completion (used for intent classification)."""
        resp = self._raw.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            **_temperature(),
        )
        return (resp.choices[0].message.content or "").strip()

    def guarded(self, system: str, user: str, json_mode: bool = False) -> str:
        """User-facing completion through OpenAI Guardrails.

        json_mode forces a valid JSON object response (used for the grounded answer, which must
        return {reply, grounded}); without it the model sometimes mixes prose and JSON.
        """
        from guardrails import GuardrailTripwireTriggered

        kwargs = _temperature()
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        try:
            resp = self._guarded.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                **kwargs,
            )
        except GuardrailTripwireTriggered as exc:
            raise GuardrailTripped(str(exc)) from exc

        # GuardrailsOpenAI proxies the underlying OpenAI response attributes directly.
        return (resp.choices[0].message.content or "").strip()
