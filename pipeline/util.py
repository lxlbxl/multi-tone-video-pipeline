"""Shared helpers: paths, JSON I/O, logging, and FFmpeg/FFprobe wrappers."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Iterable

# Windows consoles default to cp1252 and choke on non-ASCII. Prefer real UTF-8;
# all human-facing marks below are ASCII anyway as a belt-and-braces fallback.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

# Repo root = parent of the `pipeline/` package. Library folders (style_packs/,
# tone_profiles/, narrative_templates/) and projects/ live directly under it.
REPO_ROOT = Path(__file__).resolve().parent.parent


def asset_root() -> Path:
    """Where locked character refs and background images live. Defaults to the
    repo root (spec layout: /characters/<style_pack>/, /backgrounds/<project>/)
    but can point elsewhere so a character library survives outside the repo,
    and so tests don't write into it."""
    return Path(os.environ.get("MTVP_ASSET_ROOT", str(REPO_ROOT)))


def resolve_asset(rel: str | Path) -> Path:
    p = Path(rel)
    return p if p.is_absolute() else asset_root() / p

FPS = 30
CANVAS = (1080, 1920)  # 9:16 delivery


# --------------------------------------------------------------------------- #
# logging
# --------------------------------------------------------------------------- #
_START = time.time()


def log(msg: str, *, level: str = "info") -> None:
    dt = time.time() - _START
    prefix = {"info": "  ", "warn": "! ", "err": "X ", "ok": "OK"}.get(level, "  ")
    line = f"[mtvp {dt:6.1f}s] {prefix} {msg}"
    try:
        print(line, file=sys.stderr, flush=True)
    except UnicodeEncodeError:
        print(line.encode("ascii", "replace").decode(), file=sys.stderr, flush=True)


def die(msg: str, code: int = 1) -> "NoReturn":  # type: ignore[name-defined]
    log(msg, level="err")
    raise SystemExit(code)


# --------------------------------------------------------------------------- #
# json
# --------------------------------------------------------------------------- #
def read_json(path: str | Path) -> Any:
    p = Path(path)
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise
    except json.JSONDecodeError as e:
        raise ValueError(f"{p}: invalid JSON — {e}") from e


def write_json(path: str | Path, obj: Any) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return p


def read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# subprocess
# --------------------------------------------------------------------------- #
def run(cmd: Iterable[str], *, check: bool = True, capture: bool = True,
        input_: str | None = None, timeout: int | None = None) -> subprocess.CompletedProcess:
    cmd = [str(c) for c in cmd]
    proc = subprocess.run(
        cmd,
        text=True,
        input=input_,
        capture_output=capture,
        timeout=timeout,
    )
    if check and proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-25:]
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(cmd[:6])}…\n"
            + "\n".join(tail)
        )
    return proc


def which(name: str) -> str | None:
    return shutil.which(name)


# --------------------------------------------------------------------------- #
# ffmpeg / ffprobe
# --------------------------------------------------------------------------- #
def _ff(name: str) -> str:
    exe = which(name)
    if not exe:
        die(f"{name} not found on PATH — install FFmpeg 6+ (https://ffmpeg.org)")
    return exe


def ffmpeg(args: Iterable[str], *, quiet: bool = True) -> None:
    base = [_ff("ffmpeg"), "-y"]
    if quiet:
        base += ["-loglevel", "error", "-nostats"]
    run(base + [str(a) for a in args])


def ffprobe_json(path: str | Path) -> dict:
    out = run([
        _ff("ffprobe"), "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", str(path),
    ]).stdout
    return json.loads(out)


def probe_duration(path: str | Path) -> float:
    try:
        return float(ffprobe_json(path)["format"]["duration"])
    except (KeyError, ValueError):
        return 0.0


def probe_size(path: str | Path) -> tuple[int, int]:
    for s in ffprobe_json(path).get("streams", []):
        if s.get("codec_type") == "video":
            return int(s["width"]), int(s["height"])
    return (0, 0)


# --------------------------------------------------------------------------- #
# misc
# --------------------------------------------------------------------------- #
def env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "on")


def hexrgb(s: str) -> tuple[int, int, int]:
    s = s.lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)


def slugify(s: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in s.strip().lower()).strip("_")
