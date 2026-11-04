from rdbot.extract import extract, good_title

SBI = """<html><body><div class="opening"><h4>RECRUITMENT OF SPECIALIST CADRE OFFICERS ON REGULAR BASIS (ADVERTISEMENT NO: CRPD/SCO/2026-27/29)</h4>
<ul><li><a href="/docs/adv29.pdf">ADVERTISEMENT( English ) ( )</a></li><li><a href="https://ibpsreg.ibps.in/sbi29/">APPLY ONLINE (04.11.2026 to</a></li></ul></div>
<div class="opening"><h4>RECRUITMENT OF PROBATIONARY OFFICERS 2026</h4><ul><li><a href="/docs/po-res.pdf">PRELIMINARY EXAMINATION RESULT</a></li></ul></div>
<p><a href="/notices.htm">Notices.htm</a> <a href="/rec">Recruitments</a> <a href="/x">Home/ Important Information/ Vacancy</a></p>
<table><tr><td>3200</td><td><a href="/n/3200.pdf">Important Notice regarding Advt. No-30/2026 SCIENTIFIC ASSISTANT</a></td><td>25/09/2026</td></tr></table>
</body></html>"""


def test_sbi_headings():
    items = extract(SBI, "https://sbi.bank.in/web/careers/current-openings")
    titles = [i["title"] for i in items]
    assert any(t.startswith("RECRUITMENT OF SPECIALIST CADRE OFFICERS") for t in titles)
    assert any("PROBATIONARY OFFICERS" in t and "RESULT" in t for t in titles)
    assert not any(t in ("Notices.htm", "Recruitments") or "Home/" in t for t in titles)
    sci = [i for i in items if "SCIENTIFIC" in i["title"]][0]
    assert sci["title"].startswith("Important Notice") and sci["type"] == "notice"


def test_good_title():
    assert not good_title("LoginDOB.aspx")
    assert not good_title("IBPS Advertisement")
    assert not good_title("ADMIT CARDS")
    assert good_title("UP Police Constable Recruitment 2026")
    assert good_title("Recruitment of AAO Generalists Specialists Assistant Engineers 2025")
