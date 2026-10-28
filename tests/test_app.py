from pathlib import Path

import pytest

streamlit = pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_app_answers_and_abstains():
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not at.exception
    at.chat_input[0].set_value("What bottleneck dimension do the adapters use?").run()
    at.chat_input[0].set_value("What was the carbon footprint of the experiments?").run()
    assert not at.exception
    assert len(at.chat_message) == 4
    assert any("3.1 Adapter Architecture" in e.label for e in at.expander)
    assert "could not find" in at.chat_message[3].markdown[0].value
