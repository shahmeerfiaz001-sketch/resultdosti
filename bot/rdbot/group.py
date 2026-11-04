import hashlib
import re

from .text import clean, slugify

TYPE_WORDS = re.compile(
    r"\b(provisional|final|revised|written|online|offline|exam(?:ination)?s?|test|cbt|result|results|merit\s+list|answer\s+keys?|admit\s+cards?|e[\s-]*admit|"
    r"call\s+letters?|hall\s+tickets?|notice|notices|notification|recruitment|advertisement|advt\.?|no\.?|regarding|for\s+the\s+post\s+of|for\s+the\s+posts\s+of|"
    r"post\s+of|posts\s+of|schedule|date|dates|download|link|out|released?|declared|published|marks|score\s*card|cut[\s-]*off|objection|apply|online\s+form|vacancy|vacancies|"
    r"physical\s+efficiency|document\s+verification|interview|corrigendum|addendum|phase|stage|tier|paper|status|tentative|city|intimation|slip|pet|pst|pmt|pre|prelims?|preliminary|mains?|key|card|merit|list|selection|selected|candidates|roll|numbers?|wise|level\s+\d|"
    r"against|regarding|reg|important|details?|upload|uploading|documents?|candidates?|various|application|applications|form|forms|invited|inviting|"
    r"opening|portal|submission|correction|particulars|extension|extended|last|revised|regarding|scribe|surety|bond|office|order|"
    r"i|ii|iii|iv|\d|of|the|for|and|in|on|to|held|dated?|with|from|under|after|before)\b",
    re.I,
)
HINDI_WORDS = re.compile(r"परिणाम|प्रवेश\s*पत्र|उत्तर\s*कुंजी|सूचना|विज्ञापन|भर्ती|संख्या|का|की|के|हेतु|परीक्षा")
YEAR = re.compile(r"\b(20[2-3]\d)(?:\s*-\s*(?:20)?\d{2})?\b")


def year_of(item):
    m = YEAR.search(item.get("title", ""))
    if m:
        return int(m.group(1))
    d = item.get("list_date") or (item.get("first_seen") or "")[:10]
    return int(d[:4]) if d else None


def core_name(title):
    t = clean(title)
    t = re.sub(r"\(.*?\)", " ", t)
    t = re.sub(r"\d{1,2}\s*[./-]\s*\d{1,2}\s*[./-]\s*\d{2,4}", " ", t)
    t = re.sub(r"\b\d{1,4}\s*/\s*\d{2,4}\b", " ", t)
    t = YEAR.sub(" ", t)
    t = TYPE_WORDS.sub(" ", t)
    t = HINDI_WORDS.sub(" ", t)
    t = re.sub(r"[:;,.|\-–—_/&]+", " ", t)
    return clean(t)


LEAD = re.compile(r"^(?:important\s+)?(?:notice|notification|public\s+notice|press\s+note|details?)\s*(?:[:\-]\s*|regarding\s+|for\s+|of\s+|reg\.?\s+)?", re.I)
TAIL = re.compile(r"\s*[-:,]?\s*(?:notice|notification|advertisement|reg\.?|regarding)\s*$", re.I)


def display_name(title):
    t = clean(re.sub(r"\(.*?\)", " ", title))
    for _ in range(2):
        t = LEAD.sub("", t)
        t = TAIL.sub("", t)
    t = clean(t)
    if len(t) > 80:
        cut = t[:80]
        t = cut[: cut.rfind(" ")] if " " in cut else cut
    return t.strip(" -,:")


def group_key(item):
    year = year_of(item) or ""
    if item.get("advt"):
        return f"{item['source']}-advt-{slugify(item['advt'], 20)}"
    cn = core_name(item["title"])
    core = slugify(cn, 48)
    strong = [w for w in re.findall(r"[A-Za-z\u0900-\u097F]{3,}", cn) if w.lower() != item["short"].lower()]
    if not core or len(strong) < 2:
        return None
    return f"{item['source']}-{core}-{year}".strip("-")


def build_groups(items):
    groups = {}
    for it in items:
        k = group_key(it)
        if not k:
            continue
        it["group"] = k
        g = groups.setdefault(k, {"key": k, "source": it["source"], "short": it["short"], "org": it["org"], "scope": it["scope"], "items": [], "year": year_of(it)})
        g["items"].append(it["id"])
    by_id = {it["id"]: it for it in items}
    out = []
    for k, g in groups.items():
        members = [by_id[i] for i in g["items"]]
        jobs = [m for m in members if m["type"] == "job"]
        anchor = jobs[0] if jobs else members[0]
        name = display_name(anchor["title"])
        if len(name) < 8:
            name = f"Advt No. {anchor['advt']}" if anchor.get("advt") else anchor["title"]
        name = clean(f"{g['short']} {name}") if g["short"].lower() not in name.lower() else name
        if g["year"] and str(g["year"]) not in name:
            name = f"{name} {g['year']}"
        g["name"] = name[:110]
        g["slug"] = slugify(g["name"], 80) + "-" + hashlib.sha1(k.encode()).hexdigest()[:5]
        g["types"] = sorted({m["type"] for m in members})
        g["latest"] = max((m.get("list_date") or m["first_seen"][:10]) for m in members)
        out.append(g)
    return sorted(out, key=lambda g: g["latest"], reverse=True)
