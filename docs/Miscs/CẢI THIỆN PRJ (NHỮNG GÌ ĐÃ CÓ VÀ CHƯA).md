# Hiểu đúng bản chất dự án Intaaneto: AI/ML, dữ liệu, RAG, harness, Qdrant và LangChain

> Cập nhật ngày 04/08/2026. Tài liệu này giải thích bản chất kỹ thuật và nghiên
> cứu của Intaaneto theo code hiện có. Những công nghệ được nhắc tới nhưng chưa
> dùng trong repository sẽ được ghi rõ là phương án, không phải tính năng đã có.

## 1. Trả lời ngắn gọn trước

Intaaneto **là một dự án có ứng dụng machine learning**, nhưng chính xác hơn nên gọi là:

> **Một hệ thống E-learning ứng dụng các mô hình AI/ML đã được huấn luyện sẵn,
> trong đó RAG là lõi tri thức để AI Tutor trả lời dựa trên học liệu được phê
> duyệt.**

Nhóm đang **ứng dụng và đánh giá ML**, chứ hiện không tự huấn luyện một mô hình
nền tảng mới từ đầu. Đóng góp kỹ thuật và nghiên cứu của project nằm ở:

- pipeline dữ liệu học liệu;
- kiến trúc RAG có phân quyền;
- source versioning và indexing idempotent;
- retrieval, evidence threshold, grounded fallback;
- citation do ứng dụng kiểm soát;
- kết hợp RAG với assessment, reinforcement và progression;
- evaluation dataset, evaluation harness và protocol nghiên cứu;
- đo lường chất lượng, an toàn và giới hạn của hệ thống.

Việc không tự train model **không làm đề tài hết tính AI/ML**. Rất nhiều hệ thống
AI ứng dụng ngoài thực tế dùng pretrained model và tập trung vào dữ liệu, retrieval,
evaluation, safety và product integration.

Intaaneto cũng **không dùng Qdrant hoặc LangChain ở thời điểm hiện tại**. Project
dùng PostgreSQL + pgvector làm vector store/search, còn pipeline RAG được viết
thành các Django service rõ ràng. Đây là lựa chọn kỹ thuật có chủ đích, không
phải vì nhóm không biết hoặc không sử dụng công nghệ có sẵn.

## 2. “Làm machine learning” có nhiều cấp độ

Khi nghe cụm từ “dự án machine learning”, mọi người thường vô tình gom nhiều
loại công việc khác nhau vào một nhóm. Có thể tách thành bốn cấp độ.

### 2.1. Huấn luyện mô hình từ đầu

Nhóm tự thiết kế hoặc chọn kiến trúc, chuẩn bị tập train rất lớn, chạy training,
điều chỉnh trọng số và đánh giá model. Ví dụ: tự huấn luyện một language model,
một mạng phân loại ảnh hoặc một embedding model mới.

Intaaneto **không thuộc cấp độ này**. Đây cũng không phải hướng hợp lý với tài
nguyên của một đồ án E-learning, vì huấn luyện LLM hoặc embedding model tốt từ
đầu đòi hỏi dữ liệu, GPU, thời gian và kinh phí rất lớn.

### 2.2. Fine-tuning mô hình có sẵn

Nhóm lấy pretrained model và tiếp tục huấn luyện trên dữ liệu riêng. Khi đó cần:

- training/validation/test split;
- dữ liệu gán nhãn hoặc instruction-response;
- quản lý checkpoint;
- theo dõi loss, overfitting và generalization;
- so sánh model trước/sau fine-tuning.

Intaaneto hiện **chưa fine-tune** embedding model hoặc generation model. Do đó
không nên viết trong báo cáo rằng nhóm “đã huấn luyện AI Tutor”.

### 2.3. Xây dựng hệ thống ML bằng pretrained model

Nhóm dùng model đã huấn luyện, nhưng tự xây pipeline dữ liệu, retrieval,
orchestration, evaluation, quyền truy cập và trải nghiệm người dùng. Đây chính là
nhóm phù hợp nhất với Intaaneto.

Project đang dùng:

- pretrained multilingual embedding model qua FastEmbed;
- pretrained LLM từ OpenAI, Gemini hoặc Groq;
- PostgreSQL + pgvector để lưu và truy vấn vector;
- logic Django tự kiểm soát source, version, quyền, citation và fallback;
- Celery/Redis để xử lý ingestion và multimedia ngoài request.

### 2.4. Tích hợp API AI đơn thuần

Một ứng dụng chỉ gửi câu hỏi thẳng đến chatbot API rồi hiện câu trả lời cũng có
thể được gọi là “AI-enabled”, nhưng đóng góp ML/RAG khá mỏng. Intaaneto đã vượt
qua mức này vì có knowledge ingestion, vector retrieval, evidence gate, citation,
authorization và evaluation riêng.

## 3. Cách gọi đề tài cho chính xác

### Cách mô tả nên dùng

> “Nghiên cứu và xây dựng hệ thống E-learning tích hợp AI Tutor dựa trên kỹ
> thuật Retrieval-Augmented Generation, sử dụng mô hình embedding và mô hình
> ngôn ngữ tiền huấn luyện.”

Hoặc chi tiết hơn:

> “Đề tài nghiên cứu pipeline xử lý học liệu, truy xuất ngữ nghĩa có kiểm soát
> quyền, sinh câu trả lời có căn cứ và đánh giá mức độ phù hợp của RAG trong môi
> trường E-learning tiếng Việt.”

### Cách mô tả không nên dùng

- “Nhóm tự xây dựng và huấn luyện một mô hình ngôn ngữ mới.”
- “Nhóm train AI Tutor bằng các file PDF.”
- “Đưa PDF vào vector database tức là đã train model.”
- “RAG similarity là độ chính xác của model.”
- “Dùng LangChain thì mới được gọi là RAG.”

PDF trong project được **index thành knowledge base**, không được dùng để cập
nhật trọng số model. Đây là khác biệt quan trọng giữa RAG và training.

## 4. Vì sao dữ liệu vẫn là phần quan trọng nhất?

Dù không train model, chất lượng hệ thống vẫn phụ thuộc rất mạnh vào dữ liệu.
Trong RAG có nguyên lý đơn giản:

```text
Học liệu sai hoặc xử lý tệ
→ chunk sai hoặc thiếu ngữ cảnh
→ retrieval lấy sai bằng chứng
→ LLM nhận sai context
→ câu trả lời cuối khó đúng
```

LLM mạnh không thể sửa một knowledge base thiếu, lỗi hoặc không đúng phạm vi.
Ngược lại, một pipeline dữ liệu tốt giúp model vừa phải vẫn đưa ra câu trả lời
ổn định hơn.

### 4.1. Không phải mọi dữ liệu đều là training data

Intaaneto có ít nhất năm nhóm dữ liệu khác nhau:

| Nhóm dữ liệu | Ví dụ | Dùng để làm gì | Có train model không? |
|---|---|---|---|
| Học liệu nguồn | PDF, lesson content | Nội dung được giảng viên phê duyệt | Không |
| Knowledge base | normalized text, chunk, embedding, page range | Retrieval lúc learner hỏi | Không |
| Evaluation dataset | question, expected status/source marker | Đo RAG | Không |
| Assessment data | question, choice, answer key, objective | Chấm điểm deterministic | Không |
| Dữ liệu vận hành | attempt, latency, selected chunk ID | Báo cáo, quan sát, audit | Không mặc định |

Nếu sau này nhóm fine-tune model thì phải tạo thêm **training dataset** và tách
validation/test độc lập. Không được tự động lấy chat hoặc câu trả lời learner để
train nếu chưa có consent, làm sạch dữ liệu và protocol nghiên cứu.

### 4.2. Học liệu nguồn cần chất lượng gì?

Một PDF tốt cho RAG nên:

- đúng giáo trình và được teacher-owner phê duyệt;
- có text đọc được, không chỉ là ảnh scan kém chất lượng;
- có cấu trúc heading, paragraph và page rõ;
- không chứa answer key hoặc hidden tests không dành cho learner;
- có version/provenance;
- không trộn nhiều môn không liên quan vào một lesson;
- được cập nhật hoặc vô hiệu hóa khi nội dung thay đổi.

### 4.3. Evaluation data còn quan trọng hơn việc “demo thấy trả lời được”

Hỏi thử vài câu rồi thấy chatbot trả lời hay không chứng minh RAG tốt. Bộ đánh
giá cần chứa:

- câu answerable có vị trí bằng chứng mong đợi;
- câu unsupported để đo khả năng từ chối;
- câu mơ hồ;
- câu paraphrase không lặp nguyên từ tài liệu;
- câu có nhiều bằng chứng;
- prompt injection nằm trong document;
- câu cố hỏi lesson/course khác;
- câu dài, nhiễu hoặc có lỗi tiếng Việt;
- nhiều lesson và nhiều môn học;
- development set và holdout set tách biệt.

Hiện Intaaneto đã có baseline tám case trên một lesson demo. Đây là nền móng tốt
cho reproducibility, nhưng chưa đủ để tuyên bố chất lượng tổng quát.

## 5. Harness trong project là gì?

### 5.1. Định nghĩa dễ hiểu

**Evaluation harness** là bộ khung chạy và chấm thí nghiệm một cách lặp lại. Nó
không phải model, không phải vector database và cũng không phải dataset.

Hình dung như sau:

| Thành phần | Ví dụ đời thường |
|---|---|
| Dataset | đề thi và đáp án/kỳ vọng |
| RAG pipeline | thí sinh được kiểm tra |
| Harness | phòng thi + người phát đề + máy chấm |
| Metrics/report | bảng điểm và biên bản kết quả |

### 5.2. Harness của Intaaneto đang làm gì?

```text
Đọc evaluation dataset có version
→ kiểm tra actor có quyền lesson
→ chạy từng câu qua retrieval hoặc full RAG
→ thu status, source/chunk, citation, latency, token
→ so với expected result
→ tổng hợp metric
→ xuất report không làm lộ raw content mặc định
```

Hai command tiêu biểu:

- `evaluate_rag_retrieval`: chỉ đo retrieval, không gọi LLM;
- `evaluate_rag_answers`: đo toàn pipeline retrieval → generation → citation.

Tách hai harness này rất quan trọng. Nếu answer cuối sai, nhóm có thể xác định:

- retrieval không tìm thấy evidence;
- threshold từ chối evidence đúng;
- generation diễn giải sai evidence;
- citation contract bị lỗi;
- provider timeout hoặc malformed output.

### 5.3. Harness hiện đo được gì?

- status/pass theo expected answerability;
- expected-source recall;
- grounded/fallback contract;
- citation có thuộc retrieval scope;
- refusal đối với câu unsupported;
- lexical marker proxy;
- latency;
- reported token của provider.

Nó chưa tự động đo đầy đủ semantic correctness hay chất lượng sư phạm. Hai phần
này cần reviewer con người và rubric. Project đã có seam xuất phiếu hai người
chấm và tổng hợp agreement, nhưng chưa có đủ rating để tuyên bố kết quả.

### 5.4. Vì sao harness là đóng góp đáng kể?

Không có harness, mỗi lần đổi threshold/model/chunk size nhóm chỉ có cảm giác
“có vẻ tốt hơn”. Có harness, nhóm có thể tạo bảng thực nghiệm:

| Cấu hình | Recall@k | Refusal | Citation | Latency | Human score |
|---|---:|---:|---:|---:|---:|
| Model A, threshold 0,45 | ... | ... | ... | ... | ... |
| Model A, threshold 0,40 | ... | ... | ... | ... | ... |
| Model B, threshold 0,45 | ... | ... | ... | ... | ... |

Đó chính là cách biến một project tích hợp thành bài nghiên cứu có thể kiểm chứng.

## 6. RAG của Intaaneto thực sự đang làm gì?

### 6.1. Pha ingestion/indexing

```text
Teacher-owner upload PDF
→ backend kiểm tra quyền và file
→ tạo durable database job, trả HTTP 202
→ Celery worker kiểm tra lại quyền
→ parse PDF và giữ page marker
→ Unicode normalization và sanitization
→ deterministic chunking có overlap/page range
→ FastEmbed tạo vector 384 chiều
→ lưu KnowledgeSource + KnowledgeChunk vào PostgreSQL/pgvector
→ atomic activation source version hoàn chỉnh
```

Các thuộc tính quan trọng:

- PDF-only với size/page/text bounds;
- indexing tách khỏi chat request;
- checksum và source version;
- reprocess không tạo duplicate;
- source mới chỉ active khi tất cả chunk sẵn sàng;
- source cũ/stale không tham gia retrieval;
- worker reauthorize thay vì tin quyền tại thời điểm enqueue.

### 6.2. Pha query/retrieval/answering

```text
Actor + lesson_id + question
→ backend resolve enrollment/teacher ownership
→ chọn compatible active source trong lesson đã authorize
→ embed câu hỏi
→ exact cosine search bằng pgvector trong source đó
→ top-k + minimum evidence threshold
→ weak/not-indexed: fallback, không gọi LLM
→ ready: gửi bounded evidence cho provider
→ application dựng citation từ selected database chunks
→ lưu retrieval metadata giới hạn
→ UI hiện grounded/fallback và source excerpt
```

### 6.3. Stack hiện tại thay thế vai trò Qdrant/LangChain như thế nào?

| Nhu cầu | Intaaneto đang dùng |
|---|---|
| Vector storage/search | PostgreSQL + pgvector |
| Relational metadata | PostgreSQL + Django ORM |
| File storage | local hoặc private Cloudflare R2 |
| Embedding | FastEmbed adapter |
| Generation | OpenAI/Gemini/Groq provider adapters |
| Chunking/indexing | `ai_assistant.rag_services` và ingestion services |
| Orchestration | Django service functions/classes rõ ràng |
| Background processing | Celery + Redis + durable DB jobs |
| Authorization | Django querysets/access services |
| Citation | application code từ retrieved chunks |
| Evaluation | Django management commands + versioned fixtures |

Như vậy project không “làm RAG bằng tay từ số 0”. Nó tái sử dụng các primitive
và thư viện có sẵn, nhưng giữ orchestration nghiệp vụ ở code của project.

## 7. Qdrant là gì?

Qdrant là một **vector database/vector search engine chuyên dụng**. Dữ liệu được
tổ chức thành collection; mỗi point có vector và payload metadata. Qdrant hỗ trợ
dense/sparse/named vectors, filtering, payload indexes, HNSW approximate search,
quantization, sharding và deployment phân tán. Xem [Qdrant Overview](https://qdrant.tech/documentation/overview/)
và [Qdrant Filtering](https://qdrant.tech/documentation/search/filtering/).

### 7.1. Qdrant giải quyết phần nào của RAG?

Nó chủ yếu giải quyết:

- lưu vector;
- tìm nearest neighbors;
- lọc bằng payload;
- ANN/HNSW cho tập vector lớn;
- dense/sparse/hybrid retrieval;
- quantization để giảm memory;
- scale/shard/replicate vector workload.

Qdrant **không tự động giải quyết toàn bộ RAG**. Nhóm vẫn phải xử lý:

- ai được đọc lesson nào;
- PDF validation/extraction;
- chunking và source version;
- stale-source activation;
- prompt policy;
- citation ownership;
- score/progression;
- evaluation và human review.

### 7.2. Qdrant khác pgvector ra sao?

| Tiêu chí | PostgreSQL + pgvector | Qdrant |
|---|---|---|
| Bản chất | DB quan hệ có kiểu/index vector | Vector database chuyên dụng |
| Metadata nghiệp vụ | Rất mạnh, JOIN/constraint/transaction | Payload/filter tốt nhưng không thay toàn bộ relational DB |
| Hạ tầng | Tận dụng PostgreSQL sẵn có | Thêm service/cluster riêng |
| Transaction với lesson/source | Thuận lợi trong một DB | Cần đồng bộ giữa Django DB và Qdrant |
| Search quy mô nhỏ | Exact search đơn giản, dễ kiểm chứng | Làm được nhưng có thể dư hạ tầng |
| Search quy mô lớn | Cần index/tuning; có giới hạn tùy workload | HNSW, quantization, shard là thế mạnh |
| Hybrid/multi-vector nâng cao | Có thể làm nhưng cần extension/query design | Là năng lực trọng tâm của sản phẩm |
| Operational burden | Thấp hơn khi đã dùng PostgreSQL | Thêm backup, monitoring, auth, migration, consistency |

Theo tài liệu Qdrant, collection chứa point gồm vector và payload; payload có thể
dùng để filter. Qdrant dùng HNSW cho dense vector index và có filterable HNSW
cho truy vấn kết hợp điều kiện với similarity search. Xem [Qdrant Collections](https://qdrant.tech/documentation/manage-data/collections/)
và [Qdrant Indexing](https://qdrant.tech/documentation/manage-data/indexing/).

### 7.3. Vì sao Intaaneto chưa cần Qdrant?

Hiện retrieval scope chủ yếu là một lesson và corpus còn nhỏ. Exact cosine bên
trong một active source có các lợi thế:

- dễ hiểu và dễ chứng minh trong báo cáo;
- không có ANN approximation làm nhiễu baseline;
- authorization filter và vector ranking cùng nằm trong database query;
- transaction source/chunk/version nằm cùng course/lesson metadata;
- không phải đồng bộ hai data store;
- ít service hơn trong Docker/deployment;
- nhóm tập trung vào chất lượng dữ liệu/evaluation thay vì vận hành thêm cluster.

Đây là nguyên tắc “chọn thành phần đơn giản nhất đáp ứng yêu cầu hiện tại”. Không
phải Qdrant kém, mà vì chưa có bằng chứng cho thấy pgvector là bottleneck.

### 7.4. Khi nào nên cân nhắc Qdrant?

Nên chạy benchmark hoặc PoC Qdrant khi xuất hiện một hoặc nhiều dấu hiệu:

- corpus tăng lên hàng trăm nghìn hoặc hàng triệu chunk;
- course-wide/global retrieval khiến exact scan chậm;
- p95 latency không đạt mục tiêu dù đã index/tune PostgreSQL;
- cần hybrid dense+sparse hoặc multivector phức tạp;
- cần quantization để giảm RAM;
- vector workload cần scale độc lập với relational workload;
- cần sharding/replication chuyên biệt;
- benchmark trên dữ liệu thật chứng minh Qdrant cải thiện đáng kể.

Trước khi chuyển, phải đo recall/latency/cost và thiết kế consistency giữa
PostgreSQL với Qdrant. Tuyệt đối không đổi chỉ vì tutorial phổ biến dùng Qdrant.

## 8. LangChain là gì?

LangChain là một **framework mã nguồn mở để xây ứng dụng dùng LLM**, cung cấp
model/tool integrations và các abstraction cho retrieval, chains, agents và
orchestration. Tài liệu hiện tại nhấn mạnh LangChain cho việc khởi tạo nhanh ứng
dụng/agent, còn LangGraph là runtime mức thấp hơn cho workflow tùy biến. Xem
[LangChain Overview](https://docs.langchain.com/oss/python/langchain/overview)
và [LangChain Retrieval](https://docs.langchain.com/oss/python/langchain/retrieval).

### 8.1. LangChain có phải model không?

Không. LangChain:

- không phải LLM;
- không phải embedding model;
- không phải vector database;
- không tự làm dữ liệu tốt lên;
- không tự bảo đảm authorization hoặc citation đúng.

Nó là lớp kết nối/orchestration để gọi các model, retriever, prompt, tool và
workflow theo interface chung.

### 8.2. LangChain có thể giúp gì cho một project RAG?

- document loaders và text splitters có sẵn;
- wrapper cho nhiều embedding/model provider;
- vector-store integrations;
- retriever và reranker composition;
- prompt templates và output parsers;
- tracing/evaluation integrations;
- agent/tool orchestration;
- streaming và workflow primitives.

Nó đặc biệt hữu ích khi cần thử nhiều provider/integration rất nhanh hoặc xây
agent có nhiều tool và nhánh điều khiển.

### 8.3. Chi phí của LangChain

- thêm abstraction cần học và debug;
- dependency/API có thể thay đổi theo phiên bản;
- stack trace và data flow khó đọc hơn pipeline nhỏ;
- dễ vô tình dùng default không phù hợp;
- authorization nghiệp vụ vẫn phải tự viết;
- citation từ model vẫn phải kiểm chứng;
- khó chứng minh chính xác layer nào chịu trách nhiệm nếu lạm dụng chain/agent;
- có nguy cơ biến một luồng deterministic thành agentic không cần thiết.

Với E-learning, “model tự quyết định lúc nào dùng tool nào” không mặc nhiên tốt
hơn pipeline cố định. Đối với quyền lesson, answer key và progression, workflow
deterministic thường dễ kiểm thử và an toàn hơn.

## 9. Vì sao Intaaneto không dùng LangChain?

RAG hiện tại là một pipeline 2-step khá rõ:

```text
authorize → retrieve → evidence gate → generate → application citation
```

Project cần kiểm soát chặt:

- authorization phải xảy ra trước embedding/search/provider;
- source version phải active/compatible;
- weak evidence phải skip generation;
- citation phải đến từ selected database records;
- answer key/hidden test không được vào prompt;
- audit không được lưu raw data tùy tiện.

Các yêu cầu này được biểu diễn trực tiếp bằng Django services và tests. Thêm
LangChain lúc này chưa chứng minh sẽ giảm độ phức tạp; ngược lại có thể tạo thêm
một lớp abstraction giữa business rule và code thực thi.

Repository cũng đã đặt nguyên tắc: không thêm framework như LangChain nếu nó
không loại bỏ một độ phức tạp đã được chứng minh. Một pipeline nhỏ, explicit
được ưu tiên cho RAG MVP.

### Khi nào LangChain có thể đáng dùng?

- cần thử nhanh nhiều retriever/reranker có integration sẵn;
- cần agent sử dụng nhiều tool thật sự, không chỉ retrieval một lần;
- cần workflow graph có branching, checkpoint và human approval phức tạp;
- provider adapters tự viết trở nên quá nhiều và khó bảo trì;
- tracing/evaluation integration mang lại lợi ích đo được;
- một PoC chứng minh giảm code/bug mà không làm yếu security boundary.

Nếu thử LangChain, nên đặt nó **sau lớp authorization của project**, giữ citation
validation và progression trong application code, đồng thời pin version và có
contract tests. Không nên để framework tự quyết định lesson scope.

## 10. “Sao không dùng những thứ có sẵn?” — câu trả lời thẳng

### 10.1. Project đã dùng rất nhiều thứ có sẵn

- Django và Django REST Framework;
- PostgreSQL và pgvector;
- FastEmbed và pretrained embedding model;
- OpenAI-compatible SDK/provider APIs;
- Celery và Redis;
- PDF parser;
- Cloudflare R2/S3 storage adapter;
- Piper, Pillow và FFmpeg;
- React, Vite và Tailwind.

Nhóm không tự viết database, vector math engine, neural network, task queue hay
video codec. Nhóm tự viết phần tạo nên **đặc trưng và ranh giới của đề tài**:

- lesson/course authorization;
- source version và atomic activation;
- cách nối chunk với PDF page;
- evidence threshold và fallback;
- citation membership;
- assessment/progression policy;
- audit/privacy contract;
- evaluation harness.

### 10.2. “Dùng sẵn” và “tự kiểm soát” không đối lập

Kiến trúc tốt thường gồm:

```text
Primitive có sẵn, đã được kiểm chứng
+ lớp orchestration nghiệp vụ mỏng của project
+ test/evaluation cho yêu cầu riêng
```

Nếu tự viết mọi thứ, project tốn thời gian và tăng bug. Nếu giao mọi thứ cho
framework, project có thể mất quyền kiểm soát và khó giải thích đóng góp. Lựa
chọn hiện tại nằm giữa hai cực đó.

### 10.3. Dùng nhiều công nghệ hơn không đồng nghĩa RAG tốt hơn

Một stack có LangChain + Qdrant vẫn có thể:

- chunk tài liệu kém;
- retrieve chéo course;
- không có fallback;
- để LLM bịa citation;
- không version source;
- không có evaluation dataset;
- không đo semantic quality.

Ngược lại, stack Django + pgvector nhỏ nhưng có scope, citation và evaluation
rõ ràng có thể đáng tin cậy hơn cho corpus hiện tại.

## 11. So sánh ba kiến trúc

### Phương án A — Intaaneto hiện tại

```text
Django services + PostgreSQL/pgvector + FastEmbed + provider adapters
```

Phù hợp khi:

- corpus nhỏ đến vừa;
- lesson-scoped retrieval;
- business rules/authorization phức tạp;
- cần transaction và explainability;
- nhóm nhỏ, muốn ít hạ tầng.

### Phương án B — Django + Qdrant

```text
Django/PostgreSQL lưu nghiệp vụ
Qdrant lưu vector/payload
custom services orchestration
```

Phù hợp khi vector search trở thành bottleneck hoặc cần tính năng vector nâng
cao. Đổi lại phải xử lý dual-write, synchronization, backup và consistency.

### Phương án C — Django + LangChain + Qdrant

```text
Django giữ product/security
LangChain orchestration/integrations
Qdrant vector search
```

Phù hợp khi workflow/integrations đủ phức tạp để hai dependency này thực sự giảm
code. Không phù hợp nếu chỉ để giống tutorial hoặc CV có nhiều keyword hơn.

## 12. Lựa chọn hiện tại có hạn chế gì?

Cần thừa nhận công bằng các hạn chế của pgvector + custom pipeline:

- exact cosine sẽ không scale vô hạn;
- chưa có ANN index trong retrieval path hiện tại;
- chưa có sparse/dense hybrid retrieval;
- chưa có reranker;
- integration mới phải tự viết adapter;
- team tự chịu trách nhiệm bảo trì orchestration và evaluation;
- chưa có tracing UI phong phú như một số ecosystem framework;
- code custom có thể tích tụ nếu scope mở rộng quá nhanh.

Những hạn chế này là lý do để benchmark và tiến hóa kiến trúc khi có dữ liệu,
không phải lý do đổi stack ngay lập tức.

## 13. Roadmap dữ liệu và RAG nên làm tiếp

### Ưu tiên 1 — Nâng evaluation dataset

- 5–10 lesson thuộc nhiều chủ đề;
- 80–150 câu hỏi;
- answerable/unsupported/ambiguous/adversarial;
- expected source/page do người soạn xác nhận;
- development/holdout split;
- ít nhất hai reviewer độc lập.

### Ưu tiên 2 — Đặt research question rõ

Ví dụ:

> “Chunk size, overlap và evidence threshold ảnh hưởng thế nào đến recall,
> refusal accuracy và latency của RAG tiếng Việt trên học liệu E-learning?”

Hoặc:

> “Authorization-first lesson-scoped retrieval có đảm bảo citation isolation
> mà không làm giảm retrieval quality trong corpus nhiều khóa học hay không?”

### Ưu tiên 3 — Chạy ablation/benchmark

So sánh có kiểm soát:

- chunk size 600/1.000/1.400;
- overlap 10%/15%/20%;
- threshold 0,35/0,40/0,45;
- top-k 3/5/8;
- hai embedding model;
- exact pgvector với ANN/Qdrant chỉ khi corpus đủ lớn.

Mỗi lần chỉ thay một hoặc một nhóm biến có thiết kế; báo recall, refusal,
citation, latency và human score. Không chọn cấu hình vì một vài câu demo đẹp.

### Ưu tiên 4 — Quyết định Qdrant bằng benchmark

Tạo một spike độc lập, copy dataset không nhạy cảm sang Qdrant, giữ nguyên
embedding và expected cases, rồi đo:

- index time;
- storage/RAM;
- recall@k;
- p50/p95 latency;
- filtered-search correctness;
- độ phức tạp vận hành;
- effort đồng bộ source version.

Chỉ migrate nếu lợi ích thực vượt chi phí.

### Ưu tiên 5 — Quyết định LangChain bằng code delta

Chọn một vertical slice thử nghiệm, ví dụ retriever + reranker. So sánh:

- số dòng và độ rõ code;
- dependency footprint;
- error handling;
- testability;
- authorization/citation preservation;
- latency;
- khả năng pin/reproduce.

Nếu không giảm complexity đã đo, không đưa vào core.

## 14. Cách trả lời khi giảng viên hỏi

### “Các em có làm machine learning không?”

> “Dạ có, theo hướng ứng dụng và đánh giá các mô hình tiền huấn luyện. Nhóm không
> huấn luyện LLM từ đầu. Đóng góp của nhóm là pipeline dữ liệu học liệu, RAG có
> phân quyền, grounded answer/citation, assessment integration và evaluation
> harness cho dữ liệu tiếng Việt.”

### “Dữ liệu của đề tài nằm ở đâu?”

> “Dữ liệu gồm học liệu PDF đã được giảng viên phê duyệt, knowledge chunks có vị
> trí trang, bộ câu hỏi đánh giá RAG có expected source, assessment theo learning
> objective và dữ liệu attempt/audit tối thiểu. Nhóm phân biệt rõ knowledge base,
> evaluation dataset và training dataset; hiện chưa fine-tune nên không gọi PDF
> là training data.”

### “Sao không dùng LangChain?”

> “Luồng RAG hiện tại nhỏ và deterministic nên nhóm dùng Django service trực
> tiếp để kiểm soát authorization, source version, fallback và citation. Nhóm vẫn
> dùng các thư viện/model có sẵn. LangChain chỉ được cân nhắc nếu benchmark hoặc
> code spike chứng minh nó giảm complexity mà không làm yếu security boundary.”

### “Sao không dùng Qdrant?”

> “Project đã dùng PostgreSQL nên pgvector cho phép giữ lesson/source/version và
> vector trong cùng transaction. Corpus hiện nhỏ và retrieval theo một lesson,
> exact cosine dễ kiểm chứng. Qdrant sẽ đáng cân nhắc khi corpus lớn, cần ANN,
> hybrid search hoặc scale vector độc lập, sau một benchmark trên dữ liệu thật.”

### “Điểm mới của đề tài là gì nếu dùng model có sẵn?”

> “Điểm mới không nhất thiết là tạo model nền tảng. Đề tài nghiên cứu cách đưa
> pretrained model vào môi trường E-learning an toàn và có thể kiểm chứng: học
> liệu được version hóa, retrieval theo quyền, citation từ evidence thật,
> unsupported fallback, assessment/progression không giao cho LLM và protocol
> đánh giá RAG tiếng Việt.”

## 15. Kết luận cuối cùng

Intaaneto là **applied AI/ML system**, không phải project train model từ đầu. Với
project này, “làm dữ liệu” có ba công việc lớn:

1. làm sạch và version hóa học liệu để tạo knowledge base;
2. xây evaluation dataset có nhãn để đo retrieval/answer;
3. thu thập dữ liệu nghiên cứu có consent và protocol để đánh giá tác động.

Qdrant và LangChain là công cụ hữu ích nhưng thuộc hai lớp khác nhau: Qdrant là
vector database/search engine, LangChain là framework orchestration/integration.
Không công cụ nào là điều kiện bắt buộc để được gọi là RAG.

RAG hiện tại của Intaaneto dùng pgvector, FastEmbed, provider adapters và Django
services. Lựa chọn này hợp lý với corpus nhỏ, lesson-scoped retrieval và yêu cầu
authorization/transaction chặt. Điều đúng đắn tiếp theo không phải thêm công nghệ
theo xu hướng, mà là **mở rộng dữ liệu đánh giá, chạy human review và benchmark
có kiểm soát**. Khi số liệu cho thấy bottleneck, nhóm mới đưa Qdrant, LangChain,
reranker hoặc hybrid retrieval vào bằng một quyết định kiến trúc có bằng chứng.

## Tài liệu tham khảo

- [Qdrant Documentation — Overview](https://qdrant.tech/documentation/overview/)
- [Qdrant Documentation — Collections](https://qdrant.tech/documentation/manage-data/collections/)
- [Qdrant Documentation — Filtering](https://qdrant.tech/documentation/search/filtering/)
- [Qdrant Documentation — Indexing](https://qdrant.tech/documentation/manage-data/indexing/)
- [LangChain Documentation — Overview](https://docs.langchain.com/oss/python/langchain/overview)
- [LangChain Documentation — Retrieval](https://docs.langchain.com/oss/python/langchain/retrieval)
- `.ai/skills/intaaneto-rag/references/project-scope.md`
- `.ai/skills/intaaneto-rag/references/architecture.md`
- `.ai/skills/intaaneto-rag/references/delivery-plan.md`
- `backend/apps/ai_assistant/rag_services.py`
- `backend/apps/ai_assistant/rag_answering.py`
- `backend/apps/ai_assistant/rag_evaluation.py`
- `docs/RAG_RETRIEVAL_BASELINE_V1.md`
- `docs/RAG_GROUNDED_ANSWER_BASELINE_V1.md`
