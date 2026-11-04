import json
import sys

sys.path.insert(0, ".")
from rdbot import fetch
from rdbot.extract import discover_lists, extract

URLS = sys.argv[1:] or [
    "https://ssc.gov.in/api/general-website/portal/notice-boards?page=1&limit=5&contentType=notice-boards&key=createdAt&order=DESC&isAttachment=true&language=english",
    "https://ssc.gov.in/api/general-website/portal//lastUpdates",
    "https://ssc.gov.in/api/general-website/portal/records?page=1&limit=5&contentType=browse-exam&key=createdAt&order=DESC&isPaginationRequired=false&isAttachment=true",
    "https://fci.gov.in/admin/api/getWhatsNewDetails",
    "https://fci.gov.in/admin/api/ManageNewsPage/viewall",
    "https://opportunities.rbi.org.in/Scripts/Vacancies.aspx",
    "https://crpf.gov.in/",
    "https://www.cisf.gov.in/",
    "https://www.employmentnews.gov.in/NEW/Home.aspx",
    "https://pib.gov.in/allRel.aspx",
    "https://www.ncs.gov.in/",
    "https://indianrailways.gov.in/",
]

for u in URLS:
    print("=" * 80)
    print(u)
    r = fetch.get(u, timeout=(10, 30), retries=0)
    print("status", r["status"], "ctype", r.get("ctype"), "error", r.get("error"))
    body = r.get("text") or ""
    if "json" in (r.get("ctype") or "") or body.strip().startswith(("{", "[")):
        print(body[:3500])
        continue
    items = extract(body, r["url"], "")
    print("items", len(items))
    for i in items[:12]:
        print("  ", i["type"], i["list_date"], i["title"][:100], "|", i["url"][:110])
    print("discover:")
    for d in discover_lists(body, r["url"])[:25]:
        print("  ", d["text"][:50], "|", d["url"][:120])
