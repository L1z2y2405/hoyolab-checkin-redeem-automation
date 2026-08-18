"""HTTP client with HoYoLAB request defaults."""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

HOYOLAB_HEADERS = {
    "Referer": "https://act.hoyolab.com",
    "x-rpc-app_version": "1.5.0",
    "x-rpc-client_type": "5",
    "x-rpc-language": "en-us",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}

CODE_SOURCE_HEADERS = {
    "User-Agent": "HoyoAuto/1.0",
}


class HoyoClient:
    def __init__(self, timeout: float = 30.0) -> None:
        self._client = httpx.Client(timeout=timeout, follow_redirects=True)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "HoyoClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def request(
        self,
        method: str,
        url: str,
        *,
        hoyolab: bool = True,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        json: Any | None = None,
    ) -> httpx.Response:
        merged = dict(HOYOLAB_HEADERS if hoyolab else CODE_SOURCE_HEADERS)
        if headers:
            merged.update(headers)
        try:
            return self._client.request(
                method,
                url,
                params=params,
                headers=merged,
                json=json,
            )
        except httpx.HTTPError as exc:
            logger.error("HTTP request failed for %s: %s", url, exc)
            raise

    def get(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.request("POST", url, **kwargs)
