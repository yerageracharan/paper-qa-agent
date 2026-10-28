"""Agent behaviour, using a scripted fake LLM so the tests are deterministic and need no API key."""
from paperqa.agent import PaperQAAgent
from paperqa.config import Config


class FakeLLM:
    supports_rewrite = True

    def __init__(self, reply: str, rewrite: str = "") -> None:
        self.reply, self._rewrite = reply, rewrite
        self.calls = 0

    def answer(self, question, hits):
        self.calls += 1
        return self.reply

    def rewrite(self, question):
        return self._rewrite or question


def make(chunks, reply, **cfg):
    config = Config(**cfg)
    return PaperQAAgent(chunks, config, llm=FakeLLM(reply))


def test_answers_with_citation_and_quote(agent):
    a = agent.ask("What bottleneck dimension do the adapters use?")
    assert a.found and a.citations
    assert "32" in a.text
    c = a.citations[0]
    assert c.section.startswith("3.1") and c.pages and "32" in c.quote


def test_abstains_on_topic_absent_from_paper(agent):
    a = agent.ask("What was the carbon footprint of the experiments?")
    assert not a.found and a.reason == "low_coverage"
    assert a.citations == []


def test_model_not_found_is_honoured(chunks):
    ag = make(chunks, "NOT_FOUND")
    a = ag.ask("What sparsity coefficient is used for the L0 penalty?")
    assert not a.found and a.reason == "model_not_found"


def test_uncited_answer_is_rejected(chunks):
    ag = make(chunks, "The coefficient is 0.01.")
    a = ag.ask("What sparsity coefficient is used for the L0 penalty?")
    assert not a.found and a.reason == "no_valid_citation"


def test_out_of_range_citation_is_rejected(chunks):
    ag = make(chunks, "The coefficient is 0.01 [S99].")
    a = ag.ask("What sparsity coefficient is used for the L0 penalty?")
    assert not a.found and a.reason == "no_valid_citation"


def test_hallucinated_number_is_rejected(chunks):
    # 0.05 appears in the paper, but not in the passage cited as [S1] for this question's top hit
    ag = make(chunks, "The coefficient is 0.37 [S1].")
    a = ag.ask("What sparsity coefficient is used for the L0 penalty?")
    assert not a.found and a.reason == "unsupported_number"


def test_valid_llm_answer_is_accepted_and_cited(chunks):
    ag = make(chunks, "The L0 penalty uses a coefficient of 0.01 [S1][S2][S3].")
    a = ag.ask("What sparsity coefficient is used for the L0 penalty?")
    assert a.found and len(a.citations) >= 1
    assert all(1 <= c.source_id <= 5 for c in a.citations)


def test_low_coverage_skips_the_llm_call(chunks):
    llm = FakeLLM("anything [S1]")
    ag = PaperQAAgent(chunks, Config(min_coverage=0.9), llm=llm)
    a = ag.ask("quantum chromodynamics lattice simulation")
    assert not a.found and llm.calls == 0


def test_query_rewrite_is_attempted_when_coverage_is_low(chunks):
    llm = FakeLLM("The coefficient is 0.01 [S1][S2].", rewrite="L0 penalty coefficient lambda sparsity")
    ag = PaperQAAgent(chunks, Config(min_coverage=0.9), llm=llm)
    a = ag.ask("how strongly are gates discouraged")
    assert a.rewritten_query == "L0 penalty coefficient lambda sparsity"


def test_answer_serialises(agent):
    d = agent.ask("What bottleneck dimension do the adapters use?").to_dict()
    assert d["found"] is True and d["retrieved"] and "section" in d["citations"][0]
