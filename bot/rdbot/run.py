import hashlib
import json
import os
import re
import sys
import time
from datetime import date, datetime, timedelta, timezone

from . import fetch, notify
from .adapters import ADAPTERS
from .extract import extract
from .group import build_groups
from .pdfparse import parse_pdf_url
from .probe import load_sources
from .store import ROOT, DATA, ITEMS, STATE, load_items, load_json, merge, now_iso, prune, save_json
from .validate import validate, tier

SITE = json.load(open(os.path.join(ROOT, "site.config.json"), encoding="utf-8"))
MAX_PDF = int(os.environ.get("RD_MAX_PDF", "30"))
BUDGET = int(os.environ.get("RD_BUDGET_SEC", "1800"))
ANNOUNCE_DAYS = 10
IST = timezone(timedelta(hours=5, minutes=30))


def site_url(item):
    return f"{SITE['url']}/{SITE['paths'][item['type']]}/{item['slug']}/"


def fetch_list(src, lst):
    if src.get("api") in ADAPTERS:
        return ADAPTERS[src["api"]]()
    url = lst["url"]
    allowed, _ = fetch.robots_allowed(url)
    if not allowed:
        return {"ok": False, "error": "robots disallow", "items": [], "status": 0}
    res = fetch.get(url)
    items = extract(res["text"], res["url"], lst.get("hint", "")) if res["ok"] else []
    if (not res["ok"] or not items) and src.get("browser"):
        b = fetch.browser_get(url)
        if b["ok"]:
            bi = extract(b["text"], b["url"], lst.get("hint", ""))
            if len(bi) >= len(items):
                res, items = b, bi
    if src.get("require"):
        rq = re.compile(src["require"], re.I)
        items = [i for i in items if rq.search(i["title"])]
    return {"ok": res["ok"], "error": res.get("error"), "items": items, "status": res.get("status")}


def enrich(it, today):
    parsed = None
    if it["type"] == "job" and it["is_doc"] and it["url"].lower().split("?")[0].endswith(".pdf"):
        parsed = parse_pdf_url(it["url"])
    fields = validate(it, parsed, today=today) if parsed and parsed.get("ok") else {}
    it["details"] = {
        "fields": fields,
        "pdf_quality": (parsed or {}).get("quality"),
        "parsed_at": now_iso(),
        "pdf_error": None if not parsed or parsed.get("ok") else parsed.get("error"),
    }
    it["tier"] = tier(it, fields)
    if fields.get("last_date"):
        it["last_date"] = fields["last_date"]["value"]


def update_status(items, today):
    closed = []
    for it in items:
        ld = it.get("last_date")
        if it["type"] == "job" and ld:
            st = "closed" if date.fromisoformat(ld) < today else "open"
            if st == "closed" and it.get("status") == "open":
                closed.append(it)
            it["status"] = st
        else:
            it.setdefault("status", "info")
    return closed


def health(state, sid, ok, count, error):
    h = state.setdefault(sid, {})
    for k, v in (("fails", 0), ("last_ok", None), ("last_count", 0), ("zero_runs", 0)):
        h.setdefault(k, v)
    alerts = []
    if ok:
        h["fails"] = 0
        h["last_ok"] = now_iso()
        if count == 0:
            h["zero_runs"] += 1
            if h["zero_runs"] == 3:
                if h["last_count"] > 0:
                    alerts.append(f"{sid}: page loads but no items found 3 runs in a row. Layout may have changed.")
                else:
                    alerts.append(f"{sid}: page loads but has never returned items. Check its list URLs.")
        else:
            h["zero_runs"] = 0
            h["last_count"] = count
    else:
        h["fails"] += 1
        if h["fails"] in (3, 12):
            alerts.append(f"{sid}: failed {h['fails']} runs in a row ({error}).")
    h["last_error"] = None if ok else error
    return alerts


def ist_today():
    return datetime.now(IST).date()


def age_days(it, today):
    d = it.get("list_date") or it["first_seen"][:10]
    try:
        return (today - date.fromisoformat(d[:10])).days
    except ValueError:
        return 0


def is_archive(it, first_for_source, today):
    if it.get("list_date"):
        return False
    years = [int(y) for y in re.findall(r"\b(20[1-3]\d)\b", it.get("title", ""))]
    if years and max(years) < today.year - (1 if today.month <= 3 else 0):
        return True
    return first_for_source


def pdf_pending(it, today):
    if it["type"] != "job" or not it["is_doc"] or not it["url"].lower().split("?")[0].endswith(".pdf"):
        return False
    if it.get("archive"):
        return False
    if age_days(it, today) > 120:
        return False
    d = it.get("details") or {}
    if d.get("parsed_at") and not d.get("pdf_error"):
        return False
    return d.get("attempts", 0) < 3


def fingerprint(db, groups):
    core = [(i["id"], i["title"], i["type"], i.get("list_date"), i.get("status"), i.get("tier"), i.get("last_date"), json.dumps((i.get("details") or {}).get("fields") or {}, sort_keys=True)) for i in db["items"]]
    return hashlib.sha1(json.dumps([core, [(g["key"], g["items"]) for g in groups]], sort_keys=True).encode()).hexdigest()


def main(argv=None):
    argv = argv or sys.argv[1:]
    t_start = time.time()
    today = ist_today()
    sources = [s for s in load_sources() if s.get("enabled", True)]
    only = set(a for a in argv if not a.startswith("-"))
    if only:
        sources = [s for s in sources if s["id"] in only]
    db = load_items()
    pruned = prune(db, today)
    first_run = not db["items"]
    state = load_json(STATE, {})
    sources.sort(key=lambda s: (state.get(s["id"]) or {}).get("last_run") or "")
    had = {it["source"] for it in db["items"]}
    all_new, alerts, log = [], [], []
    for src in sources:
        if time.time() - t_start > BUDGET:
            log.append({"source": src["id"], "ok": None, "items": 0, "error": "skipped: time budget"})
            continue
        total, ok_any, err = 0, False, None
        try:
            for lst in src["lists"]:
                r = fetch_list(src, lst)
                ok_any = ok_any or r["ok"]
                err = err or r["error"]
                new = merge(db, src, r["items"], skip=pruned)
                bulk = len(new) > 5
                for n in new:
                    n["context"] = next((f["context"] for f in r["items"] if f["url"] == n["url"]), "")
                    if is_archive(n, src["id"] not in had or bulk, today):
                        n["archive"] = True
                all_new.extend(new)
                total += len(r["items"])
                time.sleep(1.2)
        except Exception as e:
            ok_any, err = False, f"crash: {e.__class__.__name__}: {str(e)[:120]}"
        state.setdefault(src["id"], {})["last_run"] = now_iso()
        alerts += health(state, src["id"], ok_any, total, err)
        log.append({"source": src["id"], "ok": ok_any, "items": total, "error": err})
        print(f"{src['id']:16} ok={ok_any} items={total} new={sum(1 for n in all_new if n['source'] == src['id'])}", flush=True)

    for it in db["items"]:
        if it.get("details") is None:
            it["details"] = {"fields": {}, "parsed_at": None}
            it["tier"] = tier(it, {})
    budget = MAX_PDF
    queue = sorted((it for it in db["items"] if pdf_pending(it, today)), key=lambda x: (bool(x.get("list_date")), x.get("list_date") or x["first_seen"]), reverse=True)
    for it in queue:
        if budget <= 0 or time.time() - t_start > BUDGET + 300:
            break
        budget -= 1
        attempts = (it.get("details") or {}).get("attempts", 0) + 1
        try:
            enrich(it, today)
        except Exception as e:
            it["details"] = {"fields": {}, "parsed_at": now_iso(), "pdf_error": f"crash: {e.__class__.__name__}"}
        it["details"]["attempts"] = attempts
    for it in db["items"]:
        it.pop("context", None)

    closed = update_status(db["items"], today)
    groups = build_groups(db["items"])
    fp = fingerprint(db, groups)
    changed = fp != state.get("_fingerprint")
    state["_fingerprint"] = fp
    if changed or not db.get("updated"):
        db["updated"] = now_iso()
    save_json(ITEMS, db)
    save_json(os.path.join(DATA, "exams.json"), {"updated": db["updated"], "exams": groups})
    save_json(STATE, state)

    fresh = [] if first_run else [it for it in all_new if it["tier"] >= 1 and it["source"] in had and age_days(it, today) <= ANNOUNCE_DAYS]
    entries = [{"id": it["id"], "type": it["type"], "title": it["title"], "short": it["short"], "url": site_url(it), "last_date": it.get("last_date"), "jobposting": it["type"] == "job" and it["tier"] >= 1 and it.get("status") == "open"} for it in fresh]
    if changed:
        save_json(os.path.join(DATA, "new.json"), {"run": db["updated"], "first_run": first_run, "new": entries, "closed": [site_url(c) for c in closed]})

    runlog = load_json(os.path.join(DATA, "state", "runs.json"), [])
    runlog.append({"run": now_iso(), "today": today.isoformat(), "new": len(all_new), "announce": len(entries), "changed": changed, "seconds": int(time.time() - t_start), "sources": log})
    save_json(os.path.join(DATA, "state", "runs.json"), runlog[-60:])

    for a in alerts:
        notify.alert(a)
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"site_changed={'true' if changed else 'false'}\n")
    print(f"done: new={len(all_new)} announce={len(entries)} changed={changed} alerts={len(alerts)} total={len(db['items'])} seconds={int(time.time() - t_start)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
