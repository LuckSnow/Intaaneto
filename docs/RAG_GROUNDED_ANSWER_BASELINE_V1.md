# Baseline grounded answer V1

Ngày chạy: 2026-07-17.

Đây là baseline của toàn pipeline retrieval → generation → citation trên demo
corpus không nhạy cảm. Kết quả chỉ chứng minh contract quan sát được trên tập nhỏ;
không phải tuyên bố về độ chính xác tổng quát hoặc hiệu quả sư phạm.

## Cấu hình

| Thành phần | Giá trị |
| --- | --- |
| Dataset | `intaaneto-demo-rag-retrieval-vi` v1.0.0, schema 1 |
| Số case | 8: 6 answerable, 2 unsupported |
| Provider/model | Gemini / `gemini-3.1-flash-lite` |
| Retrieval | exact pgvector cosine, top-k 5 |
| Minimum score | 0,45 |
| Source | active demo lesson source v1 |
| Report schema | 2 |
| Raw answers committed | Không |

Lệnh chạy yêu cầu actor đã được authorize và xác nhận quota/chi phí rõ ràng:

```bash
docker compose exec backend python manage.py evaluate_rag_answers \
  121 --actor-id 21 --confirm-provider-cost
```

Các ID trên chỉ thuộc development seed hiện tại và không phải cấu hình cố định.
Khi chạy lại, lấy ID từ Django admin. Không dán API key vào command hoặc report.

## Kết quả chính thức

| Metric | Kết quả |
| --- | ---: |
| `contract_pass_rate` | 0,75 |
| `strict_lexical_proxy_pass_rate` | 0,50 |
| `grounded_contract_accuracy` | 0,75 |
| `citation_scope_accuracy` | 1,00 |
| `expected_marker_recall` | 0,3333 |
| `refusal_accuracy` | 1,00 |
| Mean warm latency | 1.515,62 ms/case |
| Provider token tổng báo cáo | 2.283 trên 4 generation call |

Lần chạy đầu có mean latency 5.058,75 ms/case do tải cache embedding model;
vì vậy không so trực tiếp cold và warm latency như cùng một điều kiện.

## Diễn giải theo case

- Bốn trong sáu case answerable vượt threshold và đi qua generation; cả bốn có
  citation thuộc đúng selected chunk/lesson.
- Hai case answerable về authorization và document prompt injection bị
  `weak_evidence` tại threshold 0,45, giống retrieval baseline V1.
- Hai case unsupported đều fallback, không citation và không gọi generation.
- Hai answer grounded không chứa nguyên cụm source marker nên strict lexical
  proxy đánh trượt. Một diagnostic có `--include-answers` cho thấy output dùng
  cách diễn đạt khác; chưa tính các case này là semantic pass vì chưa có human
  review độc lập theo rubric.

Harness schema 2 tách `contract_pass_rate` khỏi lexical proxy. Contract pass chỉ
đo grounded/fallback state, citation scope và refusal contract; nó không đo câu
trả lời đúng về nghĩa. Vì vậy không dùng 0,75 như “answer accuracy”.

## Quyết định sau baseline

- Không hạ threshold 0,45 từ tám case cùng một demo lesson.
- Không đổi embedding model/chunker chỉ để làm đẹp baseline.
- Mở rộng dataset theo nhiều lesson, tạo holdout và có ít nhất hai người chấm
  semantic correctness, groundedness, citation support và pedagogical clarity.
- Đo cold/warm latency riêng, ghi quota/token provider nhưng không suy diễn thành
  chi phí ổn định nếu provider thay đổi cách tính token hoặc giá.
- Giữ raw questions/answers ngoài report mặc định; chỉ dùng `--include-answers`
  với demo data cho review có chủ đích.

## Giới hạn

Dataset nhỏ, cùng miền với seed lesson và không có blind holdout. Exact marker là
proxy từ vựng rất nghiêm, còn contract metric không đánh giá semantic correctness.
Provider có thể không deterministic giữa các lần chạy. Chưa có hai người chấm,
agreement, confidence interval, adversarial coverage rộng hoặc đánh giá tác động
học tập.
