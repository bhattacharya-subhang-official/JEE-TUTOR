"""Router — orchestrates LLMs + engines for each capability mode.
Primary: Gemini. Automatic fallback: Groq (openai/gpt-oss-120b → qwen3.8 →
gpt-oss-20b) whenever Gemini is unavailable/errored, or when LLM_PROVIDER=groq.
Yields SSE event dicts consumed by app.py."""
import asyncio
import json
import re
import uuid

from google.genai import types

import config
from engines import execute as execute_tool
from services.gemini_client import get_client, gen_config, response_text
from services import groq_client
from services import prompts
from services.manim_service import render_manim, validate_manim_code, extract_scene

MAX_TOOL_ITERATIONS = 7
DIAGRAMS_DIR = config.MEDIA_DIR / "diagrams"
DIAGRAMS_DIR.mkdir(parents=True, exist_ok=True)

_THREE_SRC = None


def _three_src():
    global _THREE_SRC
    if _THREE_SRC is None:
        p = config.STATIC_DIR / "js" / "three.min.js"
        _THREE_SRC = p.read_text(encoding="utf-8") if p.exists() else ""
    return _THREE_SRC


ORBIT_HELPER = """
function SimpleOrbit(camera, dom){
  this.camera=camera; this.dom=dom; this.target=new THREE.Vector3();
  this.sph=new THREE.Spherical().setFromVector3(camera.position.clone().sub(this.target));
  this._d=false; this._px=0; this._py=0; var self=this;
  dom.style.touchAction='none';
  dom.addEventListener('pointerdown',function(e){self._d=true;self._px=e.clientX;self._py=e.clientY;});
  window.addEventListener('pointerup',function(){self._d=false;});
  window.addEventListener('pointermove',function(e){if(!self._d)return;
    var dx=e.clientX-self._px, dy=e.clientY-self._py; self._px=e.clientX; self._py=e.clientY;
    self.sph.theta-=dx*0.006; self.sph.phi=Math.max(0.05,Math.min(Math.PI-0.05,self.sph.phi-dy*0.006));});
  dom.addEventListener('wheel',function(e){e.preventDefault();
    self.sph.radius=Math.max(0.5,Math.min(500,self.sph.radius*(e.deltaY>0?1.1:0.9)));},{passive:false});
  this.update=function(){var p=new THREE.Vector3().setFromSpherical(this.sph).add(this.target);
    this.camera.position.copy(p); this.camera.lookAt(this.target);};
  this.update();
}
window.SimpleOrbit=SimpleOrbit;
"""


def _extract_json(text: str):
    """Robustly pull the first JSON object out of an LLM response."""
    if not text:
        raise ValueError("Empty response")
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*", "", t)
    t = re.sub(r"\s*```$", "", t)
    try:
        return json.loads(t)
    except Exception:
        pass
    start = t.find("{")
    if start == -1:
        raise ValueError("No JSON object found in response")
    depth = 0
    for i in range(start, len(t)):
        if t[i] == "{":
            depth += 1
        elif t[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(t[start:i + 1])
                except Exception:
                    continue
    # last resort
    return json.loads(t[start:t.rfind("}") + 1])


def _user_parts(user_text: str, attachments: list):
    parts = []
    for att in attachments or []:
        if att.get("kind") == "image":
            parts.append(types.Part(inline_data=types.Blob(mime_type=att["mime"], data=att["data"])))
        else:
            parts.append(types.Part(text=f"[Attached file: {att['name']}]\n{att.get('text', '')}"))
    parts.append(types.Part(text=user_text))
    return [types.Content(role="user", parts=parts)]


MODEL_CHAIN = [None, "gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash",
               "gemini-flash-latest", "gemini-3.1-flash-lite"]


async def _call(contents, cfg, status_cb=None):
    """Gemini generate_content with model fallback + patient 503 retries."""
    client = get_client()
    models = [m for m in [config.Runtime.model] + MODEL_CHAIN if m]
    seen, chain = set(), []
    for m in models:
        if m and m not in seen:
            seen.add(m)
            chain.append(m)
    last = None
    for m in chain[:4]:
        for attempt in range(4):  # ride out transient 503 "high demand" spikes
            try:
                return await asyncio.wait_for(asyncio.to_thread(
                    client.models.generate_content, model=m, contents=contents, config=cfg), timeout=420)
            except asyncio.TimeoutError:
                raise RuntimeError("Gemini call timed out (420s). Try a shorter prompt.")
            except Exception as e:
                last = e
                s = str(e)
                if ("503" in s or "UNAVAILABLE" in s) and attempt < 3:
                    await asyncio.sleep(5 + 6 * attempt)
                    continue
                break  # non-transient error → try next model
    raise RuntimeError(f"Gemini API error: {last}")


async def _call_any(contents, system_text, *, status_cb=None, json_mode=False,
                    temperature=0.4, fd=None, max_tokens=8192):
    """Gemini-first call with automatic Groq fallback.
    Returns (provider, raw_text, fallback_reason). Raises only if BOTH fail."""
    provider_cfg = config.Runtime.llm_provider
    if provider_cfg in ("auto", "gemini"):
        try:
            cfg = gen_config(system_instruction=system_text,
                             response_mime_type="application/json" if json_mode else None,
                             temperature=temperature)
            if fd:
                cfg.tools = [types.Tool(function_declarations=fd)]
            resp = await _call(contents, cfg)
            return "gemini", response_text(resp), None
        except Exception as e:
            if provider_cfg == "gemini" or not groq_client.groq_available():
                raise
            reason = f"Gemini unavailable ({str(e)[:90]}) — using Groq fallback…"
            if status_cb:
                await status_cb(f"⚠️ {reason}")
            # fall through to groq
    if not groq_client.groq_available():
        raise RuntimeError("No LLM available (Gemini failed and no Groq key configured).")
    msgs = groq_client.messages_from_gemini(contents, system_text)
    res = await asyncio.to_thread(groq_client.chat, msgs,
                                  json_mode=json_mode, temperature=temperature,
                                  max_tokens=max_tokens)
    return "groq", res["content"] or "", "groq"


# ================================================================ NUMERICAL
async def run_numerical(user_text, attachments):
    sys_text = prompts.NUMERICAL_SYS + "\n\n" + prompts.CAPABILITIES_NOTE
    cfg_tools = gen_config(
        system_instruction=sys_text,
        tools=[types.Tool(function_declarations=prompts.FD)],
        temperature=0.25, thinking=False)
    contents = _user_parts(user_text, attachments)
    final_text = None
    media = []
    provider_cfg = config.Runtime.llm_provider
    groq_msgs = None
    openai_tools = groq_client.fd_to_openai_tools(prompts.FD)

    yield {"type": "status", "msg": "🧮 Analyzing the problem…"}
    used_tools = False
    for iteration in range(MAX_TOOL_ITERATIONS):
        gemini_resp = None
        if groq_msgs is None and provider_cfg in ("auto", "gemini"):
            try:
                gemini_resp = await _call(contents, cfg_tools)
            except Exception as e:
                if provider_cfg == "gemini" or not groq_client.groq_available():
                    raise
                yield {"type": "status",
                       "msg": f"⚠️ Gemini unavailable ({str(e)[:80]}) — switching to Groq fallback…"}
                groq_msgs = groq_client.messages_from_gemini(contents, sys_text)
        elif groq_msgs is None:
            if not groq_client.groq_available():
                raise RuntimeError("LLM_PROVIDER=groq but no Groq key configured.")
            groq_msgs = groq_client.messages_from_gemini(contents, sys_text)

        if groq_msgs is not None:
            res = await asyncio.to_thread(groq_client.chat, groq_msgs,
                                          tools=openai_tools, temperature=0.25)
            if res["tool_calls"]:
                used_tools = True
                groq_msgs.append({"role": "assistant",
                                  "content": res["content"] or None,
                                  "tool_calls": [{"id": t["id"], "type": "function",
                                                  "function": {"name": t["name"],
                                                               "arguments": json.dumps(t["arguments"])}}
                                                 for t in res["tool_calls"]]})
                for tc in res["tool_calls"]:
                    args = tc["arguments"]
                    yield {"type": "status", "msg": f"🔧 Running {tc['name']}…"}
                    r = await asyncio.to_thread(execute_tool, tc["name"], args)
                    ok = "error" not in r
                    brief = json.dumps(r, ensure_ascii=False, default=str)
                    yield {"type": "tool", "name": tc["name"], "args": args,
                           "ok": ok, "result": brief[:900]}
                    groq_msgs.append({"role": "tool", "tool_call_id": tc["id"],
                                      "content": brief[:6000]})
                continue
            final_text = res["content"]
            break

        # ---------- Gemini branch ----------
        if gemini_resp.function_calls:
            used_tools = True
            result_parts = []
            for fc in gemini_resp.function_calls:
                args = dict(fc.args or {})
                yield {"type": "status", "msg": f"🔧 Running {fc.name}…"}
                res = await asyncio.to_thread(execute_tool, fc.name, args)
                ok = "error" not in res
                brief = json.dumps(res, ensure_ascii=False, default=str)
                yield {"type": "tool", "name": fc.name, "args": args,
                       "ok": ok, "result": brief[:900]}
                result_parts.append(types.Part(function_response=types.FunctionResponse(
                    name=fc.name, response={"result": json.loads(brief)})))
            # Echo the model content back EXACTLY as received (preserves Gemini-3
            # thought signatures on function_call parts) — required by the API.
            try:
                model_content = gemini_resp.candidates[0].content
                contents.append(types.Content(role="model",
                                              parts=list(model_content.parts or [])))
            except Exception:
                contents.append(types.Content(role="model", parts=[
                    types.Part(function_call=types.FunctionCall(name=fc.name, args=dict(fc.args or {})))
                    for fc in gemini_resp.function_calls]))
            contents.append(types.Content(role="user", parts=result_parts))
            continue
        final_text = response_text(gemini_resp)
        break

    if final_text is None and used_tools:
        # tool loop exhausted → final write-up
        yield {"type": "status", "msg": "📝 Writing the full solution…"}
        written = False
        if groq_msgs is None:
            # Gemini streaming write-up (with fallback)
            try:
                contents.append(types.Content(role="user", parts=[types.Part(
                    text="All tool results are above. Now write the complete final solution exactly in the required format (Setup / Concept / Solution / Final Answer / Pitfalls). Do not call more tools.")]))
                client = get_client()
                cfg_final = gen_config(system_instruction=prompts.NUMERICAL_SYS, temperature=0.35)
                models = [m for m in [config.Runtime.model] + MODEL_CHAIN if m]
                seen, chain = set(), []
                for m in models:
                    if m and m not in seen:
                        seen.add(m); chain.append(m)
                outer = None
                stream = None
                for m in chain[:4]:
                    for attempt in range(3):
                        try:
                            stream = client.models.generate_content_stream(
                                model=m, contents=contents, config=cfg_final)
                            first = next(iter(stream), None)
                            if first is not None:
                                final_text = first.text or ""
                                if final_text:
                                    yield {"type": "delta", "text": final_text}
                            outer = None
                            break
                        except StopIteration:
                            stream = None
                            outer = None
                            break
                        except Exception as e:
                            outer = e
                            s = str(e)
                            if ("503" in s or "UNAVAILABLE" in s) and attempt < 2:
                                await asyncio.sleep(5 + 6 * attempt)
                                continue
                            stream = None
                            break
                    if stream is not None or outer is None:
                        break
                if stream is not None:
                    try:
                        for chunk in stream:
                            if chunk.text:
                                final_text += chunk.text
                                yield {"type": "delta", "text": chunk.text}
                    except Exception:
                        pass
                    written = bool(final_text)
                elif outer is not None and not (provider_cfg in ("auto", "groq") and groq_client.groq_available()):
                    raise RuntimeError(f"Gemini API is busy right now. Last error: {outer}.")
            except RuntimeError:
                raise
            except Exception as e:
                if not (provider_cfg in ("auto", "groq") and groq_client.groq_available()):
                    raise RuntimeError(f"Final answer generation failed: {e}")
        if not written:
            # Groq final write-up (fallback or provider=groq)
            if groq_msgs is None:
                groq_msgs = groq_client.messages_from_gemini(contents, sys_text)
                groq_msgs.append({"role": "user", "content":
                    "All tool results are above. Now write the complete final solution exactly in the required format (Setup / Concept / Solution / Final Answer / Pitfalls). Do not call more tools."})
            if "gemini" in (config.Runtime.llm_provider,) and not groq_client.groq_available():
                raise RuntimeError("Gemini unavailable and no Groq key configured.")
            res = await asyncio.to_thread(groq_client.chat, groq_msgs,
                                          temperature=0.35, max_tokens=8192)
            final_text = res["content"] or ""
            yield {"type": "delta", "text": final_text}

    if not final_text:
        final_text = "_The model returned no text. Try rephrasing the question._"
    yield {"type": "final", "text": final_text, "media": media}


# ================================================================ DIAGRAM
async def run_diagram(user_text, attachments):
    yield {"type": "status", "msg": "📐 Designing the diagram…"}
    contents = _user_parts(user_text, attachments)
    sysp = prompts.DIAGRAM_SYS + "\n\n" + prompts.CAPABILITIES_NOTE
    provider, raw, _fb = await _call_any(contents, sysp, json_mode=True, temperature=0.5)
    data = None
    try:
        data = _extract_json(raw)
    except Exception:
        yield {"type": "status", "msg": "🔄 Retrying with corrected format…"}
        contents.append(types.Content(role="model", parts=[types.Part(text=(raw or "")[:4000])]))
        contents.append(types.Content(role="user", parts=[types.Part(
            text="Your previous output was not valid JSON. Return ONLY the strict JSON object now.")]))
        provider, raw, _fb = await _call_any(contents, sysp, json_mode=True, temperature=0.4)
        data = _extract_json(raw)

    media = []
    title = data.get("title", "Diagram")
    if data.get("kind") == "3d" and data.get("scene"):
        media.append({"kind": "scene", "title": title, "scene": data["scene"]})
    elif data.get("svg"):
        svg = re.sub(r"<script[\s\S]*?</script>", "", data["svg"], flags=re.I)
        did = uuid.uuid4().hex[:10]
        (DIAGRAMS_DIR / f"{did}.svg").write_text(svg, encoding="utf-8")
        media.append({"kind": "svg", "title": title, "url": f"/media/diagrams/{did}.svg", "svg": svg})
    else:
        raise RuntimeError("Model returned neither svg nor 3d scene. Try again.")
    yield {"type": "media", "media": media[0]}
    yield {"type": "final", "text": f"**{title}**\n\n{data.get('explanation','')}", "media": media}


# ================================================================ ANIMATION
async def run_animation(user_text, attachments):
    yield {"type": "status", "msg": "🎬 Building the animation…"}
    contents = _user_parts(user_text, attachments)
    sysp = prompts.ANIM_SYS + "\n\n" + prompts.CAPABILITIES_NOTE
    provider, raw, _fb = await _call_any(contents, sysp, json_mode=True, temperature=0.55)
    data = None
    try:
        data = _extract_json(raw)
    except Exception:
        txt = raw or ""
        if "<html" in txt.lower() or "<!doctype" in txt.lower():
            data = {"html": txt, "title": "Animation", "explanation": ""}
        else:
            yield {"type": "status", "msg": "🔄 Retrying with corrected format…"}
            contents.append(types.Content(role="model", parts=[types.Part(text=txt[:4000])]))
            contents.append(types.Content(role="user", parts=[types.Part(
                text="Your output was not valid JSON with an html field. Return ONLY the strict JSON object now.")]))
            provider, raw, _fb = await _call_any(contents, sysp, json_mode=True, temperature=0.4)
            data = _extract_json(raw)

    html = data.get("html", "")
    if not html:
        raise RuntimeError("Model returned no html. Try again.")
    if "THREE" in html and "three.min.js" not in html:
        inject = "<script>" + _three_src() + "</script>"
        if "SimpleOrbit" in html:
            inject += "<script>" + ORBIT_HELPER + "</script>"
        html = re.sub(r"<head[^>]*>", "<head>" + inject, html, count=1, flags=re.I)
        if inject not in html:
            html = inject + html
    aid = uuid.uuid4().hex[:10]
    (config.MEDIA_DIR / "anim" / f"{aid}.html").write_text(html, encoding="utf-8")
    media = [{"kind": "anim", "title": data.get("title", "Animation"),
              "url": f"/media/anim/{aid}.html"}]
    yield {"type": "media", "media": media[0]}
    yield {"type": "final", "text": f"**{data.get('title','Animation')}**\n\n{data.get('explanation','')}", "media": media}


# ================================================================ VIDEO
async def run_video(user_text, attachments):
    if not config.manim_available():
        yield {"type": "status",
               "msg": "ℹ️ Manim rendering is disabled on this lite server — generating an interactive animation instead…"}
        async for ev in run_animation(user_text, attachments):
            if ev.get("type") == "final":
                ev = dict(ev)
                ev["text"] = ("**ℹ️ Video rendering isn't available on this free lite server — "
                              "I built an interactive animation instead.**\n\n" + ev.get("text", ""))
            yield ev
        return
    yield {"type": "status", "msg": "🎥 Writing the Manim script…"}
    contents = _user_parts(user_text, attachments)
    sysp = prompts.video_system_prompt() + "\n\n" + prompts.CAPABILITIES_NOTE
    provider, raw, _fb = await _call_any(contents, sysp, json_mode=True, temperature=0.5)
    data = _extract_json(raw)
    code = data.get("manim_code", "")
    if not code:
        raise RuntimeError("Model returned no manim code.")
    yield {"type": "code", "code": code}

    for attempt in (1, 2):
        yield {"type": "status", "msg": f"🎥 Rendering video (attempt {attempt})… this can take 1–3 min"}
        result = await asyncio.to_thread(render_manim, code, config.Runtime.quality)
        if result.get("ok"):
            media = [{"kind": "video", "title": data.get("title", "Manim Video"),
                      "url": result["url"], "caption": data.get("caption", ""),
                      "code": code, "code_url": result.get("code_url")}]
            yield {"type": "media", "media": media[0]}
            text = f"**{data.get('title','Manim Video')}**\n\n{data.get('caption','')}"
            yield {"type": "final", "text": text, "media": media}
            return
        err = result.get("error", "unknown error")[-1800:]
        yield {"type": "status", "msg": "⚠️ Render failed — asking model to fix…"}
        contents.append(types.Content(role="model", parts=[types.Part(text=json.dumps(data)[:4000])]))
        contents.append(types.Content(role="user", parts=[types.Part(
            text=f"Manim render failed with error:\n```\n{err}\n```\nReturn the corrected STRICT JSON (same schema) with fixed manim_code.")]))
        provider, raw, _fb = await _call_any(contents, sysp, json_mode=True, temperature=0.4)
        try:
            data = _extract_json(raw)
            code = data.get("manim_code", code)
            yield {"type": "code", "code": code}
        except Exception:
            break
    raise RuntimeError(f"Video render failed after retries. Last error:\n```\n{result.get('error','')[:800]}\n```")


# ================================================================ entry
HANDLERS = {"numerical": run_numerical, "diagram": run_diagram,
            "animation": run_animation, "video": run_video}


async def handle(mode: str, user_text: str, attachments: list):
    fn = HANDLERS.get(mode, run_numerical)
    try:
        async for ev in fn(user_text, attachments or []):
            yield ev
    except RuntimeError as e:
        yield {"type": "error", "message": str(e)}
    except Exception as e:
        yield {"type": "error", "message": f"{type(e).__name__}: {e}"}
