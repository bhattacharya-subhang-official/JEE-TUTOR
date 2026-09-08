"""Groq fallback LLM client (OpenAI-compatible REST via httpx).
Used automatically when Gemini is unavailable (404/503/quota) or when
LLM_PROVIDER=groq. Verified working models (Aug 2026): openai/gpt-oss-120b,
qwen/qwen3.8-27b, openai/gpt-oss-20b — all support tool calling + JSON mode.
NOTE: no vision model on Groq → image attachments can't be analyzed here."""
import json
import time

import httpx

import config

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_CHAIN = ["openai/gpt-oss-120b", "qwen/qwen3.8-27b", "openai/gpt-oss-20b"]


def groq_available() -> bool:
    return bool(config.Runtime.groq_key)


def _headers():
    return {"Authorization": f"Bearer {config.Runtime.groq_key}",
            "Content-Type": "application/json"}


def _lower_schema(node):
    """Gemini type enums (OBJECT/STRING/…) → OpenAI JSON-schema (object/string/…)."""
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            if k == "type" and isinstance(v, str):
                out[k] = v.lower()
            elif k == "items" and isinstance(v, dict):
                out[k] = _lower_schema(v)
            elif k == "properties" and isinstance(v, dict):
                out[k] = {pk: _lower_schema(pv) for pk, pv in v.items()}
            elif k == "enum":
                out[k] = v
            else:
                out[k] = _lower_schema(v) if isinstance(v, (dict, list)) else v
        return out
    if isinstance(node, list):
        return [_lower_schema(x) for x in node]
    return node


def fd_to_openai_tools(fd_list):
    tools = []
    for d in fd_list or []:
        fn = {"name": d["name"],
              "description": d.get("description", ""),
              "parameters": _lower_schema(d.get("parameters") or {"type": "OBJECT", "properties": {}})}
        tools.append({"type": "function", "function": fn})
    return tools


def chat(messages, tools=None, json_mode=False, temperature=0.3,
         max_tokens=8192, timeout=150):
    """Sync Groq chat completion with model chain + 503 retries.
    Returns {"content": str|None, "tool_calls": [{"id","name","arguments":dict}], "model": str}."""
    if not groq_available():
        raise RuntimeError("No Groq API key configured.")
    body = {"messages": messages, "temperature": temperature, "max_tokens": max_tokens}
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    last = None
    for model in GROQ_CHAIN:
        body["model"] = model
        for attempt in range(3):
            try:
                with httpx.Client(timeout=timeout) as client:
                    r = client.post(GROQ_URL, headers=_headers(),
                                    content=json.dumps(body))
                if r.status_code in (429, 500, 502, 503):
                    last = f"{r.status_code}: {r.text[:200]}"
                    time.sleep(2 + 3 * attempt)
                    continue
                r.raise_for_status()
                data = r.json()
                msg = data["choices"][0]["message"]
                tcs = []
                for tc in msg.get("tool_calls") or []:
                    try:
                        args = json.loads(tc["function"].get("arguments") or "{}")
                    except Exception:
                        args = {}
                    tcs.append({"id": tc.get("id") or f"call_{len(tcs)}",
                                "name": tc["function"]["name"], "arguments": args})
                return {"content": msg.get("content"), "tool_calls": tcs, "model": model}
            except httpx.TimeoutException:
                last = "timeout"
                break  # try next model
            except Exception as e:
                last = str(e)
                if attempt == 2:
                    break
                time.sleep(2)
    raise RuntimeError(f"Groq error (all models): {last}")


# ---------------- Gemini ⇄ OpenAI message conversion ----------------
def messages_from_gemini(contents, system_text: str):
    """Convert google-genai Contents (text/inline_data/function_call/function_response)
    into an OpenAI-style messages list. Images become a text note (Groq is text-only)."""
    msgs = [{"role": "system", "content": system_text}] if system_text else []
    for c in contents or []:
        role = "assistant" if getattr(c, "role", "user") == "model" else "user"
        text_bits, tool_calls, tool_results = [], [], []
        for p in (c.parts or []):
            fc = getattr(p, "function_call", None)
            fr = getattr(p, "function_response", None)
            blob = getattr(p, "inline_data", None)
            if getattr(p, "text", None):
                text_bits.append(p.text)
            elif fc is not None:
                try:
                    args = dict(fc.args or {})
                except Exception:
                    args = {}
                tool_calls.append({"id": f"call_{len(tool_calls)}", "type": "function",
                                   "function": {"name": fc.name,
                                                "arguments": json.dumps(args)}})
            elif fr is not None:
                try:
                    payload = json.dumps(dict(fr.response or {}), default=str)
                except Exception:
                    payload = str(fr.response)
                tool_results.append({"role": "tool",
                                     "tool_call_id": f"call_{len(tool_results)}",
                                     "content": payload})
            elif blob is not None:
                text_bits.append(f"[Image attached: {getattr(blob, 'mime_type', 'image')}]")
        if role == "assistant" and tool_calls:
            m = {"role": "assistant", "content": "\n".join(text_bits) or None,
                 "tool_calls": tool_calls}
            msgs.append(m)
        elif role == "assistant":
            msgs.append({"role": "assistant", "content": "\n".join(text_bits)})
        else:
            if tool_results:
                # assistant tool_calls must precede their tool results
                if not msgs or msgs[-1].get("role") != "assistant" or not msgs[-1].get("tool_calls"):
                    msgs.append({"role": "assistant", "content": None, "tool_calls": [
                        {"id": t["tool_call_id"], "type": "function",
                         "function": {"name": "tool", "arguments": "{}"}} for t in tool_results]})
                msgs.extend(tool_results)
            if text_bits:
                msgs.append({"role": "user", "content": "\n".join(text_bits)})
    return msgs


def append_tool_results(messages, result_by_call):
    """Append assistant tool_calls (if last message has them) + tool result messages."""
    last = messages[-1] if messages else None
    if last and last.get("role") == "assistant" and last.get("tool_calls"):
        pass  # already there
    for cid, name, res in result_by_call:
        messages.append({"role": "tool", "tool_call_id": cid,
                         "content": json.dumps(res, default=str)[:6000]})
