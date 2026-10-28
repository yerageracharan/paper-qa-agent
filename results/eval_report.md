# Evaluation report

Backend: embedder=`lsa`, answerer=`ExtractiveLLM`, top_k=5, chunks=18

## Retrieval (answerable questions)

| mode | hit@1 | hit@3 | hit@5 | MRR |
|---|---|---|---|---|
| bm25 | 73.9% | 91.3% | 95.7% | 0.837 |
| dense | 82.6% | 91.3% | 95.7% | 0.88 |
| hybrid | 82.6% | 91.3% | 95.7% | 0.88 |

## End-to-end

| split | answerable | unanswerable | answer accuracy | false-abstain | abstain recall | wrong when answering | citation hit | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|
| dev | 8 | 2 | 75.0% | 25.0% | 100.0% | 0.0% | 100.0% | 1.26 | 1.58 |
| test | 15 | 4 | 86.7% | 6.7% | 50.0% | 7.1% | 92.9% | 1.3 | 1.5 |
| all | 23 | 6 | 82.6% | 13.0% | 66.7% | 5.0% | 95.0% | 1.3 | 1.5 |

## Accuracy by question type

| type | n | accuracy |
|---|---|---|
| absent | 3 | 100.0% |
| fact | 16 | 100.0% |
| in_topic | 3 | 33.3% |
| list | 2 | 50.0% |
| paraphrase | 3 | 33.3% |
| table | 1 | 100.0% |
| yesno | 1 | 0.0% |

## Failures

- **a06** (test, list): Which datasets are used in the experiments?  
  found=True reason=None answer: All experiments use English datasets and a single encoder with 110 million parameters, so we cannot say whether the findings hold for multilingual or much large
- **a16** (dev, yesno): Does the paper evaluate languages other than English?  
  found=False reason=model_not_found answer: I could not find an answer to this in the paper.
- **a17** (test, paraphrase): How much does the method help when very little labeled data is available?  
  found=False reason=model_not_found answer: I could not find an answer to this in the paper.
- **a19** (dev, paraphrase): When does training halt before the maximum number of epochs?  
  found=False reason=low_coverage answer: I could not find an answer to this in the paper.
- **u05** (test, in_topic): What accuracy does SGA reach on the MNLI dataset?  
  found=True reason=None answer: SGA reaches an average macro-F1 of 80.0, which is 3.1 points higher than standard adapters (76.9) and 1.6 points higher than full fine-tuning (78.4). [S1] With 
- **u06** (test, in_topic): Did the authors run a human evaluation?  
  found=True reason=None answer: Future work includes multilingual evaluation and larger encoders. [S1]
