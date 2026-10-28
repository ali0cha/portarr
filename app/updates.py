"""Tells the user when a newer Portarr exists.

It reads `__version__` from the project's main branch and compares it with the running one. Comparing
versions rather than commits means a README or screenshot change never raises a false alarm: only a
deliberate release does. The request carries nothing about the user, is cached for hours, and any
failure (offline NAS, GitHub down) is silent: the check is a convenience, never a blocker.
"""
from __future__ import annotations

import asyncio
import logging
import re
import time

import httpx

log = logging.getLogger("uvicorn.error")
_VERSION = re.compile(r"""^__version__\s*=\s*["']([^"']+)["']""", re.M)
_NUMBER = re.compile(r"v?(\d+(?:\.\d+){0,3})")


def parse_version(text: str) -> tuple[int, ...] | None:
    m = _NUMBER.fullmatch(text.strip())
    return tuple(int(part) for part in m.group(1).split(".")) if m else None


def is_newer(latest: str, current: str) -> bool:
    a, b = parse_version(latest), parse_version(current)
    if a is None or b is None:
        return False
    size = max(len(a), len(b))  # 0.2 and 0.2.0 are the same version
    return a + (0,) * (size - len(a)) > b + (0,) * (size - len(b))


class UpdateChecker:
    def __init__(self, url: str, current: str, enabled: bool = True, transport: httpx.AsyncBaseTransport | None = None,
                 ttl: float = 6 * 3600, retry: float = 3600, timeout: float = 4.0):
        self.url, self.current, self.enabled, self.transport = url, current, enabled, transport
        self.ttl, self.retry, self.timeout = ttl, retry, timeout  # how long a result / a failure is trusted
        self._latest: str | None = None
        self._checked_at: float | None = None
        self._lock = asyncio.Lock()

    async def latest(self) -> str | None:
        if not self.enabled:
            return None
        async with self._lock:  # several pages asking at once cost a single request
            now = time.monotonic()
            if self._checked_at is not None and now < self._checked_at + (self.ttl if self._latest else self.retry):
                return self._latest
            self._latest, self._checked_at = await self._fetch(), now
            return self._latest

    async def _fetch(self) -> str | None:
        try:
            async with httpx.AsyncClient(transport=self.transport, timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(self.url)
                resp.raise_for_status()
        except httpx.HTTPError as e:
            log.info("Update check failed (%s: %s); will retry later", e.__class__.__name__, e)
            return None
        m = _VERSION.search(resp.text[:20000])
        return m.group(1) if m and parse_version(m.group(1)) else None

    async def status(self) -> dict[str, object]:
        latest = await self.latest()
        return {"enabled": self.enabled, "current": self.current, "latest": latest,
                "available": bool(latest and is_newer(latest, self.current))}
