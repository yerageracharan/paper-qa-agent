from paperqa.config import Config
from paperqa.ingest import Page, _HeadingTracker, chunk_document, clean_pages
from paperqa.text import split_sentences, tokenize


def test_headings_follow_numbering():
    t = _HeadingTracker()
    assert t.detect("Abstract") == "Abstract"
    assert t.detect("1 Introduction") == "1 Introduction"
    assert t.detect("2 Related Work") == "2 Related Work"
    assert t.detect("2.1 Adapters") == "2.1 Adapters"
    # '24 GB GPU' looks like a heading but breaks the numbering sequence -> must be treated as body text
    assert t.detect("24 GB GPU") is None
    assert t.detect("3 Method") == "3 Method"


def test_running_headers_and_page_numbers_removed():
    pages = [Page(i, f"Running Title\nreal content {i}\n{i}") for i in (1, 2, 3)]
    cleaned = clean_pages(pages)
    for p in cleaned:
        assert "Running Title" not in p.text
        assert p.text.strip() == f"real content {p.number}"


def test_sections_chunks_and_pages(chunks):
    sections = {c.section for c in chunks}
    assert {"Abstract", "3.2 Sparse Gating", "7 Limitations"} <= sections
    assert "References" not in sections                      # excluded by default
    assert max(c.pages[-1] for c in chunks) == 3
    assert [c.id for c in chunks] == list(range(len(chunks)))


def test_chunk_size_bound_and_overlap():
    sentence = "This is sentence number {} of the long section about adapters."
    text = " ".join(sentence.format(i) for i in range(40))
    pages = [Page(1, "1 Introduction\n" + text)]
    cfg = Config(chunk_words=50, overlap_sentences=1)
    out = chunk_document(pages, cfg)
    assert len(out) > 3
    assert all(c.n_words <= 50 + 12 for c in out)            # soft bound: at most one sentence over
    # overlap: last sentence of chunk i is first sentence of chunk i+1
    assert split_sentences(out[0].text)[-1] == split_sentences(out[1].text)[0]


def test_sentence_splitter_keeps_decimals_and_abbreviations():
    s = split_sentences("SGA scores 80.0 on e.g. FoodReviews. It is fast. See Fig. 3 for details.")
    assert len(s) == 3 and s[0].endswith("FoodReviews.")


def test_hyphenated_line_wrap_is_joined():
    pages = [Page(1, "1 Introduction\nWe study low-resource classifi-\ncation with adapters.")]
    out = chunk_document(pages)
    assert "classification" in out[0].text


def test_tokenize_stems_and_keeps_numbers():
    assert tokenize("Training adapters: 80.0 and 0.8%") == ["train", "adapter", "80.0", "0.8"]
