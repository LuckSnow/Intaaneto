# 🖼️ Hướng Dẫn Quản Lý Hình Ảnh - Intaaneto Project

## 📋 Mục Lục
- [Tổng Quan](#tổng-quan)
- [Ảnh Static (Giao Diện)](#ảnh-static-giao-diện)
- [Ảnh Dynamic (User Upload)](#ảnh-dynamic-user-upload)
- [Kích Thước và Format Khuyến Nghị](#kích-thước-và-format-khuyến-nghị)
- [Hướng Dẫn Thêm Ảnh](#hướng-dẫn-thêm-ảnh)
- [Tối Ưu Hóa Ảnh](#tối-ưu-hóa-ảnh)

---

## 🎨 Tổng Quan

Website Intaaneto cần các loại hình ảnh sau để hiển thị đầy đủ và chuyên nghiệp:

### Phân loại theo mục đích:
1. **Branding**: Logo, favicon
2. **Hero/Banner**: Ảnh trang chủ, landing page
3. **Minh họa**: Icons, illustrations cho features
4. **Nội dung**: Ảnh khóa học, bài học, bài tập
5. **User Generated**: Avatar, ảnh upload từ user

---

## 🖥️ Ảnh Static (Giao Diện)

### 1. **Logo & Branding**

#### Logo Chính
- **Đường dẫn**: `frontend/src/assets/images/logo/`
- **Files cần có**:
  - `logo-full.png` - Logo đầy đủ với text (1200x400px)
  - `logo-icon.png` - Chỉ icon, không text (512x512px)
  - `logo-white.png` - Logo màu trắng cho dark background
  - `logo-dark.png` - Logo màu tối cho light background
- **Format**: PNG với transparent background
- **Kích thước file**: < 100KB mỗi file

#### Favicon
- **Đường dẫn**: `frontend/public/`
- **Files cần có**:
  - `favicon.ico` - Icon chính (16x16, 32x32, 48x48 multi-size)
  - `favicon-16x16.png`
  - `favicon-32x32.png`
  - `apple-touch-icon.png` - iOS icon (180x180px)
  - `android-chrome-192x192.png` - Android icon
  - `android-chrome-512x512.png` - Android splash screen
- **Format**: ICO, PNG
- **Kích thước file**: < 50KB

---

### 2. **Hero Images / Banners**

#### Landing Page Hero
- **Đường dẫn**: `frontend/public/images/banners/`
- **Files cần có**:
  - `hero-main.jpg` - Banner chính trang chủ (1920x1080px)
  - `hero-learning.jpg` - Section học tập (1920x800px)
  - `hero-about.jpg` - Trang giới thiệu (1920x600px)
- **Format**: JPG (quality 85-90%)
- **Kích thước file**: < 300KB
- **Aspect ratio**: 16:9 hoặc 21:9

#### Section Banners
- **Đường dẫn**: `frontend/public/images/banners/sections/`
- **Files cần có**:
  - `courses-banner.jpg` - Banner trang khóa học (1920x400px)
  - `exercises-banner.jpg` - Banner trang bài tập
  - `forum-banner.jpg` - Banner trang forum
  - `profile-banner.jpg` - Background profile header (1920x300px)
- **Format**: JPG
- **Kích thước file**: < 200KB

---

### 3. **Icons & Illustrations**

#### Feature Icons
- **Đường dẫn**: `frontend/src/assets/images/icons/`
- **Files cần có**:
  - `icon-ai.svg` - AI Assistant icon
  - `icon-course.svg` - Khóa học
  - `icon-exercise.svg` - Bài tập
  - `icon-forum.svg` - Diễn đàn
  - `icon-analytics.svg` - Thống kê
  - `icon-certificate.svg` - Chứng chỉ
  - `icon-progress.svg` - Tiến độ học tập
- **Format**: SVG (vector, scalable)
- **Kích thước file**: < 20KB mỗi file
- **Màu sắc**: Có thể tùy chỉnh qua CSS

#### Illustrations
- **Đường dẫn**: `frontend/public/images/illustrations/`
- **Files cần có**:
  - `learning-illustration.svg` - Minh họa học tập
  - `empty-state.svg` - Trạng thái rỗng
  - `404-error.svg` - Trang 404
  - `success.svg` - Thành công
  - `no-results.svg` - Không có kết quả
- **Format**: SVG hoặc PNG
- **Kích thước**: 400x400px đến 800x600px
- **Kích thước file**: < 150KB

---

### 4. **Background & Patterns**

#### Background Images
- **Đường dẫn**: `frontend/public/images/backgrounds/`
- **Files cần có**:
  - `pattern-dots.svg` - Pattern chấm tròn
  - `pattern-grid.svg` - Grid pattern
  - `gradient-primary.jpg` - Gradient background
  - `texture-paper.jpg` - Paper texture
- **Format**: SVG, JPG, PNG
- **Kích thước file**: < 100KB

---

### 5. **Social Media & Marketing**

#### Open Graph Images (Chia sẻ social)
- **Đường dẫn**: `frontend/public/images/og/`
- **Files cần có**:
  - `og-default.jpg` - Ảnh chia sẻ mặc định (1200x630px)
  - `og-courses.jpg` - Ảnh cho trang khóa học
  - `og-forum.jpg` - Ảnh cho forum
- **Format**: JPG
- **Kích thước**: 1200x630px (Facebook/LinkedIn)
- **Kích thước file**: < 300KB

#### Social Icons
- **Đường dẫn**: `frontend/src/assets/images/social/`
- **Files**: Facebook, Twitter, LinkedIn, YouTube icons
- **Format**: SVG
- **Kích thước**: 24x24px, 32x32px

---

## 📤 Ảnh Dynamic (User Upload)

### 1. **User Avatars**

- **Đường dẫn lưu trữ**: `backend/media/avatars/`
- **Upload qua**: User profile, Registration
- **Kích thước cho phép**: 
  - Min: 100x100px
  - Max: 2000x2000px
  - Recommended: 400x400px
- **Format**: JPG, PNG, WebP
- **Kích thước file**: Max 2MB
- **Processing**: Tự động resize và crop thành hình vuông

**Default Avatar**: `frontend/public/images/defaults/avatar-default.png`

---

### 2. **Course Images**

#### Course Thumbnail
- **Đường dẫn lưu trữ**: `backend/media/courses/thumbnails/`
- **Upload qua**: Django Admin, Teacher dashboard
- **Kích thước**: 
  - Recommended: 1280x720px (16:9)
  - Min: 800x450px
- **Format**: JPG, PNG
- **Kích thước file**: Max 5MB

#### Course Banner
- **Đường dẫn lưu trữ**: `backend/media/courses/banners/`
- **Kích thước**: 1920x400px
- **Format**: JPG
- **Kích thước file**: Max 3MB

**Default Course Image**: `frontend/public/images/defaults/course-default.jpg`

---

### 3. **Lesson Content Images**

- **Đường dẫn lưu trữ**: `backend/media/lessons/`
- **Upload qua**: Django Admin, Teacher dashboard
- **Kích thước**: 
  - Max width: 1920px
  - Responsive: Auto scale
- **Format**: JPG, PNG, GIF
- **Kích thước file**: Max 5MB
- **Mục đích**: Minh họa nội dung bài học

---

### 4. **Exercise Images**

- **Đường dẫn lưu trữ**: `backend/media/exercises/`
- **Upload qua**: Django Admin, Teacher dashboard
- **Kích thước**: Flexible (tùy nội dung bài tập)
- **Format**: JPG, PNG
- **Kích thước file**: Max 3MB
- **Mục đích**: Đề bài, hướng dẫn, diagram

---

### 5. **Forum Post Images**

- **Đường dẫn lưu trữ**: `backend/media/forum/posts/`
- **Upload qua**: Forum post editor
- **Kích thước**: Max 1920px width
- **Format**: JPG, PNG, GIF
- **Kích thước file**: Max 5MB
- **Số lượng**: Max 10 ảnh/post

---

### 6. **Achievement Badges**

- **Đường dẫn lưu trữ**: `frontend/public/images/badges/`
- **Files cần có**:
  - `badge-beginner.png` - Người mới bắt đầu
  - `badge-intermediate.png` - Trung cấp
  - `badge-advanced.png` - Nâng cao
  - `badge-master.png` - Bậc thầy
  - `badge-streak-7.png` - Học 7 ngày liên tiếp
  - `badge-streak-30.png` - Học 30 ngày liên tiếp
  - `badge-course-complete.png` - Hoàn thành khóa học
- **Kích thước**: 256x256px
- **Format**: PNG với transparent background
- **Kích thước file**: < 100KB

---

## 📐 Kích Thước và Format Khuyến Nghị

### Bảng Tổng Hợp:

| Loại Ảnh | Kích Thước | Format | Max Size |
|----------|------------|--------|----------|
| Logo Full | 1200x400px | PNG | 100KB |
| Logo Icon | 512x512px | PNG | 50KB |
| Favicon | 32x32px | ICO/PNG | 50KB |
| Hero Banner | 1920x1080px | JPG | 300KB |
| Section Banner | 1920x400px | JPG | 200KB |
| Course Thumbnail | 1280x720px | JPG | 5MB |
| User Avatar | 400x400px | JPG/PNG | 2MB |
| Icons | 24-64px | SVG | 20KB |
| Illustrations | 800x600px | SVG/PNG | 150KB |
| OG Image | 1200x630px | JPG | 300KB |
| Badge | 256x256px | PNG | 100KB |

### Format Guidelines:

- **SVG**: Icons, logos, illustrations đơn giản
- **PNG**: Ảnh cần transparent, logos, badges
- **JPG**: Photos, banners, backgrounds
- **WebP**: Modern browsers, tối ưu hơn JPG
- **GIF**: Chỉ khi cần animation nhỏ

---

## 📂 Hướng Dẫn Thêm Ảnh

### 1. Thêm Ảnh Static (Frontend)

#### Cách 1: Qua thư mục `src/assets/` (Recommended)
```bash
# 1. Copy ảnh vào thư mục
frontend/src/assets/images/logo/logo-full.png

# 2. Import trong component
import logo from '@/assets/images/logo/logo-full.png'

# 3. Sử dụng
<img src={logo} alt="Logo" />
```

#### Cách 2: Qua thư mục `public/`
```bash
# 1. Copy ảnh vào thư mục
frontend/public/images/banners/hero-main.jpg

# 2. Sử dụng trực tiếp
<img src="/images/banners/hero-main.jpg" alt="Hero Banner" />
```

### 2. Thêm Ảnh Dynamic (Backend)

#### Upload qua Django Admin:
```bash
# 1. Truy cập Django Admin
http://localhost:8000/admin

# 2. Chọn model (Course, User, etc.)

# 3. Upload ảnh qua form

# 4. Django tự động lưu vào media/
```

#### Upload qua API:
```javascript
// Frontend - Upload avatar
const formData = new FormData()
formData.append('avatar', file)

await axios.post('/api/users/profile/avatar/', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})
```

### 3. Thêm Ảnh khi Đang Chạy Docker

#### Frontend:
```bash
# Ảnh sẽ tự động reload nhờ Vite HMR
# Chỉ cần copy vào thư mục và save file component
```

#### Backend:
```bash
# Copy ảnh vào thư mục media
# Truy cập: http://localhost:8000/media/path/to/image.jpg
```

---

## 🚀 Tối Ưu Hóa Ảnh

### Tools Khuyến Nghị:

1. **TinyPNG** (https://tinypng.com)
   - Nén PNG/JPG không mất quality
   - Giảm 60-80% kích thước file

2. **ImageOptim** (https://imageoptim.com)
   - Mac app
   - Batch optimization

3. **Squoosh** (https://squoosh.app)
   - Google web app
   - Convert sang WebP

4. **SVGOMG** (https://jakearchibald.github.io/svgomg/)
   - Optimize SVG files
   - Loại bỏ metadata không cần thiết

### Checklist Trước Khi Upload:

- [ ] Resize về kích thước phù hợp
- [ ] Compress để giảm kích thước file
- [ ] Sử dụng format đúng (JPG cho photos, PNG cho graphics)
- [ ] Đặt tên file có ý nghĩa: `hero-learning-main.jpg` thay vì `IMG_1234.jpg`
- [ ] Xóa metadata (EXIF data) nếu không cần
- [ ] Test hiển thị trên nhiều màn hình (mobile, tablet, desktop)

### Responsive Images:

```jsx
// Sử dụng srcset cho responsive
<img 
  src="/images/course-800.jpg"
  srcSet="
    /images/course-400.jpg 400w,
    /images/course-800.jpg 800w,
    /images/course-1200.jpg 1200w
  "
  sizes="(max-width: 600px) 400px, (max-width: 1200px) 800px, 1200px"
  alt="Course thumbnail"
/>
```

---

## 🎯 Placeholder Images

Khi chưa có ảnh thật, sử dụng placeholder:

### Online Placeholder Services:
- **Lorem Picsum**: `https://picsum.photos/800/600`
- **Unsplash Source**: `https://source.unsplash.com/800x600/?education`
- **PlaceKitten**: `https://placekitten.com/800/600` (cute cats!)

### Local Placeholder:
```bash
frontend/public/images/defaults/
  ├── avatar-default.png
  ├── course-default.jpg
  ├── banner-default.jpg
  └── no-image.svg
```

---

## 📝 Naming Convention

### Format: `[type]-[description]-[size/variant].[ext]`

**Ví dụ:**
- `logo-full-white.png`
- `banner-hero-home-1920x1080.jpg`
- `icon-course-primary.svg`
- `avatar-default-400x400.png`
- `badge-master-level.png`

**Quy tắc:**
- Lowercase, dùng dấu gạch ngang `-`
- Mô tả rõ ràng, ngắn gọn
- Thêm kích thước nếu có nhiều variants
- Không dùng spaces hoặc ký tự đặc biệt

---

## 🔒 Security & Best Practices

### Upload Validation (Backend):

```python
# Trong Django settings
ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB

# Validate trong model/form
def validate_image(image):
    if image.size > MAX_UPLOAD_SIZE:
        raise ValidationError('File quá lớn. Max 5MB')
    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise ValidationError('Format không hợp lệ')
```

### Best Practices:
- ✅ Validate file type và size
- ✅ Rename file khi upload (UUID)
- ✅ Scan for malware
- ✅ Serve images qua CDN nếu có
- ✅ Implement lazy loading
- ✅ Sử dụng WebP với fallback
- ✅ Add alt text cho accessibility

---

## 📊 Checklist Đầy Đủ

### Landing Page:
- [ ] Logo (full, icon, white, dark variants)
- [ ] Favicon (all sizes)
- [ ] Hero banner
- [ ] Feature illustrations
- [ ] OG image

### Dashboard:
- [ ] Default avatar
- [ ] Empty state illustrations
- [ ] Section icons
- [ ] Background patterns

### Courses:
- [ ] Default course thumbnail
- [ ] Category icons
- [ ] Difficulty badges

### Profile:
- [ ] Default avatar
- [ ] Profile banner
- [ ] Achievement badges

### Marketing:
- [ ] Social media icons
- [ ] OG images for sharing
- [ ] Email templates images

---

## 📞 Cần Thêm Ảnh?

Nếu cần thêm loại ảnh khác:
1. Xác định mục đích và kích thước
2. Thêm vào thư mục phù hợp
3. Cập nhật file này
4. Commit và push lên Git

---

*Cập nhật lần cuối: 05/02/2026*
