import html
import os
import time

import requests

API = "https://api.telegram.org/bot{token}/sendMessage"


def _send(chat, text):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token or not chat:
        return False
    try:
        r = requests.post(API.format(token=token), json={"chat_id": chat, "text": text[:4000], "parse_mode": "HTML", "disable_web_page_preview": False}, timeout=20)
        if r.status_code == 429:
            time.sleep(int(r.json().get("parameters", {}).get("retry_after", 5)) + 1)
            r = requests.post(API.format(token=token), json={"chat_id": chat, "text": text[:4000], "parse_mode": "HTML"}, timeout=20)
        return r.ok
    except requests.RequestException:
        return False


def alert(text):
    return _send(os.environ.get("TELEGRAM_ALERT_CHAT"), "⚠️ " + html.escape(text))


LABEL = {"job": "🆕 New Job", "admit": "🎫 Admit Card", "result": "✅ Result", "answer": "📝 Answer Key", "syllabus": "📚 Syllabus", "admission": "🎓 Admission", "notice": "📢 Notice"}


def channel_posts(entries, limit=15):
    chat = os.environ.get("TELEGRAM_CHANNEL")
    if not chat:
        return 0
    sent = 0
    for e in entries[:limit]:
        lines = [f"<b>{LABEL.get(e['type'], 'Update')}</b>", html.escape(e["title"]), f"🏛 {html.escape(e['short'])}"]
        if e.get("last_date"):
            lines.append(f"⏳ Last date: {e['last_date']}")
        lines.append(f"🔗 {e['url']}")
        if _send(chat, "\n".join(lines)):
            sent += 1
        time.sleep(3.2)
    return sent
