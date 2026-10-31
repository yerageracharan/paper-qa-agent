# Paper Q&A Agent

<p align="center">
  <img src="assets/hero.svg" alt="Paper Q&A Agent — ask your PDF and get answers with evidence" width="100%" />
</p>

<p align="center">
  <strong>Your research-paper sidekick. It reads one PDF, searches for evidence, and gives you an answer with a section, page, and supporting passage — or admits when it cannot find the answer.</strong>
</p>

<p align="center">
  <img alt="Python 3.10–3.13 CI" src="https://img.shields.io/badge/Python-3.10%E2%80%933.13-3776AB?logo=python&logoColor=white" />
  <img alt="Tests" src="https://img.shields.io/badge/tests-31%20in%20project-6f42c1" />
  <img alt="License MIT" src="https://img.shields.io/badge/license-MIT-2ea44f" />
  <img alt="Interface CLI and Streamlit" src="https://img.shields.io/badge/interface-CLI%20%2B%20Streamlit-ff4b4b" />
</p>

> **Your starting point:** this guide is published alongside the complete project repository. The repository contains the Python package, Streamlit app, sample PDF, tests, evaluation files, and project configuration. Clone the repository before following the setup steps; downloading this README by itself is not enough to run the agent.

---

## 0. Welcome, rookie researcher! 🎒

Ever opened a 30-page research paper, stared at a wall of academic vocabulary, and thought:

**“WHERE IS THE ONE PARAGRAPH THAT ANSWERS MY QUESTION?!”**

That is the boss fight this project is trying to make less painful.

**Paper Q&A Agent** is a document-question-answering project. Give it a text-based research-paper PDF, ask a question, and it searches the paper for relevant passages. When it answers, it is designed to attach a source marker such as `[S1]`, with the section, page, and supporting quote. When the evidence is too weak or missing, it can abstain instead of confidently inventing an answer.

Think of it as a tiny research assistant with one very important rule:

> **No evidence, no victory speech.**

### What this project does

- Reads the text from a PDF.
- Cleans extracted text and divides it into section-aware chunks while keeping page information.
- Searches using a hybrid of BM25 keyword retrieval and embeddings, fused with Reciprocal Rank Fusion (RRF).
- Uses a coverage gate before answering.
- Returns answers with source citations, or a machine-readable refusal reason.
- Offers a command-line interface and a Streamlit web interface.
- Includes an evaluation harness and a test suite, according to the supplied project README.

### What it does not promise

- It does not understand every PDF layout perfectly.
- It does not perform OCR on scanned PDFs.
- It does not guarantee that every answer is correct just because a citation is present.
- It is designed for one document at a time, not cross-paper research across a library.

---

## 1. See the mission before installing anything 🗺️

<p align="center">
  <img src="assets/workflow.svg" alt="Workflow from PDF extraction through retrieval and verification to a cited answer or refusal" width="100%" />
</p>

The flow is:

1. **PDF enters the arena.** The project extracts text from the document.
2. **Text gets cleaned.** Headers and page-number noise are removed where possible.
3. **The paper is divided into chunks.** Sentence-aware chunks retain section and page information.
4. **The search system hunts for evidence.** BM25 and embeddings contribute rankings; RRF combines them.
5. **The answer is challenged.** Coverage, citation, and number checks help reject unsupported output.
6. **The result appears.** You get an answer with citations, or an abstention reason.

### Project vocabulary, translated into human

| Project term | Plain-English meaning |
|---|---|
| **PDF extraction** | Turning a PDF's selectable text into text the program can process. |
| **Chunk** | A small passage of the paper that can be retrieved as evidence. |
| **BM25** | A keyword-search ranking method. Useful when the question shares exact terms with the paper. |
| **Embedding** | A numerical representation of text used to compare meaning-related passages. |
| **Hybrid retrieval** | Combining keyword and embedding search rather than relying on only one. |
| **RRF** | Reciprocal Rank Fusion — a way to combine ranked result lists. |
| **Coverage gate** | A check that asks whether the retrieved text covers enough of the question. |
| **Abstention** | The agent declines to answer because it cannot find enough support. |
| **Citation hit** | The cited chunk contains the evidence expected for the evaluation question. |

---

## 2. Before the first summon: what you need 🧰

| Requirement | What to prepare |
|---|---|
| Python | Python **3.10–3.13** is the CI range stated in the project README. The supplied README reports local testing on Python 3.13. |
| Terminal | PowerShell on Windows, or Terminal on macOS/Linux. |
| Project files | The full repository/source folder — not just this README. |
| PDF | A text-based PDF. A scanned image-only PDF is not supported by the documented extraction path. |
| API key | **Not needed** for the offline baseline. An Anthropic key is optional for the Claude answerer. |
| Internet | Needed to install packages. The offline baseline does not need a hosted LLM API key once dependencies are installed. |

### Check that Python is installed

Open a terminal and run:

**Windows (PowerShell):**

```powershell
py --version
```

**macOS / Linux:**

```bash
python3 --version
```

The project README says CI covers Python 3.10 to 3.13, while the local environment used for its reported run was Python 3.13. If you have several Python versions installed, use Python 3.13 for the closest match to that local run.

---

## 3. Install it — step by step, no speed-running 🏃

First, download or clone the **complete project repository** and open a terminal in its root folder. The root folder should contain `pyproject.toml`, `app.py`, and the `paperqa/` directory.

### Step 1 — Create a virtual environment

A virtual environment keeps this project's Python packages separate from other projects. Think of it as giving this agent its own little training room.

**Windows (PowerShell):**

```powershell
py -3.13 -m venv .venv
```

**macOS / Linux:**

```bash
python3 -m venv .venv
```

### Step 2 — Activate the environment

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**

```bat
.venv\Scripts\activate.bat
```

**macOS / Linux:**

```bash
source .venv/bin/activate
```

When it is active, your terminal prompt commonly shows `(.venv)` at the beginning.

### Step 3 — Upgrade pip

```bash
python -m pip install --upgrade pip
```

### Step 4 — Install the project and its development/UI tools

```bash
pip install -e ".[dev,ui]"
```

This is the documented install command for the core project, development dependencies such as pytest, and the Streamlit interface.

### Step 5 — Run the test suite

```bash
python -m pytest -q
```

The supplied project README reports **31 tests** and an approximate run time of two seconds, without a network connection or API key. That is the project's reported result, not a test run performed while preparing this README.

### Step 6 — Ask your first question

```bash
python -m paperqa ask data/sample_paper.pdf "What bottleneck dimension do the adapters use?"
```

The sample PDF is described by the project README as a synthetic paper generated by `scripts/make_sample_paper.py`.

### Step 7 — Launch the visual interface

```bash
streamlit run app.py
```

Streamlit starts a local web app. Open the local address printed in the terminal. The documented interface supports uploading a text-based PDF.

<p align="center">
  <img src="assets/use-cases.svg" alt="Four example research tasks: method check, result hunt, section finder, and asking about a fact absent from the paper" width="100%" />
</p>

---

## 4. Your first research mission 🎯

The supplied project README includes these example questions and outcomes. Use them to understand the intended behaviour.

### Mission A — Ask about a fact that appears in the paper

```bash
python -m paperqa ask data/sample_paper.pdf "Which layers keep their adapters according to the learned gates?"
```

Example output format from the supplied README:

```text
The learned gates keep adapters in the upper layers: layers 7 to 12 retain an active gate in 82% of runs, ... [S1]

[S1] Section 6.2 Which Layers Are Selected (p. 3):
     "The learned gates keep adapters in the upper layers: ..."
```

**How to read this:**

- The answer contains a source marker: `[S1]`.
- `[S1]` points to a retrieved source passage.
- The citation names **Section 6.2** and **page 3**.
- A supporting quotation is shown below the answer.

<p align="center">
  <img src="assets/citation-card.svg" alt="Illustration of an answer with a source marker, section, page, and supporting quote" width="100%" />
</p>

### Mission B — Ask about something the paper does not report

```bash
python -m paperqa ask data/sample_paper.pdf "What was the carbon footprint of the experiments?"
```

Example output from the supplied README:

```text
I could not find an answer to this in the paper.
(reason: low_coverage; coverage 0.22)
```

That is not a crash. It is an intentional refusal. The retrieval coverage was low, so the agent did not proceed as though it had evidence.

### Mission C — Explore the other CLI commands

The supplied project README lists these CLI modes:

- `ask` — ask a question about a PDF.
- `chat` — interactive question-and-answer mode.
- `chunks` — inspect the document chunks.
- `eval` — evaluate the system against a question set.

For the exact arguments supported by your checked-out version, use the built-in help:

```bash
python -m paperqa --help
python -m paperqa ask --help
```

---

## 5. How does it avoid making stuff up? 🛡️

The design uses multiple checks. None is magic, and none proves that every response is correct, but together they make unsupported answers easier to catch.

<p align="center">
  <img src="assets/abstention.svg" alt="Four checks: retrieval coverage, answerer refusal, citation validation, and number guard" width="100%" />
</p>

### The four checks

1. **Coverage gate** — calculates the IDF-weighted share of question content terms found in retrieved passages. Terms that never occur in the paper receive high weight. Below the configured threshold, the system abstains before calling the LLM.
2. **Answerer refusal** — the Claude answerer is instructed to return `NOT_FOUND` when the excerpts do not contain the answer. The extractive answerer also has a refusal condition based on question-term coverage.
3. **Citation validation** — an answer without a valid `[S#]` citation is rejected.
4. **Number guard** — every number in an answer must appear in the cited passages. This can catch unsupported figures, but it can also reject a legitimate newly calculated number.

### Refusal reasons

| Reason | Meaning in the documented design |
|---|---|
| `low_coverage` | Retrieved passages do not cover enough of the question. |
| `model_not_found` | The answerer says the evidence does not contain the answer. |
| `no_valid_citation` | The generated answer does not contain a valid source citation. |
| `unsupported_number` | A number in the answer does not appear in the cited passage. |

**Important:** a citation is a trail to inspect, not a guarantee. Open the cited passage and check that it really supports the claim before using an answer in academic work.

---

## 6. Optional power-ups: real models ⚡

The project has an offline baseline and optional backends.

### Option A — Stay with the offline baseline

This is the easiest starting point. The documented default uses:

- **LSA embeddings** — a lightweight offline representation learned from the paper's text.
- **Extractive answerer** — selects a relevant sentence rather than generating a free-form answer.

The baseline needs no paid API key. The supplied README warns that LSA trained on a single three-page sample paper is not equivalent to a modern neural embedding model.

### Option B — Add sentence-transformers embeddings

Install the optional embedding dependencies:

```bash
pip install -e ".[embeddings]"
```

Then run an evaluation using the sentence-transformers embedder and the extractive answerer:

```bash
python -m paperqa eval data/sample_paper.pdf --embedder st --llm extractive --out results_st
```

The README describes this as a way to isolate the retrieval effect while keeping the answerer extractive.

### Option C — Use the Anthropic / Claude answerer

Install the optional LLM dependency:

```bash
pip install -e ".[llm]"
```

Set your API key as an environment variable. **Never paste a real API key into a README, source file, screenshot, or public GitHub commit.**

**Windows (PowerShell):**

```powershell
$env:ANTHROPIC_API_KEY = "your-key-here"
```

**macOS / Linux:**

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

Run the Claude evaluation:

```bash
python -m paperqa eval data/sample_paper.pdf --llm anthropic --out results_claude
```

The supplied README identifies the default configured model as `claude-sonnet-5-5`. The model name is controlled by project configuration; check the current configuration and the provider's model availability before running.

### Which setup should a beginner choose?

| Your goal | Start with |
|---|---|
| Just run the project and understand the pipeline | Offline baseline |
| Experiment with semantic retrieval | `--embedder st --llm extractive` |
| Evaluate a hosted answerer | `--llm anthropic` with your own API key |

---

## 7. Evaluation: does it actually work? 📈

The supplied project README reports an evaluation on **29 questions** about **one synthetic paper**: 23 answerable questions and 6 unanswerable questions. The questions are divided into a development split (10 questions) and a test split (19 questions).

> **Read the fine print:** these are small-sample, offline-baseline results. They are useful as a reproducible starting point, not as proof that the system performs equally well on real research papers. The uploaded README says the Claude answerer and sentence-transformers embedder were implemented and unit-tested against fakes, but were **not evaluated** in that build environment because no API key or Hugging Face model-hub access was available.

### Retrieval results

| Retrieval mode | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| BM25 only | 73.9% | 91.3% | 95.7% | 0.837 |
| Dense (LSA) only | 82.6% | 91.3% | 95.7% | 0.880 |
| Hybrid (RRF) | 82.6% | 91.3% | 95.7% | 0.880 |

### End-to-end results

| Split | Answer accuracy | False-abstain | Abstain recall | Wrong when answering | Citation hit |
|---|---:|---:|---:|---:|---:|
| Dev (8 answerable / 2 unanswerable) | 75.0% | 25.0% | 100% | 0.0% | 100% |
| **Test (15 / 4)** | **86.7%** | 6.7% | **50.0%** | 7.1% | 92.9% |
| All (23 / 6) | 82.6% | 13.0% | 66.7% | 5.0% | 95.0% |

### What those numbers are saying

- The strongest documented weakness is **in-topic but unanswerable questions**. On the test split, abstain recall was 50%. The offline extractive answerer sometimes selected a nearby sentence that mentioned a related concept without answering the actual question.
- Hybrid retrieval did **not** outperform dense LSA retrieval on this tiny dataset. The project README explicitly says this is not evidence for or against hybrid retrieval on larger, real papers.
- Paraphrase questions were difficult for the offline baseline because it does not use a modern neural semantic model.
- One test question changes a percentage by about 6.7 points, so the test set is small.

### Run the evaluation yourself

```bash
python -m paperqa eval data/sample_paper.pdf
```

The documented default writes a Markdown report and JSON results under `results/`. For alternate backends, see the previous section.

---

## 8. Real-use screenshots: what belongs here 📸

A README looks much better when readers can see the actual app. But there is an important difference between a **diagram** and a **real screenshot**: a diagram explains the design; a screenshot proves what the running application looked like.

The complete source tree is now in this repository, including `app.py` and the `paperqa/` package. However, this README-and-assets update does **not** include genuine screenshots captured from a running Streamlit session. The diagrams in `assets/` explain the workflow; they are not screenshots of the live app. No illustration is labelled as a real screenshot.

After running the application locally, capture these three real screens and save them in `assets/screenshots/`:

| Screenshot filename | What the real screen should show | Suggested caption |
|---|---|---|
| `01-upload-paper.png` | The running Streamlit app with the sample PDF loaded or selected. | “Load a text-based research paper.” |
| `02-cited-answer.png` | The app answering the adapter-layer question, with the `[S1]` citation visible. | “An answer with a section, page, and supporting evidence.” |
| `03-honest-refusal.png` | The app responding to the carbon-footprint question with its refusal reason. | “When the paper does not contain the answer, the agent can abstain.” |

### How to capture them on Windows

1. Start the app with `streamlit run app.py`.
2. Open the local URL printed in the terminal.
3. Load the sample PDF through the app.
4. Run the example question from **Mission A** and wait for the full answer and citation to appear.
5. Press **Win + Shift + S**, select the app area, and save the image as `02-cited-answer.png` inside `assets/screenshots/`.
6. Ask the carbon-footprint question from **Mission B** and capture the refusal as `03-honest-refusal.png`.
7. Capture the initial upload state as `01-upload-paper.png`.
8. Add the three images to GitHub along with this README.

### How to capture them on macOS

Use **Shift + Command + 4** to select the app area, then save the image files using the same names and folder structure.

The image filenames and capture checklist are documented in [`assets/screenshots/README.md`](assets/screenshots/README.md). Once captured, embed them using these paths:

```markdown
![Paper loaded in the real Streamlit app](assets/screenshots/01-upload-paper.png)

![Cited answer in the real Streamlit app](assets/screenshots/02-cited-answer.png)

![Honest refusal in the real Streamlit app](assets/screenshots/03-honest-refusal.png)
```

**Screenshot privacy check:** close unrelated tabs, hide personal information, and make sure no API keys or other secrets are visible before committing screenshots.

---

## 9. Project structure 🧱

The repository is organized into small modules so each part has one main job:

```text
paper-qa-agent/
├── app.py                       # Streamlit interface
├── paperqa/
│   ├── ingest.py                 # PDF extraction, cleaning, sections, chunks
│   ├── index.py                  # BM25, embedders, hybrid retrieval, RRF
│   ├── llm.py                    # Anthropic and extractive answerers
│   ├── agent.py                  # Retrieval, verification, answers/refusals
│   ├── evaluate.py               # Evaluation metrics and reports
│   ├── cli.py                    # Command-line commands
│   ├── text.py                   # Text helpers
│   └── config.py                 # Configuration
├── data/
│   └── sample_paper.pdf          # Synthetic sample paper
├── eval/
│   └── eval_set.json             # 29-question evaluation set
├── tests/                        # 31 tests, according to supplied README
├── results/                      # Evaluation report and JSON output
├── docs/
│   └── demo.md                   # CLI transcript
├── scripts/
│   ├── make_sample_paper.py      # Sample PDF generator
│   └── make_demo.sh              # Demo transcript generator
├── LEARNINGS.md                 # Lessons and future improvements
└── pyproject.toml                # Package and dependency configuration
```

---

## 10. Known limitations — read this before trusting the sidekick ⚠️

- **Text-based PDFs only.** There is no OCR path for scanned, image-only PDFs.
- **Complex layouts can be messy.** Two-column text, equations, and tables may extract imperfectly. Tables can flatten into rows of cells.
- **One document at a time.** The described system does not perform cross-paper retrieval.
- **Citation granularity.** Citations identify a chunk, section, and page; they do not point to exact character offsets in the original PDF.
- **The evaluation is narrow.** The supplied benchmark uses one synthetic paper and 29 questions.
- **String-based answer scoring.** The evaluation's `must_include` check can mark a correct paraphrase as wrong; human review or an LLM judge could be more faithful.
- **The number guard is strict.** It may reject a legitimate answer that calculates a new number not literally present in the cited text.
- **Offline LSA is a baseline.** It is not the same as a pretrained neural embedding model.

Use it as a research aid, not as an authority. Verify important claims against the original paper before citing them in coursework, reports, or publications.

---

## 11. Troubleshooting dojo 🧯

### `python` or `py` is not recognised

Python may not be installed or may not be on your PATH. Install a supported Python version, reopen the terminal, and check `py --version` (Windows) or `python3 --version` (macOS/Linux).

### `No module named paperqa`

You may be outside the project root, or the editable install may not have completed. Change into the folder containing `pyproject.toml`, activate `.venv`, and run:

```bash
pip install -e ".[dev,ui]"
```

### `streamlit` is not recognised

Make sure the virtual environment is active and that you installed the UI extra:

```bash
pip install -e ".[dev,ui]"
```

### PowerShell refuses to activate the virtual environment

Use the Command Prompt activation command shown in Step 2, or follow your organisation's approved PowerShell execution-policy guidance. Do not change machine-wide security settings just to run this project.

### The PDF gives poor answers

Check that text can be selected and copied from the PDF. Scanned PDFs are outside the documented support. Complex tables and multi-column layouts can also produce imperfect extraction. Inspect the source passage behind the citation before trusting the answer.

---

## 12. Suggested learning path — level up one panel at a time 🌱

1. **Run the baseline.** Install the project, run the tests, ask the two sample questions.
2. **Inspect the evidence.** Use the cited section and page to compare the agent's answer with the paper.
3. **Explore retrieval.** Run the evaluation with BM25, dense, and hybrid settings if the checked-out version exposes the corresponding options.
4. **Try the optional embedder.** Compare the `st` evaluation with the offline LSA baseline.
5. **Try the optional answerer.** Configure Anthropic and run a separate evaluation. Keep the offline results as a comparison, not as a substitute.
6. **Improve the evaluation set.** Add difficult questions, especially questions about a topic that appears in the paper but whose exact answer is absent.

The most valuable improvement suggested by the supplied results is a stronger evaluation design for **in-topic but unanswerable questions**. The project README notes that this weakness was not represented in the development split, so threshold tuning on that split did not reveal it.

---

## 13. FAQ 💬

**Do I need an API key to try it?**  
No. The documented offline baseline uses LSA embeddings and an extractive answerer. The Anthropic answerer is optional and requires `ANTHROPIC_API_KEY`.

**Can I upload any PDF?**  
Use a text-based PDF. Scanned image-only PDFs are not supported by the documented extraction pipeline, and complex layouts may extract imperfectly.

**Does it always answer?**  
No. Refusal is an intentional behaviour when evidence is missing or fails validation.

**Can I ask questions across several papers at once?**  
Not in the described version. It is a single-document Q&A system.

**Are the reported accuracy numbers a benchmark of real academic papers?**  
No. The supplied README reports 29 questions on one synthetic paper. Treat those numbers as a small baseline evaluation.

**Can I trust every cited answer?**  
No system check replaces reading the source. Use the citation to inspect the original passage and verify that it supports the claim.

---

## 14. Credits, license, and final words 🏁

The repository includes an MIT `LICENSE` file. Read it before redistributing or adapting the project.

One last rule from the Research Guild:

> **A confident answer is not the same thing as a supported answer. Follow the citation. Check the evidence. Then decide.**

Got a paper? Bring it to the arena. 📚