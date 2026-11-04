import re
from urllib.parse import urljoin, urlparse, unquote

from bs4 import BeautifulSoup

from .classify import classify, is_generic, NOISE
from .dates import best_list_date
from .text import clean

CONTAINERS = ("tr", "li", "p", "article", "dd", "td", "div")
SKIP_SCHEMES = ("mailto:", "javascript:", "tel:", "#", "whatsapp:")
DOC_EXT = (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".jpg", ".jpeg", ".png")
DISCOVER = re.compile(r"recruit|vacanc|notice|notification|what'?s\s*new|latest|career|advertisement|result|admit|announcement|news|भर्ती|सूचना|परिणाम|विज्ञापन", re.I)


def _container(a):
    node = a
    for _ in range(7):
        node = node.parent
        if node is None:
            break
        if node.name in ("tr", "li"):
            return node
    node = a
    for _ in range(5):
        node = node.parent
        if node is None:
            return None
        if node.name in CONTAINERS:
            txt = clean(node.get_text(" "))
            if 8 <= len(txt) <= 700 and not is_generic(_strip_row_noise(txt)):
                return node
    return None


LABEL = re.compile(
    r"^(?:(?:the\s+)?(?:advertisements?|notifications?|descriptive\s+notification|notification\s*/\s*order|apply\s+online|online\s+application|corrigendum|addendum|"
    r"information\s+handout|(?:preliminary|prelims?|main|mains|final|interview)?\s*(?:examination\s+)?results?|admit\s+cards?|call\s+letters?|answer\s+keys?|"
    r"recruitments?|vacanc(?:y|ies)|tribunal\s+vacancy|important\s+notices?|notices?|notice\s+board(?:\s+\d{4})?|old\s+advertisements|download\s+forms?|forms?|"
    r"annexure(?:\s*[-\s]?\s*[0-9ivx]+)?|syllabus|instructions?|details|status|login|register|registration|"
    r"[a-z]{2,10}\s+(?:advertisement|recruitment|notification)s?|search\s+in\s+.*|home\b.*|bsf\s+recruitment.*|"
    r"apply\s+online\s*\(.*|adv(?:t|ertisement)?\.?\s*no\.?\s*[:\-]?\s*[\w()\[\]/.\-]+|last\s+date\s+to\s+apply\s*[:\-]?.*)"
    r")(?:\s*(?:\(|\)|/|-|,|english|hindi|हिंदी|अंग्रेजी|\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|to|till))*$",
    re.I,
)
FILE_LIKE = re.compile(r"^[\w\-]+\.(?:aspx?|php|html?|jsp|pdf|docx?)$|^[a-z]+[A-Z]\w*$")
SKIP_HEAD = re.compile(r"^(?:adv(?:t|ertisement)?\.?\s*no|last\s+date|start\s+date|date\s+of|apply\s+online|important\s+dates?|fee\s+payment)\b", re.I)
JUNK = re.compile(r"\bhome\s*/|can\s+check\s+below|^skip\s+to|^menu\b", re.I)


def _label_like(t):
    return bool(LABEL.match(clean(re.sub(r"\(\s*\)", " ", t))))


def _heading_for(a):
    steps = 0
    for el in a.find_all_previous(["h1", "h2", "h3", "h4", "h5", "h6", "strong", "b", "th", "p", "span", "div", "td", "li"]):
        steps += 1
        if steps > 25:
            break
        if el.find("a") is not None and el.name not in ("h1", "h2", "h3", "h4", "h5", "h6", "strong", "b", "th"):
            continue
        txt = _strip_row_noise(clean(el.get_text(" ")))
        if 18 <= len(txt) <= 220 and len(txt.split()) >= 3 and not _label_like(txt) and not JUNK.search(txt) and not SKIP_HEAD.match(txt):
            return txt
    return ""


def good_title(t):
    t = clean(t)
    if len(t) < 8 or FILE_LIKE.match(t) or JUNK.search(t) or _label_like(t):
        return False
    words = t.split()
    if len(words) < 3 and not re.search(r"\d", t):
        return False
    return True


def _title_from_url(href):
    name = unquote(urlparse(href).path.rsplit("/", 1)[-1])
    name = re.sub(r"\.(pdf|docx?|xlsx?|jpe?g|png)$", "", name, flags=re.I)
    name = re.sub(r"[_\-+]+", " ", name)
    return clean(name)


DATE_TXT = re.compile(r"\(?\s*(?:dated?|date\s+of\s+upload|posted\s+on)?\s*[:\-]?\s*\d{1,2}\s*[./-]\s*\d{1,2}\s*[./-]\s*\d{2,4}\s*\)?", re.I)


def _strip_row_noise(text):
    t = re.sub(r"\(\s*\d+(\.\d+)?\s*(kb|mb)\s*\)", " ", text, flags=re.I)
    t = re.sub(r"\|?\s*\d+(\.\d+)?\s*(kb|mb)\b", " ", t, flags=re.I)
    t = re.sub(r"\b(click\s*here|download|view|new|pdf)\b", " ", t, flags=re.I)
    t = re.sub(r"^\s*\[?\s*\d{1,4}\s*[.)\]]?\s+", "", clean(t))
    t = re.sub(r"^[A-Za-z]{2,12}(?:/[A-Za-z0-9-]+){1,4}\s+", "", t)
    return clean(t)


def _tidy_title(t):
    t = re.sub(r"(?:" + DATE_TXT.pattern + r")\s*$", " ", t, flags=re.I)
    t = re.sub(r"^\s*\[?\s*\d{1,2}\s*[./-]\s*\d{1,2}\s*[./-]\s*\d{2,4}\s*\]?\s*[:\-]?", " ", t)
    t = re.sub(r"\(\s*(?:dated?|date\s+of\s+upload|posted\s+on)\s*[:\-]?\s*\d{1,2}\s*[./-]\s*\d{1,2}\s*[./-]\s*\d{2,4}\s*\)", " ", t, flags=re.I)
    t = re.sub(r"^\s*\[\s*\]\s*[:\-]?\s*", "", t)
    t = re.sub(r"^\s*[:\-|]+\s*", "", t)
    t = re.sub(r"^\s*\d{1,5}\s+(?=[A-Za-z\u0900-\u097F])", "", clean(t))
    t = re.sub(r"\s+(?:apply|apply\s+here|click|read\s+more|more)\s*$", "", t, flags=re.I)
    t = re.sub(r"\s+(?:posted|published|uploaded)\s+on\s+.*$", "", t, flags=re.I)
    t = re.sub(r"\s*[|\u0964]?\s*\[\s*[^\]]{1,30}\]\s*$", "", t)
    t = re.sub(r"^\s*(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+20\d{2}\s+", "", t, flags=re.I)
    t = re.sub(r"\s*-\s*(?:hindi|english)(?:\s*/\s*(?:hindi|english))?\s*$", "", t, flags=re.I)
    t = re.sub(r"\(\s*\)", " ", t)
    return clean(t).strip(" -:|")


def extract(html, page_url, hint="", today=None, max_items=400):
    soup = BeautifulSoup(html or "", "lxml")
    for bad in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        bad.decompose()
    items = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.lower().startswith(SKIP_SCHEMES):
            continue
        url = urljoin(page_url, href)
        if not url.startswith(("http://", "https://")):
            continue
        if url in seen:
            continue
        raw = clean(a.get_text(" "))
        tattr = clean(a.get("title", ""))
        if raw.endswith("..") and len(tattr) > len(raw) - 2 and tattr.lower().startswith(raw.rstrip(".").lower()[:20]):
            raw = tattr
        anchor = _strip_row_noise(raw or tattr or clean(a.get("aria-label", "")))
        box = _container(a)
        ctx = clean(box.get_text(" ")) if box else anchor
        title = anchor
        if not title or is_generic(title) or len(title) < 8:
            title = _strip_row_noise(ctx) if ctx and len(ctx) <= 300 else ""
        if title and _label_like(_tidy_title(title)):
            alt = _strip_row_noise(ctx) if ctx and len(ctx) <= 300 else ""
            if alt and not _label_like(_tidy_title(alt)) and len(alt) > len(title) + 10:
                title = alt
            else:
                head = _heading_for(a)
                if not head:
                    continue
                lab = _tidy_title(title)
                title = f"{head} - {lab}" if lab and lab.lower() not in head.lower() and len(lab) <= 40 else head
                ctx = clean(head + " " + ctx)
        if not title or len(title) < 8:
            title = _title_from_url(url)
        title = _tidy_title(title)[:260]
        if not good_title(title) or NOISE.search(title):
            continue
        kind = classify(title, url, hint)
        if not kind:
            continue
        seen.add(url)
        d = best_list_date(ctx, today=today, url=url)
        items.append({
            "title": title,
            "url": url,
            "is_doc": urlparse(url).path.lower().endswith(DOC_EXT),
            "type": kind,
            "list_date": d.isoformat() if d else None,
            "context": ctx[:400],
        })
        if len(items) >= max_items:
            break
    best = {}
    order = []
    for it in items:
        key = (it["title"].lower(), it["list_date"])
        if key not in best:
            best[key] = it
            order.append(key)
        elif it["is_doc"] and not best[key]["is_doc"]:
            best[key] = it
    return [best[k] for k in order]


def discover_lists(html, page_url):
    soup = BeautifulSoup(html or "", "lxml")
    host = urlparse(page_url).netloc
    out = []
    seen = set()
    for a in soup.find_all("a", href=True):
        url = urljoin(page_url, a["href"].strip())
        if urlparse(url).netloc != host or url in seen:
            continue
        txt = clean(a.get_text(" ")) or clean(a.get("title", ""))
        if not txt or len(txt) > 60:
            continue
        if DISCOVER.search(txt) and not urlparse(url).path.lower().endswith(DOC_EXT):
            seen.add(url)
            out.append({"text": txt, "url": url})
    return out[:40]


def page_title(html):
    soup = BeautifulSoup(html or "", "lxml")
    return clean(soup.title.get_text()) if soup.title else ""
