# Bộ kiểm thử PDF, nhập cloud và báo cáo Matplotlib

Đợt mới ngày 13/10/2026 mở rộng thành **30 câu / 6 PDF / 3 lần chạy = 90 phản hồi**,
bao gồm `NodeJS.pdf` và `RouterExpressJS.pdf` do người dùng bổ sung. Người dùng
đã yêu cầu thực thi cloud import và generation; lựa chọn chạy thủ công trước
đó không còn áp dụng cho đợt này. Dataset 4 PDF cũ giữ ở
`artifacts/rag_pdf_eval/dataset_4pdf_v1.json`; bộ hiện tại là `dataset.json`.

Các kết quả riêng tư nằm trong `artifacts/rag_pdf_eval/report/`: `REPORT.html`,
`RESEARCH_REPORT.pdf`, `CORPUS_AND_NEW_PDFS.md`, `results.csv`, `tables/` và hình
PNG/SVG/PDF. Xem file `REVIEW_PROTOCOL.md` ở thư mục cha để hiểu điểm chấm sơ bộ
Codex; kết quả đó chưa thay cho chấm độc lập của giảng viên.

Lần chạy này có khoảng nghỉ `--request-delay-seconds 4` giữa các yêu cầu để
giảm áp lực quota; khoảng nghỉ không tính vào latency. Tool hiện nhận 3–6 PDF
cho một bộ nghiên cứu. Có thể xuất báo cáo sơ bộ bằng:

```bash
python backend/scripts/report_pdf_qa.py \
  --results artifacts/rag_pdf_eval/results.json \
  --ratings artifacts/rag_pdf_eval/ratings_ai_preliminary.csv \
  --review-method ai_assisted_preliminary \
  --output-dir artifacts/rag_pdf_eval/report
```

`ratings.csv`/`report/ratings.csv` là phiếu trống riêng để nhóm chấm lại. Dùng
`--review-method human` và thư mục output khác khi đã có đánh giá của người
chấm. PDF/JSON gốc, bảng và các phiếu chấm không được đưa vào Git công khai.

## Hồ sơ chuẩn bị ban đầu (4 PDF)

Chuẩn bị ngày 13/10/2026. **Chưa chạy Gemini, chưa có số đo thực nghiệm.**
Người dùng chọn tự chạy thủ công. Không tạo bài học thử nghiệm trong database
trong phiên chuẩn bị này.

## Bộ dữ liệu đã chuẩn bị

Các file riêng tư nằm trong `artifacts/rag_pdf_eval/`, được bỏ qua bởi Git:

- `QUESTIONS_AND_ANSWERS.md`: 24 câu, đáp án tham chiếu, trang nguồn, tiêu chí chấm.
- `dataset.json`: dữ liệu chạy, checksum từng PDF và tham chiếu storage.
- `pdf/PDF01.pdf` đến `pdf/PDF04.pdf`: PDF tải trực tiếp từ R2.
- `ratings.csv`: 24 dòng để người chấm điền điểm và lý do.

| Mã | Nội dung thực tế PDF | Trang | Có đáp án | Ngoài phạm vi |
|---|---|---:|---:|---:|
| PDF01 | DHCP | 5 | 5 | 1 |
| PDF02 | Giáo trình Retrieval-Augmented Generation | 16 | 5 | 1 |
| PDF03 | Thiết lập môi trường phát triển PHP | 7 | 5 | 1 |
| PDF04 | Lập trình PHP | 85 | 5 | 1 |
| Tổng | 4 PDF | 113 | 20 | 4 |

PDF01 hiện gắn với lesson 2, có tên “Tổng quan Giao thức Mạng và TCP”,
nhưng nội dung thực tế là DHCP. Không sửa tên hay nguồn bài học đó. Ba PDF
còn lại chưa có bài học trong database được kiểm tra. PDF hướng dẫn báo cáo
thực tập cũng có trong thư mục uploads nhưng không thuộc bộ bài giảng này.

Đáp án đã được soạn đối chiếu văn bản PDF; **giảng viên cần duyệt trước khi
gọi đây là gold set đã được kiểm chứng độc lập**. Giữ nguyên đáp án trong lúc
chạy, không sửa để khớp với câu trả lời của hệ thống. Bộ test không chứa đáp án
bài tập/hidden test của học viên và không được nhập vào nội dung RAG.

## Chạy thủ công

### Công cụ nhập hàng loạt và nghiên cứu Matplotlib

Tool CLI thống nhất: `backend/scripts/pdf_research.py`. Có bốn thao tác:
`upload`, `run`, `pipeline`, `report`. Tool chạy trên máy bạn, chuyển **chỉ PDF**
vào container, rồi gọi command/backend service hiện có. Không cần nhập từng
bài qua giao diện. Không tạo endpoint công khai mới.

Cài môi trường báo cáo riêng (không thêm Matplotlib vào backend web/worker):

```bash
python3 -m venv .venv-research
.venv-research/bin/pip install -r backend/requirements-research.txt
```

Chạy thử 4 PDF đã tải về, **không ghi bài học/storage hoặc gửi job**:

```bash
.venv-research/bin/python backend/scripts/pdf_research.py upload \
  --pdf-dir artifacts/rag_pdf_eval/pdf --course-id 1 --actor-id 1
```

Chạy thử vẫn đọc course để xác thực quyền, phân tích PDF trong container và
ghi manifest local. Tool nhận 1–50 file `.pdf` trực tiếp trong thư mục, không
quét đệ quy, không nhận symlink; mỗi file tối đa 20 MB, 100 trang và giới hạn
văn bản như ingestion hiện có. File lỗi có trạng thái riêng trong manifest,
file hợp lệ vẫn có thể nhập trong cùng batch; batch không phải một transaction
nguyên khối. Không tự đăng nhập bằng mật khẩu hoặc tạo tài khoản.

Để nhập thật và chờ worker hoàn tất:

```bash
.venv-research/bin/python backend/scripts/pdf_research.py upload \
  --pdf-dir artifacts/rag_pdf_eval/pdf --course-id 1 --actor-id 1 \
  --execute --wait --wait-seconds 600
```

Lệnh này ghi bài học nháp vào course 1, lưu PDF vào storage server đang cấu
hình (R2 nếu bật) và gửi job sang Celery. File trùng nội dung trong cùng course
dùng lại lesson/job; không tự đổi lesson đã publish/preview. Broker thất bại
có thể chạy lại để gửi job mới mà không tạo thêm lesson. Tên lesson lấy từ
tên file: bạn có thể đổi `PDF01.pdf` thành tên bài dễ đọc trước khi nhập.

`artifacts/rag_pdf_eval/import-manifest.json` ghi SHA-256, lesson ID, file
storage, trạng thái và số trang. Chỉ source có trạng thái `ready` mới được
nối vào bộ kiểm thử. Timeout không có nghĩa job bị hủy; kiểm tra worker rồi
chạy lại upload để lấy manifest mới khi đã hoàn tất.

Để chạy 24 câu **ba lần/câu** và tự xuất báo cáo (sau khi import `ready`):

```bash
.venv-research/bin/python backend/scripts/pdf_research.py run \
  --dataset artifacts/rag_pdf_eval/dataset.json \
  --manifest artifacts/rag_pdf_eval/import-manifest.json \
  --actor-id 1 --repeats 3 --confirm-provider-cost
```

Hoặc gộp nhập, chờ index, chạy kiểm thử và xuất báo cáo trong **một lệnh**:

```bash
.venv-research/bin/python backend/scripts/pdf_research.py pipeline \
  --pdf-dir artifacts/rag_pdf_eval/pdf \
  --dataset artifacts/rag_pdf_eval/dataset.json \
  --course-id 1 --actor-id 1 --execute \
  --repeats 3 --confirm-provider-cost
```

Pipeline nhập đủ 4 PDF thành bài nháp trong course chỉ định; nhánh pipeline
không dùng lesson 2 cũ nếu đã có bản nhập theo manifest. Kiểm tra course/actor
đúng quyền trước khi chạy. Lệnh `pipeline` ghi database/storage và gửi câu hỏi
cùng các đoạn truy xuất tới provider đang cấu hình, có thể phát sinh phí.
Với `--repeats 3`, có 72 yêu cầu và tối đa 72 lần gọi generation ở mức ứng dụng;
SDK/provider có thể retry. Phần generation không chạy trước khi nguồn được index
và có chunk. Trạng thái đủ ngưỡng retrieval mới đi đến provider.

Kết quả trong `artifacts/rag_pdf_eval/report/`:

| Nhóm | File/nội dung |
|---|---|
| Báo cáo | `REPORT.html`, `REPORT.md`, `RESEARCH_REPORT.pdf` |
| Dữ liệu từng phản hồi | `results.csv`, file gốc `../results.json` |
| Tổng hợp | `metrics.json`, `provenance.json` |
| Bảng nghiên cứu | `tables/*.csv`, `tables/*.tex`: tổng, PDF, lần chạy, loại câu, từng câu, nguồn index, lỗi, trích dẫn, điểm, trạng thái |
| Biểu đồ Matplotlib | Latency từng câu, boxplot theo PDF kèm điểm thô, histogram + ECDF, trạng thái theo PDF, accuracy, phân bố điểm, heatmap câu × lần chạy |
| Định dạng hình | Mỗi hình có PNG 300 DPI, SVG và PDF |
| Phiếu chấm đúng số lần chạy | `report/ratings.csv` (72 dòng nếu chạy 3 lần) |

Khi chưa chấm, hình accuracy hiển thị “chưa chấm đủ”; không tự sinh điểm từ
grounded hoặc citation. Điền phiếu chấm theo rubric rồi xuất lại **offline**:

```bash
.venv-research/bin/python backend/scripts/pdf_research.py report \
  --results artifacts/rag_pdf_eval/results.json \
  --ratings artifacts/rag_pdf_eval/report/ratings.csv
```

Lặp một câu nhiều lần tạo các quan sát phụ thuộc nhau. Báo cáo dùng thống kê
mô tả, không giả định 72 phản hồi là 72 câu hỏi độc lập và không tự thêm khoảng
tin cậy/p-value. TB, median, P95, SD tính riêng trên yêu cầu thành công; số lỗi
vẫn thuộc mẫu số accuracy. SD là độ phân tán, không phải SE/CI. Consistency
grounded chỉ đo sự nhất quán trạng thái kỹ thuật, không phải độ nhất quán ngữ nghĩa.

Để nhập PDF khác, thay `--pdf-dir`. Để đánh giá PDF khác, cần bộ câu hỏi/đáp án
được duyệt có đúng SHA-256 và trang tham chiếu của các file đó; tool không
tự coi đáp án LLM sinh ra là gold set. Đợt nghiên cứu giữ giới hạn 20–30 câu,
3–5 PDF và 1–5 lần chạy/câu. Có thể dùng `--output-dir` để lưu từng đợt riêng;
thư mục tùy chọn phải được ignore nếu nằm trong Git.

Skill đã tìm: [scientific-visualization (K-Dense)](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/scientific-visualization/SKILL.md),
phù hợp với biểu đồ nghiên cứu; [jupyter-notebook (OpenAI)](https://github.com/openai/skills/blob/main/skills/.curated/jupyter-notebook/SKILL.md),
phù hợp với notebook thực nghiệm. Đã tham khảo hướng dẫn scientific-visualization;
chưa cài thêm skill vào môi trường người dùng. Hình dùng nền trắng, trục có
đơn vị, giữ dữ liệu thiếu riêng với số 0 và ghi provenance. Chưa tuyên bố đáp
ứng yêu cầu xuất bản của tạp chí cụ thể.

### Cách chạy trực tiếp từng script (tùy chọn)

Các lệnh dưới đây dùng Bash/WSL, chạy từ thư mục gốc repository. Docker Desktop
phải bật WSL integration, backend phải có `.env` trỏ đúng database/R2 và Gemini.
Không in `.env`, khóa, token hoặc signed URL ra màn hình.

Kiểm tra container:

```bash
docker compose ps
docker compose exec -T backend python scripts/evaluate_pdf_qa.py --help
```

Đọc `QUESTIONS_AND_ANSWERS.md` và nhờ thầy kiểm tra đáp án/trang nguồn. Có thể
mở các PDF trong thư mục `pdf/` để đối chiếu trực tiếp.

Đưa dataset vào thư mục tạm riêng tư trong backend:

```bash
docker compose exec -T backend sh -c 'umask 077; cat > /tmp/pdf-qa-dataset.json' \
  < artifacts/rag_pdf_eval/dataset.json
```

Lệnh sau **tạo khóa học thử nghiệm nháp do actor 1 sở hữu và 3 bài học nháp**,
đọc PDF đã có từ R2, chạy extraction/indexing của ứng dụng, rồi chạy 24 câu qua
RAG và Gemini thật. Câu hỏi và các đoạn PDF được truy xuất được gửi tới Gemini;
có thể phát sinh phí/quota. Chỉ chạy khi bạn đồng ý các tác động đó.

```bash
docker compose exec -T backend python scripts/evaluate_pdf_qa.py \
  --dataset /tmp/pdf-qa-dataset.json \
  --output /tmp/pdf-qa-results.json \
  --actor-id 1 \
  --prepare-lessons \
  --confirm-provider-cost
```

Actor 1 phải là giảng viên/admin đang hoạt động, có quyền đọc lesson 2 và
quyền tạo khóa học nháp thử nghiệm. Script kiểm tra quyền backend, tên file,
checksum PDF và active source. Nếu dùng môi trường khác, sửa ID trong dataset
sau khi kiểm tra quyền và nguồn; không lấy ID của tài khoản không được phép.
Nếu đã tự upload/index ba PDF qua UI, điền `lesson_id` tương ứng trong từng
source của dataset và bỏ `--prepare-lessons`.

Script dùng mô hình generation đang cấu hình của ứng dụng; tại phiên chuẩn bị
là Gemini. Không đổi threshold, model hay top-k để cải thiện điểm trong lần đo.
Mô hình embedding được khởi động trước khi bấm giờ. Các câu chạy tuần tự,
không chia sẻ lịch sử hội thoại. Có tối đa 24 lần gọi generation nếu mọi câu
đạt ngưỡng truy xuất; fallback không gọi Gemini. Các draft mới không được
publish, không ghi enrollment, chat, điểm hay tiến độ học viên.

Khi chạy xong, xuất kết quả riêng tư ra máy:

```bash
(umask 077; docker compose exec -T backend cat /tmp/pdf-qa-results.json \
  > artifacts/rag_pdf_eval/results.json)
python3 backend/scripts/report_pdf_qa.py \
  --results artifacts/rag_pdf_eval/results.json \
  --output-dir artifacts/rag_pdf_eval/report
```

Nếu dùng script trực tiếp trên máy host, thay `python3` bằng
`.venv-research/bin/python` để có Matplotlib.

Lần đầu báo cáo chỉ có số đo và trạng thái kỹ thuật; accuracy vẫn ghi “chưa
hoàn tất chấm”. Nếu lệnh chạy bị ngắt, JSON được checkpoint sau mỗi câu, nhưng
trình báo cáo từ chối coi lần chạy chưa hoàn tất là kết quả đầy đủ. Chạy lại sẽ
đo lại toàn bộ câu và gọi provider lại; kết quả ghi đè `/tmp/pdf-qa-results.json`.
Lưu bản cũ nếu muốn so sánh nhiều lần chạy.

## Chấm độ chính xác

Mở `report/results.csv` để so câu trả lời thật với đáp án tham chiếu và PDF.
Điền `artifacts/rag_pdf_eval/ratings.csv`; không đổi cột ID:

| Điểm | Câu có đáp án | Câu ngoài phạm vi |
|---|---|---|
| 2 | Đủ các ý trong rubric, không có lỗi nội dung đáng kể | Nói rõ thiếu dữ liệu, không bịa |
| 1 | Đúng một phần nhưng thiếu ý trọng tâm | Dè dặt nhưng vẫn suy đoán nội dung |
| 0 | Sai, lỗi hệ thống/provider, hoặc từ chối câu có đáp án | Khẳng định nội dung không được PDF hỗ trợ |

Mỗi điểm phải có lý do. Ghi người chấm và ngày chấm trong hồ sơ nghiên cứu.
Nếu có hai người chấm, tạo hai bản CSV độc lập và thống nhất các bất đồng trước
khi tạo bản ratings cuối; công cụ hiện tại không tính độ đồng thuận hai người.

Xuất lại báo cáo sau khi đủ 24 điểm:

```bash
python3 backend/scripts/report_pdf_qa.py \
  --results artifacts/rag_pdf_eval/results.json \
  --ratings artifacts/rag_pdf_eval/ratings.csv \
  --output-dir artifacts/rag_pdf_eval/report
```

Kết quả:

- `REPORT.html`: báo cáo mở trực tiếp trên trình duyệt, biểu đồ nhúng, không CDN.
- `REPORT.md`: báo cáo để đưa vào luận văn sau khi đọc lại giới hạn thực nghiệm.
- `results.csv`: từng câu hỏi, đáp án chuẩn, câu trả lời thật, latency và điểm.
- `metrics.json`: số liệu tổng hợp.
- `latency_by_question.svg`, `latency_by_pdf.svg`: biểu đồ thời gian.
- `accuracy_by_pdf.svg`: biểu đồ độ chính xác; chưa đủ điểm thì chỉ hiển thị trạng thái chờ chấm.
- `RESEARCH_REPORT.pdf`, `tables/*.csv`, `tables/*.tex` và các hình PNG/PDF:
  bản tổng hợp nghiên cứu Matplotlib.

## Cách diễn giải

**Accuracy nghiêm ngặt = số câu đạt 2 / 24.** Điểm chuẩn hóa = tổng điểm / 48.
Lỗi hệ thống/provider cũng thuộc mẫu số 24, không được loại đi để tăng accuracy.
Người chấm cần cho lỗi điểm 0. Có thể phân tích riêng câu có đáp án và câu từ chối.

Thời gian được đo bằng đồng hồ monotonic quanh lời gọi `answer_lesson_question`:
gồm retrieval và generation/fallback; không gồm ingestion, browser, HTTP,
đăng nhập hoặc lưu chat. Báo cáo TB, median và P95 của yêu cầu thành công; yêu
cầu lỗi có latency riêng trong bảng. P95 dùng nội suy tuyến tính. Đây là phép
đo warm, một lần/câu, không phải thời gian người dùng cuối trên mạng Internet.

Grounded, citation scope và chồng lấp trang nguồn là chỉ số kỹ thuật/proxy,
**không được gọi là accuracy ngữ nghĩa**. Chồng lấp trang không bảo đảm đoạn
trích hỗ trợ toàn bộ đáp án. Độ đúng phải do người chấm đối chiếu nội dung.

Mẫu nhỏ chưa có holdout. Slide PHP năm 2017 và PDF DHCP có lỗi diễn đạt;
bộ test đo độ bám bài giảng, không chứng minh mọi nội dung nguồn đúng/cập nhật.
Nếu muốn đo ổn định, chạy 3 lần với cùng bộ/config, lưu từng JSON riêng và nêu
rõ số lần chạy; không lựa chọn riêng lần tốt nhất.

## Bảo quản và dọn dẹp

Các PDF, object reference và câu trả lời thật chỉ lưu local trong thư mục
đã ignore; không commit hoặc gửi toàn bộ lên repository công khai. Chỉ chia sẻ
báo cáo đã kiểm tra với thầy. Khóa truy cập R2/Gemini vẫn ở `.env` server.

Sau thực nghiệm giữ khóa học `rag-pdf-evaluation-24-v1` ở trạng thái nháp để
lưu trữ. API hiện từ chối xóa khóa học còn bài học; nếu cần dọn thì kiểm tra
hành vi xóa từng lesson/file trước. Không xóa PDF R2 gốc vì các lesson thử
nghiệm tham chiếu file có sẵn, không tạo bản sao storage. Chưa tự động dọn
dữ liệu cloud.

Trong container, xóa hai file tạm sau khi đã lưu kết quả:

```bash
docker compose exec -T backend rm -f /tmp/pdf-qa-dataset.json /tmp/pdf-qa-results.json
```
