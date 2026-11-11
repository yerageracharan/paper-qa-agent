# Agent Instructions

These instructions apply to the whole Paper QA Agent repository.

## Product contract

- Every factual answer must remain traceable to retrieved paper chunks and citations.
- When evidence is absent or insufficient, preserve the not-found/uncertain outcome instead of filling the gap.
- Keep default offline behavior working; hosted LLM and embedding integrations remain optional extras.
- Do not fabricate page numbers, quotations, paper metadata, citations, or experimental results.
- Treat PDF extraction limitations, chunk boundaries, and retrieval configuration as explicit sources of uncertainty.

## Repository map

`paperqa/` contains the package; `app.py` is the Streamlit UI; `data/` contains sample material; `eval/` and `results/` hold evaluation assets and outputs; `tests/` holds automated tests.

## Working rules

- Read the README and relevant files in `docs/` before changing behavior.
- Inspect the existing implementation and tests before editing; do not replace a subsystem just to make the diff look larger.
- Keep one concern per change. Prefer a small regression test next to the behavior it protects.
- Never invent sources, citations, measurements, paper details, or benchmark outcomes.
- Do not download, expose, or commit user papers or private research data.
- Avoid new runtime dependencies unless the feature cannot be implemented well with the current stack; explain any dependency in the change.
- Preserve existing CLI and Python API behavior unless the change explicitly documents a breaking change.
- Do not state that tests, evaluations, or commands passed unless they were run and the exact result is available.

## Validation commands

```bash
python -m pytest -q
python -m paperqa --help
```

For citation/retrieval/answer changes, include a regression case with the paper text and expected evidence behavior. Use synthetic or public sample papers in tests.
