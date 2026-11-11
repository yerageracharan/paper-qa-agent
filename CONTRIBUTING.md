# Contributing

Thanks for helping improve Paper QA Agent. This repository prioritizes reproducible research answers, traceable evidence, and predictable offline behavior.

## Before opening a change

1. Search existing issues and recent commits for overlapping work.
2. For a new feature or architectural change, open an issue first and describe the user problem, proposed behavior, alternatives, and evaluation plan.
3. For a bug, provide a minimal paper/sample input, exact command, expected result, actual result, and relevant logs.
4. Keep changes focused. Do not bundle unrelated formatting, dependency upgrades, and behavior changes.

## Development setup

**Supported Python:** Python 3.10 or newer; CI covers 3.10–3.13.

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -e ".[dev,ui]"
```

## Validation

Run the focused test first, then the full suite:

```bash
python -m pytest -q
python -m paperqa --help
```

For changes to retrieval, citations, chunking, or answer generation, add or update a regression test and use the existing evaluation assets where relevant. Do not claim that a quality improvement is demonstrated unless the evaluation was actually run and the result is recorded.

## Engineering expectations

- Preserve source attribution and make evidence boundaries visible.
- Keep optional providers optional; the core workflow must not silently acquire a paid API dependency.
- Handle empty, malformed, scanned, and unusually small PDFs explicitly.
- Update the README or the relevant page under `docs/` when a user-visible command, setting, or limitation changes.
- Add tests for the behavior changed, including the failure path.

## Pull requests

Use the repository pull-request template. Include the problem, the smallest effective change, user impact, exact validation commands/results, and known limitations. Link the related issue with `Closes #<number>` when applicable.

## Security and sensitive data

Never commit API keys, access tokens, private papers, personal data, or unredacted logs. Report vulnerabilities privately using the process in [SECURITY.md](SECURITY.md).
