# Intaaneto Frontend Design Guide

Tài liệu này mô tả ngôn ngữ thiết kế đang được sử dụng trên frontend Intaaneto. Mục tiêu là giúp các trang mới đồng bộ với phần Khóa học, Dashboard, Profile, Forum và luồng xác thực hiện tại.

## 1. Định hướng chung

Intaaneto sử dụng phong cách E-learning hiện đại, học thuật và thân thiện. Giao diện ưu tiên nội dung, khả năng đọc và hành động chính của người dùng.

- Nền website tối, có các mảng blur đỏ rượu, nâu cam, xanh navy và đen.
- Màu cam là màu nhấn thương hiệu cho CTA, trạng thái active, link và focus.
- Nội dung chính sử dụng màu trắng hoặc gần trắng; nội dung phụ giảm opacity.
- Card tối hoặc trắng tùy ngữ cảnh, có border mờ và bo góc vừa phải.
- Hiệu ứng chỉ dùng nhẹ: hover, focus, shadow nhỏ và chuyển màu ngắn.
- Không dùng quá nhiều gradient, glow, badge nhiều màu hoặc card trang trí không cần thiết.

## 2. Background và nhận diện thương hiệu

Background chuẩn của website là:

```css
background-image: url('/images/background2.png');
background-size: cover;
background-position: center;
background-repeat: no-repeat;
```

Background cần phủ toàn bộ viewport bằng `min-height: 100vh`. Không tự tạo một background gần giống cho từng trang.

Logo chuẩn là asset:

```text
frontend/src/assets/images/logo-full.png
```

Không viết lại logo bằng text hoặc thay đổi tỷ lệ. Trong các trang xác thực, logo nằm trong khung nội dung ở góc trên bên phải. Trong layout chính, logo nằm trên navbar.

## 3. Bảng màu

| Vai trò | Màu tham khảo | Cách dùng |
| --- | --- | --- |
| Nền tối | `#0F172A`, `#111827` | Fallback khi ảnh nền chưa tải |
| Đỏ rượu | `#4A180B`, `#5A1F0D` | Màu nền sâu, mảng tối |
| Nâu cam | `#A93612`, `#B33A16` | Panel thương hiệu, khu vực giáo viên |
| Cam chính | `#F97316` | CTA, link, focus, active state |
| Cam sáng | `#FB923C` | Hover và điểm nhấn nhẹ |
| Trắng kem | `#FFF8EF` | Surface sáng, vùng minh họa |
| Text sáng | `#FFFFFF` | Tiêu đề trên nền tối |
| Text phụ sáng | `rgba(255,255,255,0.70)` | Mô tả và metadata |
| Text tối | `#0F172A`, `#1F2937` | Nội dung trên card trắng |
| Border tối | `rgba(255,255,255,0.15)` | Viền card/input trên nền tối |
| Border sáng | `#D8DEE8` | Viền input/card sáng |
| Thành công | `#047857` | Xác thực, hoàn thành |
| Nguy hiểm | `#B91C1C` | Lỗi hoặc hành động xóa |

Ưu tiên các utility Tailwind tương ứng như `orange-600`, `slate-950`, `white/70` và `border-white/15` thay vì rải thêm màu gần giống.

## 4. Typography

- Font chính: `Inter`, fallback `Nunito`, `system-ui`, `sans-serif`.
- Tiêu đề trang: font-weight `700`, thường từ `30px` đến `36px` trên desktop.
- Tiêu đề card: `18px` đến `24px`, font-weight `600` hoặc `700`.
- Nội dung: `14px` đến `16px`, line-height thoáng.
- Metadata: `12px` đến `14px`, dùng màu phụ.
- Không dùng quá nhiều cỡ chữ trên cùng một màn hình.
- Nội dung dài nên giới hạn chiều rộng đọc khoảng 65–75 ký tự mỗi dòng.

## 5. Spacing và bo góc

Spacing dựa trên nhịp 4px:

- Khoảng nhỏ: `8px`, `12px`.
- Khoảng giữa các nhóm: `16px`, `24px`.
- Khoảng giữa các section: `32px`, `48px`.
- Card ứng dụng: bo góc `12px` đến `16px`.
- Card xác thực hoặc container lớn: bo góc `24px` đến `32px`.
- Chip/tag: bo tròn hoàn toàn bằng `border-radius: 999px`.

Container chính thường dùng `max-w-7xl`, căn giữa và padding ngang responsive.

## 6. Card và surface

### Card tối

Phù hợp với Forum, lesson detail và nội dung trên background gốc:

```text
border border-white/10
bg-slate-950/45
rounded-2xl
backdrop-blur-md
```

Hover chỉ tăng nhẹ độ rõ của border hoặc background. Không thêm glow lớn.

### Card sáng

Phù hợp với Dashboard, Profile và form cần độ tương phản cao:

```text
bg-white hoặc bg-white/95
border border-slate-200
rounded-xl hoặc rounded-2xl
text-slate-950
```

Shadow cần nhẹ để không cạnh tranh với nội dung.

## 7. Input và form

- Luôn có label rõ ràng; placeholder không thay thế label.
- Chiều cao input và button tối thiểu `48px`.
- Input sáng dùng text tối, border `slate-300`.
- Input tối dùng nền trong suốt nhẹ, border `white/15` và text trắng.
- Focus dùng border/ring cam thương hiệu.
- Error đặt ngay dưới field, ngắn gọn và không làm thay đổi logic validation.
- Form chỉ giữ nội dung cần thiết cho tác vụ chính.

Các class dùng chung cho auth nằm trong `frontend/src/index.css`:

- `.auth-surface`
- `.auth-card`
- `.auth-input`
- `.auth-primary-button`
- `.auth-link`

## 8. Button và link

### Primary button

- Màu cam thương hiệu hoặc gradient cam nhẹ.
- Chữ trắng, font-weight `600` hoặc `700`.
- Hover có thể sáng/tối hơn và nâng tối đa 1–2px.
- Có trạng thái focus-visible và disabled rõ ràng.

### Secondary button

- Dùng outline trung tính hoặc nền trắng nhẹ.
- Không cạnh tranh thị giác với primary action.

### Link

- Dùng cam sáng trên nền tối.
- Hover tăng độ sáng hoặc underline.
- Điều hướng nội bộ nên dùng `Link` của React Router.

## 9. Tag và trạng thái

Tag Forum hoặc tag khóa học dùng cùng một phong cách:

```text
rounded-full
border border-orange-400/30
bg-orange-500/10
text-orange-300
text-xs font-semibold
```

Nội dung tag bắt đầu bằng `#`, ví dụ `#nodejs`. Active state dùng nền cam đặc và chữ trắng. Không dùng badge danh mục nhiều màu như xanh, tím, hồng nếu không mang ý nghĩa trạng thái thực tế.

Trạng thái không được truyền đạt chỉ bằng màu; khi cần phải có icon hoặc nhãn chữ đi kèm.

## 10. Icon và hình ảnh

- Ưu tiên Lucide React cho icon giao diện.
- Kích thước thông thường: `16px` đến `20px`.
- Không trộn emoji với icon Lucide trong cùng một khu vực.
- Avatar dùng `getUserAvatar()` để ưu tiên ảnh người dùng mới cập nhật và xử lý cache.
- Ảnh card dùng `object-cover`, `w-full` và một chiều cao hoặc aspect ratio ổn định.
- Ảnh nội dung phải responsive, không tràn container và có lightbox khi cần xem đầy đủ.

## 11. Layout theo khu vực

### Authentication

- Dùng chung `AuthLayout` để lấy đúng background và logo.
- Login học viên có thể nhấn mạnh AI Tutor nhưng không được làm rối form.
- Login giáo viên nghiêm túc và tối giản hơn.
- Register có thể rộng/cao hơn vì có nhiều field.
- Forgot/reset password dùng card nhỏ ở giữa.
- Không thay đổi background hoặc logo theo vai trò.

### Dashboard và Profile

- Nội dung chia cột rõ ràng trên desktop.
- Card sáng giúp thông tin dễ đọc trên background nhiều màu.
- Chỉ số phải lấy từ backend, không hiển thị tiến độ giả.

### Course và Lesson

- Ưu tiên tiêu đề, nội dung học, tiến độ thực và hành động tiếp theo.
- Breadcrumb đi từ Trang chủ đến vị trí hiện tại.
- AI Tutor và trạng thái xử lý phải phản ánh đúng dữ liệu backend.

### Forum

- Desktop giữ bố cục hai cột: bài viết bên trái, chủ đề nổi bật bên phải.
- Card bài viết tối, nội dung preview tối đa 2–3 dòng.
- Tag khóa học đặt gần tiêu đề.
- Ảnh phủ hết chiều ngang card nhưng giới hạn chiều cao.
- Sidebar chỉ giữ thông tin hỗ trợ trực tiếp cho việc tìm nội dung.

## 12. Responsive

- Mobile-first, sau đó mở rộng cho tablet và desktop.
- Mobile dùng `calc(100% - 32px)` hoặc padding ngang tối thiểu `16px`.
- Layout hai cột chuyển thành một cột khi không đủ không gian.
- Form đăng nhập đặt trước phần minh họa trên mobile nếu đó là tác vụ chính.
- Tag phải wrap hoặc scroll ngang, không được tràn màn hình.
- Navbar, logo và form không che nhau trên màn hình thấp.
- Không dùng fixed height cho nội dung tiếng Việt có thể xuống dòng.
- Touch target nên tối thiểu `44px`.

## 13. Accessibility và trạng thái giao diện

- Dùng semantic HTML và label liên kết đúng với input.
- Mọi control phải thao tác được bằng bàn phím.
- Luôn có focus-visible dễ nhận biết.
- Icon-only button phải có `aria-label` hoặc `title` phù hợp.
- Cần có loading, empty, error, success và disabled state khi API có thể tạo ra các trạng thái đó.
- Animation chỉ kéo dài khoảng 100–200ms và tôn trọng `prefers-reduced-motion`.

## 14. Nguyên tắc khi thêm trang mới

1. Tái sử dụng layout, logo, background và component hiện có trước khi tạo mới.
2. Chọn một hành động chính cho mỗi màn hình.
3. Dùng spacing và typography để phân cấp trước khi thêm màu hoặc shadow.
4. Không tự tạo dữ liệu UI nếu backend chưa cung cấp.
5. Không thay đổi API, authentication hoặc phân quyền chỉ để phục vụ giao diện.
6. Kiểm tra desktop, tablet và mobile.
7. Chạy lint và production build trước khi bàn giao.

## 15. File tham chiếu chính

- `frontend/src/index.css`: token và class dùng chung.
- `frontend/src/components/auth/AuthLayout.jsx`: background và logo của auth.
- `frontend/src/components/layouts/MainLayout.jsx`: navbar và background trang chính.
- `frontend/src/components/layouts/DashboardLayout.jsx`: layout khu vực dashboard.
- `frontend/src/components/navigation/AppBreadcrumbs.jsx`: breadcrumb dùng chung.
- `frontend/src/utils/avatar.js`: lựa chọn avatar và cache busting.
- `frontend/src/assets/images/logo-full.png`: logo chuẩn.
- `frontend/public/images/background2.png`: background chuẩn của website.

