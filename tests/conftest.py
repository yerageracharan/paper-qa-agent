import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from paperqa import Config, PaperQAAgent  # noqa: E402
from paperqa.ingest import load_pdf  # noqa: E402


@pytest.fixture(scope="session")
def sample_pdf(tmp_path_factory) -> Path:
    """Build the synthetic paper fresh so tests never depend on a checked-in binary."""
    from make_sample_paper import build

    out = tmp_path_factory.mktemp("pdf") / "sample.pdf"
    build(out)
    return out


@pytest.fixture(scope="session")
def chunks(sample_pdf):
    return load_pdf(sample_pdf)


@pytest.fixture(scope="session")
def agent(sample_pdf):
    cfg = Config(llm="extractive")
    return PaperQAAgent.from_pdf(sample_pdf, cfg)
