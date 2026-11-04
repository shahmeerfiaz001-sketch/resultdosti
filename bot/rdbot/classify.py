import re

from .text import clean

RULES = [
    ("answer", [r"answer\s*key", r"answer\s*sheet", r"provisional\s+key", r"final\s+key", r"उत्तर\s*कुंजी", r"उत्तरकुंजी", r"objection"]),
    ("admit", [r"admit\s*card", r"e[\s-]*admit", r"call\s*letter", r"hall\s*ticket", r"प्रवेश\s*पत्र", r"exam\s*city", r"city\s*intimation", r"admission\s*certificate"]),
    ("result", [r"\bresult", r"merit\s*list", r"select(ed|ion)\s+list", r"(provisionally\s+)?selected\s+candidates", r"shortlisted\s+candidates", r"final\s+selection", r"score\s*card", r"marks\s+of", r"cut[\s-]*off", r"qualified\s+candidates", r"परिणाम", r"रिजल्ट", r"मेधा\s*सूची", r"चयन\s*सूची"]),
    ("syllabus", [r"syllabus", r"exam(ination)?\s+pattern", r"scheme\s+of\s+exam", r"पाठ्यक्रम"]),
    ("admission", [r"admission", r"counsell?ing", r"seat\s+allotment", r"प्रवेश\s+हेतु"]),
    ("notice", [r"corrigendum", r"addendum", r"postpone", r"cancell?ation", r"rebuttal", r"important\s+notices?\b", r"extension\s+(of|in)\b", r"extended", r"शुद्धि\s*पत्र", r"स्थगित", r"physical\s+(efficiency|standard|measurement)", r"\bp\.?e\.?t\b", r"\bp\.?s\.?t\b", r"document\s+verification", r"\bd\.?v\.?\s+(schedule|notice)", r"interview\s+(schedule|programme|program|letter)", r"exam(ination)?\s+(schedule|date|programme)", r"date\s*sheet", r"शारीरिक\s+दक्षता", r"साक्षात्कार"]),
    ("job", [r"recruit", r"advertisement", r"\badvt\b", r"vacanc", r"notification", r"apply\s+online", r"online\s+application", r"engagement\s+of", r"walk[\s-]*in", r"\bposts?\s+of\b", r"\bcen\s*\d", r"भर्ती", r"विज्ञापन", r"रिक्ति", r"नियुक्ति", r"आवेदन"]),
    ("notice", [r"notice", r"schedule", r"date\s*sheet", r"exam\s+date", r"interview", r"document\s+verification", r"\bdv\b", r"physical", r"\bpet\b", r"\bpst\b", r"corrigendum", r"addendum", r"सूचना", r"विज्ञप्ति", r"शुद्धि\s*पत्र"]),
]
COMPILED = [(k, [re.compile(p, re.I) for p in pats]) for k, pats in RULES]

NOISE = re.compile(
    r"tender|quotation|auction|\brfp\b|\beoi\b|expression\s+of\s+interest|e-?procurement|"
    r"\brti\b|right\s+to\s+information|annual\s+report|budget|citizen\s+charter|screen\s*reader|sitemap|site\s*map|"
    r"contact\s+us|about\s+us|privacy|terms|disclaimer|copyright|hyperlink|accessibility|feedback|faq|help\s*desk|"
    r"photo\s+gallery|video\s+gallery|press\s+release|newsletter|holiday\s+list|transfer\s+order|promotion\s+order|"
    r"pension|gpf|salary\s+slip|leave\s+rules|seniority|inventory|purchase|website\s+policy|"
    r"chambers?\b|guest\s*house|advocates?\b|debar|chargeback|refund|enlisted\s+former|cause\s+list|roster|court\s+fee|"
    r"logindob|screen\s+reader|बिहार\s+सूचना\s+आयोग|सूचना\s+पट्ट|"
    r"निविदा|टेंडर|सूचना\s+का\s+अधिकार",
    re.I,
)
GENERIC = re.compile(r"^(click\s*here|here|download|view|pdf|new|details?|more|read\s*more|open|link|apply|hindi|english|हिंदी|देखें|यहाँ\s*क्लिक\s*करें)$", re.I)


def classify(title, url="", hint=""):
    t = clean(title)
    if NOISE.search(t):
        return None
    for kind, pats in COMPILED:
        if any(p.search(t) for p in pats):
            if kind == "admission" and re.search(r"admission\s+certificate", t, re.I):
                return "admit"
            return kind
    u = (url or "").lower()
    if hint and (u.endswith(".pdf") or "download" in u or "upload" in u):
        return hint
    return None


def is_generic(text):
    return bool(GENERIC.match(clean(text)))


ADVT = re.compile(r"(?:advt\.?|advertisement|विज्ञापन|cen|notice)\s*(?:no\.?|number|संख्या|सं\.?)?\s*[:\-]?\s*([0-9]{1,4}\s*/\s*(?:20)?[0-9]{2,4}(?:\s*-\s*[0-9]{2,4})?)", re.I)


def advt_number(text):
    m = ADVT.search(clean(text))
    if not m:
        return None
    return re.sub(r"\s+", "", m.group(1))
