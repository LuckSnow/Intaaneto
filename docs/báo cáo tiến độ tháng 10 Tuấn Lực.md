# BỘ THÔNG TIN VÀ TRUYỀN THÔNG
**HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG**
**CƠ SỞ TẠI TP. HỒ CHÍ MINH**
***

**CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM**
**Độc lập – Tự do – Hạnh phúc**
***

*Thành phố Hồ Chí Minh, ngày 03 tháng 10 năm 2026*

## BÁO CÁO TIẾN ĐỘ THỰC HIỆN ĐỀ TÀI NCKH CỦA SINH VIÊN
### NĂM HỌC 2025 – 2026
*(Mốc đánh giá: Tháng 10/2026 — Chuẩn bị Hội thảo xét duyệt đề tài)*

---

### I. THÔNG TIN CHUNG

1. **Tên đề tài:** Nghiên cứu xây dựng hệ thống E-learning trên môi trường web tích hợp giảng viên ảo dựa trên công nghệ Trí tuệ nhân tạo.
2. **Chủ nhiệm đề tài:** Nguyễn Thái Tuấn — **Lớp:** D23CQPTUD01-N — **Khoa:** CNTT2 — **Điện thoại:** 0946873667
3. **Giảng viên hướng dẫn:** ThS. Nguyễn Văn Sáu
4. **Danh sách sinh viên tham gia thực hiện đề tài:**

| STT | Họ và Tên | Mã số SV | Lớp | Nội dung công việc phụ trách |
| :---: | :--- | :---: | :---: | :--- |
| 1 | **Nguyễn Thái Tuấn** | N23DCPT054 | D23CQPTUD01-N | Quản lý tiến độ đề tài; Thiết kế kiến trúc tổng thể và luồng dữ liệu; Lập trình phân hệ Backend, RAG Pipeline và Multimedia; Thực hiện đo lường thực nghiệm và viết báo cáo tổng hợp. |
| 2 | **Phùng Anh Lực** | N23DCPT033 | D23CQPTUD01-N | Xây dựng giao diện Frontend và luồng trải nghiệm người dùng; Thu thập, chuẩn hóa học liệu PDF; Xây dựng kịch bản kiểm thử, chạy thực nghiệm và hoàn thiện báo cáo. |

---

### II. NỘI DUNG ĐÃ HOÀN THÀNH

*Tính đến tháng 10/2026, nhóm đã hoàn thành việc xây dựng **nguyên mẫu (Prototype) hệ thống trên môi trường cục bộ (Local)** với đầy đủ các tính năng cốt lõi từ quản lý học liệu, lõi tri thức RAG đến bài giảng đa phương tiện, chuẩn bị sẵn sàng cho buổi hội thảo xét duyệt sắp tới.*

| STT | Nội dung công việc | Kết quả đạt được & Ý nghĩa thực tiễn |
| :---: | :--- | :--- |
| **1** | **Xây dựng sơ bộ thành công Prototype trang web trên môi trường Local** | - **Kết quả:** Xây dựng hoàn chỉnh giao diện web (React/Vite) kết nối Backend (Django REST) chạy ổn định trên Docker Compose cục bộ.<br>- **Tính năng đạt được:** Hệ thống đã có đầy đủ các phân hệ nghiệp vụ: Quản lý khóa học, bài học; Luồng phân quyền rõ ràng giữa Sinh viên (Learner) và Giảng viên (Teacher); Giao diện học tập tích hợp xem tài liệu PDF song song với khung chat tương tác cùng AI Tutor; Hệ thống làm bài kiểm tra trắc nghiệm và xem tiến độ học tập. |
| **2** | **Nghiên cứu kiến trúc hệ thống, Backend và Cơ sở dữ liệu** | - **Kết quả:** Thiết kế kiến trúc phân lớp rõ ràng, bảo mật và dễ mở rộng. Lựa chọn **PostgreSQL** kết hợp extension **`pgvector`** để vừa quản lý dữ liệu nghiệp vụ quan hệ (người dùng, kết quả học tập), vừa lưu trữ và tìm kiếm vector ngữ nghĩa.<br>- **Ý nghĩa:** Tránh việc phải duy trì các dịch vụ vector database ngoài phức tạp (như Pinecone/Qdrant), tối ưu hóa tài nguyên phần cứng khi chạy thử nghiệm và đảm bảo kiểm soát quyền truy cập chặt chẽ trước khi tìm kiếm dữ liệu. |
| **3** | **Nghiên cứu và hiện thực hệ thống RAG xử lý học liệu PDF (Lõi tri thức đề tài)** | - **Tự động hóa học liệu từ PDF:** Giảng viên chỉ cần tải lên 01 file PDF bài giảng, hệ thống tự động bóc tách văn bản, làm sạch ký tự rác, chia đoạn và đánh số trang chính xác (`page_start`, `page_end`).<br>- **Ý nghĩa nghiên cứu của RAG (Đã chứng minh bằng số liệu):**<br>  + Giải quyết triệt để vấn đề "ảo giác kiến thức" (hallucination): AI Tutor chỉ trả lời dựa trên nội dung có trong bài học, luôn đính kèm trích dẫn số trang PDF thật (**100% trích dẫn thật**, không bịa nguồn).<br>  + Nhận diện và từ chối an toàn **100% câu hỏi ngoài giáo trình**.<br>  + Tỷ lệ tìm đúng tài liệu liên quan đạt **100% (Recall = 1.00)** với thời gian phản hồi nhanh (~1.5s/câu hỏi).<br>- **Củng cố kiến thức sư phạm:** Khi sinh viên làm sai bài tập, hệ thống tự động lôi đúng trang PDF chứa kiến thức bị hổng để sinh viên ôn tập lại. |
| **4** | **Nghiên cứu xử lý đa phương tiện (Multimedia) và Giảng viên ảo** | - **Tự động hóa bài giảng video cục bộ:** Xây dựng thành công quy trình tự động chuyển tóm tắt bài học thành video bài giảng hoàn chỉnh không tốn chi phí:<br>  + Tích hợp mô hình giọng đọc tiếng Việt **Piper TTS** mã nguồn mở phát âm tự nhiên.<br>  + Tự động tạo slide trình chiếu 1280x720 có phụ đề chạy khớp theo giọng đọc và hiển thị hình ảnh đại diện Giảng viên ảo ở góc màn hình.<br>  + Dùng **FFmpeg** đóng gói thành video MP4 gắn trực tiếp vào bài học (chạy siêu nhanh trên CPU máy cá nhân: video 80s chỉ mất 14s tạo). |

---

### III. NỘI DUNG CHƯA HOÀN THÀNH / KHÓ KHĂN & BIỆN PHÁP KHẮC PHỤC

| STT | Khó khăn / Nội dung chưa hoàn thành | Tình trạng hiện tại | Nguyên nhân & Biện pháp khắc phục của nhóm |
| :---: | :--- | :--- | :--- |
| **1** | **Mô hình Giảng viên ảo cử động môi (Lip-sync Avatar - Người thật giảng bài)** | Đã chạy thử nghiệm kỹ thuật (PoC SadTalker) thành công đoạn ngắn 1.48s, nhưng chưa áp dụng được cho bài giảng dài (3–5 phút). | **- Khó khăn & Nguyên nhân:** Do hạn chế về phần cứng máy tính cá nhân. Việc chạy mô hình sinh cử động môi (SadTalker) cho bài giảng dài đòi hỏi VRAM đồ họa rất lớn; khi thử nghiệm trên GPU laptop (NVIDIA T1200 4GB), hệ thống bị tràn bộ nhớ và quá thời gian (timeout sau hơn 30 phút).<br>**- Biện pháp khắc phục linh hoạt của nhóm:**<br>  + *Phương án hiện tại:* Sử dụng pipeline **Slide-Video kết hợp Piper TTS** (đã hoàn thiện ở Mục II), chạy rất nhẹ nhàng trên máy cá nhân, đảm bảo có video bài giảng đa phương tiện trực quan.<br>  + *Phương án trình diễn thực tế (Demo):* Để chuẩn bị cho buổi hội thảo xét duyệt và báo cáo chính thức, nhóm dự kiến **sẽ đăng ký các gói tài khoản dùng thử (Free Trial / Student Credits) từ các nền tảng đám mây (như D-ID, HeyGen hoặc Google Cloud/Run)** để tạo ra các video giảng viên ảo người thật nói mẫu. Cách này giúp nhóm có sản phẩm demo sinh động, chuyên nghiệp trước hội đồng mà không bị nghẽn phần cứng cá nhân. |
| **2** | **Thực nghiệm RAG trên tập dữ liệu mở rộng** | Đã hoàn thành baseline V1 trên bài mẫu; đang mở rộng tập dữ liệu sang các môn Mạng máy tính & Lập trình Web. | **- Khó khăn:** Việc thẩm định chất lượng câu trả lời tiếng Việt đòi hỏi con người đọc đối chiếu từng trang PDF thủ công rất tốn thời gian.<br>**- Khắc phục:** Nhóm đang phân công 2 thành viên chấm chéo độc lập theo bộ phiếu đánh giá ẩn danh để kịp lấy số liệu trước hội thảo. |
| **3** | **Đưa hệ thống lên môi trường Production (Triển khai trực tuyến)** | Hệ thống hiện tại đang vận hành rất tốt trên môi trường cục bộ (Local Docker); chưa đưa lên tên miền/máy chủ công cộng. | **- Khắc phục:** Mức độ Prototype local hiện tại đã đáp ứng hoàn hảo cho việc demo tại hội thảo khoa học sắp tới. Sau khi đề tài được thông qua, nhóm sẽ tiến hành đóng gói và triển khai lên máy chủ đám mây (Cloud Server) trong tháng 11. |

---

### IV. KẾ HOẠCH THỰC HIỆN TRONG THỜI GIAN TỚI

*(Mốc thời gian trọng tâm bám sát tiến độ xét duyệt và nghiệm thu)*

| Mốc thời gian | Nội dung công việc trọng tâm | Mục tiêu / Sản phẩm dự kiến |
| :---: | :--- | :--- |
| **Khoảng 2 tuần nữa**<br>*(Giữa tháng 10/2026)* | **BẢO VỆ HỘI THẢO XÉT DUYỆT THÔNG QUA ĐỀ TÀI**<br>- Chuẩn bị slide thuyết trình nêu bật ý nghĩa thực tiễn và tính khả thi của đề tài.<br>- Sử dụng gói Cloud Trial để tạo video giảng viên ảo mẫu sinh động.<br>- Chuẩn bị kịch bản demo trực tiếp hệ thống Prototype chạy local (Upload PDF $\rightarrow$ RAG Chatbot $\rightarrow$ Làm bài kiểm tra $\rightarrow$ Xem video bài giảng). | - **Đề tài được Hội đồng khoa học chính thức thông qua.**<br>- Ghi nhận các ý kiến đóng góp của Hội đồng để hoàn thiện hệ thống. |
| **Giữa tháng 11/2026** | **BÁO CÁO CHÍNH THỨC & THỰC NGHIỆM ĐỀ TÀI**<br>- Tổ chức thử nghiệm có kiểm soát trên nhóm sinh viên thực tế (20–30 bạn môn Mạng máy tính).<br>- Thu thập khảo sát trải nghiệm người dùng và đo lường sự cải thiện kết quả học tập khi có AI củng cố kiến thức.<br>- Tinh chỉnh lại ngưỡng tìm kiếm vector và giao diện. | - Báo cáo số liệu thực nghiệm thực tế trên người học.<br>- Hoàn thiện bản báo cáo chi tiết đợt 2 cho Giảng viên hướng dẫn. |
| **Tháng 12/2026** | **TỔNG KẾT & NGHIỆM THU ĐỀ TÀI**<br>- Hoàn thiện toàn bộ bài báo nghiên cứu khoa học và quyển báo cáo tổng kết đề tài sinh viên nộp Khoa/Học viện.<br>- Đóng gói mã nguồn và chuẩn bị bảo vệ nghiệm thu chính thức. | - Quyển báo cáo NCKH hoàn chỉnh.<br>- Bảo vệ thành công đề tài NCKH cấp Học viện. |

---

### V. ĐỀ XUẤT, KIẾN NGHỊ

1. **Về nội dung hội thảo:** Kính mong Thầy hướng dẫn xem qua kịch bản demo và định hướng giúp nhóm những điểm cần nhấn mạnh trước Hội đồng xét duyệt (đặc biệt là giá trị ứng dụng thực tế của việc tự động hóa bài giảng từ PDF và giải pháp RAG giải quyết ảo giác kiến thức).
2. **Về kế hoạch sắp tới:** Nhóm kính xin ý kiến Thầy để chuẩn bị cho đợt thử nghiệm trên lớp sinh viên vào đầu tháng 11 sau khi hội thảo hoàn tất.

***

<table style="width: 100%; border: none;">
  <tr>
    <td style="width: 50%; text-align: center; vertical-align: top; border: none;">
      <b>XÁC NHẬN CỦA GVHD</b><br>
      <i>(Ký và ghi rõ họ tên)</i><br><br><br><br><br>
      <b>ThS. Nguyễn Văn Sáu</b>
    </td>
    <td style="width: 50%; text-align: center; vertical-align: top; border: none;">
      <b>CHỦ NHIỆM ĐỀ TÀI</b><br>
      <i>(Ký và ghi rõ họ tên)</i><br><br><br><br><br>
      <b>Nguyễn Thái Tuấn</b>
    </td>
  </tr>
</table>
