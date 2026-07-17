# Lập Trình Web (Web Programming)

> Bản thảo học liệu Intaaneto · Phiên bản biên tập: 2026-07-17. Nội dung cần được giảng viên duyệt trước khi xuất bản và lập chỉ mục cho AI Tutor.

## Tổng Quan

**Lập trình web** là quá trình xây dựng các ứng dụng và trang web hoạt động trên Internet hoặc Intranet. Nó bao gồm việc phát triển cả phía client (frontend) và phía server (backend).

## Các Thành Phần Chính

### 1. Frontend (Client-side)

Frontend là phần giao diện người dùng của website, chạy trực tiếp trên trình duyệt web.

**Công nghệ cơ bản:**
- **HTML (HyperText Markup Language)**: Ngôn ngữ đánh dấu cấu trúc nội dung web
- **CSS (Cascading Style Sheets)**: Ngôn ngữ định dạng và tạo kiểu cho trang web
- **JavaScript**: Ngôn ngữ lập trình tạo tính tương tác

**Frameworks & Libraries phổ biến:**
- React.js - Thư viện JavaScript được Meta và cộng đồng duy trì
- Vue.js - Framework JavaScript progressive
- Angular - Framework TypeScript do Google phát triển
- Svelte - Compiler framework hiện đại

### 2. Backend (Server-side)

Backend xử lý logic nghiệp vụ, quản lý cơ sở dữ liệu và API.

**Ngôn ngữ lập trình phổ biến:**
- **Python**: Django, Flask, FastAPI
- **JavaScript/Node.js**: Express.js, Nest.js, Koa
- **Java**: Spring Boot, Jakarta EE
- **PHP**: Laravel, Symfony
- **Ruby**: Ruby on Rails
- **Go**: Gin, Echo
- **C#/.NET**: ASP.NET Core

### 3. Database (Cơ sở dữ liệu)

**Relational Databases (SQL):**
- PostgreSQL
- MySQL
- Microsoft SQL Server
- Oracle Database

**NoSQL Databases:**
- MongoDB (Document-based)
- Redis (Key-value store)
- Cassandra (Column-family)
- Neo4j (Graph database)

## Kiến Trúc Web

### 1. Client-Server Architecture
Mô hình truyền thống với client gửi request và server trả về response.

### 2. RESTful API
- Sử dụng HTTP methods: GET, POST, PUT, DELETE, PATCH
- Stateless communication
- JSON hoặc XML format

### 3. GraphQL
- Query language cho API
- Client có thể request chính xác dữ liệu cần thiết
- Giảm over-fetching và under-fetching

### 4. Microservices
- Chia nhỏ ứng dụng thành các services độc lập
- Dễ scale và maintain
- Sử dụng API Gateway

### 5. Single Page Application (SPA)
- Tải một trang HTML duy nhất
- Cập nhật nội dung động qua JavaScript
- Trải nghiệm người dùng mượt mà như ứng dụng desktop

## Giao Thức và Chuẩn

### HTTP/HTTPS
- **HTTP**: HyperText Transfer Protocol
- **HTTPS**: HTTP được bảo vệ bằng TLS; SSL đã lỗi thời
- Status codes: 200 (OK), 404 (Not Found), 500 (Server Error)

### WebSocket
- Giao thức cho real-time, two-way communication
- Dùng cho chat apps, live updates, gaming

### WebRTC
- Real-Time Communication trong browser
- Video calls, audio streaming, file sharing

## Web Security

### Các Mối Đe Dọa Phổ Biến:
1. **XSS (Cross-Site Scripting)**: Dữ liệu không tin cậy trở thành script chạy trong trình duyệt của người dùng
2. **CSRF (Cross-Site Request Forgery)**: Lừa trình duyệt đã đăng nhập gửi một yêu cầu thay đổi trạng thái ngoài ý muốn
3. **SQL Injection**: Dữ liệu đầu vào làm thay đổi cấu trúc câu truy vấn SQL
4. **Man-in-the-Middle Attack**: Kẻ tấn công chặn hoặc sửa communication giữa client-server

### Best Practices:
- Sử dụng HTTPS cho mọi connection
- Input validation và sanitization
- Sử dụng parameterized queries
- Implement authentication và authorization đúng cách
- Regular security updates và patches

Mỗi loại rủi ro cần control đúng ngữ cảnh. Truy vấn tham số hóa tách dữ liệu khỏi
cấu trúc SQL để phòng SQL injection. Khi đưa dữ liệu không tin cậy vào HTML,
ứng dụng vẫn phải mã hóa đầu ra theo đúng ngữ cảnh để phòng XSS; input validation
không thay thế bước này. Với CSRF, ứng dụng dùng CSRF token và thuộc tính cookie
phù hợp như `SameSite` cho các yêu cầu thay đổi trạng thái.

**Authentication** xác minh người dùng là ai, còn **authorization** quyết định
người đó được phép làm gì trên một tài nguyên cụ thể. Một người đã đăng nhập vẫn
phải bị từ chối nếu cố sửa khóa học thuộc quyền sở hữu của giảng viên khác.

## Web Performance Optimization

### 1. Frontend Optimization
- Minification của CSS, JavaScript
- Image optimization và lazy loading
- Code splitting
- Browser caching
- CDN (Content Delivery Network)

### 2. Backend Optimization
- Database indexing
- Query optimization
- Caching (Redis, Memcached)
- Load balancing
- Horizontal scaling

## Progressive Web Apps (PWA)

**Đặc điểm:**
- Hoạt động offline với Service Workers
- Installable trên thiết bị
- Push notifications
- Responsive design
- Fast và reliable

## Modern Web Development Tools

### Package Managers:
- npm (Node Package Manager)
- Yarn
- pnpm

### Build Tools:
- Webpack
- Vite
- Rollup
- Parcel

### Version Control:
- Git
- GitHub, GitLab, Bitbucket

### DevOps & Deployment:
- Docker & Kubernetes
- CI/CD pipelines
- Cloud platforms: AWS, Azure, Google Cloud
- Serverless computing

## Web Standards và Organizations

### W3C (World Wide Web Consortium)
- Phát triển web standards và guidelines
- HTML, CSS, XML specifications

### WHATWG (Web Hypertext Application Technology Working Group)
- HTML Living Standard
- DOM, URL, Fetch API specifications

### ECMA International
- ECMAScript (JavaScript) specification
- JSON standard

## Xu Hướng Hiện Đại

1. **JAMstack**: JavaScript, APIs, Markup
2. **Server-Side Rendering (SSR)**: Next.js, Nuxt.js
3. **Static Site Generators**: Gatsby, Hugo, Jekyll
4. **WebAssembly**: Chạy code performance-critical trong browser
5. **AI Integration**: ChatGPT, ML models trong web apps
6. **Web3**: Blockchain, decentralized applications

## Học Lập Trình Web

### Roadmap Cơ Bản:
1. HTML & CSS fundamentals
2. JavaScript basics
3. DOM manipulation
4. Version control (Git)
5. Frontend framework (React/Vue/Angular)
6. Backend language và framework
7. Databases
8. RESTful APIs
9. Authentication & Security
10. Deployment & DevOps

### Resources:
- MDN Web Docs
- FreeCodeCamp
- The Odin Project
- W3Schools
- JavaScript.info

## Tham Khảo

Nội dung được tổng hợp từ:
- Wikipedia: Web Development, World Wide Web
- MDN Web Docs
- W3C Standards
- WHATWG Specifications

---

*Tài liệu này được tạo cho mục đích giáo dục trong hệ thống Intaaneto.*
