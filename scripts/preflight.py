#!/usr/bin/env python3
"""
preflight.py — verify this machine can run the pipeline.

    python scripts/preflight.py           # offline checks only
    python scripts/preflight.py --ping     # also test KIE_API_KEY against the API
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.request

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

OK, WARN, FAIL = "[ OK ]", "[WARN]", "[FAIL]"


def _v(cmd: list[str]) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True).stdout.splitlines()[0]
    except Exception:  # noqa: BLE001
        return ""


def main() -> int:
    ping = "--ping" in sys.argv
    fails = 0

    print("-- multi-tone-video-pipeline preflight --")

    # python deps
    for mod in ("jsonschema", "PIL"):
        try:
            __import__(mod)
            print(f"  {OK} python: {mod}")
        except ImportError:
            print(f"  {FAIL} python: {mod} missing  →  pip install -r requirements.txt")
            fails += 1
    try:
        import faster_whisper  # noqa: F401
        print(f"  {OK} python: faster-whisper (tight caption sync)")
    except ImportError:
        print(f"  {WARN} python: faster-whisper not installed — captions use the "
              f"proportional fallback (fine for short pops)")

    # binaries
    for exe in ("ffmpeg", "ffprobe"):
        if shutil.which(exe):
            print(f"  {OK} {exe}: {_v([exe, '-version'])[:60]}")
        else:
            print(f"  {FAIL} {exe} not on PATH  →  https://ffmpeg.org/download.html")
            fails += 1
    if shutil.which("kie-cli"):
        print(f"  {OK} kie-cli present")
    else:
        print(f"  {FAIL} kie-cli not on PATH  →  npm install -g kie-cli")
        fails += 1

    # env
    key = os.environ.get("KIE_API_KEY") or os.environ.get("KIE_AI_API_KEY")
    if key:
        print(f"  {OK} KIE_API_KEY set (…{key[-4:]})")
    else:
        print(f"  {FAIL} KIE_API_KEY not set  →  https://kie.ai/api-key")
        fails += 1

    # libass in ffmpeg
    if shutil.which("ffmpeg"):
        cfg = subprocess.run(["ffmpeg", "-hide_banner", "-filters"],
                             capture_output=True, text=True).stdout
        if " ass " in cfg or "\nass" in cfg:
            print(f"  {OK} ffmpeg: libass (caption burn-in)")
        else:
            print(f"  {WARN} ffmpeg: 'ass' filter not found — captions won't burn. "
                  f"Use a full build (gyan.dev / BtbN).")

    if ping and key:
        try:
            req = urllib.request.Request(
                "https://api.kie.ai/api/v1/chat/credit",
                headers={"Authorization": f"Bearer {key}", "User-Agent": "Mozilla/5.0"})
            data = json.loads(urllib.request.urlopen(req, timeout=20).read())
            print(f"  {OK} kie.ai reachable — credit balance: {data.get('data')}")
        except Exception as e:  # noqa: BLE001
            print(f"  {FAIL} kie.ai ping failed: {e}")
            fails += 1

    print("──────────────────────────────────────────")
    if fails:
        print(f"{FAIL} {fails} blocker(s). Fix the ✗ lines above.")
        return 1
    print(f"{OK} ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
