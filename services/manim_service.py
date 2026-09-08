"""Manim render service — validate LLM code, render to MP4, serve from /media/manim/."""
import re
import shutil
import subprocess
import sys
import uuid

from config import MEDIA_DIR, Runtime

MANIM_DIR = MEDIA_DIR / "manim"
BANNED_PATTERNS = [
    r"\bimport\s+(os|sys|subprocess|socket|shutil|requests|urllib|pathlib|importlib|ctypes)",
    r"\bfrom\s+(os|sys|subprocess|socket|shutil|requests|urllib|pathlib|importlib|ctypes)\b",
    r"\b__import__\b", r"\binput\s*\(", r"\beval\s*\(", r"\bexec\s*\(", r"\bopen\s*\(",
]


def extract_scene(code: str):
    """Return (scene_class_name, scene_base) from manim code."""
    matches = re.findall(r"class\s+(\w+)\s*\(\s*(\w*Scene\w*)\s*\)\s*:", code)
    if not matches:
        return None, None
    name, base = matches[-1]
    return name, base


def validate_manim_code(code: str):
    for pat in BANNED_PATTERNS:
        if re.search(pat, code):
            return f"Blocked for safety: code uses `{pat}`."
    name, base = extract_scene(code)
    if not name:
        return "No Scene subclass found. Define exactly one class like `class MyScene(Scene):` with `def construct(self):`."
    return None


def render_manim(code: str, quality: str = None, timeout: int = 420) -> dict:
    """Render manim code → MP4. Returns {ok, url?, code?, error?}."""
    quality = quality or Runtime.quality
    err = validate_manim_code(code)
    if err:
        return {"ok": False, "error": err}
    name, _ = extract_scene(code)
    rid = uuid.uuid4().hex[:10]
    py_file = MANIM_DIR / f"{rid}.py"
    py_file.write_text(code, encoding="utf-8")
    media_dir = MANIM_DIR / ".media"
    cmd = [shutil.which("manim") or "manim", quality, "--disable_caching",
           "-o", f"{rid}.mp4", str(py_file), name, "--media_dir", str(media_dir)]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           cwd=str(MANIM_DIR))
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"Render timed out after {timeout}s — simplify the scene.", "code": code}
    # find produced file
    produced = list(media_dir.glob(f"videos/**/{rid}.mp4"))
    if p.returncode != 0 or not produced:
        tail = (p.stderr or p.stdout or "")[-2500:]
        return {"ok": False, "error": tail or "Manim render failed.", "code": code}
    out = MANIM_DIR / f"{rid}.mp4"
    shutil.move(str(produced[0]), str(out))
    return {"ok": True, "url": f"/media/manim/{rid}.mp4", "code": code,
            "code_url": f"/media/manim/{rid}.py", "scene": name}
