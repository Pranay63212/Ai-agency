"""One place to ask an AI model for a JSON answer, via NVIDIA or Claude.

    from estimate_recovery.llm import chat_json
    data = chat_json("nvidia", system_prompt, user_prompt, ["field_a", "field_b"])

Keys come from NVIDIA_API_KEY / ANTHROPIC_API_KEY. Model overrides: NVIDIA_MODEL, CLAUDE_MODEL.
"""

import json
import os
import re
from functools import lru_cache

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = os.environ.get("NVIDIA_MODEL", "nvidia/nemotron-3-ultra-550b-a55b")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5-5")
DEFAULT_PROVIDER = os.environ.get("AI_PROVIDER", "nvidia")


class AIError(RuntimeError):
    pass


def parse_json(text: str, required: list[str]) -> dict:
    """Pull the JSON object out of a reply that may wrap it in prose or code fences."""
    match = re.search(r"\{.*\}", text or "", re.DOTALL)
    if not match:
        raise AIError(f"No JSON in model reply: {(text or '')[:200]!r}")
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError as e:
        raise AIError(f"Bad JSON in model reply: {e}") from e
    missing = [k for k in required if k not in data]
    if missing:
        raise AIError(f"Model reply missing fields: {missing}")
    return data


@lru_cache(maxsize=None)
def _nvidia_client():
    from openai import OpenAI
    return OpenAI(base_url=NVIDIA_BASE_URL, api_key=os.environ.get("NVIDIA_API_KEY", "proxy-injected"))


@lru_cache(maxsize=None)
def _claude_client():
    import anthropic
    return anthropic.Anthropic()


def _schema(required: list[str]) -> dict:
    return {
        "type": "object",
        "properties": {k: {"type": "string"} for k in required},
        "required": required,
        "additionalProperties": False,
    }


def _ask_nvidia(system: str, user: str, required: list[str]) -> dict:
    prompt = (f"{user}\n\nReturn only a JSON object with these string fields: "
              f"{', '.join(required)}. No other text.")
    last = None
    for _ in range(3):  # retry empty or malformed replies
        resp = _nvidia_client().chat.completions.create(
            model=NVIDIA_MODEL,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=4096,
        )
        try:
            return parse_json(resp.choices[0].message.content or "", required)
        except AIError as e:
            last = e
    raise last


def _ask_claude(system: str, user: str, required: list[str]) -> dict:
    resp = _claude_client().beta.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=16000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=system,
        output_config={"effort": "medium", "format": {"type": "json_schema", "schema": _schema(required)}},
        messages=[{"role": "user", "content": user}],
    )
    if resp.stop_reason == "refusal":
        raise AIError("Claude declined this request")
    text = next((b.text for b in resp.content if b.type == "text"), "")
    return parse_json(text, required)


def chat_json(provider: str | None, system: str, user: str, required: list[str]) -> dict:
    provider = provider or DEFAULT_PROVIDER
    if provider == "nvidia":
        return _ask_nvidia(system, user, required)
    if provider == "claude":
        return _ask_claude(system, user, required)
    raise ValueError(f"Unknown AI provider: {provider}")
