import json

from . import fetch
from .classify import NOISE, classify
from .text import clean

SSC_NOTICES = (
    "https://ssc.gov.in/api/general-website/portal/notice-boards?page=1&limit={limit}&contentType=notice-boards"
    "&key=createdAt&order=DESC&isAttachment=true&language=english"
    "&attributes=id,headline,examId,contentType,redirectUrl,startDate,endDate,language,createdAt"
)
SSC_PAGE = "https://ssc.gov.in/home/notice-board"


def ssc_items(payload):
    out = []
    for rec in (payload or {}).get("data") or []:
        title = clean(rec.get("headline") or "")
        rid = rec.get("id")
        if not title or not rid or NOISE.search(title):
            continue
        kind = classify(title, "", "") or "notice"
        created = (rec.get("createdAt") or "")[:10] or None
        files = [a.get("fileName") for a in rec.get("attachments") or [] if a.get("fileName")]
        out.append({
            "title": title,
            "url": f"{SSC_PAGE}?notice={rid}",
            "is_doc": False,
            "type": kind,
            "list_date": created,
            "context": f"{title} {' '.join(files)}",
        })
    return out


def ssc(limit=60):
    res = fetch.get(SSC_NOTICES.format(limit=limit), timeout=(10, 30), retries=1)
    if not res["ok"]:
        return {"ok": False, "error": res["error"], "items": [], "status": res["status"]}
    try:
        payload = json.loads(res["text"] or "{}")
    except ValueError:
        return {"ok": False, "error": "bad json", "items": [], "status": res["status"]}
    if str(payload.get("statusCode")) != "200":
        return {"ok": False, "error": f"api {payload.get('statusCode')}: {payload.get('error')}", "items": [], "status": res["status"]}
    return {"ok": True, "error": None, "items": ssc_items(payload), "status": res["status"]}


ADAPTERS = {"ssc": ssc}
