# ĐẶC TẢ HỆ THỐNG: MULTIMEDIA AI ORCHESTRATION PIPELINE (MAOP)
## 1. GIỚI THIỆU TỔNG QUAN (INTRODUCTION)
Hệ thống nghiên cứu một quy trình tự động hóa (Pipeline) nhằm chuyển đổi dữ liệu phi cấu trúc (Unstructured Data) từ các tài liệu học thuật thành các thực thể đa phương tiện (Multimedia Entities). Mục tiêu cốt lõi là tối ưu hóa trải nghiệm người dùng thông qua mô hình tương tác giữa người và máy (Human-Computer Interaction - HCI) dựa trên trí tuệ nhân tạo.

## 2. KIẾN TRÚC HỆ THỐNG (SYSTEM ARCHITECTURE)
Hệ thống được thiết kế theo mô hình Sequential & Event-driven Orchestration, chia làm 4 phân lớp xử lý dữ liệu:

### 2.1. Tầng Trích xuất Tri thức (Knowledge Extraction Layer)
Lý thuyết: Sử dụng cơ chế In-context Learning của các mô hình ngôn ngữ lớn (LLM).

Thực thi: Tiếp nhận input PDF. Hệ thống thực hiện chuẩn hóa văn bản, sau đó sử dụng mô hình AI để phân tích cấu trúc.

Sản phẩm đầu ra: Một cấu trúc Semantically Structured JSON bao gồm: Key concepts, Script cho giảng viên ảo và kịch bản phân cảnh (Storyboarding).

### 2.2. Tầng Tổng hợp Thị giác (Visual Synthesis Layer)
Lý thuyết: Áp dụng nguyên lý thiết kế đồ họa tự động (Automated Graphic Design).

Thực thi: Sử dụng thư viện Pillow (PIL) để tạo tài nguyên hình ảnh khi cần.

Cơ chế: Map các "Key concepts" từ JSON vào các Template slide có sẵn. Tính toán bố cục (Layouting) và phối màu tự động dựa trên chủ đề của tài liệu đầu vào.

### 2.3. Tầng Sản xuất Video Đa hình thái (Multimodal Video Production)
Lý thuyết: Sử dụng công nghệ Lip-sync Synthesis và Neural Text-to-Speech (TTS).

Thực thi:

Audio: Chuyển đổi kịch bản thuyết trình thành giọng nói tự nhiên với cảm xúc phù hợp.

Video: Sử dụng các model như SadTalker hoặc Wav2Lip (được host trên Hugging Face) để điều khiển một Avatar AI thuyết trình dựa trên file Audio đã tạo.

### 2.4. Tầng Tương tác Thông minh (Orchestration & Agentic Layer)
Lý thuyết: Đây là lớp Orchestration, đóng vai trò "Nhạc trưởng" điều phối các Agent chuyên biệt.

Tính năng:

RAG (Retrieval-Augmented Generation): Khi người dùng đặt câu hỏi qua Mic/Chat, Agent sẽ truy vấn lại nội dung file gốc để trả lời chính xác, tránh hiện tượng "ảo giác" (Hallucination) của AI.

Context Management: Duy trì trạng thái hội thoại (State management) để đảm bảo AI hiểu các câu hỏi tiếp nối của người dùng.

## 3. CƠ SỞ KỸ THUẬT (TECHNICAL STACK)
Hệ thống được xây dựng trên nền tảng Python tập trung vào khả năng xử lý bất đồng bộ (Asynchronous):

Backend Core: Django Framework - Đảm bảo tính bảo mật và khả năng quản lý User/Media chuyên nghiệp cho NCKH.

Task Queue: Celery & Redis - Xử lý các tác vụ nặng (tạo video, render slide) ở chế độ chạy ngầm (Background tasks), tránh block request của người dùng.

AI Engine: GitHub Models (GPT-4o), Hugging Face Diffusers (Video/Image Generation).

Frontend: React hoặc Vue.js để tạo giao diện tương tác thời gian thực thông qua WebSockets.

## 4. QUY TRÌNH VẬN HÀNH (WORKFLOW)
Upload: User tải tài liệu lên hệ thống Django.

Analysis: Django trigger một Celery task để chạy LLM Pipeline.

Generation: Hệ thống song song tạo Slide và Video giảng viên ảo.

Deployment: Kết quả được lưu trữ vào Media Server và hiển thị lên giao diện tương tác.
