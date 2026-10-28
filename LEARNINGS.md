# What I learned, and what I would improve next

## What I learned

1. **Build the eval before tuning anything.** Writing 29 questions with gold evidence strings first meant every later change (thresholds, the header-stripping fix) could be checked against numbers instead of eyeballing a few answers.
2. **My dev/test split exposed a blind spot in my own eval.** I tuned the abstention thresholds on 10 dev questions and got a clean 100% abstain recall. On the test split it dropped to 50%. The cause was not overfitting in the usual sense: dev contained only *off-topic* unanswerable questions, while test also contained *in-topic but absent* ones ("accuracy on MNLI"). An eval set must cover the failure modes you care about in every split, and unanswerable questions need a difficulty gradient.
3. **A lexical "do the words appear?" gate cannot detect an absent-but-related fact.** The words "evaluation" and "accuracy" do appear in the paper, so the gate passes and the extractive answerer returns the nearest sentence. Refusing correctly needs a model that judges whether a passage *entails* the answer.
4. **Unit tests found a real bug.** My header/footer remover looked at the first two and last two lines of each page and normalised digits, so a body line like "Figure 1" / "Figure 2" repeated at page tops would be silently deleted. A 3-line fixture exposed it; I narrowed it to the first and last line only.
5. **Tiny eval sets cannot rank retrieval strategies.** Hybrid, dense and BM25 tied at hit@3 and hit@5. I should not (and do not) claim hybrid is better from this; I would need several real papers.
6. **Honest limits beat impressive claims.** The environment had no API key or model-hub access, so I shipped the Claude and sentence-transformers paths as tested-but-unevaluated and said so, rather than reporting numbers I had not measured.

## What I would improve next (in priority order)

1. **Measure the real backends.** Run the two commands in the README with `--embedder st` and `--llm anthropic` and add the comparison table. This is the single most valuable next step, and the harness already supports it.
2. **Fix the in-topic abstention weakness.** Add an entailment/verification pass (an LLM call or a small NLI model) that checks "does this passage actually state the answer?" before returning, and measure abstain recall on a bigger set of in-topic unanswerable questions.
3. **A larger, real eval set.** 5 to 10 open-access papers with 20+ questions each, written by someone other than the author of the pipeline, with a held-out test split that is read once.
4. **Better document parsing.** Two-column layout handling and table extraction (for example `pdfplumber`), so table cells keep their row and column context instead of becoming a flat string.
5. **Reranking.** A cross-encoder reranker over the top 20 hybrid results; measure the hit@1 gain against its latency.
6. **Sharper citations.** Highlight the quoted span in the PDF page, and validate each sentence of the answer against its own cited sentence rather than the union of cited chunks.
7. **Cost and latency tracking** in the eval report (tokens, dollars, p95) once an LLM backend is evaluated.
