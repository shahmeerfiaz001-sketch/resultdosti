import json
import subprocess
import sys

URLS = sys.argv[1:] or [
    "https://ssc.gov.in/",
    "https://www.epfindia.gov.in/site_en/Recruitments.php",
    "https://rectt.bsf.gov.in/",
    "https://upsssc.gov.in/",
    "https://biharboardonline.bihar.gov.in/",
    "https://opportunities.rbi.org.in/scripts/index.aspx",
    "https://fci.gov.in/recruitments.php",
    "https://www.rrbapply.gov.in/",
]
UAS = {
    "chrome": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
    "curl": "curl/8.5.0",
}


def curl(url, ua, extra=()):
    cmd = ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code} %{size_download} %{time_total} %{http_version}", "-m", "25", "-A", ua, "-L", *extra, url]
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=40).stdout.strip() or "err"
    except Exception as e:
        return f"exc {e.__class__.__name__}"


def browser(url):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {"error": "no playwright"}
    out = {"xhr": []}
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(args=["--no-sandbox"])
            pg = b.new_page(user_agent=UAS["chrome"], locale="en-IN")
            pg.on("response", lambda r: out["xhr"].append(f"{r.status} {r.request.resource_type} {r.url[:160]}") if r.request.resource_type in ("xhr", "fetch", "document") else None)
            resp = pg.goto(url, timeout=45000, wait_until="networkidle")
            pg.wait_for_timeout(3000)
            out["status"] = resp.status if resp else None
            out["title"] = pg.title()
            out["links"] = pg.eval_on_selector_all("a", "els => els.length")
            out["text"] = pg.inner_text("body")[:400]
            b.close()
    except Exception as e:
        out["error"] = f"{e.__class__.__name__}: {str(e)[:200]}"
    out["xhr"] = out["xhr"][:40]
    return out


for u in URLS:
    print("=" * 80)
    print(u)
    print("curl chrome h1.1 :", curl(u, UAS["chrome"], ["--http1.1"]))
    print("curl chrome h2   :", curl(u, UAS["chrome"], ["--http2"]))
    print("curl plain       :", curl(u, UAS["curl"]))
    print("curl insecure tls:", curl(u, UAS["chrome"], ["-k", "--tlsv1.0", "--ciphers", "DEFAULT@SECLEVEL=0"]))
    print("browser          :", json.dumps(browser(u), ensure_ascii=False, indent=1)[:3000])
