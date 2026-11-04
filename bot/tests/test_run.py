import json
import os

import pytest

from rdbot import pdfparse, run, store


def test_posts_ignore_year():
    f = pdfparse.parse_fields("Recruitment 2026 Posts of Constable. Total Posts: 7994")
    assert f["posts"]["value"] == 7994
    f = pdfparse.parse_fields("UP Police Recruitment 2026 Posts of Constable")
    assert "posts" not in f


def test_health_never_items():
    st = {}
    msgs = []
    for _ in range(3):
        msgs += run.health(st, "x", True, 0, None)
    assert msgs and "never" in msgs[0]


@pytest.fixture
def tmpdata(tmp_path, monkeypatch):
    d = tmp_path / "data"
    monkeypatch.setattr(store, "DATA", str(d))
    monkeypatch.setattr(store, "ITEMS", str(d / "items.json"))
    monkeypatch.setattr(store, "STATE", str(d / "state" / "sources.json"))
    monkeypatch.setattr(store, "SEEN", str(d / "state" / "pruned.json"))
    monkeypatch.setattr(run, "DATA", str(d))
    monkeypatch.setattr(run, "ITEMS", str(d / "items.json"))
    monkeypatch.setattr(run, "STATE", str(d / "state" / "sources.json"))
    monkeypatch.setattr(run.notify, "alert", lambda t: None)
    monkeypatch.setattr(run.time, "sleep", lambda s: None)
    return d


def test_run_cycle(tmpdata, monkeypatch):
    src = {"id": "bpsc", "name": "Bihar Public Service Commission", "short": "BPSC", "scope": "bihar", "base": "https://bpsc.bihar.gov.in", "lists": [{"url": "https://bpsc.bihar.gov.in/", "hint": ""}]}
    monkeypatch.setattr(run, "load_sources", lambda: [src])
    today = run.ist_today().isoformat()
    found = [{"title": "71st Combined Competitive Examination Admit Card", "url": "https://bpsc.bihar.gov.in/a.pdf", "is_doc": True, "type": "admit", "list_date": today, "context": ""}]
    monkeypatch.setattr(run, "fetch_list", lambda s, l: {"ok": True, "error": None, "items": list(found), "status": 200})
    run.main([])
    n1 = json.load(open(tmpdata / "new.json"))
    assert n1["first_run"] and n1["new"] == []
    run.main([])
    assert not os.path.getsize(tmpdata / "new.json") == 0
    found.append({"title": "71st Combined Competitive Examination Result", "url": "https://bpsc.bihar.gov.in/r.pdf", "is_doc": True, "type": "result", "list_date": today, "context": ""})
    run.main([])
    n3 = json.load(open(tmpdata / "new.json"))
    assert len(n3["new"]) == 1 and "/result/" in n3["new"][0]["url"]
    ex = json.load(open(tmpdata / "exams.json"))
    assert any(len(e["items"]) == 2 for e in ex["exams"])


def test_run_survives_crash(tmpdata, monkeypatch):
    src = {"id": "bad", "name": "Bad", "short": "BAD", "scope": "up", "base": "https://x.gov.in", "lists": [{"url": "https://x.gov.in/", "hint": ""}]}
    monkeypatch.setattr(run, "load_sources", lambda: [src])
    def boom(s, l):
        raise RuntimeError("x")
    monkeypatch.setattr(run, "fetch_list", boom)
    assert run.main([]) == 0
    st = json.load(open(tmpdata / "state" / "sources.json"))
    assert st["bad"]["fails"] == 1


def test_corrupt_items_fails(tmpdata):
    os.makedirs(tmpdata, exist_ok=True)
    (tmpdata / "items.json").write_text("<<<<<<< HEAD")
    with pytest.raises(Exception):
        store.load_items()
