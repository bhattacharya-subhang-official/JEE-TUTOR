"""JEE Tutor — FastAPI backend. Serves the SPA + SSE chat + media + uploads APIs."""
import asyncio
import hashlib
import json

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import StreamingResponse, FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import config
import storage
from services import router as ai_router
from services import uploads

app = FastAPI(title="JEE Tutor — Advanced Solver")

# ---------------------------------------------------------------- PIN lock
PIN_PAGE = """<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Locked</title>
<style>
body{margin:0;min-height:100vh;display:grid;place-items:center;background:#0b0e1a;
color:#e8ecf8;font-family:"Segoe UI",system-ui,sans-serif}
.card{background:#10152e;border:1px solid #2e3763;border-radius:16px;padding:28px;
width:min(360px,92vw);text-align:center;box-shadow:0 20px 60px rgba(0,0,0,.5)}
.logo{width:56px;height:56px;margin:0 auto 12px;border-radius:16px;display:grid;
place-items:center;font:700 28px Georgia;background:linear-gradient(135deg,#6ea8ff,#8b5cf6);color:#0b0e1a}
h1{font-size:18px;margin:0 0 4px}p{color:#aab2d0;font-size:13px;margin:0 0 18px}
input{width:100%;box-sizing:border-box;background:#0d1226;border:1px solid #2e3763;color:#e8ecf8;
border-radius:10px;padding:11px 13px;font-size:16px;text-align:center;letter-spacing:4px;outline:none}
input:focus{border-color:#6ea8ff}
button{width:100%;margin-top:12px;background:linear-gradient(135deg,#6ea8ff,#8b5cf6);
border:0;color:#0b0e1a;font-weight:700;font-size:15px;padding:11px;border-radius:10px;cursor:pointer}
.err{color:#f87171;font-size:12.5px;margin-top:10px;min-height:16px}
</style></head><body><div class="card">
<div class="logo">Σ</div><h1>JEE Tutor is locked</h1>
<p>Enter the access PIN to continue.</p>
<input id="pin" type="password" inputmode="numeric" placeholder="••••" autofocus>
<button onclick="go()">Unlock</button><div class="err" id="err"></div></div>
<script>async function go(){const p=document.getElementById('pin').value;
const r=await fetch('/api/unlock',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pin:p})});
if(r.ok){location.reload()}else{document.getElementById('err').textContent='Wrong PIN — try again';}}
document.getElementById('pin').addEventListener('keydown',e=>{if(e.key==='Enter')go()});</script>
</body></html>"""


def pin_token() -> str:
    return hashlib.sha256(("jee-tutor::" + (config.Runtime.pin or "")).encode()).hexdigest()


def _locked(request: Request) -> bool:
    if not config.Runtime.pin:
        return False
    return request.cookies.get("jt_pin") != pin_token()


@app.post("/api/unlock")
async def unlock(body: dict):
    if not config.Runtime.pin:
        return {"ok": True}
    if str(body.get("pin", "")) == config.Runtime.pin:
        resp = JSONResponse({"ok": True})
        # session cookie: no max_age → cleared when the browser closes, so the
        # PIN is asked EVERY time the app is opened (owner requirement).
        resp.set_cookie("jt_pin", pin_token(),
                        httponly=True, samesite="lax")
        return resp
    raise HTTPException(401, "Wrong PIN")

# ---------------------------------------------------------------- static & media
app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")
app.mount("/media", StaticFiles(directory=config.MEDIA_DIR), name="media")


@app.get("/")
async def index(request: Request):
    if _locked(request):
        return HTMLResponse(PIN_PAGE)
    return FileResponse(config.STATIC_DIR / "index.html")


@app.get("/api/health")
async def health():
    return {"ok": True, "key": bool(config.Runtime.api_key),
            "manim": config.manim_available(), "latex": config.latex_available()}


# ---------------------------------------------------------------- config
@app.get("/api/config")
async def get_config(request: Request):
    if _locked(request):
        return {"pin_locked": True}
    return {
        "has_key": bool(config.Runtime.api_key),
        "key_masked": config.mask_key(config.Runtime.api_key),
        "has_groq": bool(config.Runtime.groq_key),
        "provider": config.Runtime.llm_provider,
        "model": config.Runtime.model,
        "quality": config.Runtime.quality,
        "thinking": config.Runtime.thinking,
        "manim": config.manim_available(),
        "latex": config.latex_available(),
        "has_pin": bool(config.Runtime.pin),
        "pin_locked": _locked(request),
    }


@app.post("/api/config")
async def set_config(request: Request, body: dict):
    if _locked(request):
        raise HTTPException(401, "PIN required")
    updated = {}
    if "api_key" in body and body["api_key"] is not None:
        config.Runtime.api_key = str(body["api_key"]).strip()
        config.save_env_field("GEMINI_API_KEY", config.Runtime.api_key)
        updated["api_key"] = True
    for field in ("model", "quality"):
        if field in body and body[field]:
            setattr(config.Runtime, field, body[field])
            config.save_env_field(field.upper() if field != "model" else "GEMINI_MODEL", body[field])
            updated[field] = body[field]
    if "thinking" in body:
        config.Runtime.thinking = bool(body["thinking"])
        config.save_env_field("THINKING", "1" if body["thinking"] else "0")
        updated["thinking"] = config.Runtime.thinking
    if "app_pin" in body and body["app_pin"] is not None:
        pin = str(body["app_pin"]).strip()
        config.Runtime.pin = pin or config.EMBEDDED_PIN
        config.save_env_field("APP_PIN", pin)
        updated["app_pin"] = bool(pin)
    if "llm_provider" in body and body["llm_provider"] in ("auto", "gemini", "groq"):
        config.Runtime.llm_provider = body["llm_provider"]
        config.save_env_field("LLM_PROVIDER", body["llm_provider"])
        updated["llm_provider"] = body["llm_provider"]
    return {"ok": True, "updated": updated}


# ---------------------------------------------------------------- chats
@app.get("/api/chats")
async def chats(request: Request):
    if _locked(request):
        raise HTTPException(401, "PIN required")
    return storage.list_chats()


@app.get("/api/chats/{cid}")
async def get_chat(cid: str, request: Request):
    if _locked(request):
        raise HTTPException(401, "PIN required")
    c = storage.get_chat(cid)
    if not c:
        raise HTTPException(404, "chat not found")
    return c


@app.delete("/api/chats/{cid}")
async def del_chat(cid: str, request: Request):
    if _locked(request):
        raise HTTPException(401, "PIN required")
    if not storage.delete_chat(cid):
        raise HTTPException(404, "chat not found")
    return {"ok": True}


# ---------------------------------------------------------------- uploads
@app.post("/api/upload")
async def upload(request: Request, file: UploadFile = File(...)):
    if _locked(request):
        raise HTTPException(401, "PIN required")
    data = await file.read()
    if len(data) > 20 * 1024 * 1024:
        raise HTTPException(413, "File too large (max 20 MB)")
    try:
        meta = uploads.save_and_parse(file.filename, file.content_type or "", data)
    except Exception as e:
        raise HTTPException(400, f"Could not process file: {e}")
    return meta


# ---------------------------------------------------------------- chat (SSE)
def _sse(obj: dict) -> str:
    return "data: " + json.dumps(obj, ensure_ascii=False) + "\n\n"


@app.post("/api/chat")
async def chat(request: Request, body: dict):
    if _locked(request):
        raise HTTPException(401, "PIN required")
    mode = body.get("mode", "numerical")
    message = (body.get("message") or "").strip()
    attachment_ids = body.get("attachment_ids") or []
    chat_id = body.get("chat_id")

    if not message and not attachment_ids:
        raise HTTPException(400, "Empty message")

    attachments = []
    for aid in attachment_ids:
        att = uploads.get_attachment(aid)
        if att:
            attachments.append(att)

    # create / load chat, persist the user message
    chat_obj = storage.get_chat(chat_id) if chat_id else None
    is_new = chat_obj is None
    if is_new:
        chat_obj = storage.new_chat(title=message[:60] if message else "Attachment chat")
    user_msg = {"role": "user", "text": message, "mode": mode, "attachments": []}
    for aid in attachment_ids:
        att = uploads.get_attachment(aid)
        if att:
            user_msg["attachments"].append({
                "id": aid, "name": att["name"], "kind": att["kind"], "url": att.get("url")})
    storage.append_message(chat_obj["id"], user_msg)
    chat_id = chat_obj["id"]

    async def gen():
        yield _sse({"type": "chat", "chat_id": chat_id, "title": chat_obj["title"], "new": is_new})
        final_text, final_media = "", []
        try:
            async for ev in ai_router.handle(mode, message, attachments):
                if ev.get("type") == "final":
                    final_text, final_media = ev.get("text", ""), ev.get("media", [])
                yield _sse(ev)
        except Exception as e:
            yield _sse({"type": "error", "message": f"Server error: {type(e).__name__}: {e}"})
        storage.append_message(chat_id, {"role": "assistant", "text": final_text,
                                         "mode": mode, "media": final_media})
        yield _sse({"type": "done"})

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no",
                                      "Connection": "keep-alive"})


# SPA fallback for any unknown GET (not /api, /static, /media)
@app.get("/{path:path}")
async def spa(path: str, request: Request):
    if path.startswith(("api/", "static/", "media/")):
        raise HTTPException(404)
    if _locked(request):
        return HTMLResponse(PIN_PAGE)
    return FileResponse(config.STATIC_DIR / "index.html")
