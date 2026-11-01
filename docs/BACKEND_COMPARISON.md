# Embedding backend comparison: LSA versus Sentence Transformers

Date: 2 November 2026
GitHub Actions run: https://github.com/yerageracharan/paper-qa-agent/actions/runs/41358948059
Artifact: paperqa-backend-comparison (ID 13104432820)

## Purpose

We compared the offline LSA embedder with the optional Sentence Transformers model. Both runs used the same synthetic three-page PDF, the same 29 questions, top-k=5, and the same offline extractive answerer. Only the embedding backend changed. No Anthropic API key or paid hosted LLM was used.

## Workflow result

The GitHub Actions workflow completed successfully. Dependency installation, the full test suite, both evaluations, and artifact upload all passed. The artifact includes combined and per-backend Markdown and JSON reports. It was created on 1 November 2026 UTC and has a 30-day retention period.

## Retrieval results

There are 23 answerable questions. Hit@k is the percentage of questions with an evidence-bearing passage among the first k retrieved chunks. MRR rewards placing the first relevant passage near rank 1.

| Embedder | Mode | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---|---:|---:|---:|---:|
| LSA | BM25 | 73.9% | 91.3% | 95.7% | 0.837 |
| LSA | Dense | 82.6% | 91.3% | 95.7% | 0.880 |
| LSA | Hybrid | 82.6% | 91.3% | 95.7% | 0.880 |
| Sentence Transformers | BM25 | 73.9% | 91.3% | 95.7% | 0.837 |
| Sentence Transformers | Dense | 56.5% | 87.0% | 91.3% | 0.714 |
| Sentence Transformers | Hybrid | 78.3% | 95.7% | 95.7% | 0.848 |

BM25 is unchanged because it does not use embeddings. Sentence Transformers dense retrieval did worse than LSA on every measure. Its hybrid mode lifted Hit@3 from 91.3% to 95.7%, but Hit@1 fell from 82.6% to 78.3% and MRR fell from 0.880 to 0.848. This is a mixed trade-off, not a consistent win.

## End-to-end results

| Embedder | Split | Answer accuracy | False abstain | Abstain recall on unanswerable | Wrong when answering | Citation hit | p50 | p95 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| LSA | Dev | 75.0% | 25.0% | 100.0% | 0.0% | 100.0% | 0.98 ms | 1.24 ms |
| ST | Dev | 75.0% | 25.0% | 100.0% | 0.0% | 100.0% | 6.63 ms | 7.43 ms |
| LSA | Test | 86.7% | 6.7% | 50.0% | 7.1% | 92.9% | 1.00 ms | 1.18 ms |
| ST | Test | 86.7% | 6.7% | 50.0% | 7.1% | 92.9% | 6.66 ms | 7.08 ms |
| LSA | All | 82.6% | 13.0% | 66.7% | 5.0% | 95.0% | 1.00 ms | 1.18 ms |
| ST | All | 82.6% | 13.0% | 66.7% | 5.0% | 95.0% | 6.66 ms | 7.14 ms |

Answer and refusal metrics were identical. The embedding change did not fix any answer failure. The neural embedder took longer in this small runner/document measurement; p50 increased from approximately 1.00 ms to 6.66 ms. These timings are not a general production latency benchmark.

## Failures shared by both backends

| ID | Problem |
|---|---|
| a06 | Asked for the five datasets; selected a nearby limitations sentence instead of the dataset list. |
| a16 | Asked whether languages other than English were evaluated; abstained despite the paper saying all datasets are English. |
| a17 | Asked how the method helps with very little labelled data; abstained despite the 100-example result. |
| a19 | Asked when training halts early; abstained despite the three-epoch rule. |
| u05 | Asked for SGA accuracy on MNLI, a result absent from the paper; returned an unrelated macro-F1 result. |
| u06 | Asked whether human evaluation was run; returned an unrelated future-work sentence. |

The highest-priority weakness is the inability to distinguish a passage that is merely about the same topic from a passage that supports the exact requested fact.

## Decision

Do not change the default from LSA to Sentence Transformers on the basis of this run. On this one synthetic paper and 29 questions, the neural embedder did not improve final answers, performed worse in dense retrieval, showed mixed hybrid ranking, and had higher measured latency. This does not prove it is worse on real multi-paper collections; the benchmark is too small for that conclusion.

## Next engineering step

Build and test an answer-support verification stage. It must check not just whether retrieved text is relevant, but whether it explicitly supports the particular fact requested. Add tests for absent MNLI results, an unreported method-specific metric, an unmentioned human-evaluation procedure, answerable paraphrases, and valid list questions. Preserve citations and number guards. Add independent real-paper evaluations before making real-world accuracy claims.

## Reproduction

From the repository root in PowerShell:

~~~powershell
python -m pip install -e ".[dev,embeddings]"
python scripts/evaluate_backends.py --pdf data/sample_paper.pdf --eval-set eval/eval_set.json --llm extractive --top-k 5 --out results/backend-comparison
~~~

The GitHub Actions workflow is .github/workflows/backend-evaluation.yml. It uses a public embedding model and needs no Anthropic API key.

## Commits

- Runner: 9e1a0edeafecb62cf0bda15a12bf8cd841c64f4e
- Tests: bf90141863b8878eb53d6c9992a66187d367285f
- Workflow: 0f1736ff6cf7062cc03865c488f5f30e9fc2c942
- README: 4380e8cd30b9ee86d0495ed1f05f105d8746553f
- LEARNINGS: a2bc9930461536bb4f9e1442e2f475eb7002f50a
