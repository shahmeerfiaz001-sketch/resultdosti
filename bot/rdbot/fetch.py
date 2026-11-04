import ssl
import time
import urllib.robotparser
from urllib.parse import urlparse

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/pdf;q=0.8,*/*;q=0.7",
    "Accept-Language": "en-IN,en;q=0.9,hi;q=0.8",
}

_session = None
_legacy = None
_robots = {}


class _LegacyAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *a, **kw):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.options |= getattr(ssl, "OP_LEGACY_SERVER_CONNECT", 0x4)
        try:
            ctx.set_ciphers("DEFAULT@SECLEVEL=0")
        except ssl.SSLError:
            pass
        ctx.minimum_version = ssl.TLSVersion.TLSv1
        kw["ssl_context"] = ctx
        return super().init_poolmanager(*a, **kw)


def legacy_session():
    global _legacy
    if _legacy is None:
        _legacy = requests.Session()
        _legacy.headers.update(HEADERS)
        _legacy.mount("https://", _LegacyAdapter())
    return _legacy


def session():
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update(HEADERS)
    return _session


def get(url, timeout=(10, 25), retries=1, binary=False):
    last = None
    for attempt in range(retries + 1):
        for verify in (True, False, "legacy"):
            try:
                t0 = time.time()
                if verify == "legacy":
                    r = legacy_session().get(url, timeout=timeout, verify=False, allow_redirects=True)
                else:
                    r = session().get(url, timeout=timeout, verify=verify, allow_redirects=True)
                return {
                    "ok": r.status_code < 400,
                    "status": r.status_code,
                    "url": r.url,
                    "ms": int((time.time() - t0) * 1000),
                    "content": r.content if binary else None,
                    "text": None if binary else _decode(r),
                    "ctype": r.headers.get("content-type", ""),
                    "tls_insecure": verify is not True,
                    "error": None if r.status_code < 400 else f"HTTP {r.status_code}",
                }
            except requests.exceptions.SSLError as e:
                last = f"SSL: {e.__class__.__name__}"
                continue
            except requests.RequestException as e:
                last = f"{e.__class__.__name__}: {str(e)[:160]}"
                break
        time.sleep(2 * (attempt + 1))
    return {"ok": False, "status": 0, "url": url, "ms": 0, "content": None, "text": None, "ctype": "", "tls_insecure": False, "error": last}


def _decode(r):
    if not r.encoding or r.encoding.lower() == "iso-8859-1":
        r.encoding = r.apparent_encoding or "utf-8"
    try:
        return r.text
    except Exception:
        return r.content.decode("utf-8", "replace")


def robots_allowed(url):
    p = urlparse(url)
    root = f"{p.scheme}://{p.netloc}"
    if root not in _robots:
        rp = urllib.robotparser.RobotFileParser()
        res = get(root + "/robots.txt", timeout=(8, 10), retries=0)
        body = res["text"] if res["ok"] and res["text"] and "html" not in (res["ctype"] or "") else ""
        rp.parse(body.splitlines())
        _robots[root] = {"rp": rp, "status": res["status"], "body": body[:2000]}
    return _robots[root]["rp"].can_fetch(UA, url), _robots[root]


def browser_get(url, timeout=45):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {"ok": False, "status": 0, "url": url, "text": None, "error": "playwright not installed", "ms": 0}
    t0 = time.time()
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(args=["--no-sandbox"])
            pg = b.new_page(user_agent=UA, locale="en-IN")
            resp = pg.goto(url, timeout=timeout * 1000, wait_until="networkidle")
            html = pg.content()
            final = pg.url
            status = resp.status if resp else 0
            b.close()
        return {"ok": status < 400 and bool(html), "status": status, "url": final, "text": html, "error": None, "ms": int((time.time() - t0) * 1000), "ctype": "text/html", "tls_insecure": False}
    except Exception as e:
        return {"ok": False, "status": 0, "url": url, "text": None, "error": f"browser: {str(e)[:160]}", "ms": int((time.time() - t0) * 1000), "ctype": "", "tls_insecure": False}
