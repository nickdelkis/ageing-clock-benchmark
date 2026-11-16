"""Minimal JSON-over-HTTP helpers on the standard library (no extra dependencies).

`TRANSPORT` can be replaced in tests with a function that fakes responses.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

USER_AGENT = "ageing-clock-benchmark/targetrank (research demo)"


def _urllib_transport(method: str, url: str, headers: dict, body: bytes | None, timeout: float) -> tuple[int, bytes]:
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as err:
        return err.code, err.read()


TRANSPORT = _urllib_transport


class HTTPFailure(RuntimeError):
    pass


def request_json(method: str, url: str, payload: dict | None = None, headers: dict | None = None,
                 timeout: float = 60, retries: int = 2):
    """Send a request and parse a JSON response. Retries on 429 and 5xx."""
    hdrs = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if payload is not None:
        hdrs["Content-Type"] = "application/json"
    hdrs.update(headers or {})
    body = json.dumps(payload).encode() if payload is not None else None
    last = None
    for attempt in range(retries + 1):
        status, raw = TRANSPORT(method, url, hdrs, body, timeout)
        if status < 400:
            return json.loads(raw.decode() or "null")
        last = f"HTTP {status} from {url}: {raw[:300]!r}"
        if status in (429, 500, 502, 503, 504) and attempt < retries:
            time.sleep(2 ** attempt)
            continue
        break
    raise HTTPFailure(last)


def get_json(url: str, **kw):
    return request_json("GET", url, **kw)


def post_json(url: str, payload: dict, **kw):
    return request_json("POST", url, payload=payload, **kw)
