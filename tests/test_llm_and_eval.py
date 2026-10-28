from types import SimpleNamespace

from paperqa.config import Config
from paperqa.evaluate import answer_correct, is_relevant, summarize
from paperqa.index import HybridIndex
from paperqa.llm import AnthropicLLM, ExtractiveLLM, format_sources


class FakeAnthropic:
    """Mimics anthropic.Anthropic().messages.create(...) and records the request."""

    def __init__(self, text):
        self.text, self.last = text, None
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        self.last = kwargs
        return SimpleNamespace(content=[SimpleNamespace(text=self.text)])


def test_anthropic_request_is_grounded_and_deterministic(chunks):
    idx = HybridIndex(chunks)
    hits = idx.search("bottleneck dimension")
    client = FakeAnthropic("The bottleneck is 32 [S1].")
    llm = AnthropicLLM(Config(), client=client)
    out = llm.answer("What bottleneck dimension?", hits)
    assert out == "The bottleneck is 32 [S1]."
    req = client.last
    assert req["temperature"] == 0 and req["model"] == Config().model
    assert "NOT_FOUND" in req["system"] and "ONLY" in req["system"]
    assert "[S1]" in req["messages"][0]["content"] and "Section:" in req["messages"][0]["content"]


def test_format_sources_numbers_each_excerpt(chunks):
    hits = HybridIndex(chunks).search("limitations english", k=3)
    text = format_sources(hits)
    assert text.count("[S") == 3 and "page" in text


def test_extractive_llm_abstains_without_overlap(chunks):
    idx = HybridIndex(chunks)
    llm = ExtractiveLLM(Config(), idx.idf)
    assert llm.answer("What is the carbon footprint?", idx.search("carbon footprint")) == "NOT_FOUND"


def test_relevance_and_correctness_helpers():
    assert is_relevant("SGA trains 0.8 %  of the parameters", ["trains 0.8% of the parameters"])
    assert not is_relevant("nothing here", ["trains 0.8%"])
    assert answer_correct("Both AdamW and 3e-4 are used", [["adamw"], ["3E-4"]])
    assert not answer_correct("only AdamW", [["adamw"], ["3e-4"]])


def test_summarize_counts_abstention_correctly():
    recs = [
        dict(split="test", type="fact", answerable=True, found=True, correct=True, citation_ok=True, latency_ms=1.0),
        dict(split="test", type="fact", answerable=True, found=False, correct=False, latency_ms=2.0),
        dict(split="test", type="absent", answerable=False, found=False, correct=True, latency_ms=3.0),
        dict(split="test", type="absent", answerable=False, found=True, correct=False, latency_ms=4.0),
    ]
    s = summarize(recs)
    assert s["answer_accuracy"] == 50.0 and s["false_abstain_rate"] == 50.0
    assert s["abstain_recall_on_unanswerable"] == 50.0
    assert s["wrong_answer_rate_when_answering"] == 0.0 and s["citation_hit_rate"] == 100.0
