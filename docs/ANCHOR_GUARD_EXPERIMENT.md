# Experimental question-anchor guard

## Why this experiment exists

The original offline answerer sometimes treated a paragraph about the right subject as support for a fact that the paper did not actually report. The most obvious test examples were:

- `u05`: What accuracy does SGA reach on the MNLI dataset? The paper contains SGA results but does not mention MNLI.
- `u06`: Did the authors run a human evaluation? The paper reports model metrics, but does not describe participants, interviews, surveys, user studies or usability studies.

## First implementation

The first implementation added an **opt-in** setting, `strict_question_anchors`, defaulting to `False`. When enabled, it checks:

1. All-caps technical acronyms in the question, such as MNLI, must appear as whole tokens in the paper.
2. A question explicitly asking about a human evaluation/study must have recognised human-study evidence in the paper.

It is a narrow lexical check. It is not a semantic entailment model and it is not proof that a cited passage supports every requested fact.

## First completed evaluation

GitHub Actions run [41360095700](https://github.com/yerageracharan/paper-qa-agent/actions/runs/41360095700) completed successfully. The workflow ran the full suite, ran both evaluation variants and uploaded artifact `paperqa-anchor-guard` (ID `13105075255`). It reported 45 passed tests and 1 skipped test.

Baseline and guarded variants used the same synthetic PDF, 29-question evaluation set, LSA embedder, extractive answerer and top-k=5. Only `strict_question_anchors` changed.

| Test-split metric | Baseline | Guard enabled |
|---|---:|---:|
| Answer accuracy | 86.7% | 86.7% |
| False-abstain rate | 6.7% | 6.7% |
| Abstain recall on unanswerable | 50.0% | 100.0% |
| Wrong when answering | 7.1% | 7.1% |
| Citation hit | 92.9% | 92.9% |
| Overall accuracy | 78.9% | 89.5% |

The guard newly refused two formerly incorrect answers: `u05` (missing MNLI anchor) and `u06` (no recognised human-evaluation evidence). No previously refused question became answered. Answerable-question accuracy, false abstention and citation-hit rate stayed unchanged in this test.

The unanswerable test subset contains only four questions. The 100% abstention recall is a result on this small synthetic test, not proof of real-world performance.

## Second refinement: mixed-case technical names

The first acronym rule handled all-caps names such as MNLI but missed technical names with internal capital letters, such as `LoRA`. The rule was extended to detect both all-caps acronyms and CamelCase technical names. It compares normalised tokens case-insensitively so a name like `FoodReviews` is accepted when it actually appears in the paper.

The LoRA evaluation question (`u03`) was already refused by the baseline as `model_not_found`; the new check should make its reason more specific (`missing_question_anchor`). It should not be counted as an additional answer-correction gain.

The mixed-case update and its additional tests are in commits `c8c833c36808d50a772aae23e1ffa857abd20a06`, `38a84b17cb2fed8db76fd11d9ffa584645c6ccb7`, `73416405733e6539253c683a828f1d5437bf93b4`, `88549865008ae1b5ff980160acce7b56b6c13292`, `9734ebe86b17f204aef247ac7bbba8b361c16c39`, and `2b87de8573a703547d484368b8d75c8554627b6f`.

At the time this section was written, the final post-refinement GitHub Actions run was queued/in progress: [run 41360773574](https://github.com/yerageracharan/paper-qa-agent/actions/runs/41360773574). Its result must be checked before this refinement is marked validated.

## Reproduce

From the repository root:

~~~powershell
python -m pytest -q
python scripts/evaluate_anchor_guard.py --pdf data/sample_paper.pdf --eval-set eval/eval_set.json --top-k 5 --out results/anchor-guard
~~~

No paid API key is required. The experiment uses the offline extractive answerer.

## Decision and limitations

- Keep `strict_question_anchors=False` by default until it has been tested on independent real papers.
- A question can use a long form without using the same acronym; the lexical check may refuse a valid question if the paper uses a different name.
- A paper may describe a human study using terminology outside the current recognised vocabulary.
- This safeguard does not prove entailment. It only checks whether some specific anchors occur.
- Continue to measure answerable accuracy, false abstention, unanswerable refusal, citation quality and latency together.
- The current evaluation uses one synthetic paper and 29 questions. Larger, independently reviewed real-paper datasets are required before making product-quality claims.
