"""Shared test helpers."""

from __future__ import annotations

import json
from typing import Any

import httpx


def json_response(payload: dict[str, Any], status_code: int = 200) -> httpx.Response:
    request = httpx.Request("GET", "https://example.test")
    return httpx.Response(status_code, json=payload, request=request)
