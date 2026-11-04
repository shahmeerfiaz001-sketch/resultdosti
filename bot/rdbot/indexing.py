import base64
import json
import os
import time

import requests

TOKEN_URL = "https://oauth2.googleapis.com/token"
PUBLISH_URL = "https://indexing.googleapis.com/v3/urlNotifications:publish"
SCOPE = "https://www.googleapis.com/auth/indexing"


def _b64(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=")


def _token(sa):
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding

    now = int(time.time())
    header = _b64(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    claim = _b64(json.dumps({"iss": sa["client_email"], "scope": SCOPE, "aud": TOKEN_URL, "iat": now, "exp": now + 3600}).encode())
    key = serialization.load_pem_private_key(sa["private_key"].encode(), password=None)
    sig = _b64(key.sign(header + b"." + claim, padding.PKCS1v15(), hashes.SHA256()))
    jwt = (header + b"." + claim + b"." + sig).decode()
    r = requests.post(TOKEN_URL, data={"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": jwt}, timeout=20)
    r.raise_for_status()
    return r.json()["access_token"]


def google_publish(urls, kind="URL_UPDATED", budget=180):
    raw = os.environ.get("GOOGLE_SA_JSON")
    if not raw or not urls:
        return {"sent": 0, "skipped": len(urls or [])}
    try:
        tok = _token(json.loads(raw))
    except Exception as e:
        return {"sent": 0, "error": f"auth: {e.__class__.__name__}"}
    sent, errors = 0, []
    for u in urls[:budget]:
        try:
            r = requests.post(PUBLISH_URL, headers={"Authorization": f"Bearer {tok}"}, json={"url": u, "type": kind}, timeout=20)
            if r.ok:
                sent += 1
            else:
                errors.append(f"{r.status_code}")
                if r.status_code == 429:
                    break
        except requests.RequestException as e:
            errors.append(e.__class__.__name__)
    return {"sent": sent, "errors": errors[:5]}


def indexnow(urls, host, key=None):
    key = os.environ.get("INDEXNOW_KEY") or key
    if not key or not urls:
        return {"sent": 0}
    body = {"host": host, "key": key, "keyLocation": f"https://{host}/{key}.txt", "urlList": urls[:10000]}
    try:
        r = requests.post("https://api.indexnow.org/indexnow", json=body, timeout=20)
        return {"sent": len(urls) if r.status_code in (200, 202) else 0, "status": r.status_code}
    except requests.RequestException as e:
        return {"sent": 0, "error": e.__class__.__name__}
