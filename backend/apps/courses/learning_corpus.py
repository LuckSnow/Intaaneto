"""Compile reviewed Markdown documents into deterministic course lessons."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


MAX_SOURCE_BYTES = 1_000_000
MANAGED_MARKER_PREFIX = '<!-- intaaneto-learning-corpus:'
HEADING_PATTERN = re.compile(r'^## (?P<title>.+?)\s*$', re.MULTILINE)


class LearningCorpusError(ValueError):
    """Raised when an authoring source cannot be compiled safely."""


@dataclass(frozen=True)
class LessonDefinition:
    slug: str
    title: str
    headings: tuple[str, ...]
    objectives: tuple[str, ...]
    duration_minutes: int
    references: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class CourseDefinition:
    slug: str
    title: str
    source_file: str
    revision: str
    description: str
    objectives: tuple[str, ...]
    prerequisites: str
    duration_hours: int
    lessons: tuple[LessonDefinition, ...]


@dataclass(frozen=True)
class CompiledLesson:
    definition: LessonDefinition
    content: str


@dataclass(frozen=True)
class CompiledCourse:
    definition: CourseDefinition
    lessons: tuple[CompiledLesson, ...]


NETWORK_REFERENCES = (
    ('IETF RFC Index', 'https://www.rfc-editor.org/rfc-index.html'),
    ('Cisco Networking Basics', 'https://www.cisco.com/c/en/us/solutions/enterprise-networks/what-is-computer-networking.html'),
)
WEB_REFERENCES = (
    ('MDN Web Docs', 'https://developer.mozilla.org/'),
    ('WHATWG HTML Living Standard', 'https://html.spec.whatwg.org/'),
)


COURSE_DEFINITIONS = (
    CourseDefinition(
        slug='hoc-lieu-mang-may-tinh',
        title='Nền tảng Mạng máy tính',
        source_file='computer-networks.md',
        revision='2026-07-16',
        description=(
            'Giáo trình nhập môn về mô hình mạng, địa chỉ IP, giao thức, thiết bị, '
            'an toàn, hiệu năng và xử lý sự cố mạng.'
        ),
        objectives=(
            'Giải thích được các lớp của mô hình OSI và TCP/IP.',
            'Nhận diện được vai trò của địa chỉ, giao thức và thiết bị mạng.',
            'Phân tích được các yêu cầu cơ bản về an toàn và hiệu năng mạng.',
            'Vận dụng công cụ cơ bản để chẩn đoán sự cố kết nối.',
        ),
        prerequisites='Biết sử dụng máy tính và Internet ở mức cơ bản.',
        duration_hours=4,
        lessons=(
            LessonDefinition(
                'tong-quan-va-mo-hinh-mang',
                'Tổng quan và mô hình mạng',
                ('Tổng Quan', 'Mô Hình OSI (Open Systems Interconnection)', 'Mô Hình TCP/IP'),
                (
                    'Mô tả được mục đích của mạng máy tính.',
                    'So sánh được cách phân tầng của OSI và TCP/IP.',
                    'Gắn được một số giao thức phổ biến với tầng tương ứng.',
                ),
                35,
                NETWORK_REFERENCES,
            ),
            LessonDefinition(
                'dia-chi-ip-va-chia-mang',
                'Địa chỉ IP và chia mạng',
                ('Địa Chỉ IP (IP Addressing)',),
                (
                    'Phân biệt được IPv4 và IPv6.',
                    'Giải thích được địa chỉ riêng, subnet mask và ký hiệu CIDR.',
                    'Nhận biết được việc phân lớp IPv4 chỉ còn ý nghĩa lịch sử.',
                ),
                30,
                (('IETF RFC 4632: CIDR', 'https://www.rfc-editor.org/rfc/rfc4632'),) + NETWORK_REFERENCES,
            ),
            LessonDefinition(
                'giao-thuc-mang',
                'Các giao thức mạng quan trọng',
                ('Giao Thức Mạng Quan Trọng',),
                (
                    'So sánh được đặc tính truyền dữ liệu của TCP và UDP.',
                    'Nêu được vai trò của HTTP, DNS, DHCP, SSH và giao thức thư điện tử.',
                    'Phân biệt được FTP, FTPS và SFTP ở mức khái niệm.',
                ),
                35,
                NETWORK_REFERENCES,
            ),
            LessonDefinition(
                'thiet-bi-va-kien-truc-ket-noi',
                'Thiết bị và kiến trúc kết nối',
                ('Thiết Bị Mạng', 'Các Loại Mạng', 'Network Topologies'),
                (
                    'Phân biệt được router, switch, access point và firewall.',
                    'Phân loại được LAN, WAN, PAN, WLAN và VPN.',
                    'Đánh giá được ưu, nhược điểm cơ bản của các topology phổ biến.',
                ),
                40,
                NETWORK_REFERENCES,
            ),
            LessonDefinition(
                'an-toan-mang',
                'An toàn mạng cơ bản',
                ('Network Security',),
                (
                    'Nhận diện được các nhóm mối đe dọa mạng phổ biến.',
                    'Giải thích được vai trò của mã hóa, xác thực và phân đoạn mạng.',
                    'Đề xuất được các biện pháp phòng vệ theo lớp.',
                ),
                30,
                (('NIST Cybersecurity Framework', 'https://www.nist.gov/cyberframework'),) + NETWORK_REFERENCES,
            ),
            LessonDefinition(
                'mang-khong-day-va-hieu-nang',
                'Mạng không dây và hiệu năng',
                ('Wireless Networks', 'Network Performance'),
                (
                    'Nhận biết được các thế hệ Wi-Fi và băng tần chính.',
                    'Phân biệt được bandwidth, throughput, latency, jitter và packet loss.',
                    'Giải thích được mục đích của QoS.',
                ),
                35,
                NETWORK_REFERENCES,
            ),
            LessonDefinition(
                'cloud-networking',
                'Nhập môn Cloud Networking',
                ('Cloud Networking',),
                (
                    'Giải thích được SDN, NFV, load balancer và CDN ở mức nhập môn.',
                    'Mô tả được mục tiêu của kết nối multi-cloud.',
                ),
                20,
                NETWORK_REFERENCES,
            ),
            LessonDefinition(
                'xu-ly-su-co-va-xu-huong',
                'Xử lý sự cố và xu hướng mạng',
                ('Network Troubleshooting Tools', 'Xu Hướng Hiện Đại'),
                (
                    'Chọn được công cụ phù hợp cho một số lỗi kết nối thường gặp.',
                    'Diễn giải được kết quả cơ bản của ping, traceroute và DNS lookup.',
                    'Nhận diện được một số xu hướng phát triển của mạng hiện đại.',
                ),
                35,
                NETWORK_REFERENCES,
            ),
        ),
    ),
    CourseDefinition(
        slug='hoc-lieu-lap-trinh-web',
        title='Nền tảng Lập trình Web',
        source_file='web-programming.md',
        revision='2026-07-16',
        description=(
            'Giáo trình nhập môn về frontend, backend, cơ sở dữ liệu, kiến trúc, '
            'giao thức, bảo mật, hiệu năng và lộ trình phát triển web.'
        ),
        objectives=(
            'Mô tả được các thành phần chính của một ứng dụng web.',
            'So sánh được một số kiểu kiến trúc và giao tiếp web.',
            'Nhận diện được rủi ro bảo mật và biện pháp phòng vệ cơ bản.',
            'Xây dựng được lộ trình học và triển khai một ứng dụng web nhỏ.',
        ),
        prerequisites='Biết sử dụng máy tính và trình duyệt web ở mức cơ bản.',
        duration_hours=4,
        lessons=(
            LessonDefinition(
                'tong-quan-va-thanh-phan-web',
                'Tổng quan và thành phần của ứng dụng web',
                ('Tổng Quan', 'Các Thành Phần Chính'),
                (
                    'Phân biệt được frontend, backend và cơ sở dữ liệu.',
                    'Nêu được vai trò của HTML, CSS và JavaScript.',
                    'Nhận diện được một số hệ quản trị dữ liệu và framework phổ biến.',
                ),
                35,
                WEB_REFERENCES,
            ),
            LessonDefinition(
                'kien-truc-web',
                'Kiến trúc ứng dụng web',
                ('Kiến Trúc Web',),
                (
                    'Mô tả được mô hình client-server và tính stateless của REST.',
                    'So sánh được REST, GraphQL, microservices và SPA ở mức khái niệm.',
                    'Nhận biết được khi nào độ phức tạp kiến trúc là không cần thiết.',
                ),
                35,
                WEB_REFERENCES,
            ),
            LessonDefinition(
                'giao-thuc-va-chuan-web',
                'Giao thức và chuẩn giao tiếp web',
                ('Giao Thức và Chuẩn',),
                (
                    'Giải thích được vai trò của HTTP và HTTPS.',
                    'Phân biệt được HTTP request-response, WebSocket và WebRTC.',
                    'Diễn giải được một số mã trạng thái HTTP thông dụng.',
                ),
                25,
                WEB_REFERENCES,
            ),
            LessonDefinition(
                'bao-mat-web',
                'Bảo mật web cơ bản',
                ('Web Security',),
                (
                    'Nhận diện được XSS, CSRF, SQL injection và tấn công xen giữa.',
                    'Phân biệt được kiểm tra đầu vào, mã hóa đầu ra và truy vấn tham số hóa.',
                    'Giải thích được vì sao xác thực không thay thế cho phân quyền.',
                ),
                35,
                (('OWASP Top 10', 'https://owasp.org/www-project-top-ten/'),) + WEB_REFERENCES,
            ),
            LessonDefinition(
                'hieu-nang-va-pwa',
                'Hiệu năng Web và Progressive Web App',
                ('Web Performance Optimization', 'Progressive Web Apps (PWA)'),
                (
                    'Phân loại được các kỹ thuật tối ưu frontend và backend.',
                    'Giải thích được vai trò của cache, CDN và lazy loading.',
                    'Mô tả được các đặc trưng cốt lõi của PWA.',
                ),
                35,
                WEB_REFERENCES,
            ),
            LessonDefinition(
                'cong-cu-va-tieu-chuan-web',
                'Công cụ và tiêu chuẩn Web',
                ('Modern Web Development Tools', 'Web Standards và Organizations'),
                (
                    'Phân loại được package manager, build tool và công cụ triển khai.',
                    'Nêu được vai trò của W3C, WHATWG và ECMA International.',
                    'Giải thích được lợi ích của version control và CI/CD.',
                ),
                30,
                WEB_REFERENCES,
            ),
            LessonDefinition(
                'xu-huong-va-lo-trinh-web',
                'Xu hướng và lộ trình học Web',
                ('Xu Hướng Hiện Đại', 'Học Lập Trình Web'),
                (
                    'Nhận diện được một số hướng phát triển web hiện đại.',
                    'Sắp xếp được lộ trình học web theo các năng lực nền tảng.',
                    'Chọn được nguồn tài liệu chính thống để tiếp tục tự học.',
                ),
                30,
                WEB_REFERENCES,
            ),
        ),
    ),
)


def managed_marker(course_slug: str, lesson_slug: str, revision: str) -> str:
    return (
        f'{MANAGED_MARKER_PREFIX}{course_slug}/{lesson_slug}; '
        f'revision={revision} -->'
    )


def is_managed_content(content: str) -> bool:
    return content.lstrip().startswith(MANAGED_MARKER_PREFIX)


def compile_learning_corpus(source_root: Path) -> tuple[CompiledCourse, ...]:
    root = source_root.expanduser().resolve()
    if not root.is_dir():
        raise LearningCorpusError(f'Source root does not exist: {root}')

    compiled_courses = []
    for course in COURSE_DEFINITIONS:
        source_path = root / course.source_file
        sections = _read_sections(source_path)
        compiled_lessons = []
        used_headings = set()
        for lesson in course.lessons:
            duplicate_use = used_headings.intersection(lesson.headings)
            if duplicate_use:
                raise LearningCorpusError(
                    f'Headings assigned more than once in {course.source_file}: '
                    f'{sorted(duplicate_use)}'
                )
            used_headings.update(lesson.headings)
            missing = [heading for heading in lesson.headings if heading not in sections]
            if missing:
                raise LearningCorpusError(
                    f'Missing headings in {course.source_file}: {missing}'
                )
            selected = '\n\n'.join(sections[heading] for heading in lesson.headings)
            objectives = '\n'.join(f'- {objective}' for objective in lesson.objectives)
            references = '\n'.join(
                f'- [{label}]({url})' for label, url in lesson.references
            )
            content = (
                f'{managed_marker(course.slug, lesson.slug, course.revision)}\n'
                f'# {lesson.title}\n\n'
                f'> Nguồn biên tập: `docs/{course.source_file}` · '
                f'Phiên bản: {course.revision}\n\n'
                f'## Mục tiêu học tập\n\n{objectives}\n\n'
                f'{selected}\n\n'
                f'## Nguồn tham khảo chính\n\n{references}'
            )
            compiled_lessons.append(CompiledLesson(lesson, content.strip()))
        compiled_courses.append(CompiledCourse(course, tuple(compiled_lessons)))
    return tuple(compiled_courses)


def _read_sections(source_path: Path) -> dict[str, str]:
    try:
        size = source_path.stat().st_size
    except FileNotFoundError as exc:
        raise LearningCorpusError(f'Missing source file: {source_path}') from exc
    if size > MAX_SOURCE_BYTES:
        raise LearningCorpusError(
            f'Source file exceeds {MAX_SOURCE_BYTES} bytes: {source_path}'
        )
    try:
        text = source_path.read_text(encoding='utf-8')
    except UnicodeDecodeError as exc:
        raise LearningCorpusError(f'Source file must be UTF-8: {source_path}') from exc
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    if '\x00' in text:
        raise LearningCorpusError(f'Source file contains NUL bytes: {source_path}')

    matches = list(HEADING_PATTERN.finditer(text))
    sections = {}
    for index, match in enumerate(matches):
        heading = match.group('title').strip()
        if heading in sections:
            raise LearningCorpusError(
                f'Duplicate H2 heading in {source_path.name}: {heading!r}'
            )
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[heading] = text[match.start():end].strip()
    return sections
