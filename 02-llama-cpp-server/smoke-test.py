#!/usr/bin/env python3
"""Smoke-test the local llama-server's OpenAI-compatible endpoint."""
from __future__ import annotations

import json
import sys
import time

import httpx

BASE_URL = "http://localhost:8089/v1"


def main() -> int:
    print(f"==> POST {BASE_URL}/chat/completions")
    payload = {
        "model": "local",
        "messages": [
            {"role": "system", "content": "You are a serving-engineering tutor."},
            {"role": "user", "content": "Define goodput@SLO in one sentence."},
        ],
        "max_tokens": 80,
        "temperature": 0.3,
        "stream": False,
    }
    t0 = time.perf_counter()
    try:
        r = httpx.post(f"{BASE_URL}/chat/completions", json=payload, timeout=120.0)
        r.raise_for_status()
    except httpx.HTTPError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print("Is llama-server running on :8089? Start it first (see this directory's README).", file=sys.stderr)
        return 1
    elapsed = (time.perf_counter() - t0) * 1000.0
    body = r.json()
    msg = body["choices"][0]["message"]["content"]
    print(f"\n[{elapsed:.0f} ms]\n{msg}\n")

    print("==> GET /metrics (head)")
    try:
        m = httpx.get("http://localhost:8089/metrics", timeout=5.0)
        for line in m.text.splitlines()[:25]:
            print(f"   {line}")
    except httpx.HTTPError:
        print("   /metrics unavailable. Start llama-server with --metrics flag.")

    print("\nOK. Smoke test passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
