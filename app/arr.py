"""Minimal async client for the Sonarr / Radarr / Whisparr (API v3) and Lidarr / Prowlarr (API v1) APIs."""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from pathlib import Path
from typing import Any, ClassVar

import httpx

# Radarr, Sonarr and Whisparr expose /api/v3; Lidarr and Prowlarr /api/v1.
API_VERSIONS = {"radarr": "v3", "sonarr": "v3", "whisparr": "v3", "lidarr": "v1", "prowlarr": "v1"}
SUPPORTED_APPS = tuple(API_VERSIONS)


class ArrError(Exception):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


def _error_message(resp: httpx.Response) -> str:
    try:
        data = resp.json()
    except ValueError:
        return f"HTTP {resp.status_code}"
    if isinstance(data, list):
        parts = []
        for d in data:
            if not isinstance(d, dict):
                continue
            msg = d.get("errorMessage") or str(d)
            prop = d.get("propertyName")
            parts.append(f"{prop}: {msg}" if prop else msg)
        if parts:
            return "; ".join(parts)
    if isinstance(data, dict):
        return data.get("message") or data.get("errorMessage") or f"HTTP {resp.status_code}"
    return f"HTTP {resp.status_code}"


def _raise_for(resp: httpx.Response, path: str) -> None:
    """Turns an unsuccessful response into an ArrError that says what to check."""
    if 300 <= resp.status_code < 400:
        raise ArrError("Redirected: check the URL (http vs https, URL base)", resp.status_code)
    if resp.status_code == 401:
        raise ArrError("Unauthorized: check the API key", 401)
    if resp.status_code == 404 and path.startswith("system/status"):
        raise ArrError("API not found: check the URL base, and that this is Radarr, Sonarr, Lidarr, Whisparr or Prowlarr", 404)
    if resp.status_code >= 400:
        raise ArrError(_error_message(resp), resp.status_code)


async def gather(*aws: Awaitable[Any]) -> list[Any]:
    """asyncio.gather that cancels the siblings as soon as one fails, so none outlives the HTTP client."""
    tasks = [asyncio.ensure_future(a) for a in aws]
    try:
        return await asyncio.gather(*tasks)
    except BaseException:
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise


class ArrClient:
    # Tests point this at an in-process fake server.
    transport_override: ClassVar[httpx.AsyncBaseTransport | None] = None

    def __init__(self, url: str, api_key: str, verify: bool = True, app: str | None = None):
        # Unknown app: the first status() call probes v3 then v1.
        self.api: str | None = API_VERSIONS.get(app or "")
        self._status: dict[str, Any] | None = None  # one status read per client, not per step
        self._http = httpx.AsyncClient(
            base_url=url.rstrip("/"),
            headers={"X-Api-Key": api_key, "Accept": "application/json"},
            verify=verify,
            timeout=20.0,
            follow_redirects=False,
            transport=self.transport_override,
        )

    async def __aenter__(self) -> ArrClient:
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self._http.aclose()

    async def request(self, method: str, path: str, json: Any = None) -> Any:
        try:
            resp = await self._http.request(method, f"/api/{self.api}/{path.lstrip('/')}", json=json)
        except (httpx.HTTPError, httpx.InvalidURL) as e:
            raise ArrError(f"Cannot reach {self._http.base_url}: {e.__class__.__name__}: {e}") from e
        _raise_for(resp, path)
        if not resp.content:
            return None
        try:
            return resp.json()
        except ValueError as e:
            raise ArrError("Response is not JSON: check the URL (and URL base)") from e

    async def download(self, path: str, dest: Path) -> int:
        """Streams a file the application serves outside its API (its backups) into `dest`; returns its size.

        `path` is what the application reports. It may or may not already include the URL base, which the
        client adds itself."""
        base = self._http.base_url.path.rstrip("/")
        rel = path[len(base):] if base and path.startswith(base + "/") else path
        size = 0
        try:
            async with self._http.stream("GET", rel) as resp:
                if resp.status_code >= 300:
                    await resp.aread()
                    _raise_for(resp, rel)
                with dest.open("wb") as out:
                    async for chunk in resp.aiter_bytes(65536):
                        out.write(chunk)
                        size += len(chunk)
        except (httpx.HTTPError, httpx.InvalidURL) as e:
            raise ArrError(f"Cannot reach {self._http.base_url}: {e.__class__.__name__}: {e}") from e
        return size

    async def upload(self, path: str, file: Path, timeout: float = 600.0) -> Any:
        """POSTs a file as multipart form data to an API path (restoring a backup)."""
        try:
            with file.open("rb") as f:
                resp = await self._http.post(f"/api/{self.api}/{path.lstrip('/')}", files={"file": (file.name, f, "application/zip")},
                                             timeout=timeout)
        except (httpx.HTTPError, httpx.InvalidURL) as e:
            raise ArrError(f"Cannot reach {self._http.base_url}: {e.__class__.__name__}: {e}") from e
        _raise_for(resp, path)
        try:
            return resp.json() if resp.content else None
        except ValueError:
            return None

    async def get(self, path: str) -> Any:
        return await self.request("GET", path)

    async def post(self, path: str, json: Any) -> Any:
        return await self.request("POST", path, json)

    async def put(self, path: str, json: Any) -> Any:
        return await self.request("PUT", path, json)

    async def status(self) -> dict[str, Any]:
        if self._status is not None:
            return self._status
        candidates = [self.api] if self.api else ["v3", "v1"]
        for i, version in enumerate(candidates):
            self.api = version
            try:
                s = await self.get("system/status")
                break
            except ArrError as e:
                if e.status == 404 and i < len(candidates) - 1:
                    continue
                raise
        name = str(s.get("appName", "")).lower()
        if name not in SUPPORTED_APPS:
            raise ArrError(f"Unsupported application {s.get('appName')!r}: only Radarr, Sonarr, Lidarr, Whisparr and Prowlarr")
        self.api = API_VERSIONS[name]
        self._status = {"app": name, "version": s.get("version"), "instanceName": s.get("instanceName")}
        return self._status
