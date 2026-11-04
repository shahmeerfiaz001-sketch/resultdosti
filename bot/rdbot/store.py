import hashlib
import json
import os
from datetime import date, datetime, timezone

from .classify import advt_number
from .text import slugify, title_case_fix

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA = os.path.join(ROOT, "data")
ITEMS = os.path.join(DATA, "items.json")
STATE = os.path.join(DATA, "state", "sources.json")


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, sort_keys=False)
    os.replace(tmp, path)


def item_id(url):
    u = url.strip().split("#")[0]
    return hashlib.sha1(u.encode("utf-8")).hexdigest()[:12]


SEEN = os.path.join(DATA, "state", "pruned.json")


def load_items():
    if os.path.exists(ITEMS):
        with open(ITEMS, encoding="utf-8") as f:
            db = json.load(f)
        if not isinstance(db, dict) or not isinstance(db.get("items"), list):
            raise ValueError("items.json is not valid")
        return db
    return {"updated": None, "items": []}


def prune(db, today, keep_days=600):
    pruned = set(load_json(SEEN, []))
    keep = []
    for it in db["items"]:
        d = it.get("list_date") or it["first_seen"][:10]
        try:
            age = (today - date.fromisoformat(d[:10])).days
        except ValueError:
            age = 0
        if age > keep_days:
            pruned.add(it["id"])
        else:
            keep.append(it)
    removed = len(db["items"]) - len(keep)
    db["items"] = keep
    if removed:
        save_json(SEEN, sorted(pruned))
    return pruned


def merge(db, source, found, seen_at=None, skip=None):
    seen_at = seen_at or now_iso()
    skip = skip or set()
    by_id = {it["id"]: it for it in db["items"]}
    new = []
    for f in found:
        iid = item_id(f["url"])
        if iid in skip:
            continue
        title = title_case_fix(f["title"])
        if iid in by_id:
            it = by_id[iid]
            if (it.get("last_seen") or "")[:10] != seen_at[:10]:
                it["last_seen"] = seen_at
            if not it.get("list_date") and f.get("list_date"):
                it["list_date"] = f["list_date"]
            continue
        it = {
            "id": iid,
            "source": source["id"],
            "org": source["name"],
            "short": source["short"],
            "scope": source["scope"],
            "title": title,
            "url": f["url"],
            "is_doc": f["is_doc"],
            "type": f["type"],
            "list_date": f.get("list_date"),
            "first_seen": seen_at,
            "last_seen": seen_at,
            "advt": advt_number(title + " " + f.get("context", "")),
            "link_policy": source.get("link_policy", "deep"),
            "official_home": source["base"],
            "slug": f"{slugify(title if source['short'].lower() in title.lower() else source['short'] + ' ' + title, 70)}-{iid[:6]}",
            "details": None,
            "tier": 0,
        }
        db["items"].append(it)
        by_id[iid] = it
        new.append(it)
    return new
