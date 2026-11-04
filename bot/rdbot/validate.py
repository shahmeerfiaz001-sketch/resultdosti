from datetime import date

from .dates import find_dates


def _d(s):
    try:
        return date.fromisoformat(s)
    except (TypeError, ValueError):
        return None


def _single(field):
    if not field:
        return None
    vals = field.get("values") or []
    return vals[0] if len(vals) == 1 else None


def validate(item, parsed, today=None):
    today = today or date.today()
    base = _d(item.get("list_date")) or _d((item.get("first_seen") or "")[:10]) or today
    ctx_dates = {d.isoformat() for d in find_dates(item.get("context", "") + " " + item.get("title", ""))}
    f = (parsed or {}).get("fields") or {}
    out = {}
    start = _single(f.get("start_date"))
    last = _single(f.get("last_date"))
    exam = _single(f.get("exam_date"))
    sd, ld, ed = _d(start), _d(last), _d(exam)

    if ld and 0 <= (ld - base).days <= 150 and (not sd or sd <= ld):
        out["last_date"] = {"value": last, "confidence": "confirmed" if last in ctx_dates else "valid"}
    if sd and -30 <= (sd - base).days <= 90 and (not ld or sd <= ld):
        out["start_date"] = {"value": start, "confidence": "confirmed" if start in ctx_dates else "valid"}
    if ed and (not ld or ed > ld) and 0 <= (ed - base).days <= 400:
        out["exam_date"] = {"value": exam, "confidence": "valid"}

    fees = (f.get("fee") or {}).get("values") or []
    fees = [v for v in fees if 0 <= v <= 2500]
    if fees and len(fees) <= 6:
        out["fee"] = {"values": fees, "max": max(fees), "min": min(fees), "confidence": "valid"}

    age = f.get("age") or {}
    amin, amax = age.get("min"), age.get("max")
    if amin and amax and 14 <= amin < amax <= 65:
        out["age"] = {"min": amin, "max": amax, "confidence": "valid"}
    elif amax and 18 <= amax <= 65 and not amin:
        out["age"] = {"min": None, "max": amax, "confidence": "valid"}

    posts = (f.get("posts") or {}).get("value")
    if posts and 1 <= posts <= 200000:
        out["posts"] = {"value": posts, "confidence": "valid"}
    return out


def tier(item, fields):
    if item["type"] != "job":
        return 1 if len(item["title"]) >= 18 else 0
    strong = [k for k in ("last_date", "start_date", "fee", "age", "posts") if k in (fields or {})]
    if "last_date" in strong and len(strong) >= 2:
        return 2
    if len(item["title"]) >= 18:
        return 1
    return 0
