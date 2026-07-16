# RAG retrieval baseline v1

Ngày chạy: 2026-07-16  
Dataset: `intaaneto-demo-rag-retrieval-vi` v1.0.0, schema v1  
Phạm vi: lesson demo đã được teacher-owner authorize, PostgreSQL exact cosine  
Generation provider: không gọi

## Cấu hình

- Embedding provider: `fastembed`
- Model: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- Revision label: `fastembed-0.8.0-mean-pooling`
- Dimension: 384
- Top-k: 5
- Minimum score: 0.45
- Active source version: 1, 2 chunks

## Kết quả

- Cases: 8
- Pass rate: 0.75
- Status accuracy: 0.75
- Expected-source recall: 1.00
- Mean retrieval latency: 225.12 ms, gồm lần khởi tạo model đầu tiên

| Case ID | Expected | Actual | Expected source hit | Top score | Pass |
| --- | --- | --- | --- | ---: | --- |
| `rag-purpose` | ready | ready | yes | 0.639174 | yes |
| `indexing-stage` | ready | ready | yes | 0.500169 | yes |
| `authorization-before-retrieval` | ready | weak_evidence | yes | 0.274681 | no |
| `application-citations` | ready | ready | yes | 0.453222 | yes |
| `weak-evidence-fallback` | ready | ready | yes | 0.684963 | yes |
| `document-prompt-injection` | ready | weak_evidence | yes | 0.442463 | no |
| `unsupported-weather` | weak_evidence | weak_evidence | n/a | -0.013164 | yes |
| `unsupported-cooking` | weak_evidence | weak_evidence | n/a | 0.041467 | yes |

## Diễn giải và giới hạn

Expected-source recall 1.00 cho thấy marker mong đợi nằm trong top-k của cả sáu
case answerable. Tuy nhiên threshold hiện tại từ chối hai case answerable, trong
đó prompt-injection chỉ thấp hơn threshold khoảng 0.008. Hai case unsupported đều
fallback đúng và có score thấp.

Không hạ threshold chỉ từ tám case này. Cần mở rộng tập unsupported/ambiguous và
tách development/holdout trước khi tuning để tránh tăng false positive. Latency
lần đầu bao gồm khởi tạo model local nên chưa đại diện steady-state hoặc môi
trường production. Baseline này chỉ đo retrieval; nó không đo answer correctness,
groundedness, citation correctness, generation latency hay cost.
