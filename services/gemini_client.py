"""Gemini client wrapper (google-genai SDK)."""
import threading

from google import genai
from google.genai import types

import config

_local = threading.local()
_last_key = [None]


def get_client() -> genai.Client:
    key = config.Runtime.api_key
    if not key:
        raise RuntimeError("No Gemini API key configured. Open Settings (⚙) and add your key.")
    c = getattr(_local, "client", None)
    if c is None or _last_key[0] != key:
        c = genai.Client(api_key=key)
        _local.client = c
        _last_key[0] = key
    return c


def gen_config(**kw) -> types.GenerateContentConfig:
    """Build a GenerateContentConfig from raw kwargs."""
    if "thinking" not in kw:
        kw["thinking"] = config.Runtime.thinking
    thinking = kw.pop("thinking")
    tcfg = None
    model = (config.Runtime.model or "")
    if not model.startswith("gemini-3") and not model.startswith("gemma"):
        # Gemini 2.5-era models accept thinking_budget; 3.x manages thinking internally.
        tcfg = None if thinking else types.ThinkingConfig(thinking_budget=0)
    return types.GenerateContentConfig(thinking_config=tcfg, **kw)


def response_text(resp) -> str:
    try:
        return resp.text or ""
    except Exception:
        parts = []
        try:
            for c in resp.candidates or []:
                for p in (c.content.parts or []):
                    if getattr(p, "text", None):
                        parts.append(p.text)
        except Exception:
            pass
        return "\n".join(parts)
