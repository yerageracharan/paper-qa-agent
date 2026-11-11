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

## Change ownership and proof

- Keep one authoritative owner for each domain rule and each persisted state. UI, CLI, MCP, and provider adapters translate inputs and outputs; they must not reimplement business policy or become competing sources of truth.
- Before changing a contract, trace the input through its owner to every consumer. Update callers, schemas, examples, docs, and regression tests together. Remove superseded paths unless a documented public-compatibility requirement keeps them.
- Keep optional external model/provider integrations behind adapters. Use injected or mocked adapters for deterministic unit tests; label live network/provider checks separately and never describe a mock as live verification.
- Validate untrusted user, model, file, and network data at the boundary. Preserve the product's evidence/provenance rules and reject malformed inputs rather than silently inventing defaults.
- Verify the supported user entry point and at least one relevant failure path. Report exact commands and results; CI on a different commit SHA is not proof for the current change.
- Keep the root README as the user entry point, `docs/README.md` as the documentation map, and focused guides as the owners of detailed contracts. Update links when files move. Do not hand-edit generated output when a source or generator owns it.


## Repository automation rules

- Treat files under `.github/workflows/` as production code. When changing a workflow, inspect the triggered run for the exact commit SHA; a prior green run is not proof for a newer commit.
- Pin third-party GitHub Actions to full 40-character commit SHAs and keep the upstream release tag in a trailing comment. Do not replace a pinned SHA with a floating major-version tag.
- Use the least-privilege `permissions` block. Default to read-only; grant write access only to the specific job that must publish or commit generated output.
- Give every job a finite `timeout-minutes`. Add a clear `concurrency` group for expensive or supersedable work; cancel stale pull-request runs, but do not cancel workflows whose purpose is to publish a completed artifact or evidence.
- Keep workflow logs and uploaded artifacts free of secrets and personal data. Set retention to the shortest period that still serves the evaluation or debugging purpose.
- Rely on the existing Dependabot configuration for action updates, then review release notes and run the affected workflow before considering the update complete.
