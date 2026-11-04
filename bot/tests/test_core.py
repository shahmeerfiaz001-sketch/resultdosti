import os
from datetime import date

from rdbot.extract import extract
from rdbot.dates import find_dates, best_list_date
from rdbot.classify import classify, advt_number

FX = os.path.join(os.path.dirname(__file__), "fixtures")
TODAY = date(2026, 11, 4)


def load(n):
    with open(os.path.join(FX, n), encoding="utf-8") as f:
        return f.read()


def test_dates():
    assert find_dates("Last date: 15-11-2026") == [date(2026, 11, 15)]
    assert find_dates("15 November 2026")[0] == date(2026, 11, 15)
    assert find_dates("Nov 5, 2026")[0] == date(2026, 11, 5)
    assert find_dates("१५ नवंबर २०२६")[0] == date(2026, 11, 15)
    assert find_dates("2026-10-30")[0] == date(2026, 10, 30)
    assert find_dates("12.10.2026")[0] == date(2026, 10, 12)
    assert find_dates("31/02/2026") == []
    assert best_list_date("posted 01/11/2026 exam 20/12/2026", today=TODAY) == date(2026, 11, 1)


def test_classify():
    assert classify("Provisional Answer Key of X") == "answer"
    assert classify("Admit Card for Y") == "admit"
    assert classify("Written Result: CMS 2026") == "result"
    assert classify("Recruitment Advertisement No. 17/2026") == "job"
    assert classify("Tender for supply of printers") is None
    assert classify("सिपाही भर्ती का परिणाम") == "result"
    assert classify("Photo Gallery") is None
    assert advt_number("Advertisement No. 05/2026 for recruitment") == "05/2026"
    assert advt_number("विज्ञापन संख्या 02/2026") == "02/2026"


def test_btsc():
    items = extract(load("btsc.html"), "https://btsc.bihar.gov.in/important-notices", today=TODAY)
    titles = [i["title"] for i in items]
    assert not any("Tender" in t for t in titles)
    job = [i for i in items if i["type"] == "job"][0]
    assert job["url"].endswith("advt-05-2026.pdf")
    assert job["list_date"] == "2026-10-28"
    assert "Assistant Engineer" in job["title"]
    ak = [i for i in items if i["type"] == "answer"][0]
    assert ak["list_date"] == "2026-10-30"
    adm = [i for i in items if i["type"] == "admit"][0]
    assert "Lab Technician" in adm["title"]
    assert adm["list_date"] == "2026-11-02"


def test_csbc():
    items = extract(load("csbc.html"), "https://csbc-bih.bihar.gov.in/notifications", today=TODAY)
    kinds = {i["type"] for i in items}
    assert "result" in kinds and "notice" in kinds
    assert len(items) == 2
    assert all(i["list_date"] for i in items)


def test_upsc():
    items = extract(load("upsc.html"), "https://upsc.gov.in/whats-new", today=TODAY)
    byt = {i["type"]: i for i in items}
    assert byt["result"]["url"] == "https://upsc.gov.in/sites/default/files/WR-CMS-2026-engl-311026.pdf"
    assert byt["job"]["list_date"] == "2026-11-01"
    assert "notice" in byt
    assert not any(i["url"].startswith("mailto") for i in items)


def test_pdf_fields():
    from rdbot.pdfparse import pdf_text, parse_fields
    from rdbot.validate import validate, tier
    with open(os.path.join(FX, "advt.pdf"), "rb") as f:
        t = pdf_text(f.read())
    fields = parse_fields(t)
    item = {"type": "job", "title": "Advertisement No. 07/2026 Junior Assistant Recruitment", "list_date": "2026-11-03", "first_seen": "2026-11-04T00:00:00", "context": "Last date 04/12/2026"}
    v = validate(item, {"fields": fields}, today=TODAY)
    assert v["last_date"] == {"value": "2026-12-04", "confidence": "confirmed"}
    assert v["start_date"]["value"] == "2026-11-05"
    assert v["exam_date"]["value"] == "2027-01-18"
    assert v["fee"]["values"] == [250, 500]
    assert v["age"]["min"] == 18 and v["age"]["max"] == 40
    assert v["posts"]["value"] == 1250
    assert tier(item, v) == 2


def test_validate_rejects_bad():
    from rdbot.validate import validate
    item = {"type": "job", "title": "x" * 20, "list_date": "2026-11-03", "first_seen": "2026-11-04", "context": ""}
    bad = {"fields": {"last_date": {"values": ["2026-10-01"]}, "start_date": {"values": ["2026-12-30"]}, "fee": {"values": [99999]}, "age": {"min": 40, "max": 18}, "posts": {"value": 0}}}
    assert validate(item, bad, today=TODAY) == {}
