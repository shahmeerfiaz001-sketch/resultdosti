import io
import re

from . import fetch
from .dates import find_dates
from .text import clean

MAX_BYTES = 15 * 1024 * 1024
LABELS = {
    "start_date": r"(?:start(?:ing)?|commencement|opening|begin(?:ning)?)\s+(?:date\s+)?(?:of|for)?\s*(?:online\s+)?(?:application|registration|apply|submission)|application\s+(?:start|begin|opening)s?\s*(?:date)?|online\s+(?:application|registration)\s+(?:start|begin)s?|आवेदन\s+(?:प्रारंभ|शुरू|आरंभ)",
    "last_date": r"(?:last|closing|end)\s+date\s+(?:of|for)?\s*(?:online\s+)?(?:application|registration|apply|submission|receipt)?|application\s+(?:last|closing|end)\s+date|last\s+date|अंतिम\s+(?:तिथि|तारीख)",
    "fee_last_date": r"last\s+date\s+(?:for|of)\s+(?:fee|payment)|fee\s+payment\s+last\s+date",
    "exam_date": r"(?:date\s+of\s+(?:written\s+|online\s+|computer\s+based\s+)?(?:exam(?:ination)?|test|cbt))|(?:exam(?:ination)?|cbt|test)\s+date|परीक्षा\s+(?:तिथि|तारीख)",
}
LABEL_RE = {k: re.compile(v, re.I) for k, v in LABELS.items()}
AMOUNT = re.compile(r"(?:rs\.?|₹|inr|रु\.?|रुपये)\s*[:\-]?\s*(\d{1,4}(?:,\d{3})?)(?:\s*/-)?", re.I)
AGE_RANGE = re.compile(r"(\d{2})\s*(?:years?|yrs?|वर्ष)?\s*(?:to|-|–|से)\s*(\d{2})\s*(?:years?|yrs?|वर्ष)", re.I)
AGE_MIN = re.compile(r"min(?:imum)?\.?\s+age[^0-9]{0,25}(\d{2})", re.I)
AGE_MAX = re.compile(r"max(?:imum)?\.?\s+age[^0-9]{0,25}(\d{2})", re.I)
POSTS = [
    re.compile(r"total\s+(?:no\.?\s+of\s+)?(?:posts?|vacanc(?:y|ies))\s*[:\-–]?\s*(\d{1,6})", re.I),
    re.compile(r"(?<![\d/.-])(\d{1,6})\s+(?:posts?|vacanc(?:y|ies))\b", re.I),
    re.compile(r"कुल\s+(?:पद|रिक्तियां|रिक्तियाँ)\s*[:\-–]?\s*(\d{1,6})"),
]
LEGACY_HINT = re.compile(r"[¼½¾ƒ‡ˆ‰Š‹ŒŽ•–—˜™š›œžŸ¡¢£¤¥¦§¨©ª«¬®¯°±²³´µ¶·¸¹º»¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ]")


def text_quality(t):
    if not t:
        return {"chars": 0, "latin": 0.0, "devanagari": 0.0, "legacy_suspect": False, "scanned_suspect": True}
    n = len(t)
    latin = sum(1 for c in t if "a" <= c.lower() <= "z") / n
    dev = sum(1 for c in t if "ऀ" <= c <= "ॿ") / n
    legacy = len(LEGACY_HINT.findall(t)) / n > 0.01
    return {"chars": n, "latin": round(latin, 3), "devanagari": round(dev, 3), "legacy_suspect": legacy, "scanned_suspect": n < 200}


def pdf_text(content, max_pages=8):
    import pdfplumber
    out = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages[:max_pages]:
            try:
                out.append(page.extract_text() or "")
            except Exception:
                out.append("")
    return clean("\n".join(out)) if out else ""


def _date_after(label_re, text, window=140):
    hits = []
    for m in label_re.finditer(text):
        seg = text[m.end(): m.end() + window]
        ds = find_dates(seg)
        if ds:
            hits.append(ds[0])
    return hits


def _amounts_near_fee(text):
    vals = []
    for m in re.finditer(r"(application\s+fee|examination\s+fee|fee\s+details|fees?\s*[:\-])|(?:आवेदन\s+)?शुल्क", text, re.I):
        seg = text[m.start(): m.start() + 600]
        for a in AMOUNT.finditer(seg):
            v = int(a.group(1).replace(",", ""))
            vals.append(v)
        if re.search(r"\bnil\b|no\s+fee|exempt|शुल्क\s+नहीं", seg, re.I):
            vals.append(0)
    return vals


def parse_fields(text):
    f = {}
    for key in ("start_date", "last_date", "exam_date", "fee_last_date"):
        hits = _date_after(LABEL_RE[key], text)
        if hits:
            f[key] = {"values": sorted(set(d.isoformat() for d in hits)), "count": len(hits)}
    if "last_date" in f and "fee_last_date" in f:
        rest = [v for v in f["last_date"]["values"] if v not in f["fee_last_date"]["values"]]
        if rest:
            f["last_date"]["values"] = rest
    fees = _amounts_near_fee(text)
    if fees:
        f["fee"] = {"values": sorted(set(fees))}
    m = AGE_RANGE.search(text[text.lower().find("age"):] if "age" in text.lower() else text)
    amin = AGE_MIN.search(text)
    amax = AGE_MAX.search(text)
    if amin or amax:
        f["age"] = {"min": int(amin.group(1)) if amin else None, "max": int(amax.group(1)) if amax else None}
    elif m:
        f["age"] = {"min": int(m.group(1)), "max": int(m.group(2))}
    for n, p in enumerate(POSTS):
        for mm in p.finditer(text):
            v = int(mm.group(1))
            if n == 1 and 1990 <= v <= 2100:
                continue
            f["posts"] = {"value": v}
            break
        if "posts" in f:
            break
    return f


def parse_pdf_url(url):
    res = fetch.get(url, timeout=(10, 40), retries=0, binary=True)
    if not res["ok"] or not res["content"]:
        return {"ok": False, "error": res["error"] or "empty"}
    if len(res["content"]) > MAX_BYTES:
        return {"ok": False, "error": "too large"}
    if not res["content"][:5].startswith(b"%PDF"):
        return {"ok": False, "error": "not a pdf"}
    try:
        text = pdf_text(res["content"])
    except Exception as e:
        return {"ok": False, "error": f"pdf: {e.__class__.__name__}"}
    q = text_quality(text)
    usable = text
    if q["legacy_suspect"]:
        usable = " ".join(w for w in text.split(" ") if not LEGACY_HINT.search(w))
    return {"ok": True, "quality": q, "fields": parse_fields(usable), "excerpt": usable[:1200]}
