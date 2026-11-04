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


ACRONYMS = {
    "UP", "UPSC", "SSC", "RRB", "IBPS", "SBI", "RBI", "NTA", "CBSE", "BSF", "CRPF", "CISF", "ITBP", "SSB", "AIIMS", "ESIC", "LIC", "EPFO", "FCI",
    "DSSSB", "UPPSC", "UPSSSC", "UPPRPB", "UPMSP", "UPPCL", "BPSC", "BSSC", "CSBC", "BPSSC", "BTSC", "BSEB", "SHS", "BCECEB", "NHM", "HC",
    "PCS", "IAS", "IPS", "PET", "PST", "PMT", "DV", "CBT", "CEN", "ITI", "ANM", "GNM", "TGT", "PGT", "PRT", "CHO", "AYUSH", "NEET", "JEE",
    "UGC", "NET", "CUET", "CSIR", "ICAR", "NIFT", "CMAT", "GPAT", "NCET", "AISSEE", "OMR", "SCO", "PO", "SO", "RO", "ARO", "ASI", "SI",
    "ASO", "LDC", "UDC", "MTS", "CHSL", "CGL", "GD", "JE", "ALP", "NTPC", "IT", "HR", "OBC", "SC", "ST", "EWS", "PWD", "PH", "MBBS", "BDS",
    "MD", "MS", "DNB", "PG", "UG", "B.ED", "D.EL.ED", "BCECE", "PGMAC", "UGMAC", "PGDAC", "DET", "FMT", "CCE", "CRP", "PSU", "AAO", "AE",
    "DEO", "PA", "PS", "RSBL", "CWC", "NABARD", "SIDBI", "EXIM", "ECGC", "IFFCO", "DRDO", "ISRO", "BEL", "BHEL", "NTPC", "ONGC", "IOCL",
    "MP", "MLA", "TET", "CTET", "STET", "UPTET", "PSC", "IIT", "NIT", "TOR", "OT", "IV", "II", "III", "VI", "VII", "VIII", "IX", "XI", "XII",
}


def title_case_fix(s):
    s = clean(s)
    letters = [c for c in s if c.isalpha() and c.isascii()]
    if len(s) > 12 and letters and sum(c.isupper() for c in letters) / len(letters) > 0.7:
        small = {"of", "for", "and", "the", "in", "on", "to", "a", "an", "at", "by", "or", "under", "against", "with", "from"}
        words = []
        for i, w in enumerate(s.split(" ")):
            core = re.sub(r"^[^\w]+|[^\w.]+$", "", w)
            lw = w.lower()
            if re.search(r"[\d/]", w) or core.upper() in ACRONYMS or (core.isalpha() and len(core) >= 3 and not re.search(r"[AEIOU]", core.upper())):
                words.append(w)
            elif i and lw in small:
                words.append(lw)
            else:
                words.append(w[:1].upper() + w[1:].lower() if w[:1].isalpha() else w[:1] + w[1:2].upper() + w[2:].lower())
        return " ".join(words)
    return s
