# Protocol đánh giá assessment và progression

Tài liệu này định nghĩa thí nghiệm E2 cho Intaaneto. Mục tiêu là kiểm tra tính
nhất quán và khả năng giải thích của baseline trắc nghiệm deterministic trước
khi nghiên cứu chấm kiến thức bằng hội thoại AI. Đây là protocol chuẩn bị thí
nghiệm, không phải bằng chứng rằng AI dialogue grading đã được triển khai hoặc
đã đạt chất lượng.

## 1. Câu hỏi nghiên cứu

1. Kết quả pass/fail do backend tính có lặp lại và khớp đáp án giáo viên duyệt?
2. Điểm số có phản ánh đúng các learning objective mà bộ câu hỏi tuyên bố đo?
3. Hai người chấm độc lập có đồng thuận về tính đúng, độ rõ và objective của câu
   hỏi không?
4. Một đánh giá hội thoại AI trong tương lai có đồng thuận với người chấm tới
   mức nào khi chỉ hoạt động ở chế độ recommendation?

Không dùng retrieval similarity, độ dài câu trả lời hoặc độ tự tin do model tự
báo làm điểm năng lực người học.

## 2. Phạm vi và dữ liệu

- Chọn ít nhất 3 lesson đại diện và 3–5 learning objective cho mỗi lesson.
- Mỗi objective có ít nhất 3 câu hỏi đã được giáo viên duyệt; gồm câu nhớ, hiểu
  và vận dụng đơn giản nếu học liệu hỗ trợ.
- Tạo tối thiểu 30 response case, cân bằng giữa đúng, sai phổ biến và bỏ trống.
  Dataset E2 V1 hiện sinh 81 row tổng hợp: 27 row cho mỗi loại.
- Tách tập dùng để chỉnh câu hỏi khỏi tập dùng để báo cáo kết quả cuối.
- Ghi rõ course, lesson, assessment version, ngưỡng đạt và ngày xuất dữ liệu.
- Chỉ dùng ID giả danh trong file nghiên cứu; không xuất email, chat, access
  token, prompt hệ thống hoặc nội dung học viên có thông tin cá nhân.

Đáp án assessment không được đưa vào tài liệu RAG. Nếu dùng câu trả lời thật của
người học, cần có mục đích, thời hạn lưu và sự đồng ý phù hợp trước khi xuất.

## 3. Mẫu dữ liệu

Mỗi dòng response case nên có các trường sau:

| Trường | Ý nghĩa |
| --- | --- |
| `case_id` | ID giả danh, không chứa user ID trực tiếp |
| `lesson_slug` | Lesson được đánh giá |
| `assessment_version` | Phiên bản bất biến của assessment |
| `question_order` | Thứ tự câu trong phiên bản đó |
| `declared_objective` | Objective do giáo viên khai báo |
| `response_type` | `correct`, `misconception` hoặc `blank` |
| `selected_choice` | Lựa chọn đầu vào; để trống nếu không trả lời |
| `server_is_correct` | Kết quả do backend sở hữu |
| `rater_a_correct` | Nhận định đúng/sai của người chấm A |
| `rater_b_correct` | Nhận định đúng/sai của người chấm B |
| `rater_a_objective` | Objective mà A cho rằng câu hỏi thực sự đo |
| `rater_b_objective` | Objective mà B cho rằng câu hỏi thực sự đo |
| `clarity_a`, `clarity_b` | Độ rõ theo thang 1–4 |
| `ai_recommendation` | Để trống cho tới khi có dialogue grader riêng |
| `adjudicated_result` | Kết quả sau khi giải quyết bất đồng |
| `notes` | Ghi chú ngắn, không chứa dữ liệu nhạy cảm |

Lưu dữ liệu thí nghiệm ngoài repository nếu chứa response thật. Chỉ commit mẫu
đã tổng hợp hoặc dữ liệu demo không nhạy cảm.

## 4. Quy trình

1. Giáo viên biên soạn objective, câu hỏi, lựa chọn và lời giải thích; một người
   khác review trước khi publish.
2. Khóa assessment version. Không sửa câu hỏi sau khi đã có attempt; tạo version
   mới nếu cần thay đổi.
3. Sinh hoặc thu thập các response case theo phạm vi trên và chạy qua endpoint
   submit thật. Không tự tính điểm trong bảng tính làm nguồn chuẩn.
4. Hai người chấm độc lập, chưa xem kết quả của nhau và chưa xem recommendation
   của AI. Mỗi người đánh giá correctness, objective alignment và clarity.
5. Tính chỉ số, sau đó hai người chấm giải quyết bất đồng và ghi lý do. Không xóa
   nhãn ban đầu sau adjudication.
6. Nếu bổ sung dialogue grader, chạy nó sau khi đã khóa nhãn người chấm. Kết quả
   chỉ là recommendation và không cập nhật score, completion hoặc progression.
7. Lặp lại một mẫu nhỏ sau ít nhất 7 ngày để kiểm tra độ ổn định nội-người-chấm.

Với baseline hiện tại, software case và question-quality review được tách riêng:
81 response row kiểm tra deterministic label/boundary; mỗi reviewer chỉ chấm 27
question item một lần cho answer-key validity, objective alignment và clarity.
Blank row là contract từ chối incomplete submission, không phải scored attempt.

## 4.1. Command và dữ liệu review local

Chạy baseline trên assessment đã import, mặc định không in 81 case:

```bash
docker compose exec backend python manage.py evaluate_corpus_assessments \
  --teacher-id TEACHER_ID
```

Export mỗi phiếu riêng cần cờ xác nhận vì chứa answer key. File phải ở ngoài Git,
chỉ reviewer tương ứng được đọc:

```bash
docker compose exec backend python manage.py evaluate_corpus_assessments \
  --teacher-id TEACHER_ID \
  --export-review-template /app/media/private-research/e2/reviewer-a.json \
  --rater-id reviewer_a --confirm-answer-key-export
```

Sau khi hai reviewer hoàn thành file riêng, tổng hợp aggregate:

```bash
docker compose exec backend python manage.py summarize_assessment_reviews \
  --rater-a /app/media/private-research/e2/reviewer-a.json \
  --rater-b /app/media/private-research/e2/reviewer-b.json
```

Không dùng cùng một người cho cả hai pseudonym và không điền rating hộ reviewer.
Nguồn baseline phần mềm: [ASSESSMENT_SOFTWARE_BASELINE_V1.md](ASSESSMENT_SOFTWARE_BASELINE_V1.md).

## 5. Chỉ số báo cáo

- `server_accuracy`: tỷ lệ kết quả backend khớp nhãn đúng/sai đã adjudicate.
- `objective_alignment`: tỷ lệ hai người chấm đồng ý câu hỏi đo objective khai báo.
- `pass_fail_agreement`: tỷ lệ quyết định pass/fail giống nhau trên cùng case.
- `percent_agreement`: số nhãn giống nhau chia tổng số case.
- Cohen's kappa cho nhãn phân loại hai người chấm; báo cả kappa và bảng phân bố
  nhãn vì kappa nhạy với mất cân bằng lớp.
- Trung vị và khoảng tứ phân vị clarity 1–4; không coi thang ordinal là dữ liệu
  liên tục nếu chưa có lý do phương pháp luận.
- Với AI recommendation trong tương lai: accuracy, confusion matrix, false-pass
  rate và false-fail rate so với adjudicated result.

Không công bố một ngưỡng “khách quan cao” chỉ từ một tập demo nhỏ. Báo số case,
confidence interval khi phù hợp và các trường hợp bất đồng điển hình.

## 6. Điều kiện chấp nhận cho baseline

- Backend phải khớp 100% đáp án/version đã khóa trên tập deterministic.
- Không có answer key trong learner response hoặc frontend state công khai.
- Không có case ngoài enrollment/course scope được đọc hoặc submit.
- Mọi thay đổi progress đều truy được về assessment attempt/version và ngưỡng.
- Câu hỏi mơ hồ hoặc hai đáp án hợp lý phải bị sửa/loại, không “giải quyết” bằng
  cách yêu cầu AI tự suy đoán ý giáo viên.

Chưa đặt ngưỡng chấp nhận cho dialogue grading trước khi có pilot đủ lớn và hai
người chấm. Dù đạt agreement tốt, thay đổi progression vẫn cần một quyết định
sản phẩm riêng, audit trail và cơ chế giáo viên xem xét/khiếu nại.

## 7. Cách ghi vào báo cáo

Ghi dataset/version, cách lấy mẫu, số người chấm, hướng dẫn chấm, chỉ số, kết quả
aggregate và giới hạn. Phân biệt rõ ba lớp bằng chứng:

- test phần mềm chứng minh contract được thực thi;
- agreement study đo tính nhất quán với người chấm;
- nghiên cứu tác động học tập cần thiết kế riêng và không suy ra từ hai lớp trên.
