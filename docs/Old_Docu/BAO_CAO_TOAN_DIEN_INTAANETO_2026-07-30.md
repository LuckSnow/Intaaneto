---
title: "BÁO CÁO TOÀN DIỆN DỰ ÁN INTAANETO"
subtitle: "Hệ thống E-learning tích hợp AI Tutor dựa trên Retrieval-Augmented Generation"
author:
  - "Nguyễn Thái Tuấn — N23DCPT054"
  - "Phùng Anh Lực — N23DCPT033"
date: "Ngày 30 tháng 7 năm 2026"
lang: vi-VN
toc: true
toc-depth: 3
numbersections: true
geometry: margin=2.2cm
fontsize: 11pt
mainfont: "DejaVu Serif"
sansfont: "DejaVu Sans"
monofont: "Noto Sans Mono"
colorlinks: true
linkcolor: "blue"
urlcolor: "blue"
header-includes:
  - |
    \usepackage{longtable}
    \usepackage{booktabs}
    \usepackage{array}
    \usepackage{float}
    \usepackage{xcolor}
    \usepackage{fancyhdr}
    \pagestyle{fancy}
    \fancyhead[L]{Intaaneto}
    \fancyhead[R]{Báo cáo toàn diện 2026}
    \fancyfoot[C]{\thepage}
---

\newpage

# Tóm tắt điều hành

Intaaneto là một hệ thống E-learning full-stack phục vụ ba nhóm tác nhân chính:
học viên, giảng viên và quản trị viên. Điểm khác biệt của đề tài không nằm ở việc
chỉ gắn một chatbot vào website, mà ở việc xây dựng một chuỗi tri thức có kiểm
soát: học liệu được giảng viên phê duyệt được trích xuất, chuẩn hóa, chia đoạn,
biểu diễn thành vector, truy xuất trong đúng phạm vi được cấp quyền, sau đó mới
được dùng làm bằng chứng cho AI Tutor. Citation, quyền truy cập, điểm số và luật
chuyển bài đều do ứng dụng quyết định, không giao cho mô hình ngôn ngữ.

Qua kiểm tra repository tại ngày 30/07/2026, dự án đã có một prototype tích hợp
khá hoàn chỉnh từ quản lý người dùng, khóa học, bài học, PDF, RAG, hội thoại AI,
assessment, tiến độ, báo cáo giảng viên, forum đến multimedia cục bộ. Phần RAG
MVP đã đi hết bốn lát cắt kỹ thuật quan trọng: ingestion, indexing, retrieval và
grounded answering. Hệ thống còn có evaluation harness và baseline thực nghiệm
ban đầu, nhưng tập đánh giá mới gồm tám trường hợp trên một lesson demo; chưa đủ
để tuyên bố độ chính xác tổng quát hay hiệu quả sư phạm.

## Kết luận nhanh về mức độ hoàn thành

Để tránh đánh đồng “code chạy được”, “nghiên cứu đã chứng minh” và “sẵn sàng
triển khai thật”, báo cáo đánh giá theo ba trục:

| Trục đánh giá | Ước lượng | Nhận định |
|---|---:|---|
| Prototype chức năng | **86%** | Đã có các luồng chính A–Z; còn thiếu polish, E2E frontend và một số trải nghiệm nâng cao |
| Bằng chứng nghiên cứu | **64%** | Có protocol, harness và baseline; thiếu holdout đa lesson, hai người chấm, thí nghiệm người học |
| Sẵn sàng production | **57%** | Có nhiều boundary bảo mật và R2 opt-in; thiếu CI/CD, monitoring, HA, malware scan và kiểm thử triển khai thật |
| **Tiến độ tổng hợp có trọng số** | **75%** | \(0,50 \times 86 + 0,30 \times 64 + 0,20 \times 57 = 73,6\%\), làm tròn theo sai số đánh giá thành khoảng **74–76%** |

Con số nên dùng trong báo cáo tiến độ là **khoảng 75% mục tiêu toàn đề tài**.
Nếu chỉ nói về **phần mềm prototype phục vụ demo**, dự án ở khoảng **85–87%**.
Nếu yêu cầu là một sản phẩm production có bằng chứng khoa học đủ mạnh, không nên
nói dự án đã hoàn thành trên 80%.

## Năm kết luận quan trọng nhất

1. **RAG đã được triển khai thật, không chỉ là prompt có gắn nội dung.** Có mô
   hình `KnowledgeSource`, `KnowledgeChunk`, vector 384 chiều, source version,
   checksum, exact cosine search và citation từ record đã truy xuất.
2. **Authorization đi trước retrieval.** Learner phải có enrollment; teacher
   phải sở hữu course; client không được tự mở rộng lesson/course scope.
3. **AI không tự chấm điểm tiến độ.** Trắc nghiệm đã duyệt được backend chấm
   deterministic; dialogue AI mới ở mức recommendation sau khi pass.
4. **Video đã có pipeline slide-video cục bộ nhưng chưa có nhân vật nói hoàn
   thiện.** Piper/FFmpeg có thể tạo narration, slide, caption và MP4; SadTalker
   còn là PoC lịch sử, chưa có render học liệu với portrait được duyệt và đánh
   giá chất lượng tiếng Việt.
5. **Khoảng trống lớn nhất hiện nay là bằng chứng nghiên cứu và vận hành**, không
   còn là việc thiếu skeleton chức năng.

# Giới thiệu đề tài

## Bối cảnh

E-learning truyền thống thường cung cấp nội dung theo mô hình một chiều: người
học đọc tài liệu, xem video và làm bài kiểm tra. Mô hình này có khả năng mở rộng
cao nhưng thiếu phản hồi tức thời, khó đảm bảo người học hiểu đúng nội dung trước
khi chuyển sang bài tiếp theo, đồng thời tạo thêm công việc lặp lại cho giảng
viên khi phải giải thích cùng một kiến thức hoặc biên soạn câu hỏi cơ bản.

Mô hình ngôn ngữ lớn có thể tạo câu trả lời tự nhiên nhưng tồn tại ba vấn đề:

- kiến thức nền có thể không trùng với giáo trình;
- mô hình có thể “hallucinate”, trả lời tự tin nhưng không có bằng chứng;
- nếu truyền dữ liệu không kiểm soát, mô hình có thể làm lộ học liệu, đáp án hoặc
  thông tin của lớp khác.

Retrieval-Augmented Generation (RAG) giải quyết một phần các vấn đề này bằng
cách truy xuất bằng chứng từ kho tri thức được phê duyệt trước khi sinh câu trả
lời. Intaaneto chọn RAG làm lõi tri thức, còn assessment, progression và
multimedia là những lớp ứng dụng xung quanh lõi đó.

## Tên và mục tiêu nghiên cứu

**Đề tài:** Nghiên cứu xây dựng hệ thống E-learning trên môi trường web tích hợp
giảng viên ảo dựa trên công nghệ Trí tuệ nhân tạo.

Mục tiêu tổng quát là xây dựng môi trường học tập chủ động, trong đó:

- giảng viên quản lý khóa học, bài học và học liệu;
- học liệu PDF được chuyển thành kho tri thức có thể truy xuất;
- AI Tutor trả lời trong phạm vi bài học với nguồn dẫn;
- người học phải thể hiện mức độ hiểu bài trước khi tiến tiếp;
- giảng viên giảm công việc tạo bản tóm tắt và assessment cơ bản;
- kết quả học tập được tổng hợp thành báo cáo có thể giải thích;
- giảng viên ảo trình bày nội dung bằng giọng nói và hình ảnh như một lớp tăng
  cường, không làm hỏng luồng học khi multimedia thất bại.

## Câu hỏi nghiên cứu đề xuất

1. RAG có giúp AI Tutor trả lời đúng phạm vi học liệu và từ chối câu hỏi thiếu
   bằng chứng một cách ổn định hay không?
2. Cơ chế source version, authorization-first retrieval và application-owned
   citation có giảm nguy cơ lộ dữ liệu hoặc citation giả hay không?
3. Assessment deterministic kết hợp reinforcement từ RAG có hỗ trợ progression
   giải thích được tốt hơn việc để LLM trực tiếp quyết định điểm hay không?
4. Dialogue knowledge check ở chế độ recommendation có mức agreement, false
   pass và false fail như thế nào so với người chấm?
5. Pipeline video cục bộ có đạt mức chấp nhận được về thời gian sinh, chất lượng
   giọng tiếng Việt, đồng bộ caption và quyền sử dụng hình ảnh hay không?

# Cơ sở lý thuyết và cách áp dụng

## Kiến trúc E-learning phân lớp

Một hệ thống E-learning có thể được mô hình hóa thành bốn lớp:

- **lớp trình bày:** giao diện learner/teacher/admin;
- **lớp nghiệp vụ:** enrollment, course lifecycle, assessment, progression;
- **lớp dữ liệu:** người dùng, học liệu, vector, attempt và log an toàn;
- **lớp dịch vụ ngoài hoặc tính toán:** LLM, embedding, TTS, video, object
  storage.

Intaaneto hiện thực mô hình này bằng React/Vite ở frontend, Django REST Framework
ở backend, PostgreSQL/pgvector ở lớp dữ liệu, Redis/Celery cho tác vụ nền, và các
adapter cho generation provider, embedding, R2, TTS/video.

Nguyên lý quan trọng là frontend không phải ranh giới tin cậy. Việc ẩn một nút
theo role chỉ có giá trị UX; backend vẫn phải giới hạn queryset và kiểm tra object
ownership hoặc enrollment trước khi đọc/ghi.

## Retrieval-Augmented Generation

RAG gồm hai pha độc lập.

**Pha offline/ingestion:**

```text
Tài liệu → trích xuất → chuẩn hóa → chunk → embedding → lưu vector + metadata
```

**Pha online/query:**

```text
Câu hỏi → kiểm tra quyền → embedding câu hỏi → tìm đoạn gần nhất
→ đánh giá ngưỡng bằng chứng → sinh câu trả lời có căn cứ hoặc fallback
```

Với vector tài liệu \(\mathbf{d}\) và vector câu hỏi \(\mathbf{q}\), cosine
similarity được tính:

\[
\operatorname{cos}(\mathbf{q},\mathbf{d}) =
\frac{\mathbf{q}\cdot\mathbf{d}}
{\|\mathbf{q}\|\|\mathbf{d}\|}
\]

Điểm càng cao thường biểu thị nội dung càng gần về ngữ nghĩa. Tuy nhiên similarity
không phải xác suất câu trả lời đúng, càng không phải điểm năng lực người học.
Trong Intaaneto, ngưỡng tạm thời là 0,45; kết quả baseline cho thấy ngưỡng này
đang tạo false negative ở hai case có đúng marker trong top-k.

## Chunking, overlap và metadata vị trí

Tài liệu dài không thể truyền toàn bộ vào LLM ở mỗi câu hỏi. Chunking chia nội
dung thành các đoạn giới hạn. Overlap giúp giảm nguy cơ một ý bị cắt đúng biên.
Intaaneto dùng:

- chunk size mặc định 1.000 ký tự;
- overlap 150 ký tự;
- tối đa 500 chunk/source;
- page range, ordinal và stable offsets để truy vết.

Chunking deterministic có lợi cho nghiên cứu và vận hành: cùng một nội dung và
cấu hình tạo ra cùng vị trí chunk, giúp kiểm tra idempotency và so sánh thí
nghiệm. Checksum giúp nhận biết tài liệu thay đổi.

## Embedding đa ngôn ngữ

Embedding biến văn bản thành vector số. Hệ thống dùng FastEmbed/ONNX cục bộ với
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, 384 chiều. Lựa
chọn đa ngôn ngữ phù hợp với câu hỏi tiếng Việt và giảm việc gửi nguyên học liệu
ra provider chỉ để lập chỉ mục. Hạn chế là chất lượng trên miền học liệu cụ thể
chưa được đánh giá rộng.

## Grounded generation và citation

Grounded generation yêu cầu mô hình chỉ dựa trên evidence đã truy xuất. Evidence
được đặt trong vùng dữ liệu không tin cậy và không được quyền thay đổi system
policy. Mô hình không được tự quyết định citation ID. Ứng dụng xây citation từ
`KnowledgeChunk` thực sự đã chọn, gồm source, lesson, chunk, trang và excerpt.

Khi score dưới ngưỡng hoặc lesson chưa được index, hệ thống trả trạng thái
`weak_evidence` hoặc `not_indexed`, không gọi provider. Đây là cơ chế “abstention”
quan trọng: biết từ chối là một phần của chất lượng RAG.

## Human-in-the-loop

AI tạo summary và assessment dưới dạng draft. Giảng viên phải:

- sửa và phê duyệt summary;
- kiểm tra câu hỏi, đáp án, explanation và learning objective;
- chủ động publish assessment.

Thiết kế này áp dụng lý thuyết human-in-the-loop: AI làm giảm công việc lặp lại
nhưng quyết định học thuật vẫn thuộc người có trách nhiệm. Nó cũng giảm rủi ro
AI output sai tự động đi vào nội dung học hoặc ảnh hưởng điểm.

## Mastery learning và progression

Mastery learning yêu cầu người học đạt ngưỡng trước khi chuyển tiếp. Intaaneto
dùng assessment trắc nghiệm theo version và pass threshold. Backend tính điểm,
lưu snapshot immutable và chỉ hoàn thành bài khi pass. Sau failed attempt, hệ
thống trả weak objectives để learner xem reinforcement có citation.

Điểm đáng chú ý: mastery percentage, content progress và dialogue recommendation
là ba khái niệm tách biệt. Dialogue AI hiện không sửa điểm hoặc progression.

## Hàng đợi tác vụ và eventual consistency

PDF parsing, embedding và video rendering là tác vụ tốn thời gian. Thay vì giữ
HTTP request mở, backend tạo job bền vững trong database rồi Celery worker xử lý.
Frontend poll trạng thái. Hệ thống vì thế có eventual consistency: upload thành
công không đồng nghĩa RAG lập tức ready; trạng thái phải đi qua queued/running/
completed hoặc failed.

## Bảo mật theo trust boundary

Các đầu vào không tin cậy gồm PDF, extracted text, câu hỏi, chat history, ID từ
client, provider response và citation do model đề xuất. Quyết định tin cậy phải
ở application code:

- ai được đọc lesson nào;
- source version nào active;
- chunk nào thuộc scope;
- điểm và pass/fail;
- citation có thuộc retrieval set hay không;
- video asset có quyền và checksum đúng hay không.

# Phạm vi chức năng website hiện có

## Người dùng, xác thực và vai trò

Backend có custom user model, profile, daily activity và teacher application.
Các luồng đã có gồm:

- đăng ký learner và xác thực email;
- đăng nhập learner, đăng nhập teacher riêng;
- JWT access/refresh, rotation và logout;
- Google OAuth;
- quên và đặt lại mật khẩu;
- learner nộp đơn xin teacher;
- admin duyệt/từ chối đơn, người dùng không tự nâng role;
- profile cá nhân và public profile giới hạn dữ liệu.

Email verification token có expiry, digest lưu dạng SHA-256 và single-use.
Resend dùng phản hồi chung để giảm account enumeration. Nhiều endpoint nhạy cảm
có scoped throttling.

## Catalog, khóa học và enrollment

Website có trang landing, danh sách course, course detail, enrollment và
dashboard. Teacher có thể:

- tạo course ở trạng thái draft;
- cập nhật course thuộc sở hữu;
- thêm và quản lý lesson;
- chỉ publish course khi có ít nhất một published lesson usable;
- không tự đặt featured;
- không xóa course đã có lesson hoặc enrollment theo cách cascade phá lịch sử.

Learner có thể xem catalog published, enroll, mở lesson được phép và tiếp tục từ
resume position. Preview không được làm lộ next lesson thuộc enrollment.

## Bài học và học liệu

Lesson lưu text thủ công, PDF, extracted text, AI summary, processing status và
media. PDF được hiển thị bằng protected action và browser-local blob viewer, có
zoom, search, page control, fullscreen và mở tab mới. Extracted text có thể xem
trong panel giới hạn.

Giới hạn ingestion hiện tại:

- chỉ PDF;
- tối đa 20 MB;
- tối đa 100 trang;
- tối đa 250.000 ký tự trích xuất;
- kiểm tra extension, MIME, `%PDF-`, encrypted/malformed/empty;
- chuẩn hóa Unicode, loại NUL/control và giữ page marker an toàn.

DOCX, PPT và PPTX được xác định là ngoài phạm vi nghiên cứu hiện tại.

## AI Tutor

Trang lesson có tab chat AI. Contract chính:

```text
input: question + lesson_id + optional session
output: answer + citations[] + grounded + retrieval status
```

Chat khôi phục session gần nhất theo lesson sau reload. Citation được hydrate lại
từ database; nếu enrollment bị thu hồi thì lịch sử và chi tiết session không còn
được trả. UI dùng React text rendering, không inject raw HTML.

Ngoài chat lesson, backend còn có code explanation và exercise hint. Hint dùng
lesson/course authorization và không đưa `solution_code` hoặc hidden test vào
prompt.

## Assessment và bài tập

Hai nhánh cùng tồn tại:

- exercise/submission legacy cho bài tập, có access boundary;
- lesson assessment trắc nghiệm theo version cho progression hiện tại.

Teacher authoring cho phép tạo/sửa/xóa draft, khai báo threshold, câu hỏi,
choices, correct answer, explanation và learning objective; tối đa 50 câu.
Assessment đã có attempt không bị sửa/xóa trong lát cắt đầu tiên.

Learner nhận serializer không có answer key. Khi submit, backend xác thực đủ bộ
câu trả lời, chống câu hỏi chéo assessment, tính score/pass, lưu immutable
attempt/answer snapshot và cập nhật mastery/progression.

## Reinforcement và dialogue knowledge check

Sau failed attempt, weak objectives được dùng để retrieval trong đúng lesson,
trả đoạn củng cố và citation. Reinforcement không sửa điểm.

Sau khi learner đã pass assessment hiện hành, dialogue knowledge check có thể
chọn một câu/rubric server-owned, retrieval evidence và nhờ provider đề xuất
feedback. Event audit chỉ lưu HMAC answer digest và metadata giới hạn; không lưu
raw answer, rubric, prompt, feedback hoặc answer key. Kết quả vẫn chỉ là
recommendation.

## Báo cáo học tập và analytics

Learner dashboard phản ánh tiến độ của chính mình. Teacher report chỉ tổng hợp
course sở hữu, gồm:

- roster giới hạn;
- content progress và mastery;
- objective distribution theo attempt mới nhất của version hiện hành;
- CSV export có chống spreadsheet injection;
- paired reinforcement outcome ở mức aggregate, không nêu danh tính;
- achievement, streak và daily activity ở app analytics.

Paired outcome chỉ là dữ liệu quan sát; không chứng minh reinforcement gây ra
cải thiện nếu chưa có thiết kế thực nghiệm.

## Forum và tương tác cộng đồng

Forum có post, comment, tag, reaction, report, follow và public profile. Có
ownership boundary cho sửa/xóa, action riêng cho trạng thái đặc quyền, kiểm tra
target của reaction/report và giới hạn dữ liệu tác giả public. Course forum,
lesson comment và review cũng có scope enrollment/ownership.

## Công cụ giảng viên

Các route frontend cho teacher gồm:

- `/teacher/courses`;
- `/teacher/courses/:courseId`;
- `/teacher/courses/:courseId/students`;
- `/teacher/upload`;
- `/teacher/courses/:courseId/lessons/:lessonId/assessment`.

Teacher có thể quản lý course/lesson, upload/reprocess PDF, theo dõi job, tạo và
duyệt summary, sinh assessment draft theo batch, review/publish, xem learner và
báo cáo.

## Multimedia và giảng viên ảo

Pipeline hiện hành ưu tiên video slide cục bộ:

```text
Active RAG source + approved summary
→ video script draft
→ teacher sửa/approve
→ Piper WAV
→ slide 1280×720 + caption
→ FFmpeg H.264 MP4
→ Lesson.video_file
```

Script giới hạn khoảng 4.800 ký tự/50 segment; checksum source, summary và asset
được kiểm tra lại trước queue và trong worker. Job có deduplication, stage và
failure code giới hạn. Hai run thật trước đây với summary 1.602 ký tự tạo video
12 slide, khoảng 78,9 giây trong 14,285 và 13,663 giây.

Tuy nhiên video hiện **chưa có nhân vật ảo nói hoàn chỉnh trong web flow**. Ảnh
AI Tutor chủ yếu là hình tĩnh trên slide. SadTalker adapter và GPU PoC còn trong
repository cho bằng chứng lịch sử, nhưng portrait upload/enqueue đã được gỡ khỏi
UI và API lesson. PoC 1,48 giây từ asset demo chỉ chứng minh runtime, không chứng
minh quyền asset, chất lượng tiếng Việt, lip-sync hay giá trị sư phạm.

# Kiến trúc kỹ thuật toàn hệ thống

## Sơ đồ triển khai logic

```text
┌──────────────────────────────────────────────────────────────┐
│ React 18 + Vite + Tailwind                                  │
│ Learner UI | Teacher UI | Forum | Dashboard | AI Tutor      │
└──────────────────────────┬───────────────────────────────────┘
                           │ HTTPS/JSON, JWT
┌──────────────────────────▼───────────────────────────────────┐
│ Django 5 + Django REST Framework                            │
│ users | courses | exercises | ai_assistant | forum | analytics│
│ serializers → views/querysets → services → models           │
└──────────────┬─────────────────┬──────────────────┬───────────┘
               │                 │                  │
      ┌────────▼────────┐ ┌──────▼───────┐ ┌──────▼──────────┐
      │ PostgreSQL 15   │ │ Redis/Celery │ │ Provider adapters│
      │ relational data │ │ durable jobs │ │ OpenAI/Gemini/  │
      │ + pgvector      │ │ ingestion/   │ │ Groq, FastEmbed │
      └────────┬────────┘ │ multimedia   │ └─────────────────┘
               │          └──────────────┘
      ┌────────▼──────────────────────────────────────────────┐
      │ File storage: local development hoặc private R2      │
      │ PDF | WAV | ảnh | MP4 | signed URL ngắn hạn          │
      └───────────────────────────────────────────────────────┘
```

## Trách nhiệm từng layer

| Layer | Thành phần | Trách nhiệm | Không nên làm |
|---|---|---|---|
| Presentation | React pages/components | hiển thị state, form, navigation | quyết định quyền, điểm, citation |
| API contract | DRF serializer/view | validate request/response, throttle | chứa toàn bộ orchestration RAG |
| Access | querysets/access services | enrollment, ownership, role | tin ID do client cung cấp |
| Domain service | RAG, scoring, ingestion | nghiệp vụ, transaction, provider seam | phụ thuộc trực tiếp UI |
| Persistence | Django models/PostgreSQL | invariant, version, audit tối thiểu | lưu secret/full prompt tùy tiện |
| Async | Celery/Redis + DB jobs | retry, lease, expensive processing | xác nhận quyền chỉ ở thời điểm enqueue |
| External/local compute | LLM, FastEmbed, Piper, FFmpeg, R2 | generation/embedding/media/storage | quyết định authorization/progression |

## Mô hình dữ liệu chính

Repository có khoảng 40 model/domain entity, nổi bật:

- `User`, `Profile`, `TeacherApplication`, `DailyActivity`;
- `Course`, `Lesson`, `Enrollment`, `LessonProgress`, `Review`,
  `LessonComment`;
- `LessonIngestionJob`, summary/video script/audio/multimedia job;
- `KnowledgeSource`, `KnowledgeChunk`, `ChatSession`, `ChatMessage`;
- `Exercise`, `Submission`, `LessonAssessment`, `AssessmentQuestion`,
  `AssessmentAttempt`, `AssessmentAnswer`;
- reinforcement/dialogue audit events;
- `Post`, `Comment`, `Reaction`, `Report`, `Follow`, `Tag`;
- `Achievement`, `UserAchievement`, `LearningAnalytics`.

Quan hệ trung tâm:

```text
User ──owns──> Course ──contains──> Lesson
  │               │                   │
  └─Enrollment────┘                   ├─KnowledgeSource─KnowledgeChunk
                                      ├─ChatSession─ChatMessage
                                      ├─LessonAssessment─Question
                                      │                    └─Attempt─Answer
                                      └─Ingestion/Media Jobs
```

## Hạ tầng development

Docker Compose mô tả:

- PostgreSQL image `pgvector/pgvector:0.8.2-pg15-bookworm`;
- Redis 7.2.7 với AOF;
- Django backend;
- Celery worker non-root, concurrency 1, prefetch 1;
- React/Vite frontend;
- Adminer;
- volumes cho database, media, static, Redis, model cache và TTS model.

Đây là topology development. Production settings có HTTPS redirect, secure
cookie và HSTS, nhưng chưa thể xem là production deployment hoàn chỉnh.

# RAG từ A đến Z

## Bước A — Phê duyệt và upload học liệu

Teacher tạo hoặc chọn course/lesson thuộc sở hữu. Request upload bị kiểm tra role,
ownership và throttle trước khi enqueue. Tên object do server sinh; không dùng
filename làm quyền hoặc đường dẫn tin cậy.

## Bước B — Job ingestion bền vững

Backend tạo `LessonIngestionJob`, đảm bảo chỉ có một job queued/running cho mỗi
lesson và trả HTTP 202. Celery worker nhận job, kiểm tra lại lesson còn tồn tại,
teacher còn quyền và source chưa bị thay đổi. Kiểm tra lại ở worker là bắt buộc
vì quyền có thể thay đổi sau thời điểm upload.

## Bước C — Kiểm tra PDF

File phải qua allowlist `.pdf`, MIME và magic signature, size/page/text bounds.
Encrypted, malformed, empty hoặc giả mạo bị từ chối. Parser giữ page markers để
citation có vị trí, đồng thời escape dòng tài liệu cố giả page marker của ứng
dụng.

## Bước D — Chuẩn hóa

Text được normalize Unicode, dọn whitespace, NUL/control và tạo representation
ổn định. `Lesson.extracted_text` được ưu tiên hơn content thủ công khi có.
Checksum đại diện source content cho versioning và stale-state check.

## Bước E — Chia đoạn

Chunker deterministic tạo ordinal, start/end offset và page range. Overlap giữ
ngữ cảnh biên. Giới hạn chunk ngăn tài liệu làm cạn memory hoặc tạo chi phí bất
thường.

## Bước F — Embedding

Embedding provider protocol che giấu implementation. Adapter FastEmbed lazy-load
model multilingual và xác nhận vector đúng 384 chiều. Provider/model/revision/
dimension được lưu cùng source để retrieval không trộn vector không tương thích.

## Bước G — Atomic activation

Chunk mới được ghi theo source version. Chỉ khi toàn bộ indexing thành công,
transaction mới activate source mới và deactivate source cũ. Nếu embedding hoặc
database lỗi, source dở dang không xuất hiện trong retrieval. Reprocess cùng
checksum không tạo duplicate; thay đổi content không để stale chunk active.

## Bước H — Nhận câu hỏi

Learner gửi question và lesson ID; session lesson scope là server-owned. Question
bị giới hạn 1.000 ký tự. Chat history và evidence context có bounds riêng để hội
thoại cũ không chiếm hết context của tài liệu.

## Bước I — Authorization trước embedding/search

Backend giải actor scope:

- learner phải enrolled và lesson/course còn accessible;
- teacher phải sở hữu course;
- admin theo policy quản trị.

Outsider bị từ chối trước query embedding và provider call. Điều này vừa bảo mật
vừa tránh chi phí cho request không hợp lệ.

## Bước J — Vector retrieval

Hệ thống chọn compatible, complete, active source trong đúng lesson. PostgreSQL
dùng exact pgvector cosine distance trong source đã lọc. Top-k mặc định 5, tối đa
10. SQLite chỉ có cosine fallback phục vụ isolated tests sau khi database đã
giới hạn source.

## Bước K — Evidence gate

Nếu không có source: `not_indexed`. Nếu top score dưới 0,45:
`weak_evidence`. Hai trạng thái này trả grounded fallback và không gọi LLM. Nếu
đủ evidence: `ready`.

## Bước L — Prompt construction

System prompt xác định vai trò gia sư tiếng Việt và yêu cầu chỉ dựa trên
evidence. Retrieved chunk được đặt như dữ liệu không tin cậy. Document prompt
injection không được phép thay đổi policy. Context được giới hạn số chunk/ký tự.

## Bước M — Generation provider

Provider adapter hỗ trợ OpenAI, Gemini và Groq theo cấu hình server. Key/model/
timeout ở environment/settings. Missing key hoặc provider lạ fail closed. RAG
retrieval không phụ thuộc vendor generation.

## Bước N — Citation

LLM không tạo citation authority. Ứng dụng ánh xạ selected chunk thành citation
ổn định với lesson, source/version, chunk ID, page range và excerpt giới hạn.
Nhờ đó citation scope accuracy có thể kiểm thử độc lập.

## Bước O — Persistence an toàn

Chat message lưu latency/token và retrieval metadata giới hạn: status,
source/version, selected chunk IDs/scores. Không lưu embeddings, full prompt,
provider error hoặc citation excerpt. Khi đọc lại, chunk reference được
rehydrate từ đúng lesson/source/version.

## Bước P — UI

Lesson chat hiển thị answer, grounded/fallback status và source excerpt có thể
mở rộng. UI không mô phỏng RAG ready nếu backend chưa xác nhận. Enrollment bị
thu hồi làm session/history không còn accessible.

## RAG kết nối với các phần khác

```text
                         ┌─> AI Tutor Q&A + citation
PDF → RAG knowledge core ├─> summary draft → teacher approval
                         ├─> assessment draft → teacher review
                         ├─> weak-objective reinforcement
                         ├─> post-pass dialogue recommendation
                         └─> approved script → TTS/video
```

RAG là nguồn bằng chứng dùng chung, nhưng mỗi consumer có policy riêng. Summary
và assessment không tự publish; reinforcement/dialogue không tự sửa điểm; video
không quyết định lesson readiness.

# Luồng dữ liệu end-to-end

## Luồng 1 — Từ giảng viên đến lesson RAG ready

1. Teacher đăng nhập qua boundary dành cho teacher.
2. Backend xác nhận role, active và verified.
3. Teacher tạo course draft.
4. Teacher tạo lesson và upload PDF.
5. API kiểm tra ownership/file metadata, tạo ingestion job, trả 202.
6. Worker kiểm tra lại quyền và file.
7. PDF được parse, normalize, chunk và embed.
8. PostgreSQL lưu source version/chunk/vector.
9. Transaction activate source hoàn chỉnh.
10. Lesson trả `rag_ready`; teacher có thể reprocess idempotent.

## Luồng 2 — Learner học và hỏi AI

1. Learner xem catalog và enroll course published.
2. Backend cấp quyền lesson theo enrollment/publication.
3. UI tải content/PDF/video nếu có.
4. Learner gửi question trong lesson.
5. Backend resolve lesson scope trước retrieval.
6. Query được embed, exact cosine search trong active source.
7. Evidence gate quyết định fallback hay generation.
8. Provider sinh answer từ context giới hạn.
9. Application dựng citation.
10. Answer/status/citation được trả và metadata an toàn được lưu.

## Luồng 3 — Assessment và progression

1. Teacher tạo hoặc review assessment draft.
2. Teacher publish assessment.
3. Learner tải learner-safe schema không có đáp án.
4. Learner gửi bộ answer đầy đủ.
5. Backend kiểm tra enrollment, version và question membership.
6. Pure scoring function tính score; transaction lưu snapshot.
7. Nếu fail, trả weak objectives và có thể gọi reinforcement retrieval.
8. Nếu pass, cập nhật mastery/completion/resume và trả next lesson hợp lệ.
9. Dialogue check sau pass chỉ cung cấp feedback, không đổi state.

## Luồng 4 — Báo cáo giảng viên

1. Teacher chọn course sở hữu.
2. Queryset lọc course trước aggregation.
3. Backend lấy attempt version hiện hành, progress và objective outcomes.
4. API trả aggregate/roster giới hạn hoặc CSV an toàn.
5. Không trả chat, answer key, email không cần thiết hay raw reinforcement answer.

## Luồng 5 — Multimedia

1. RAG source ready và summary đã được teacher approve.
2. Provider tạo video-script draft giới hạn.
3. Teacher edit/approve.
4. API tạo durable media job, checksum-bind input.
5. Worker kiểm tra lại quyền và stale state.
6. Piper sinh WAV; Pillow sinh slide/caption; FFmpeg ghép MP4.
7. File attach vào lesson; lỗi video không chặn RAG/assessment.

# Đánh giá thực nghiệm RAG hiện có

## Retrieval baseline V1

Điều kiện:

- 8 case tiếng Việt: 6 answerable, 2 unsupported;
- 1 lesson demo, active source v1, 2 chunks;
- exact pgvector cosine, top-k 5, threshold 0,45;
- FastEmbed multilingual MiniLM 384 chiều;
- không gọi generation provider.

| Metric | Kết quả |
|---|---:|
| Pass/status accuracy | 0,75 |
| Expected-source recall | 1,00 |
| Mean latency gồm cold initialization | 225,12 ms |
| Unsupported fallback | 2/2 |
| Answerable bị false negative | 2/6 |

Diễn giải đúng: evidence mong đợi xuất hiện trong top-k của cả sáu case
answerable, nhưng hai case bị threshold từ chối. Không được diễn giải 0,75 là độ
chính xác câu trả lời.

## Grounded-answer baseline V1 với Gemini

| Metric | Kết quả |
|---|---:|
| Contract pass rate | 0,75 |
| Citation scope accuracy | 1,00 |
| Refusal accuracy | 1,00 |
| Strict lexical proxy pass | 0,50 |
| Mean warm latency | 1.515,62 ms/case |
| Provider token reported | 2.283 trên 4 generation call |

Bốn case answerable vượt threshold được generation và citation đúng scope. Hai
case answerable bị retrieval từ chối. Hai unsupported case fallback, không gọi
generation. Lexical proxy thấp không đồng nghĩa answer sai về nghĩa; cần human
review độc lập.

## Groq baseline bổ sung

Living state ghi nhận baseline Groq `llama-3.3-70b-versatile` ngày 21/07/2026:
contract pass 0,75, citation scope 1,00, refusal 1,00, latency trung bình
1.343,75 ms. Đây vẫn là tập nhỏ cùng miền, chưa đủ để đổi provider mặc định.

## Điểm mạnh phương pháp hiện tại

- evaluation dataset có version;
- retrieval evaluation không cần LLM, giúp tách lỗi retrieval khỏi generation;
- full-pipeline command yêu cầu xác nhận cost rõ ràng;
- report mặc định không commit raw questions/answers;
- contract, citation, refusal và lexical proxy được tách, tránh gọi nhầm là
  semantic accuracy;
- có prompt-injection case;
- có quy trình hai người chấm và Cohen's kappa, dù chưa hoàn tất rating.

## Khoảng trống thực nghiệm

- chỉ một lesson demo và tám case;
- chưa có development/holdout split;
- chưa có precision@k, MRR/nDCG hoặc confidence interval đủ ý nghĩa;
- chưa đánh giá nhiều loại PDF, câu hỏi đa nghĩa và adversarial rộng;
- chưa có hai reviewer hoàn thành semantic/pedagogical rating;
- chưa đo cost/latency dưới tải đồng thời;
- chưa so sánh model/chunk/threshold bằng thiết kế ablation có kiểm soát;
- chưa có study người học để đo learning gain.

# Đánh giá tiến độ có trọng số

## Phương pháp chấm

Mỗi nhóm mục tiêu được chấm theo bốn mức:

- 0%: chưa có;
- 25%: thiết kế hoặc skeleton;
- 50%: có vertical slice nhưng thiếu integration/bằng chứng;
- 75%: hoạt động và có test, còn thiếu hardening/evaluation;
- 100%: đạt tiêu chí nghiên cứu và triển khai đã xác định.

Điểm tổng hợp ưu tiên đúng đề tài: RAG 25%, nền tảng E-learning 20%, assessment và
progress 15%, teacher/reports 10%, multimedia 10%, security/quality 10%, nghiên
cứu/tài liệu/deployment 10%.

| Nhóm | Trọng số | Điểm | Đóng góp | Căn cứ |
|---|---:|---:|---:|---|
| RAG core và AI Tutor | 25% | 84% | 21,0 | ingestion/index/retrieval/answer/citation có test; evaluation còn nhỏ |
| Nền tảng E-learning | 20% | 88% | 17,6 | auth, course, lesson, enroll, forum, dashboard đã có |
| Assessment/progression | 15% | 82% | 12,3 | deterministic loop hoàn chỉnh; AI dialogue chưa calibrate |
| Teacher tools/report | 10% | 84% | 8,4 | CRUD, upload, authoring, roster, CSV, objective report |
| Multimedia/virtual lecturer | 10% | 58% | 5,8 | slide video chạy; thiếu nhân vật/quality/consent experiment |
| Security/quality | 10% | 72% | 7,2 | nhiều negative tests/throttle/scope; thiếu pentest, parser isolation |
| Research/deployment/docs | 10% | 49% | 4,9 | có protocol/baseline/docs; thiếu human study, CI/CD, production |
| **Tổng** | **100%** |  | **77,2%** | Điểm theo feature map |

Feature-map score 77,2% cao hơn công thức ba trục 73,6% vì nhiều chức năng đã
được code nhưng chưa có bằng chứng nghiên cứu/production tương ứng. Do đó báo cáo
chọn **khoảng 75%** làm con số trung tâm thận trọng.

## RAG riêng đã đạt bao nhiêu?

| Thành phần RAG | Điểm ước lượng |
|---|---:|
| Ingestion PDF an toàn, async, idempotent | 90% |
| Versioning/chunking/embedding/atomic activation | 92% |
| Authorization-first retrieval | 94% |
| Grounded answer/fallback/citation | 88% |
| Chat history và UI evidence | 85% |
| Provider abstraction/observability | 80% |
| Evaluation và tuning | 55% |
| Production scale/monitoring | 48% |
| **RAG prototype** | **khoảng 86%** |
| **RAG như kết quả nghiên cứu hoàn chỉnh** | **khoảng 70%** |

RAG đủ mạnh để demo và tiếp tục thí nghiệm. Nó chưa đủ bằng chứng để viết kết
luận “độ chính xác cao” hoặc “cải thiện kết quả học tập”.

# Kiểm thử và bằng chứng phần mềm

Living state gần nhất ghi nhận **266 backend tests pass ngày 26/07/2026** sau khi
thêm private R2 seam. Trước đó có 235 test ngày 17/07. Repository hiện có khoảng
256 hàm test được nhận diện theo tên; số case pytest thực tế có thể lớn hơn do
parameterization.

Coverage chức năng đã ghi nhận gồm:

- indexing deterministic/idempotent/rollback/concurrent edit;
- retrieval relevance, scope, cross-course isolation, provider failure;
- grounded answer, citation, fallback, prompt injection, history;
- PDF validation và durable ingestion retry/dedup/revocation;
- auth, role escalation, verification token;
- assessment, scoring, progression, reinforcement/dialogue;
- reports, CSV privacy và spreadsheet injection;
- multimedia job, owner/worker reauthorization, stale checksum;
- R2 key, signed URL, bounded materialization và cleanup;
- forum ownership/target constraints;
- scoped throttling.

Frontend **đã được chạy lại ngày 30/07/2026**: ESLint pass với 0 warning theo
ngưỡng cấu hình và Vite production build pass, transform 1.886 module trong
4,44 giây. Main JS chunk hiện 586,40 kB (gzip 162,83 kB), vì vậy Vite cảnh báo
chunk trên 500 kB; dữ liệu Browserslist cũng đã cũ sáu tháng. `npm audit` 0 là
baseline được ghi nhận trước đó, không được chạy lại trong lần này. Frontend chưa
có test runner tự động/E2E riêng. Không thể chạy lại Docker backend suite vì
Docker CLI trong WSL chưa được tích hợp; vì vậy các con số backend test là bằng
chứng đã lưu trong repository, không phải kết quả tái chạy ngày 30/07.

# Bảo mật, quyền riêng tư và đạo đức

## Điểm đã làm tốt

- authorization trước retrieval/provider;
- object-level ownership/enrollment, không chỉ role;
- learner serializers không lộ answer key/hidden tests;
- application-owned citation;
- rate limit cho auth, upload, chat, assessment và video;
- JWT rotation/blacklist và email verification token an toàn hơn;
- private R2 opt-in, server-generated UUID key, signed URL mặc định 5 phút;
- logs/audit ưu tiên ID, checksum, score, latency thay vì raw content;
- worker non-root và reauthorization;
- consent/rights assertion trong SadTalker historical path;
- AI không quyết định score/progression.

## Rủi ro còn lại

| Mức | Rủi ro | Tác động | Hướng xử lý |
|---|---|---|---|
| P1 | Token browser còn có trade-off localStorage/XSS | chiếm phiên nếu XSS | đánh giá HttpOnly cookie/BFF, CSP chặt |
| P1 | Chưa có parser subprocess wall-clock/malware scan | PDF độc hại/DoS | isolate parser, timeout, scan/quarantine |
| P1 | Chưa có pentest và production threat validation | boundary có thể còn lỗ hổng | test role matrix, SAST/DAST, review độc lập |
| P1 | Chưa có retention/deletion policy đầy đủ | rủi ro dữ liệu nghiên cứu | định nghĩa lifecycle chat/attempt/media |
| P1 | Provider data terms chưa được chứng minh | học liệu có thể ra bên thứ ba | DPA, data minimization, provider policy |
| P2 | Redis/Postgres/R2 chưa có HA/restore drill | mất hoặc gián đoạn dữ liệu | backup, restore test, monitoring |
| P2 | Swagger public và debug topology là dev | lộ schema/dev surface | tắt/hạn chế ngoài development |
| P2 | Chưa có malware/orphan cleanup tự động | storage phình hoặc giữ file rác | lifecycle job và audit cleanup |

Đối với nghiên cứu có người tham gia, cần consent, pseudonymization, mục đích và
thời hạn lưu dữ liệu; không dùng raw chat hoặc câu trả lời learner làm dataset
provider nếu chưa có phê duyệt.

# Multimedia: hiện trạng và kế hoạch cải thiện

## Hiện trạng thật

Hệ thống đã có media pipeline kỹ thuật và video slide; chưa nên mô tả là “nhân
vật giảng viên ảo hoàn chỉnh”. Hình AI Tutor tĩnh, giọng Piper và caption tạo trải
nghiệm thuyết minh, nhưng thiếu:

- nhân vật có biểu cảm/lip-sync được tích hợp lại vào web flow;
- provenance và consent của portrait;
- đánh giá intelligibility/tự nhiên của giọng Việt;
- caption timing theo câu/âm vị thay vì chỉ segment;
- rubric artifact, facial stability và uncanny effect;
- benchmark cold/warm trên máy mục tiêu;
- accessibility transcript và lựa chọn tắt motion;
- quyết định license/phân phối thương mại.

## Lộ trình cải thiện đề xuất

1. Giữ video là optional enhancement.
2. Chọn một portrait do nhóm sở hữu hoặc có giấy phép/consent.
3. Tạo clip 30–60 giây từ lesson thật đã phê duyệt.
4. Ghi commit/model/checkpoint, CPU/GPU, RAM/VRAM, latency và file size.
5. Hai người review theo rubric: phát âm, nhịp, caption, lip-sync, artifact,
   pedagogical clarity.
6. So sánh slide-only với talking avatar; chỉ tích hợp avatar nếu có lợi rõ và
   chi phí chấp nhận được.
7. Giữ transcript/text lesson làm đường truy cập chính khi video lỗi.

# Hạn chế và đe dọa tính hợp lệ

## Tính hợp lệ nội tại

- Dataset và demo lesson do chính nhóm xây dựng có thể thiên lệch.
- Threshold có thể bị tune quá mức nếu không tách holdout.
- Provider output không hoàn toàn deterministic.
- Paired reinforcement report không loại trừ self-selection và repeated
  measures.
- Software baseline assessment 1,00 chỉ chứng minh scoring khớp fixture, không
  chứng minh câu hỏi hay.

## Tính hợp lệ ngoại tại

- Chưa chứng minh với nhiều môn học, nhiều phong cách PDF và learner population.
- Exact vector search phù hợp corpus nhỏ; chưa đo khi số lesson/chunk tăng lớn.
- Kết quả trên môi trường development không đại diện production network/load.
- Chất lượng tiếng Việt của model/TTS có thể thay đổi theo miền thuật ngữ.

## Tính hợp lệ cấu trúc

- Lexical marker không thay thế semantic correctness.
- Similarity không phải confidence probability.
- Progress/mastery trong hệ thống không tự động đồng nghĩa kiến thức thực.
- Contract pass không phải answer accuracy.
- Video render thành công không phải hiệu quả sư phạm.

## Tính hợp lệ kết luận

Tám case không đủ power cho kết luận tổng quát hoặc confidence interval hẹp.
Chưa có inter-rater agreement hoàn chỉnh. Vì vậy kết luận hiện tại phải giới hạn
ở việc pipeline và safety contract hoạt động trên baseline đã mô tả.

# Kế hoạch hoàn thiện ưu tiên

## Giai đoạn 1 — Khóa bằng chứng RAG

Mục tiêu: đưa RAG từ prototype 86% lên mức nghiên cứu 85%+.

- mở rộng tối thiểu 5–10 lesson, 80–150 câu hỏi;
- phân tầng answerable, unsupported, ambiguous, adversarial;
- tách development/holdout trước tuning;
- hai reviewer độc lập chấm correctness, groundedness, citation support,
  pedagogical clarity và refusal;
- báo Cohen's kappa/percent agreement và adjudication;
- so sánh threshold, top-k, chunk size/overlap, embedding model;
- đo cold/warm latency, p50/p95, provider calls/tokens;
- không tune trực tiếp trên holdout.

## Giai đoạn 2 — Hoàn tất assessment research

- teacher review/publish ba assessment blueprint;
- hoàn thành hai rating sheet E2;
- xây free-text dialogue cases có adjudicated labels;
- đo false pass, false fail, stability và agreement;
- giữ AI recommendation-only cho tới khi calibration đủ;
- chạy study reinforcement có protocol, consent và repeated-measure analysis.

## Giai đoạn 3 — Video/nhân vật

- hoàn thành consented Vietnamese render;
- đánh giá Piper voice và caption;
- thử avatar có kiểm soát;
- chọn slide-only hoặc avatar theo bằng chứng, không theo cảm tính;
- bổ sung transcript, fallback và accessibility.

## Giai đoạn 4 — Production hardening

- CI pipeline cho backend test, frontend lint/build, dependency/secret scan;
- frontend component/E2E tests cho năm critical journeys;
- parser isolation, malware scan, cleanup;
- production deployment, domain/HTTPS/CSP;
- monitoring Celery/Redis/PostgreSQL/R2/provider;
- backup/restore và deletion drill;
- load test chat, ingestion, assessment;
- logging/alerting không chứa dữ liệu nhạy cảm.

## Năm critical E2E journeys cần tự động hóa

1. Register → verify → login → enroll → open lesson.
2. Teacher create draft course → upload PDF → wait RAG ready → publish.
3. Learner ask grounded/unsupported questions → inspect citation/fallback.
4. Learner fail → reinforcement → retry → pass → next lesson.
5. Teacher review summary/assessment → generate video → learner playback.

# Khuyến nghị cách trình bày trong bài nghiên cứu

## Các tuyên bố có thể dùng

- “Hệ thống đã triển khai pipeline RAG lesson-scoped với authorization trước
  vector retrieval, source versioning và citation do ứng dụng tạo.”
- “Baseline retrieval tám case đạt expected-source recall 1,00 nhưng status
  accuracy 0,75 do hai false negative ở ngưỡng 0,45.”
- “Grounded-answer contract đạt 0,75, citation scope và refusal đạt 1,00 trên
  baseline nhỏ; các chỉ số này không được diễn giải là semantic accuracy.”
- “Assessment progression hiện dựa trên scoring deterministic đã được teacher
  phê duyệt; AI dialogue chỉ cung cấp recommendation.”
- “Video slide cục bộ đã chạy kỹ thuật; talking-avatar và đánh giá chất lượng
  tiếng Việt chưa hoàn tất.”

## Các tuyên bố chưa nên dùng

- “RAG chính xác 75%.”
- “AI chấm bài khách quan hơn giảng viên.”
- “AI Tutor cải thiện kết quả học tập.”
- “Hệ thống bảo mật tuyệt đối.”
- “Giảng viên ảo đã hoàn chỉnh.”
- “Sẵn sàng triển khai production.”

# Kết luận

Intaaneto đã vượt qua giai đoạn demo giao diện đơn giản và hình thành một hệ
thống nghiên cứu có kiến trúc rõ. Chuỗi PDF → ingestion job → normalized chunks
→ local embedding → pgvector retrieval → grounded generation → application-owned
citation đã hiện diện trong code và có regression tests. Chuỗi assessment →
deterministic score → mastery/progression → reinforcement/report cũng đã khép
kín. Các layer frontend, API, access control, service, persistence, async worker
và provider adapter có trách nhiệm tương đối tách bạch.

Đánh giá thận trọng cho thấy dự án đạt **khoảng 75% mục tiêu toàn đề tài**,
trong đó prototype chức năng đạt khoảng 86%, nhưng bằng chứng nghiên cứu và
production readiness thấp hơn. Phần cần đầu tư tiếp không phải thêm thật nhiều
tính năng, mà là mở rộng evaluation, hoàn thành human review, tự động hóa E2E,
hardening production và thực nghiệm video có nhân vật/giọng Việt với asset được
phép.

Nếu hoàn thành bốn nhóm việc trên, nhóm có thể chuyển kết luận từ “pipeline hoạt
động và có baseline” sang “hệ thống được đánh giá có kiểm soát, có giới hạn rõ
và có bằng chứng đủ sức bảo vệ trong một bài nghiên cứu khoa học”.

# Phụ lục A — Inventory kỹ thuật

| Hạng mục | Hiện trạng |
|---|---|
| Backend | Python 3.11, Django 5, DRF, Simple JWT |
| Frontend | React 18, Vite, Tailwind, Zustand, React Router |
| Database | PostgreSQL 15, pgvector 0.8.2 |
| Queue | Redis 7.2.7 AOF, Celery |
| Embedding | FastEmbed ONNX, multilingual MiniLM, 384D |
| Generation | OpenAI/Gemini/Groq adapters |
| Storage | local hoặc private Cloudflare R2 opt-in |
| PDF | validation, extraction, page markers, 20MB/100 pages/250k chars |
| TTS/video | Piper/espeak seam, Pillow slides, FFmpeg, SadTalker historical PoC |
| Apps | users, courses, exercises, ai_assistant, forum, analytics |
| Frontend pages | landing, auth, catalog, lesson, dashboard, teacher, forum, profile |
| Migrations | 33 migration files tại thời điểm kiểm tra |
| Test evidence | 266 backend tests pass được ghi nhận ngày 26/07/2026 |

# Phụ lục B — Cấu hình RAG chính

| Cấu hình | Mặc định |
|---|---:|
| Embedding dimension | 384 |
| Chunk size | 1.000 ký tự |
| Chunk overlap | 150 ký tự |
| Max chunks/source | 500 |
| Retrieval top-k | 5 |
| Max top-k | 10 |
| Minimum score | 0,45 |
| Max question | 1.000 ký tự |
| Chat history | 12 messages |
| PDF bytes | 20 MB |
| PDF pages | 100 |
| Extracted chars | 250.000 |

# Phụ lục C — Tài liệu bằng chứng trong repository

- `README.md`: phạm vi và cách chạy hiện tại.
- `.ai/skills/intaaneto-rag/references/current-state.md`: living state chi tiết.
- `.ai/skills/intaaneto-rag/references/project-scope.md`: mục tiêu nghiên cứu.
- `.ai/skills/intaaneto-rag/references/architecture.md`: kiến trúc RAG.
- `.ai/skills/intaaneto-rag/references/delivery-plan.md`: tiêu chí từng slice.
- `docs/RAG_RETRIEVAL_BASELINE_V1.md`: baseline retrieval.
- `docs/RAG_GROUNDED_ANSWER_BASELINE_V1.md`: baseline full pipeline.
- `docs/RAG_GROUNDED_ANSWER_EVALUATION.md`: protocol đánh giá answer.
- `docs/ASSESSMENT_EVALUATION_PROTOCOL.md`: protocol E2.
- `docs/ASSESSMENT_SOFTWARE_BASELINE_V1.md`: baseline scoring.
- `docs/LOCAL_MULTIMEDIA_SETUP.md`: pipeline media cục bộ.
- `docs/SADTALKER_POC.md`: bằng chứng PoC lịch sử.
- `docs/CLOUDFLARE_R2_SETUP.md`: private object storage.
- `docs/MANUAL_TESTING_GUIDE.md`: hành trình kiểm thử thủ công.

# Phụ lục D — Ghi chú kiểm chứng báo cáo

Báo cáo được lập bằng cách đối chiếu code, models, routes, settings, Docker
Compose, frontend route inventory, skill living state và các baseline đã lưu.
Không coi roadmap cũ là nguồn sự thật khi mâu thuẫn với code. Không đọc hoặc đưa
secret từ `.env` vào báo cáo. Tại ngày lập báo cáo, Docker không khả dụng trong
WSL hiện tại nên backend suite không được tái chạy; mọi con số test đều ghi rõ
ngày bằng chứng gần nhất.
