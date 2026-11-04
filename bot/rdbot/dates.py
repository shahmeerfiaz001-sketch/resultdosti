import re
from datetime import date, datetime, timezone

from .text import clean

MONTHS = {
    "jan": 1, "january": 1, "जनवरी": 1,
    "feb": 2, "february": 2, "फरवरी": 2, "फ़रवरी": 2,
    "mar": 3, "march": 3, "मार्च": 3,
    "apr": 4, "april": 4, "अप्रैल": 4, "अप्रेल": 4,
    "may": 5, "मई": 5,
    "jun": 6, "june": 6, "जून": 6,
    "jul": 7, "july": 7, "जुलाई": 7,
    "aug": 8, "august": 8, "अगस्त": 8,
    "sep": 9, "sept": 9, "september": 9, "सितंबर": 9, "सितम्बर": 9,
    "oct": 10, "october": 10, "अक्टूबर": 10, "अक्तूबर": 10,
    "nov": 11, "november": 11, "नवंबर": 11, "नवम्बर": 11,
    "dec": 12, "december": 12, "दिसंबर": 12, "दिसम्बर": 12,
}
MONTH_ALT = "|".join(sorted((re.escape(k) for k in MONTHS), key=len, reverse=True))

NUMERIC = re.compile(r"(?<!\d)(\d{1,2})\s*[./-]\s*(\d{1,2})\s*[./-]\s*(\d{4}|\d{2})(?!\d)")
ISO = re.compile(r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)")
DMY_WORD = re.compile(r"(?<!\d)(\d{1,2})(?:st|nd|rd|th)?\s*[-,.]?\s*(" + MONTH_ALT + r")[a-z]*\.?\s*[-,.]?\s*(\d{4})", re.I)
MDY_WORD = re.compile(r"(" + MONTH_ALT + r")[a-z]*\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})", re.I)


def _mk(y, m, d):
    try:
        y = int(y)
        if y < 100:
            y += 2000
        dt = date(y, int(m), int(d))
    except (ValueError, TypeError):
        return None
    if dt.year < 2000 or dt.year > 2100:
        return None
    return dt


def find_dates(text):
    t = clean(text)
    found = []
    for m in ISO.finditer(t):
        dt = _mk(m.group(1), m.group(2), m.group(3))
        if dt:
            found.append((m.start(), dt))
    for m in NUMERIC.finditer(t):
        dt = _mk(m.group(3), m.group(2), m.group(1))
        if dt:
            found.append((m.start(), dt))
    for m in DMY_WORD.finditer(t):
        mon = MONTHS.get(m.group(2).lower()) or MONTHS.get(m.group(2).lower()[:3])
        dt = _mk(m.group(3), mon, m.group(1)) if mon else None
        if dt:
            found.append((m.start(), dt))
    for m in MDY_WORD.finditer(t):
        mon = MONTHS.get(m.group(1).lower()) or MONTHS.get(m.group(1).lower()[:3])
        dt = _mk(m.group(3), mon, m.group(2)) if mon else None
        if dt:
            found.append((m.start(), dt))
    found.sort(key=lambda x: x[0])
    out = []
    for _, dt in found:
        if dt not in out:
            out.append(dt)
    return out


def best_list_date(text, today=None, url=""):
    today = today or date.today()
    cands = [d for d in find_dates(text) if (d - today).days <= 1 and (today - d).days <= 730]
    if not cands and url:
        cands = [d for d in find_dates(url.replace("_", " ")) if (d - today).days <= 1 and (today - d).days <= 730]
    if not cands and url:
        m = re.search(r"/(20[1-3]\d)/(0[1-9]|1[0-2])/", url)
        if m:
            d = date(int(m.group(1)), int(m.group(2)), 1)
            if (today - d).days <= 730 and (d - today).days <= 1:
                cands.append(d)
    if not cands and url:
        for m in re.finditer(r"(?<!\d)(1[4-9]\d{8})(?!\d)", url):
            try:
                d = datetime.fromtimestamp(int(m.group(1)), tz=timezone.utc).date()
            except (ValueError, OSError):
                continue
            if (d - today).days <= 1 and (today - d).days <= 730:
                cands.append(d)
    if not cands:
        return None
    return max(cands)


def iso(d):
    return d.isoformat() if d else None
