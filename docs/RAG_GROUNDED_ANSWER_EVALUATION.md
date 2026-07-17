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

Mặc định report không chứa câu hỏi hay câu trả lời. Khi cần chấm thủ công, thêm
`--include-answers`; chỉ bật với demo data và không commit raw output nếu có dữ
liệu người dùng. Không có `--confirm-provider-cost`, command dừng trước truy vấn
database/provider.

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
metrics. Chấm thủ công correctness, groundedness, refusal clarity theo rubric và
ít nhất hai người chấm nếu muốn tuyên bố agreement. Không ghi key, full prompt,
embedding hoặc lỗi nội bộ của provider.

Baseline live đầu tiên được ghi tại
[RAG_GROUNDED_ANSWER_BASELINE_V1.md](RAG_GROUNDED_ANSWER_BASELINE_V1.md).
