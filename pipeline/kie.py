"""
Kie.ai access layer.

Wraps the `kie-cli` npm tool for generation, plus the Kie file-upload endpoint
so local reference images become the public URLs that GPT Image 2 needs for
image-to-image. Nothing else in the pipeline talks to Kie directly.

Env:
    KIE_API_KEY            required for real calls (upload + generation auth)
    MTVP_FAKE_KIE=1        skip real work: generation returns a fixture path,
                           uploads echo a fake URL. Used by the test suite and
                           by `--dry-run`-adjacent smoke checks.
    MTVP_FAKE_MEDIA=<png>  fixture returned by fake generation (default:
                           tests/fixtures/ref.png)
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from . import util

def _resolve_cli() -> str | None:
    override = os.environ.get("MTVP_KIE_CLI")
    if override:
        return shutil.which(override) or override
    # npm global shims on Windows are kie-cli.cmd / .ps1; bare name won't exec
    for cand in ("kie-cli", "kie-cli.cmd", "kie-cli.exe"):
        found = shutil.which(cand)
        if found:
            return found
    return None


CLI = _resolve_cli() or "kie-cli"
UPLOAD_URL = "https://kieai.redpandaai.co/api/file-base64-upload"
_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/122.0 Safari/537.36")

_MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
         ".webp": "image/webp", ".mp3": "audio/mpeg", ".wav": "audio/wav",
         ".mp4": "video/mp4"}


class KieError(RuntimeError):
    pass


def _fake() -> bool:
    return util.env_flag("MTVP_FAKE_KIE")


def _fixture() -> Path:
    p = os.environ.get("MTVP_FAKE_MEDIA")
    if p:
        return Path(p)
    return util.REPO_ROOT / "tests" / "fixtures" / "ref.png"


# --------------------------------------------------------------------------- #
# generation
# --------------------------------------------------------------------------- #
def _flags(opts: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for k, v in opts.items():
        if v is None:
            continue
        flag = f"--{k}"
        if isinstance(v, bool):
            if v:
                out.append(flag)
        elif isinstance(v, (list, tuple)):
            if v:
                out.append(flag)
                out.extend(str(x) for x in v)
        else:
            out += [flag, str(v)]
    return out


def submit(tool: str, **opts: Any) -> str:
    """Create a generation task; return its task_id."""
    if not util.which(CLI):
        raise KieError(f"{CLI} not found on PATH — `npm i -g kie-cli`")
    cmd = [CLI, tool, "--json", *_flags(opts)]
    util.log(f"kie submit: {tool} {' '.join(_flags(opts))[:120]}")
    proc = util.run(cmd, timeout=180)
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise KieError(f"{tool}: non-JSON response: {proc.stdout[:300]}") from e
    tid = data.get("task_id") or data.get("taskId")
    if not tid:
        raise KieError(f"{tool}: no task_id in response: {json.dumps(data)[:300]}")
    return tid


def wait(task_id: str, *, timeout: int = 1200) -> list[str]:
    """Block until the task completes; return its result URLs.

    kie-cli's `wait_for_task` gives up after its own ~180s window and returns
    ``status: timed_out`` while the task is still running — that is not a
    failure, so keep re-calling it until the task actually resolves or our own
    `timeout` budget is spent."""
    import time as _t
    cmd = [CLI, "wait_for_task", "--json", "--task_id", task_id]
    deadline = _t.time() + timeout
    last = {}
    while _t.time() < deadline:
        proc = util.run(cmd, timeout=300, check=False)
        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError:
            _t.sleep(10)
            continue
        last = data
        status = (data.get("status") or data.get("state") or "").lower()
        urls = data.get("result_urls") or data.get("resultUrls") or []
        if status in ("success", "completed") and urls:
            return urls
        if status in ("fail", "failed", "error"):
            raise KieError(f"task {task_id} failed: {json.dumps(data)[:400]}")
        # timed_out / running / queued / generating -> poll again
        util.log(f"kie wait: {task_id} still {status or 'running'}…")
        _t.sleep(5)
    raise KieError(f"task {task_id} not done within {timeout}s: {json.dumps(last)[:300]}")


_AUDIO_TOOLS = {"elevenlabs_tts", "elevenlabs_ttsfx", "suno_generate_music"}
_AUDIO_EXT = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}


def _fake_media(tool: str, dest: Path) -> Path:
    """Produce a valid stub file of the right modality for offline runs/tests."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    is_audio = tool in _AUDIO_TOOLS or dest.suffix.lower() in _AUDIO_EXT
    if is_audio:
        util.ffmpeg(["-f", "lavfi", "-t", "6", "-i",
                     "anullsrc=r=44100:cl=mono", "-q:a", "9", str(dest)])
    else:
        shutil.copyfile(_fixture(), dest)
    return dest


def generate(tool: str, *, dest: str | Path, timeout: int = 900, **opts: Any) -> Path:
    """Submit + wait + download the first result to `dest`. Returns dest."""
    dest = Path(dest)
    if _fake():
        util.log(f"[fake] {tool} -> {dest.name}")
        return _fake_media(tool, dest)
    tid = submit(tool, **opts)
    urls = wait(tid, timeout=timeout)
    return download(urls[0], dest)


# --------------------------------------------------------------------------- #
# upload  (local file -> public URL)
# --------------------------------------------------------------------------- #
def upload(path: str | Path, *, subdir: str = "mtvp") -> str:
    path = Path(path)
    if _fake() or util.env_flag("MTVP_SKIP_UPLOAD"):
        return f"https://example.invalid/{subdir}/{path.name}"
    key = os.environ.get("KIE_API_KEY") or os.environ.get("KIE_AI_API_KEY")
    if not key:
        raise KieError("KIE_API_KEY not set — cannot upload reference images")
    raw = path.read_bytes()
    mime = _MIME.get(path.suffix.lower(), "application/octet-stream")
    body = json.dumps({
        "base64Data": f"data:{mime};base64,{base64.b64encode(raw).decode()}",
        "uploadPath": f"images/{subdir}",
        "fileName": path.name,
    }).encode()
    req = urllib.request.Request(UPLOAD_URL, data=body, headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "User-Agent": _UA,
        "Accept": "application/json",
    })
    last = None
    for attempt in range(3):
        try:
            resp = json.loads(urllib.request.urlopen(req, timeout=90).read().decode())
            url = (resp.get("data") or {}).get("downloadUrl")
            if not url:
                raise KieError(f"upload: no downloadUrl: {json.dumps(resp)[:300]}")
            util.log(f"uploaded {path.name} -> {url}")
            return url
        except (urllib.error.URLError, TimeoutError) as e:  # noqa: PERF203
            last = e
            time.sleep(2 * (attempt + 1))
    raise KieError(f"upload failed after retries: {last}")


# --------------------------------------------------------------------------- #
# download
# --------------------------------------------------------------------------- #
def download(url: str, dest: str | Path) -> Path:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if url.startswith("file://"):
        src = urllib.request.url2pathname(url[7:])
        shutil.copyfile(src, dest)
        return dest
    if url.startswith(("http://", "https://")):
        req = urllib.request.Request(url, headers={"User-Agent": _UA})
        with urllib.request.urlopen(req, timeout=180) as r, open(dest, "wb") as f:
            shutil.copyfileobj(r, f)
        return dest
    # bare local path
    shutil.copyfile(url, dest)
    return dest


def cache_key(*parts: Any) -> str:
    h = hashlib.sha1("::".join(str(p) for p in parts).encode()).hexdigest()
    return h[:12]
