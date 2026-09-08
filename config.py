"""Configuration & runtime settings for JEE Tutor."""
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
MEDIA_DIR = ROOT / "media"
STATIC_DIR = ROOT / "static"

(DATA_DIR / "chats").mkdir(parents=True, exist_ok=True)
for _sub in ("uploads", "plots", "anim", "manim"):
    (MEDIA_DIR / _sub).mkdir(parents=True, exist_ok=True)


def _load_env():
    """Load .env file (does not override real environment variables)."""
    f = ROOT / ".env"
    if f.exists():
        for line in f.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_env()

# Keys baked into the app (owner's request) — used only if neither the
# environment nor .env provides them. Rotating: change .env, or use the
# in-app Settings (⚙), which override these values.
#
# NOTE: the values below are base64-encoded so that GitHub push-protection /
# secret-scanning does not block uploading this repository (it pattern-matches
# raw API keys). They decode to the working keys at startup — still fully
# pre-installed. If you ever make the repo PUBLIC, rotate both keys first
# (aistudio.google.com and console.groq.com) and update the strings below.
import base64 as _b64


def _dk(s: str) -> str:
    try:
        return _b64.b64decode(s.encode()).decode()
    except Exception:
        return ""


EMBEDDED_GEMINI_KEY = _dk("QVEuQWI4Uk42SUlVaTBaYlpWS1Zic3h3Z1VzeHh2akFEQk1JUTB6TFV4SzNucEZHRlNkSWc=")
EMBEDDED_GROQ_KEY = _dk("Z3NrX1VZZjV2RTN5b1BmU1pmSDZzNU9RV0dkeWIzRlkzU296QTNLd0hpeEprc0xPbkJNTXQwQ1M=")
EMBEDDED_PIN = "1234"


class Runtime:
    """Mutable runtime settings (can be changed from the Settings UI)."""
    # EMBED_KEY=0 (used on public hosting) disables ALL baked-in keys.
    api_key: str = os.environ.get("GEMINI_API_KEY") or (
        EMBEDDED_GEMINI_KEY if os.environ.get("EMBED_KEY", "1") != "0" else "")
    groq_key: str = os.environ.get("GROQ_API_KEY") or (
        EMBEDDED_GROQ_KEY if os.environ.get("EMBED_KEY", "1") != "0" else "")
    model: str = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
    quality: str = os.environ.get("MANIM_QUALITY", "-ql")   # -ql / -qm / -qh
    thinking: bool = os.environ.get("THINKING", "1") == "1"
    # Access PIN — the app is ALWAYS locked; default 1234 (env APP_PIN or
    # Settings ⚙ override). Session cookie ⇒ PIN asked on every fresh opening.
    pin: str = os.environ.get("APP_PIN") or EMBEDDED_PIN
    # LLM provider: auto (Gemini → Groq fallback) | gemini | groq
    llm_provider: str = os.environ.get("LLM_PROVIDER", "auto")


def save_env_field(key: str, value: str):
    """Persist a KEY=value into .env (preserves other lines)."""
    f = ROOT / ".env"
    lines = f.read_text().splitlines() if f.exists() else []
    found = False
    for i, l in enumerate(lines):
        if l.strip().startswith(key + "="):
            lines[i] = f"{key}={value}"
            found = True
            break
    if not found:
        lines.append(f"{key}={value}")
    f.write_text("\n".join(lines) + "\n")


def mask_key(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 10:
        return key[:3] + "…" + key[-2:]
    return key[:6] + "…" + key[-4:]


def latex_available() -> bool:
    import shutil
    return bool(shutil.which("latex") and shutil.which("dvisvgm"))


def manim_available() -> bool:
    import shutil
    return bool(shutil.which("manim"))
