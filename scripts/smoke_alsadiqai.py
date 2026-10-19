#!/usr/bin/env python3
"""Smoke test for a running Al-Sadiq stack. Standard library only; needs no keys.

Usage:
    python scripts/smoke_alsadiqai.py https://alsadiqai.com
    python scripts/smoke_alsadiqai.py http://localhost:5442 --no-session
    python scripts/smoke_alsadiqai.py https://alsadiqai.com --json

What it checks (each line prints PASS, FAIL or SKIP):
    1. Health       GET /api/health/ answers 200 with status "ok" (database and redis).
    2. Landing      GET / answers 200 with an HTML page that has a script and a root element.
    3. Demo login   POST /api/demo/start answers 201 with child and parent tokens (needs DEMO_MODE=1;
                    use --no-demo to skip). It leases one demo family for the lease time (45 minutes
                    by default), so do not run it in a tight loop against a small pool.
    4. Tokens       Both demo tokens are access JWTs with an expiry (no extra request).
    5. Session      POST /api/conversation/sessions/ with the child token and text_only=true answers 2xx
                    with a livekit_token (a JWT), a wss:// or ws:// livekit_url and a room name; the
                    session is ended again. text_only keeps it from spending ElevenLabs characters.
                    It does count as one of the family's daily sessions (DEMO_DAILY_SESSIONS). Skip
                    with --no-session.
    6. Static GLB   GET the avatar model (default /models/avatar/avatar-animated.glb) starts with the
                    glTF magic bytes. Only the first 12 bytes are read.
    7. No keys      The landing page, every same-origin script and stylesheet it links, the health
                    answer, the demo answer and the session answer contain no API-key-looking strings
                    (sk-..., sk_..., xi-api-key, private key blocks, key variable names).
    8. Admin        GET /admin/ is not open to the public: 404, 403, or a redirect that is not the Django
                    admin login. (The Caddyfile blocks it unless ADMIN_ALLOWED_IPS lists your address.)

The script never prints a token or a key. Exit code 0 when nothing failed, 1 otherwise.
It sends an honest User-Agent and does nothing to get past bot checks: if a CDN challenges it,
that shows up as a FAIL and the answer is to allow the smoke test's address, not to evade.
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import sys
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

USER_AGENT = "AlSadiqSmoke/1.0 (+deploy smoke test)"
DEFAULT_GLB = "/models/avatar/avatar-animated.glb"
MAX_ASSET_BYTES = 8 * 1024 * 1024
MAX_ASSETS = 40

# Things that must never be in anything a visitor can download. The lookbehind keeps a random
# stretch of a base64 token from matching by accident.
KEY_PATTERNS = [
    ("OpenAI-style key", re.compile(r"(?<![A-Za-z0-9_-])sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{24,}")),
    ("ElevenLabs-style key", re.compile(r"(?<![A-Za-z0-9_-])sk_[A-Fa-f0-9]{30,}")),
    ("xi-api-key header", re.compile(r"xi-api-key", re.I)),
    ("private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("secret variable name", re.compile(
        r"\b(?:OPENAI_API_KEY|ELEVEN_API_KEY|XAI_API_KEY|LIVEKIT_API_SECRET|DJANGO_SECRET_KEY|"
        r"POSTGRES_PASSWORD|DJANGO_SUPERUSER_PASSWORD)\b")),
]
JWT_RE = re.compile(r"eyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]*")


class Result:
    def __init__(self, as_json: bool):
        self.rows: list[dict] = []
        self.as_json = as_json

    def add(self, status: str, name: str, detail: str = "") -> bool:
        self.rows.append({"status": status, "check": name, "detail": detail})
        if not self.as_json:
            print(f"{status:<4}  {name}" + (f"  - {detail}" if detail else ""), flush=True)
        return status != "FAIL"

    @property
    def failed(self) -> int:
        return sum(1 for r in self.rows if r["status"] == "FAIL")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):  # noqa: D401 - urllib hook
        return None


def request(method: str, url: str, *, body: dict | None = None, token: str | None = None,
            timeout: float = 20.0, follow: bool = True, max_bytes: int = MAX_ASSET_BYTES,
            read: int | None = None) -> tuple[int, dict[str, str], bytes]:
    """Return (status, headers, body). Never raises for an HTTP error status; raises OSError
    for a network failure. `read` limits how many bytes of the body are read."""
    data = None
    headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    opener = urllib.request.build_opener() if follow else urllib.request.build_opener(_NoRedirect)
    try:
        resp = opener.open(req, timeout=timeout)
    except urllib.error.HTTPError as e:
        resp = e
    try:
        payload = resp.read(read if read is not None else max_bytes + 1)
    finally:
        resp.close()
    hdrs = {k.lower(): v for k, v in resp.headers.items()}
    return resp.status if hasattr(resp, "status") else resp.code, hdrs, payload


def jwt_claims(token: str) -> dict | None:
    try:
        part = token.split(".")[1]
        part += "=" * (-len(part) % 4)
        return json.loads(base64.urlsafe_b64decode(part))
    except Exception:  # noqa: BLE001 - any malformed token is "not a JWT"
        return None


def scan_for_keys(label: str, text: str, found: list[str]) -> None:
    text = JWT_RE.sub("<jwt>", text)
    for what, pattern in KEY_PATTERNS:
        if pattern.search(text):
            found.append(f"{what} in {label}")


class _Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.assets: list[str] = []
        self.has_script = False
        self.has_root = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "script":
            self.has_script = True
            if a.get("src"):
                self.assets.append(a["src"])
        elif tag == "link" and a.get("href") and (
                "stylesheet" in (a.get("rel") or "") or "modulepreload" in (a.get("rel") or "")):
            self.assets.append(a["href"])
        if a.get("id") in ("root", "app"):
            self.has_root = True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Smoke test for a running Al-Sadiq stack (no keys needed).")
    ap.add_argument("base_url", help="for example https://alsadiqai.com or http://localhost:5442")
    ap.add_argument("--timeout", type=float, default=20.0, help="seconds per request (default 20)")
    ap.add_argument("--no-demo", action="store_true", help="skip demo login and session (DEMO_MODE off)")
    ap.add_argument("--no-session", action="store_true",
                    help="skip starting a session (it uses one of the family's daily sessions)")
    ap.add_argument("--glb-path", default=DEFAULT_GLB, help=f"avatar model path (default {DEFAULT_GLB})")
    ap.add_argument("--json", action="store_true", help="print one JSON object instead of lines")
    args = ap.parse_args(argv)

    base = args.base_url.rstrip("/")
    if not re.match(r"^https?://", base):
        ap.error("base_url must start with http:// or https://")
    res = Result(args.json)
    scanned: list[tuple[str, str]] = []  # (label, text) to scan for keys at the end
    t0 = time.time()

    def call(*a, **kw):
        kw.setdefault("timeout", args.timeout)
        return request(*a, **kw)

    # 1. Health
    try:
        status, _, body = call("GET", base + "/api/health/")
        text = body.decode("utf-8", "replace")
        scanned.append(("health", text))
        try:
            doc = json.loads(text)
        except ValueError:
            doc = {}
        if status == 200 and doc.get("status") == "ok":
            checks = doc.get("checks") or {}
            res.add("PASS", "health", "status ok; " + ", ".join(f"{k}={v}" for k, v in sorted(checks.items())))
        else:
            res.add("FAIL", "health", f"HTTP {status}, body starts: {text[:160]!r}")
    except OSError as e:
        res.add("FAIL", "health", f"no answer: {e}")

    # 2. Landing page (and the assets it links, kept for the key scan)
    try:
        status, hdrs, body = call("GET", base + "/")
        html = body.decode("utf-8", "replace")
        parser = _Links()
        parser.feed(html)
        ctype = hdrs.get("content-type", "")
        if status == 200 and "html" in ctype and parser.has_script and parser.has_root:
            res.add("PASS", "landing", f"HTML with a script and a root element, {len(body)} bytes")
        else:
            res.add("FAIL", "landing", f"HTTP {status}, content-type {ctype!r}, "
                    f"script={parser.has_script}, root={parser.has_root}")
        scanned.append(("landing page", html))
        seen = 0
        host = urlparse(base).netloc
        for href in parser.assets:
            full = urljoin(base + "/", href)
            if urlparse(full).netloc != host or seen >= MAX_ASSETS:
                continue
            seen += 1
            try:
                st, _, ab = call("GET", full)
                if st == 200:
                    scanned.append((urlparse(full).path, ab.decode("utf-8", "replace")))
            except OSError:
                pass
    except OSError as e:
        res.add("FAIL", "landing", f"no answer: {e}")

    # 3. Demo login
    child_token = parent_token = None
    if args.no_demo:
        res.add("SKIP", "demo login", "--no-demo")
    else:
        try:
            status, _, body = call("POST", base + "/api/demo/start", body={})
            text = body.decode("utf-8", "replace")
            try:
                doc = json.loads(text)
            except ValueError:
                doc = {}
            scanned.append(("demo start answer", text))
            child_token = (doc.get("child") or {}).get("access")
            parent_token = (doc.get("parent") or {}).get("access")
            if status == 201 and child_token and parent_token:
                fam = doc.get("family") or {}
                res.add("PASS", "demo login", f"leased family slot {fam.get('slot')}, "
                        f"lease {doc.get('expires_in')} s, child and parent tokens present")
            elif status == 503 and doc.get("code") == "demo_busy":
                res.add("FAIL", "demo login", "every demo family is leased (demo_busy); retry later or raise DEMO_POOL_SIZE")
            elif status == 404:
                res.add("FAIL", "demo login", "404: DEMO_MODE is off on the server (use --no-demo to skip)")
            else:
                res.add("FAIL", "demo login", f"HTTP {status}, body starts: {text[:160]!r}")
        except OSError as e:
            res.add("FAIL", "demo login", f"no answer: {e}")

    # 4. Parent token shape (no request)
    if args.no_demo:
        res.add("SKIP", "parent token", "--no-demo")
    elif parent_token and child_token:
        pc, cc = jwt_claims(parent_token) or {}, jwt_claims(child_token) or {}
        if pc.get("token_type") == "access" and cc.get("token_type") == "access" and pc.get("exp") and cc.get("exp"):
            ttl = int(min(pc["exp"], cc["exp"]) - time.time())
            res.add("PASS", "parent and child tokens", f"both are access JWTs, valid for at least {ttl} s")
        else:
            res.add("FAIL", "parent and child tokens", "not access JWTs with an expiry")
    else:
        res.add("FAIL", "parent and child tokens", "no tokens to check (demo login failed)")

    # 5. Session token (text only, then ended)
    if args.no_demo or args.no_session:
        res.add("SKIP", "session token", "--no-demo" if args.no_demo else "--no-session")
    elif not child_token:
        res.add("FAIL", "session token", "no child token (demo login failed)")
    else:
        try:
            status, _, body = call("POST", base + "/api/conversation/sessions/",
                                   body={"text_only": True}, token=child_token)
            text = body.decode("utf-8", "replace")
            try:
                doc = json.loads(text)
            except ValueError:
                doc = {}
            scanned.append(("session answer", text))
            lk = doc.get("livekit_token")
            url = str(doc.get("livekit_url") or "")
            if status in (200, 201) and lk and jwt_claims(lk) and re.match(r"^wss?://", url) and doc.get("livekit_room_name"):
                res.add("PASS", "session token", f"HTTP {status}, LiveKit token (JWT), url {urlparse(url).scheme}://{urlparse(url).netloc}, "
                        f"voice_mode={doc.get('voice_mode')}")
            elif status in (429, 503) and doc.get("code"):
                res.add("FAIL", "session token", f"refused by a guard: HTTP {status} code={doc.get('code')} "
                        "(daily_limit, rate_limited or voice_off); see docs/hackathon/demo-guards.md")
            else:
                res.add("FAIL", "session token", f"HTTP {status}, body starts: {text[:160]!r}")
            sid = doc.get("session_id")
            if sid:
                try:
                    call("POST", f"{base}/api/conversation/sessions/{sid}/end/", body={}, token=child_token)
                except OSError:
                    pass
        except OSError as e:
            res.add("FAIL", "session token", f"no answer: {e}")

    # 6. Static GLB: first 12 bytes only
    try:
        status, hdrs, head = call("GET", base + args.glb_path, read=12)
        if status == 200 and head[:4] == b"glTF":
            size = hdrs.get("content-length", "unknown size")
            res.add("PASS", "static GLB", f"{args.glb_path}: glTF header, content-length {size}")
        else:
            res.add("FAIL", "static GLB", f"{args.glb_path}: HTTP {status}, first bytes {head[:8]!r}")
    except OSError as e:
        res.add("FAIL", "static GLB", f"no answer: {e}")

    # 7. No keys anywhere a visitor can read
    found: list[str] = []
    for label, text in scanned:
        scan_for_keys(label, text, found)
    if found:
        res.add("FAIL", "no keys", "; ".join(found))
    elif not scanned:
        res.add("FAIL", "no keys", "nothing was downloaded, so nothing was scanned")
    else:
        res.add("PASS", "no keys", f"nothing key-like in {len(scanned)} downloaded texts "
                f"({sum(len(t) for _, t in scanned) // 1024} KB)")

    # 8. /admin must not be open to the public
    try:
        status, hdrs, body = call("GET", base + "/admin/", follow=False)
        if status in (404, 403):
            res.add("PASS", "admin closed", f"HTTP {status}")
        elif status in (301, 302, 307, 308) and "/admin/login" not in hdrs.get("location", ""):
            res.add("PASS", "admin closed", f"HTTP {status} redirect to {hdrs.get('location', '')[:60]!r} (not the admin login)")
        else:
            res.add("FAIL", "admin closed", f"HTTP {status}: /admin answers a visitor; set ADMIN_ALLOWED_IPS (Caddyfile)")
    except OSError as e:
        res.add("FAIL", "admin closed", f"no answer: {e}")

    elapsed = time.time() - t0
    if args.json:
        print(json.dumps({"base_url": base, "seconds": round(elapsed, 1), "failed": res.failed, "checks": res.rows},
                         ensure_ascii=False, indent=2))
    else:
        verdict = "OK" if res.failed == 0 else f"{res.failed} FAILED"
        print(f"\n{verdict}: {len(res.rows)} checks in {elapsed:.1f} s against {base}")
    return 0 if res.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
