# Experimental question-anchor guard

## Why this experiment exists

The original offline answerer sometimes treated a paragraph about the right subject as support for a fact that the paper did not actually report. The clearest test examples were:

- `u05`: What accuracy does SGA reach on the MNLI dataset? The paper contains SGA results but does not mention MNLI.
- `u06`: Did the authors run a human evaluation? The paper reports model metrics, but does not describe participants, interviews, surveys, user studies or usability studies.
- `u03`: What macro-F1 does LoRA achieve on FoodReviews? The paper includes a FoodReviews result, but does not mention LoRA.

## How the guard works

The implementation adds an **opt-in** setting, `strict_question_anchors`, defaulting to `False`. When enabled, it checks:

1. All-caps technical acronyms in the question, such as MNLI, must appear as whole tokens in the paper.
2. Technical CamelCase names in the question, such as LoRA or FoodReviews, are normalised and compared case-insensitively against whole tokens in the paper.
3. A question explicitly asking about a human evaluation/study must have recognised human-study evidence in the paper.

It is a narrow lexical check. It is not a semantic entailment model and it is not proof that a cited passage supports every requested fact.

## First completed evaluation

GitHub Actions run [41360095700](https://github.com/yerageracharan/paper-qa-agent/actions/runs/41360095700) completed successfully. It ran the full suite, the baseline-versus-guard comparison and uploaded the first `paperqa-anchor-guard` artifact. It reported 45 passed tests and 1 skipped test.

The first version newly refused two formerly incorrect answers: `u05` (missing MNLI anchor) and `u06` (no recognised human-evaluation evidence). It did not newly refuse any answerable question.

## Refined evaluation: mixed-case technical names

After the first result, the anchor detector was extended to recognise mixed-case names such as LoRA. It also received regression tests to ensure a name such as FoodReviews is accepted when the paper actually contains it. The `u03` question was already refused by the baseline as `model_not_found`; the refined guard now reports the more specific reason `missing_question_anchor`. This is a better explanation of the refusal, not an additional correction of a previously answered question.

The refined workflow [41360773574](https://github.com/yerageracharan/paper-qa-agent/actions/runs/41360773574) completed successfully. The test suite reported **48 passed, 1 skipped**, the comparison ran, and artifact `paperqa-anchor-guard` (ID `13105700458`) was uploaded. The standard CI run [41360773599](https://github.com/yerageracharan/paper-qa-agent/actions/runs/41360773599) also passed on Python 3.10, 3.11, 3.12 and 3.13, including the original evaluation command.

### Test-split results

Both variants use the same synthetic PDF, 29-question evaluation set, LSA embedder, extractive answerer and top-k=5. Only `strict_question_anchors` changes.

| Test-split metric | Baseline | Guard enabled |
|---|---:|---:|
| Answer accuracy | 86.7% | 86.7% |
| False-abstain rate | 6.7% | 6.7% |
| Abstain recall on unanswerable | 50.0% | 100.0% |
| Wrong when answering | 7.1% | 7.1% |
| Citation hit | 92.9% | 92.9% |
| Overall accuracy | 78.9% | 89.5% |

The guard newly refused `u05` and `u06`; it newly answered no questions. It changed the refusal reason for three examples: `u03`, `u05` and `u06`. In `u03`, the baseline already abstained, but the refined guard explained that the requested method name (LoRA) was absent. The other two were previously incorrect answers and are now refusals.

The test set has only four unanswerable questions. Its 100% abstention recall is a result on this small synthetic test, not proof of real-world performance. In addition, `u03`'s more specific refusal reason should not be counted as another answer-accuracy gain.

### Overall split comparison

| All-question metric | Baseline | Guard enabled |
|---|---:|---:|
| Answer accuracy on answerable questions | 82.6% | 82.6% |
| False-abstain rate | 13.0% | 13.0% |
| Abstain recall on unanswerable | 66.7% | 100.0% |
| Wrong when answering | 5.0% | 5.0% |
| Citation hit | 95.0% | 95.0% |
| Overall accuracy | 79.3% | 86.2% |

## Reproduce

From the repository root:

~~~powershell
python -m pytest -q
python scripts/evaluate_anchor_guard.py --pdf data/sample_paper.pdf --eval-set eval/eval_set.json --top-k 5 --out results/anchor-guard
~~~

No paid API key is required. The experiment uses the offline extractive answerer.

## Decision and limitations

- Keep `strict_question_anchors=False` by default until the rule has been tested on independent real papers.
- A question can use a long form without using the same acronym; the lexical check may refuse a valid question if the paper uses a different name.
- A paper may describe a human study using terminology outside the current recognised vocabulary.
- This safeguard does not prove entailment. It only checks whether some high-specificity anchors occur.
- Continue to measure answerable accuracy, false abstention, unanswerable refusal, citation quality and latency together.
- The current evaluation uses one synthetic paper and 29 questions. Larger, independently reviewed real-paper datasets are required before making product-quality claims.
