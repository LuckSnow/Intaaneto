# Baseline phần mềm assessment E2 V1

Ngày chạy: 2026-07-17.

Baseline này kiểm tra contract deterministic của ba assessment corpus đã import
trong PostgreSQL. Nó dùng dữ liệu tổng hợp, không tạo learner attempt và không
được diễn giải là bằng chứng về chất lượng câu hỏi hay tác động học tập.

## Phạm vi

| Thành phần | Giá trị |
| --- | --- |
| Dataset | `intaaneto-corpus-assessment-e2` v1.0.0, schema 1 |
| Blueprint revision | `2026-07-17` |
| Assessment | 3 draft, version 1 |
| Question/objective | 27 câu / 9 objective |
| Response case | 81 tổng hợp |
| Phân bố | 27 correct, 27 misconception, 27 blank |
| Attempt profile | 12, gồm boundary pass/fail cho mỗi assessment |

Mỗi câu tạo ba row tổng hợp. `blank` ghi contract từ chối vì API yêu cầu trả lời
đầy đủ; nó không phải một attempt được chấm điểm. Bốn attempt profile trên mỗi
assessment gồm 9/9, 7/9, 6/9 và 0/9 câu đúng tại threshold 70%.

## Kết quả

| Metric | Kết quả |
| --- | ---: |
| `fixture_contract_accuracy` | 1,00 |
| `pass_boundary_accuracy` | 1,00 |
| 9/9 | 100,00 — pass |
| 7/9 | 77,78 — pass |
| 6/9 | 66,67 — fail |
| 0/9 | 0,00 — fail |

Scoring baseline và production `grade_assessment` dùng chung hàm pure
`calculate_assessment_score`; kiểm thử regression vẫn đi qua production service
để kiểm tra attempt/progression. Command E2 còn xác nhận ba record PostgreSQL
khớp chính xác blueprint và teacher ownership trước khi đọc authoring state.

## Phiếu review độc lập

Hai template local đã được tạo trong development media volume tại
`/app/media/private-research/e2/`. Mỗi file có quyền `0600`, chứa câu hỏi, lựa
chọn, đáp án đề xuất và explanation; không chứa email/user ID và không nằm trong
repository. Reviewer phải dùng pseudonym, làm độc lập và điền:

- `answer_key_valid`: đáp án đề xuất có duy nhất và đúng không;
- `objective_aligned`: câu hỏi có thực sự đo objective khai báo không;
- `clarity`: độ rõ từ 1 đến 4;
- `notes`: tối đa 500 ký tự, không có dữ liệu cá nhân.

Tool tổng hợp kiểm tra đúng dataset/đủ 27 item, hai pseudonym khác nhau, rồi chỉ
trả percent agreement, Cohen's kappa, positive rates và median/IQR clarity. Nó
không in raw rating, rater ID, answer key hoặc notes.

## Giới hạn

Kết quả 1,00 là software consistency trên fixture do chính blueprint xác định,
không phải `server_accuracy` so với adjudicated human labels. Chưa có teacher
review hoàn tất, hai file rating, adjudication, test-retest sau 7 ngày hoặc learner
outcome. Không publish assessment và không báo Cohen's kappa cho tới khi hai
reviewer thật hoàn thành độc lập.
