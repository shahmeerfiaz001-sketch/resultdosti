import json
import os
import sys
import time

import requests

from . import notify
from .indexing import google_publish, indexnow
from .store import DATA, ROOT, load_json

SITE = json.load(open(os.path.join(ROOT, "site.config.json"), encoding="utf-8"))


def wait_live(url, limit=900):
    t0 = time.time()
    while time.time() - t0 < limit:
        try:
            r = requests.get(url, timeout=20, headers={"Cache-Control": "no-cache"})
            if r.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(30)
    return False


def main():
    data = load_json(os.path.join(DATA, "new.json"), {"new": [], "closed": [], "first_run": False})
    new = data.get("new", [])
    probe = (new[-1]["url"] if new else None) or (data.get("closed") or [None])[0]
    if probe and not wait_live(probe):
        notify.alert(f"Site did not show new page within 15 minutes: {probe}")
        return 0
    urls = [e["url"] for e in new]
    jobs = [e["url"] for e in new if e.get("jobposting")]
    r1 = google_publish(jobs, "URL_UPDATED", budget=150)
    r2 = google_publish(data.get("closed", []), "URL_UPDATED", budget=40)
    r3 = indexnow(urls + data.get("closed", []), SITE["domain"], SITE.get("indexNowKey"))
    sent = 0 if data.get("first_run") else notify.channel_posts(new)
    print(json.dumps({"google_jobs": r1, "google_closed": r2, "indexnow": r3, "telegram": sent}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
