"""PDF text extraction, cleaning, section detection and section-aware chunking."""
from __future__ import annotations

import bisect
import re
from collections import Counter
from dataclasses import dataclass, asdict
from pathlib import Path

from pypdf import PdfReader

from .config import Config
from .text import sentence_spans

NAMED_SECTIONS = {"abstract", "references", "acknowledgments", "acknowledgements", "appendix"}
_HEADING_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+(.+)$")
_SMALL_WORDS = {"of", "and", "the", "for", "in", "on", "to", "a", "an", "with", "vs", "by"}


@dataclass
class Page:
    number: int  # 1-based
    text: str


@dataclass
class Chunk:
    id: int
    section: str
    pages: list[int]
    text: str

    @property
    def n_words(self) -> int:
        return len(self.text.split())

    @property
    def embed_text(self) -> str:
        """Section title is prepended so retrieval can match on structure ("limitations", "ablation")."""
        return f"{self.section}. {self.text}"

    def to_dict(self) -> dict:
        return asdict(self)


# ----------------------------------------------------------------------------- extraction
def extract_pages(path: str | Path) -> list[Page]:
    reader = PdfReader(str(path))
    return [Page(i + 1, page.extract_text() or "") for i, page in enumerate(reader.pages)]


def _shape(line: str) -> str:
    return re.sub(r"\d+", "#", line.strip().lower())


def clean_pages(pages: list[Page]) -> list[Page]:
    """Drop page numbers and running headers/footers.

    Only the first and last line of a page are candidates (that is where running headers/footers live), and
    only if their digit-normalised form repeats on at least half the pages. Looking deeper into the page would
    delete body lines such as 'Figure 1' / 'Figure 2' captions that differ only by a digit.
    """
    edge_counts: Counter[str] = Counter()
    for page in pages:
        lines = [ln for ln in page.text.splitlines() if ln.strip()]
        for ln in {lines[0], lines[-1]} if lines else ():
            edge_counts[_shape(ln)] += 1
    threshold = max(2, len(pages) // 2)
    repeated = {shape for shape, n in edge_counts.items() if n >= threshold and len(pages) >= 3}

    cleaned = []
    for page in pages:
        kept = []
        for ln in page.text.splitlines():
            s = ln.strip()
            if not s:
                continue
            if re.fullmatch(r"(page\s*)?\d{1,3}", s.lower()) or _shape(s) in repeated:
                continue
            kept.append(s)
        cleaned.append(Page(page.number, "\n".join(kept)))
    return cleaned


# ----------------------------------------------------------------------------- sections
def _title_like(text: str) -> bool:
    words = text.split()
    if not 1 <= len(words) <= 8 or text.endswith((".", ",", ";", ":")):
        return False
    return all(w[0].isupper() or w.lower() in _SMALL_WORDS or not w[0].isalpha() for w in words)


class _HeadingTracker:
    """Accepts a numbered line as a heading only if its number follows the previous heading's number.

    This stops table rows or wrapped body lines such as '24 GB GPU' from being mistaken for headings.
    """

    def __init__(self) -> None:
        self.top = 0
        self.sub = 0

    def detect(self, line: str) -> str | None:
        s = line.strip()
        if not s or len(s) > 80:
            return None
        if s.lower() in NAMED_SECTIONS:
            return s.title()
        m = _HEADING_RE.match(s)
        if not m or not _title_like(m.group(2)):
            return None
        parts = [int(p) for p in m.group(1).split(".")]
        if len(parts) == 1 and parts[0] == self.top + 1:
            self.top, self.sub = parts[0], 0
            return s
        if len(parts) == 2 and parts[0] == self.top and parts[1] == self.sub + 1:
            self.sub = parts[1]
            return s
        return None


def split_sections(pages: list[Page]) -> list[tuple[str, list[tuple[int, str]]]]:
    """Return [(section_title, [(page_number, line), ...]), ...] in document order."""
    tracker = _HeadingTracker()
    sections: list[tuple[str, list[tuple[int, str]]]] = [("Front Matter", [])]
    for page in pages:
        for line in page.text.splitlines():
            heading = tracker.detect(line)
            if heading:
                sections.append((heading, []))
            else:
                sections[-1][1].append((page.number, line))
    return [(title, lines) for title, lines in sections if lines]


def _join_lines(lines: list[tuple[int, str]]) -> tuple[str, list[int], list[int]]:
    """Join wrapped lines into running text (de-hyphenating) and remember each line's start offset + page."""
    text = ""
    starts: list[int] = []
    pages: list[int] = []
    for page, line in lines:
        if text.endswith("-") and line[:1].islower():
            text = text[:-1]
        elif text:
            text += " "
        starts.append(len(text))
        pages.append(page)
        text += line
    return text, starts, pages


# ----------------------------------------------------------------------------- chunking
def chunk_document(pages: list[Page], config: Config | None = None) -> list[Chunk]:
    config = config or Config()
    chunks: list[Chunk] = []
    for title, lines in split_sections(pages):
        if title in config.exclude_sections:
            continue
        text, starts, line_pages = _join_lines(lines)
        sents = []  # (sentence, page)
        for a, b in sentence_spans(text):
            sentence = text[a:b].strip()
            if sentence:
                page = line_pages[max(bisect.bisect_right(starts, a) - 1, 0)]
                sents.append((sentence, page))
        i = 0
        while i < len(sents):
            group, words = [], 0
            j = i
            while j < len(sents) and (not group or words + len(sents[j][0].split()) <= config.chunk_words):
                group.append(sents[j])
                words += len(sents[j][0].split())
                j += 1
            chunks.append(
                Chunk(
                    id=len(chunks),
                    section=title,
                    pages=sorted({p for _, p in group}),
                    text=" ".join(s for s, _ in group),
                )
            )
            if j >= len(sents):
                break
            i = max(j - config.overlap_sentences, i + 1)
    return chunks


def load_pdf(path: str | Path, config: Config | None = None) -> list[Chunk]:
    return chunk_document(clean_pages(extract_pages(path)), config)
