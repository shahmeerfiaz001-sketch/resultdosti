import re
import unicodedata

DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
WS = re.compile(r"\s+")


def clean(s):
    if not s:
        return ""
    s = unicodedata.normalize("NFC", str(s)).translate(DEV_DIGITS)
    s = s.replace(" ", " ").replace("​", "").replace("﻿", "")
    return WS.sub(" ", s).strip()


def slugify(s, limit=80):
    s = clean(s).lower()
    s = re.sub(r"&", " and ", s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    if len(s) > limit:
        s = s[:limit].rsplit("-", 1)[0]
    return s or "notice"


def has_devanagari(s):
    return bool(re.search(r"[ऀ-ॿ]", s or ""))


def title_case_fix(s):
    s = clean(s)
    if s.isupper() and len(s) > 12:
        small = {"of", "for", "and", "the", "in", "on", "to", "a", "an", "at", "by"}
        words = []
        for i, w in enumerate(s.split(" ")):
            lw = w.lower()
            if re.fullmatch(r"[A-Z]{2,6}", w) and lw not in small:
                words.append(w)
            elif i and lw in small:
                words.append(lw)
            else:
                words.append(w.capitalize())
        return " ".join(words)
    return s
