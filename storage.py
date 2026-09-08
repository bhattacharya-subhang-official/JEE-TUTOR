"""Chat persistence — one JSON file per chat under data/chats/."""
import json
import time
import uuid
import threading
from config import DATA_DIR

_lock = threading.Lock()


def _path(cid: str):
    return DATA_DIR / "chats" / f"{cid}.json"


def new_chat(title: str = "New chat") -> dict:
    cid = uuid.uuid4().hex[:12]
    chat = {"id": cid, "title": title[:60], "created": time.time(), "updated": time.time(), "messages": []}
    save_chat(chat)
    return chat


def save_chat(chat: dict):
    with _lock:
        chat["updated"] = time.time()
        tmp = _path(chat["id"]).with_suffix(".tmp")
        tmp.write_text(json.dumps(chat, ensure_ascii=False, indent=1))
        tmp.replace(_path(chat["id"]))


def get_chat(cid: str):
    p = _path(cid)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def list_chats():
    out = []
    for p in (DATA_DIR / "chats").glob("*.json"):
        try:
            c = json.loads(p.read_text())
            out.append({"id": c["id"], "title": c.get("title", "Untitled"),
                        "updated": c.get("updated", 0), "count": len(c.get("messages", []))})
        except Exception:
            continue
    out.sort(key=lambda c: -c["updated"])
    return out


def delete_chat(cid: str) -> bool:
    with _lock:
        p = _path(cid)
        if p.exists():
            p.unlink()
            return True
        return False


def append_message(cid: str, msg: dict):
    chat = get_chat(cid)
    if chat is None:
        return None
    chat["messages"].append(msg)
    save_chat(chat)
    return chat


def set_title(cid: str, title: str):
    chat = get_chat(cid)
    if chat:
        chat["title"] = title[:60]
        save_chat(chat)
