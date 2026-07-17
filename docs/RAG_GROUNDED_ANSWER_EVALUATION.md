# Grounded-answer evaluation

Tài liệu này hướng dẫn chạy thí nghiệm E1 trên dataset tiếng Việt đã version.
Harness đo contract của toàn bộ retrieval → generation → citation; nó không tự
động chứng minh câu trả lời đúng về ngữ nghĩa hay có chất lượng sư phạm.

## Điều kiện

- Lesson có slug `demo-rag-la-gi`, active ready source và actor được quyền đọc.
- Backend cấu hình `AI_GENERATION_PROVIDER=openai` hoặc `gemini` cùng key hợp lệ.
- Không dán key vào command, ảnh chụp, report hoặc file trong repository.
- Chỉ dùng demo corpus không nhạy cảm khi thử free-tier provider.

## Chạy

Lấy `lesson_id` và actor ID từ Django admin, sau đó chủ động xác nhận chi phí:

```bash
docker compose exec backend python manage.py evaluate_rag_answers \
  <lesson_id> --actor-id <actor_id> --confirm-provider-cost
```

Mặc định report không chứa câu hỏi hay câu trả lời. `--include-answers` chỉ dành
cho chẩn đoán local có chủ đích; không redirect raw output vào repository.
Không có `--confirm-provider-cost`, command dừng trước truy vấn database/provider.

## Hai người chấm độc lập

Tạo hai phiếu từ **cùng một lần chạy provider** để tránh mỗi reviewer thấy một
câu trả lời ngẫu nhiên khác nhau. Thư mục đích phải tồn tại và nằm ngoài Git:

```bash
docker compose exec backend python manage.py evaluate_rag_answers \
  <lesson_id> --actor-id <actor_id> --confirm-provider-cost \
  --export-review-dir /app/media/private-research/e1 \
  --rater-a reviewer_a --rater-b reviewer_b \
  --confirm-sensitive-export
```

Hai file JSON được tạo với quyền `0600`, cùng `package_sha256`, chứa bounded demo
question/answer/citation để chấm. Không dùng email hoặc user ID làm pseudonym,
không commit/chia sẻ file, và không dùng dữ liệu học viên hay học liệu nhạy cảm
với provider free-tier. Mỗi reviewer điền độc lập:

- `answer_correct`, `evidence_aligned`, `pedagogically_helpful`: `true/false`;
- `clarity`: số nguyên 1–4;
- `notes`: ghi chú ngắn, không chứa dữ liệu cá nhân.

Sau khi điền đủ hai phiếu:

```bash
docker compose exec backend python manage.py summarize_rag_answer_reviews \
  --rater-a /app/media/private-research/e1/rag-answer-review-reviewer_a.json \
  --rater-b /app/media/private-research/e1/rag-answer-review-reviewer_b.json
```

Lệnh tổng hợp kiểm tra package bất biến, reviewer khác nhau và rating đầy đủ,
sau đó chỉ in percent agreement, Cohen's kappa, positive rates và median/IQR
clarity. Nó không in raw answer, citation, rating riêng lẻ hay pseudonym. Agreement
không tự chứng minh correctness; bất đồng vẫn cần adjudication trước khi báo cáo.

## Cách đọc số liệu

- `contract_pass_rate`: contract grounded/fallback, citation scope và refusal
  cùng đạt; không đo semantic correctness.
- `strict_lexical_proxy_pass_rate`: contract đạt và answerable case còn chứa
  nguyên source marker; đây là proxy nghiêm, không phải answer accuracy.
- `grounded_contract_accuracy`: case answerable được grounded và case unsupported
  được fallback đúng contract.
- `citation_scope_accuracy`: citation thuộc lesson và tập chunk ứng dụng đã chọn.
- `refusal_accuracy`: câu ngoài tài liệu bị từ chối, không có citation giả.
- `expected_marker_recall`: khớp cụm chữ chính xác; đây chỉ là lexical proxy.
- `mean_latency_ms`, `total_tokens_reported`: dữ liệu vận hành do harness/provider
  quan sát được; token có thể thiếu nếu provider không trả usage.

Khi ghi baseline vào báo cáo, lưu dataset/model/provider/config/date và aggregate
metrics. Chỉ tuyên bố human-review agreement sau khi hai người thật hoàn thành
phiếu và kết quả aggregate được lưu; tooling hoặc phiếu trống không phải kết quả.
Không ghi key, full prompt, embedding hoặc lỗi nội bộ của provider.

Baseline live đầu tiên được ghi tại
[RAG_GROUNDED_ANSWER_BASELINE_V1.md](RAG_GROUNDED_ANSWER_BASELINE_V1.md).
