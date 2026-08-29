import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Every test runs with Kie stubbed: generation copies the fixture PNG, uploads
# echo a fake URL. Real ffmpeg/ffprobe are still exercised.
os.environ.setdefault("MTVP_FAKE_KIE", "1")
os.environ.setdefault("MTVP_SKIP_UPLOAD", "1")
os.environ.setdefault("MTVP_FAKE_MEDIA", str(ROOT / "tests" / "fixtures" / "ref.png"))


@pytest.fixture
def fixture_png() -> Path:
    return ROOT / "tests" / "fixtures" / "ref.png"


@pytest.fixture
def repo_root() -> Path:
    return ROOT


@pytest.fixture
def example_project() -> Path:
    return ROOT / "projects" / "example_playful_app" / "project.json"


def _have(exe: str) -> bool:
    from shutil import which
    return which(exe) is not None


requires_ffmpeg = pytest.mark.skipif(
    not (_have("ffmpeg") and _have("ffprobe")), reason="ffmpeg/ffprobe not on PATH"
)
