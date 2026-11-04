import json
import os
import sys
import time
from datetime import date

from . import fetch
from .adapters import ADAPTERS
from .extract import extract, discover_lists, page_title
from .store import ROOT, DATA, save_json, now_iso

CONFIG = os.path.join(ROOT, "bot", "config", "sources.json")


def load_sources(include_disabled=False):
    with open(CONFIG, encoding="utf-8") as f:
        src = json.load(f)
    return src if include_disabled else [s for s in src if s.get("enabled", True)]


def probe_source(src, use_browser=True):
    out = {"id": src["id"], "name": src["name"], "scope": src["scope"], "lists": [], "robots": None, "verdict": "fail"}
    for lst in src["lists"]:
        url = lst["url"]
        allowed, rob = fetch.robots_allowed(url)
        out["robots"] = {"status": rob["status"], "allowed": allowed, "snippet": rob["body"][:400]}
        if src.get("api") in ADAPTERS:
            a = ADAPTERS[src["api"]]()
            res = {"url": url, "ok": a["ok"], "status": a["status"], "error": a["error"], "text": "", "ms": 0, "tls_insecure": False}
            items, via = a["items"], "api"
        else:
            res = fetch.get(url)
            via = "requests"
            items = extract(res["text"], res["url"], lst.get("hint", "")) if res["ok"] else []
        if (not res["ok"] or len(items) == 0) and use_browser and src.get("browser"):
            b = fetch.browser_get(url)
            if b["ok"]:
                bi = extract(b["text"], b["url"], lst.get("hint", ""))
                if len(bi) > len(items):
                    res, items, via = b, bi, "browser"
        entry = {
            "url": url,
            "final_url": res["url"],
            "ok": res["ok"],
            "status": res["status"],
            "error": res["error"],
            "ms": res["ms"],
            "via": via,
            "tls_insecure": res.get("tls_insecure", False),
            "page_title": page_title(res["text"]) if res.get("text") else "",
            "html_kb": round(len(res["text"] or "") / 1024, 1),
            "robots_allowed": allowed,
            "items": len(items),
            "dated": sum(1 for i in items if i["list_date"]),
            "types": {},
            "sample": items[:6],
            "discovered": discover_lists(res["text"], res["url"]) if res.get("text") else [],
        }
        for i in items:
            entry["types"][i["type"]] = entry["types"].get(i["type"], 0) + 1
        out["lists"].append(entry)
        time.sleep(1.5)
    good = [l for l in out["lists"] if l["ok"] and l["items"] > 0 and l["robots_allowed"]]
    if good:
        out["verdict"] = "ok" if any(l["dated"] for l in good) else "ok-nodates"
    elif any(l["ok"] for l in out["lists"]):
        out["verdict"] = "loaded-no-items"
    return out


def to_markdown(report):
    lines = [f"# Source probe report", f"Run: {report['run']}", ""]
    counts = {}
    for s in report["sources"]:
        counts[s["verdict"]] = counts.get(s["verdict"], 0) + 1
    lines.append("Summary: " + ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())))
    lines.append("")
    lines.append("| Source | Verdict | HTTP | Items | Dated | Via | Robots | Error |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for s in report["sources"]:
        for l in s["lists"]:
            lines.append(f"| {s['id']} | {s['verdict']} | {l['status']} | {l['items']} | {l['dated']} | {l['via']} | {'yes' if l['robots_allowed'] else 'NO'} | {(l['error'] or '')[:60]} |")
    lines.append("")
    for s in report["sources"]:
        lines.append(f"## {s['id']} — {s['verdict']}")
        for l in s["lists"]:
            lines.append(f"- {l['url']} → {l['final_url']} ({l['status']}, {l['ms']} ms, {l['html_kb']} KB) title: {l['page_title'][:80]}")
            for it in l["sample"]:
                lines.append(f"  - [{it['type']}] {it['list_date'] or '-'} | {it['title'][:110]} | {it['url'][:120]}")
            if l["items"] == 0 and l["discovered"]:
                lines.append("  - discovered list links: " + "; ".join(f"{d['text']} → {d['url']}" for d in l["discovered"][:12]))
        lines.append("")
    return "\n".join(lines)


def main(argv=None):
    argv = argv or sys.argv[1:]
    only = set(a for a in argv if not a.startswith("-"))
    use_browser = "--no-browser" not in argv
    srcs = [s for s in load_sources() if not only or s["id"] in only]
    report = {"run": now_iso(), "today": date.today().isoformat(), "sources": []}
    for s in srcs:
        r = probe_source(s, use_browser=use_browser)
        report["sources"].append(r)
        print(f"{s['id']:16} {r['verdict']:16} " + " ".join(f"{l['status']}/{l['items']}" for l in r["lists"]), flush=True)
    os.makedirs(os.path.join(DATA, "probe"), exist_ok=True)
    save_json(os.path.join(DATA, "probe", "report.json"), report)
    with open(os.path.join(DATA, "probe", "report.md"), "w", encoding="utf-8") as f:
        f.write(to_markdown(report))
    return report


if __name__ == "__main__":
    main()
