import json
import sys

from playwright.sync_api import sync_playwright

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
PAGES = sys.argv[1:] or ["https://ssc.gov.in/", "https://ssc.gov.in/home/notice-board", "https://fci.gov.in/recruitments.php", "https://www.rrbapply.gov.in/#/auth/landing"]

with sync_playwright() as p:
    b = p.chromium.launch(args=["--no-sandbox"])
    for url in PAGES:
        print("=" * 80)
        print(url)
        pg = b.new_page(user_agent=UA, locale="en-IN")
        seen = []

        def on_resp(r):
            if r.request.resource_type not in ("xhr", "fetch"):
                return
            if "google" in r.url:
                return
            try:
                body = r.text()
            except Exception:
                body = ""
            seen.append((r.status, r.url, body[:1800]))

        pg.on("response", on_resp)
        try:
            pg.goto(url, timeout=60000, wait_until="networkidle")
            pg.wait_for_timeout(4000)
        except Exception as e:
            print("error", e.__class__.__name__, str(e)[:200])
        for st, u, body in seen[:25]:
            print("-" * 40)
            print(st, u)
            print(body)
        pg.close()
    b.close()
