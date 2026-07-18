"""Curated draft assessment blueprints kept outside the RAG learning corpus."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass


BLUEPRINT_REVISION = '2026-07-17'
QUESTIONS_PER_OBJECTIVE = 3


class AssessmentBlueprintError(ValueError):
    """Raised when checked-in assessment authoring data is inconsistent."""


@dataclass(frozen=True)
class QuestionBlueprint:
    prompt: str
    choices: tuple[str, ...]
    correct_choice: int
    learning_objective: str
    explanation: str
    order: int


@dataclass(frozen=True)
class AssessmentBlueprint:
    course_slug: str
    lesson_slug: str
    title: str
    instructions: str
    pass_threshold: int
    objectives: tuple[str, ...]
    questions: tuple[QuestionBlueprint, ...]


NETWORK_MODELS_OBJECTIVES = (
    'Mô tả được mục đích của mạng máy tính.',
    'So sánh được cách phân tầng của OSI và TCP/IP.',
    'Gắn được một số giao thức phổ biến với tầng tương ứng.',
)

NETWORK_SECURITY_OBJECTIVES = (
    'Nhận diện được các nhóm mối đe dọa mạng phổ biến.',
    'Giải thích được vai trò của mã hóa, xác thực và phân đoạn mạng.',
    'Đề xuất được các biện pháp phòng vệ theo lớp.',
)

WEB_SECURITY_OBJECTIVES = (
    'Nhận diện được XSS, CSRF, SQL injection và tấn công xen giữa.',
    'Phân biệt được kiểm tra đầu vào, mã hóa đầu ra và truy vấn tham số hóa.',
    'Giải thích được vì sao xác thực không thay thế cho phân quyền.',
)


ASSESSMENT_BLUEPRINTS = (
    AssessmentBlueprint(
        course_slug='hoc-lieu-mang-may-tinh',
        lesson_slug='tong-quan-va-mo-hinh-mang',
        title='Kiểm tra: Tổng quan và mô hình mạng',
        instructions=(
            'Chọn một đáp án phù hợp nhất cho mỗi câu. Đây là bản nháp đã biên '
            'soạn; giảng viên phải duyệt trước khi xuất bản.'
        ),
        pass_threshold=70,
        objectives=NETWORK_MODELS_OBJECTIVES,
        questions=(
            QuestionBlueprint(
                prompt='Mục đích cốt lõi của mạng máy tính là gì?',
                choices=(
                    'Kết nối thiết bị để chia sẻ tài nguyên và thông tin',
                    'Biến mọi thiết bị thành máy chủ công khai',
                    'Loại bỏ hoàn toàn nhu cầu lưu trữ dữ liệu',
                ),
                correct_choice=0,
                learning_objective=NETWORK_MODELS_OBJECTIVES[0],
                explanation=(
                    'Mạng kết nối các thiết bị để chúng trao đổi thông tin và '
                    'chia sẻ tài nguyên.'
                ),
                order=1,
            ),
            QuestionBlueprint(
                prompt='Tình huống nào mô tả đúng một mạng máy tính?',
                choices=(
                    'Một máy tính không kết nối với thiết bị nào',
                    'Nhiều thiết bị kết nối để cùng truy cập máy chủ tệp',
                    'Một tài liệu được in ra giấy',
                ),
                correct_choice=1,
                learning_objective=NETWORK_MODELS_OBJECTIVES[0],
                explanation=(
                    'Các thiết bị kết nối và dùng chung máy chủ tệp là một ví dụ '
                    'trực tiếp về chia sẻ tài nguyên qua mạng.'
                ),
                order=2,
            ),
            QuestionBlueprint(
                prompt='Vì sao thiết bị IoT thường được kết nối vào mạng?',
                choices=(
                    'Để trao đổi dữ liệu với thiết bị hoặc dịch vụ khác',
                    'Để luôn hoạt động mà không cần giao thức',
                    'Để thay thế mọi thiết bị di động',
                ),
                correct_choice=0,
                learning_objective=NETWORK_MODELS_OBJECTIVES[0],
                explanation=(
                    'Thiết bị IoT tham gia mạng để gửi, nhận và chia sẻ dữ liệu '
                    'với các thiết bị hoặc dịch vụ.'
                ),
                order=3,
            ),
            QuestionBlueprint(
                prompt='Mô hình OSI và TCP/IP khác nhau rõ nhất ở số tầng nào?',
                choices=(
                    'OSI có 4 tầng, TCP/IP có 7 tầng',
                    'Cả hai đều có 5 tầng',
                    'OSI có 7 tầng, TCP/IP có 4 tầng',
                ),
                correct_choice=2,
                learning_objective=NETWORK_MODELS_OBJECTIVES[1],
                explanation='OSI có 7 tầng trong khi mô hình TCP/IP có 4 tầng.',
                order=4,
            ),
            QuestionBlueprint(
                prompt='Network Access của TCP/IP tương ứng với phần nào của OSI?',
                choices=(
                    'Physical và Data Link',
                    'Session và Presentation',
                    'Transport và Application',
                ),
                correct_choice=0,
                learning_objective=NETWORK_MODELS_OBJECTIVES[1],
                explanation=(
                    'Network Access gộp chức năng của Physical và Data Link '
                    'trong mô hình OSI.'
                ),
                order=5,
            ),
            QuestionBlueprint(
                prompt='Internet Layer của TCP/IP gần tương ứng với tầng OSI nào?',
                choices=('Application', 'Network', 'Presentation'),
                correct_choice=1,
                learning_objective=NETWORK_MODELS_OBJECTIVES[1],
                explanation=(
                    'Internet Layer đảm nhiệm IP và định tuyến, tương ứng Network '
                    'Layer của OSI.'
                ),
                order=6,
            ),
            QuestionBlueprint(
                prompt='Cặp giao thức nào thuộc tầng Transport?',
                choices=('HTTP và DNS', 'IP và ICMP', 'TCP và UDP'),
                correct_choice=2,
                learning_objective=NETWORK_MODELS_OBJECTIVES[2],
                explanation='TCP và UDP là các giao thức của tầng Transport.',
                order=7,
            ),
            QuestionBlueprint(
                prompt='HTTP và DNS được xếp vào tầng nào trong TCP/IP?',
                choices=('Application', 'Internet', 'Network Access'),
                correct_choice=0,
                learning_objective=NETWORK_MODELS_OBJECTIVES[2],
                explanation=(
                    'HTTP và DNS cung cấp dịch vụ cho ứng dụng nên thuộc '
                    'Application Layer.'
                ),
                order=8,
            ),
            QuestionBlueprint(
                prompt='IP và ICMP được gắn với cặp tầng tương ứng nào?',
                choices=(
                    'OSI Presentation và TCP/IP Application',
                    'OSI Network và TCP/IP Internet',
                    'OSI Session và TCP/IP Transport',
                ),
                correct_choice=1,
                learning_objective=NETWORK_MODELS_OBJECTIVES[2],
                explanation=(
                    'IP và ICMP nằm ở Network Layer của OSI và Internet Layer '
                    'của TCP/IP.'
                ),
                order=9,
            ),
        ),
    ),
    AssessmentBlueprint(
        course_slug='hoc-lieu-mang-may-tinh',
        lesson_slug='an-toan-mang',
        title='Kiểm tra: An toàn mạng cơ bản',
        instructions=(
            'Chọn một đáp án phù hợp nhất cho mỗi câu. Giảng viên cần kiểm tra '
            'tính rõ ràng và độ khó trước khi xuất bản.'
        ),
        pass_threshold=70,
        objectives=NETWORK_SECURITY_OBJECTIVES,
        questions=(
            QuestionBlueprint(
                prompt='Mối đe dọa nào chủ yếu dùng kỹ thuật social engineering?',
                choices=('Phishing', 'Packet loss', 'QoS'),
                correct_choice=0,
                learning_objective=NETWORK_SECURITY_OBJECTIVES[0],
                explanation='Phishing lừa người dùng thông qua social engineering.',
                order=1,
            ),
            QuestionBlueprint(
                prompt='Man-in-the-Middle mô tả hành vi nào?',
                choices=(
                    'Tăng băng thông đường truyền',
                    'Chặn hoặc can thiệp communication giữa các bên',
                    'Chia một mạng thành nhiều VLAN',
                ),
                correct_choice=1,
                learning_objective=NETWORK_SECURITY_OBJECTIVES[0],
                explanation=(
                    'Man-in-the-Middle liên quan đến việc chặn hoặc can thiệp '
                    'vào communication giữa các bên.'
                ),
                order=2,
            ),
            QuestionBlueprint(
                prompt='DoS/DDoS thường nhắm trực tiếp tới thuộc tính nào?',
                choices=(
                    'Khả năng sẵn sàng của dịch vụ',
                    'Cách đặt tên biến trong mã nguồn',
                    'Độ phân giải của màn hình',
                ),
                correct_choice=0,
                learning_objective=NETWORK_SECURITY_OBJECTIVES[0],
                explanation=(
                    'DoS/DDoS làm cạn tài nguyên hoặc lưu lượng để người dùng '
                    'hợp lệ khó truy cập dịch vụ.'
                ),
                order=3,
            ),
            QuestionBlueprint(
                prompt='Mã hóa SSL/TLS, VPN hoặc IPSec chủ yếu bảo vệ điều gì?',
                choices=(
                    'Tính bí mật và toàn vẹn của dữ liệu khi truyền',
                    'Số lượng cổng vật lý trên switch',
                    'Tên miền khỏi hết hạn',
                ),
                correct_choice=0,
                learning_objective=NETWORK_SECURITY_OBJECTIVES[1],
                explanation=(
                    'Mã hóa bảo vệ dữ liệu trên đường truyền khỏi bị đọc hoặc '
                    'sửa trái phép.'
                ),
                order=4,
            ),
            QuestionBlueprint(
                prompt='Password, 2FA và biometrics thuộc nhóm biện pháp nào?',
                choices=('Authentication', 'Load balancing', 'Compression'),
                correct_choice=0,
                learning_objective=NETWORK_SECURITY_OBJECTIVES[1],
                explanation='Các biện pháp này được dùng để xác minh danh tính.',
                order=5,
            ),
            QuestionBlueprint(
                prompt='Phân đoạn mạng bằng VLAN hoặc subnet giúp ích gì khi có sự cố?',
                choices=(
                    'Bảo đảm không bao giờ có mã độc',
                    'Giới hạn phạm vi ảnh hưởng và di chuyển ngang',
                    'Thay thế hoàn toàn authentication',
                ),
                correct_choice=1,
                learning_objective=NETWORK_SECURITY_OBJECTIVES[1],
                explanation=(
                    'Phân đoạn cô lập các vùng mạng và hạn chế kẻ tấn công di '
                    'chuyển sang tài nguyên khác.'
                ),
                order=6,
            ),
            QuestionBlueprint(
                prompt='Phương án nào thể hiện phòng vệ theo lớp cho endpoint?',
                choices=(
                    'Chỉ đổi hình nền máy tính',
                    'Antimalware, cập nhật và phân đoạn mạng',
                    'Chỉ tăng tốc độ đường truyền',
                ),
                correct_choice=1,
                learning_objective=NETWORK_SECURITY_OBJECTIVES[2],
                explanation=(
                    'Antimalware và cập nhật giảm rủi ro tại endpoint; phân đoạn '
                    'giới hạn ảnh hưởng nếu vẫn xảy ra xâm nhập.'
                ),
                order=7,
            ),
            QuestionBlueprint(
                prompt='Biện pháp nào phù hợp nhất để giảm rủi ro lỗ hổng đã biết?',
                choices=(
                    'Cài đặt patches và updates định kỳ',
                    'Tắt mọi log bảo mật',
                    'Dùng chung một mật khẩu cho mọi tài khoản',
                ),
                correct_choice=0,
                learning_objective=NETWORK_SECURITY_OBJECTIVES[2],
                explanation=(
                    'Cập nhật định kỳ vá các lỗ hổng đã được nhà cung cấp xử lý.'
                ),
                order=8,
            ),
            QuestionBlueprint(
                prompt='Tại sao không nên chỉ dựa vào một firewall?',
                choices=(
                    'Vì firewall chỉ dùng để tăng dung lượng ổ đĩa',
                    'Vì một control đơn lẻ không bao phủ mọi mối đe dọa',
                    'Vì firewall luôn làm mất toàn bộ dữ liệu',
                ),
                correct_choice=1,
                learning_objective=NETWORK_SECURITY_OBJECTIVES[2],
                explanation=(
                    'Phòng vệ theo lớp kết hợp identity, endpoint, đường truyền '
                    'và phân đoạn thay vì phụ thuộc một control.'
                ),
                order=9,
            ),
        ),
    ),
    AssessmentBlueprint(
        course_slug='hoc-lieu-lap-trinh-web',
        lesson_slug='bao-mat-web',
        title='Kiểm tra: Bảo mật web cơ bản',
        instructions=(
            'Chọn một đáp án phù hợp nhất. Bài kiểm tra ở trạng thái draft cho '
            'tới khi giảng viên duyệt nội dung và đáp án.'
        ),
        pass_threshold=70,
        objectives=WEB_SECURITY_OBJECTIVES,
        questions=(
            QuestionBlueprint(
                prompt='XSS xảy ra khi nào?',
                choices=(
                    'Dữ liệu không tin cậy trở thành script chạy trong trình duyệt',
                    'Máy chủ chia tải sang nhiều instance',
                    'Trình duyệt tải ảnh từ cache',
                ),
                correct_choice=0,
                learning_objective=WEB_SECURITY_OBJECTIVES[0],
                explanation=(
                    'XSS biến dữ liệu không tin cậy thành mã script thực thi '
                    'trong trình duyệt của người dùng.'
                ),
                order=1,
            ),
            QuestionBlueprint(
                prompt='CSRF lợi dụng điều gì?',
                choices=(
                    'Trình duyệt đã đăng nhập gửi yêu cầu ngoài ý muốn',
                    'Một truy vấn chỉ đọc dùng tham số hóa',
                    'Một file CSS được nén',
                ),
                correct_choice=0,
                learning_objective=WEB_SECURITY_OBJECTIVES[0],
                explanation=(
                    'CSRF lừa trình duyệt có phiên đăng nhập gửi yêu cầu thay '
                    'đổi trạng thái mà người dùng không chủ ý.'
                ),
                order=2,
            ),
            QuestionBlueprint(
                prompt='SQL injection làm thay đổi thành phần nào?',
                choices=(
                    'Cấu trúc hoặc ý nghĩa câu truy vấn SQL',
                    'Độ phân giải video',
                    'Thuộc tính cache của CSS',
                ),
                correct_choice=0,
                learning_objective=WEB_SECURITY_OBJECTIVES[0],
                explanation=(
                    'SQL injection xảy ra khi input không an toàn can thiệp vào '
                    'cấu trúc truy vấn.'
                ),
                order=3,
            ),
            QuestionBlueprint(
                prompt='Control chính để phòng SQL injection là gì?',
                choices=(
                    'Ghép chuỗi input trực tiếp vào SQL',
                    'Dùng truy vấn tham số hóa',
                    'Ẩn nút submit bằng CSS',
                ),
                correct_choice=1,
                learning_objective=WEB_SECURITY_OBJECTIVES[1],
                explanation=(
                    'Truy vấn tham số hóa tách dữ liệu đầu vào khỏi cấu trúc SQL.'
                ),
                order=4,
            ),
            QuestionBlueprint(
                prompt='Khi hiển thị dữ liệu không tin cậy trong HTML, cần làm gì?',
                choices=(
                    'Mã hóa đầu ra theo đúng ngữ cảnh',
                    'Coi mọi input đã đăng nhập là an toàn',
                    'Chuyển toàn bộ dữ liệu thành câu SQL',
                ),
                correct_choice=0,
                learning_objective=WEB_SECURITY_OBJECTIVES[1],
                explanation=(
                    'Context-aware output encoding ngăn dữ liệu trở thành mã '
                    'thực thi trong HTML.'
                ),
                order=5,
            ),
            QuestionBlueprint(
                prompt='Nhận định nào đúng về input validation?',
                choices=(
                    'Nó thay thế mọi control bảo mật khác',
                    'Nó hữu ích nhưng không thay output encoding hay parameterized query',
                    'Nó chỉ cần thực hiện ở CSS',
                ),
                correct_choice=1,
                learning_objective=WEB_SECURITY_OBJECTIVES[1],
                explanation=(
                    'Validation giới hạn input nhưng mỗi sink vẫn cần control '
                    'đúng ngữ cảnh.'
                ),
                order=6,
            ),
            QuestionBlueprint(
                prompt='Authentication trả lời câu hỏi nào?',
                choices=('Người dùng là ai?', 'Người dùng sở hữu course nào?', 'API có nhanh không?'),
                correct_choice=0,
                learning_objective=WEB_SECURITY_OBJECTIVES[2],
                explanation='Authentication xác minh danh tính của người dùng.',
                order=7,
            ),
            QuestionBlueprint(
                prompt='Authorization quyết định điều gì?',
                choices=(
                    'Danh tính được phép thực hiện hành động nào trên tài nguyên',
                    'Mật khẩu có được băm bằng thuật toán nào',
                    'Trình duyệt dùng font chữ nào',
                ),
                correct_choice=0,
                learning_objective=WEB_SECURITY_OBJECTIVES[2],
                explanation=(
                    'Authorization kiểm tra quyền đối với hành động và tài '
                    'nguyên cụ thể.'
                ),
                order=8,
            ),
            QuestionBlueprint(
                prompt='Một giảng viên đã đăng nhập sửa course của giảng viên khác. Hệ thống phải làm gì?',
                choices=(
                    'Cho phép vì authentication đã thành công',
                    'Từ chối vì không có authorization trên course đó',
                    'Tự chuyển quyền sở hữu course',
                ),
                correct_choice=1,
                learning_objective=WEB_SECURITY_OBJECTIVES[2],
                explanation=(
                    'Đăng nhập chỉ xác minh danh tính; ownership authorization '
                    'vẫn phải từ chối hành động ngoài phạm vi.'
                ),
                order=9,
            ),
        ),
    ),
)


def validate_assessment_blueprints(
    blueprints: tuple[AssessmentBlueprint, ...] = ASSESSMENT_BLUEPRINTS,
) -> tuple[AssessmentBlueprint, ...]:
    """Validate bounded authoring data before any database access."""

    if not blueprints:
        raise AssessmentBlueprintError('At least one assessment blueprint is required')
    lesson_keys = [(item.course_slug, item.lesson_slug) for item in blueprints]
    if len(lesson_keys) != len(set(lesson_keys)):
        raise AssessmentBlueprintError('Assessment blueprint lesson keys must be unique')

    for blueprint in blueprints:
        if not 1 <= blueprint.pass_threshold <= 100:
            raise AssessmentBlueprintError('Pass threshold must be between 1 and 100')
        if not blueprint.title.strip() or len(blueprint.title) > 255:
            raise AssessmentBlueprintError('Assessment title is invalid')
        if len(blueprint.instructions) > 2000:
            raise AssessmentBlueprintError('Assessment instructions are too long')
        if not blueprint.objectives or len(set(blueprint.objectives)) != len(
            blueprint.objectives
        ):
            raise AssessmentBlueprintError('Assessment objectives are invalid')
        if not blueprint.questions or len(blueprint.questions) > 50:
            raise AssessmentBlueprintError('Assessment question count is invalid')

        orders = [question.order for question in blueprint.questions]
        prompts = [question.prompt.strip() for question in blueprint.questions]
        if orders != list(range(1, len(orders) + 1)):
            raise AssessmentBlueprintError('Question orders must be contiguous from one')
        if len(prompts) != len(set(prompts)):
            raise AssessmentBlueprintError('Assessment prompts must be unique')

        objective_counts = Counter()
        for question in blueprint.questions:
            if not question.prompt.strip() or len(question.prompt) > 2000:
                raise AssessmentBlueprintError('Question prompt is invalid')
            if not 2 <= len(question.choices) <= 6:
                raise AssessmentBlueprintError('Question choices are invalid')
            normalized_choices = [choice.strip() for choice in question.choices]
            if any(not choice or len(choice) > 500 for choice in normalized_choices):
                raise AssessmentBlueprintError('Question choice is invalid')
            if len(normalized_choices) != len(set(normalized_choices)):
                raise AssessmentBlueprintError('Question choices must be unique')
            if not 0 <= question.correct_choice < len(question.choices):
                raise AssessmentBlueprintError('Correct choice index is invalid')
            if question.learning_objective not in blueprint.objectives:
                raise AssessmentBlueprintError('Question objective is not declared')
            if not question.explanation.strip() or len(question.explanation) > 2000:
                raise AssessmentBlueprintError('Question explanation is invalid')
            objective_counts[question.learning_objective] += 1

        if any(
            objective_counts[objective] < QUESTIONS_PER_OBJECTIVE
            for objective in blueprint.objectives
        ):
            raise AssessmentBlueprintError(
                'Each objective requires at least three assessment questions'
            )

    return blueprints


def question_blueprint_payload(question: QuestionBlueprint) -> dict:
    return {
        'prompt': question.prompt,
        'choices': list(question.choices),
        'correct_choice': question.correct_choice,
        'learning_objective': question.learning_objective,
        'explanation': question.explanation,
        'order': question.order,
    }


def assessment_matches_blueprint(*, assessment, blueprint: AssessmentBlueprint) -> bool:
    """Compare persisted authoring state without mutating it."""

    if (
        assessment.title != blueprint.title
        or assessment.instructions != blueprint.instructions
        or assessment.pass_threshold != blueprint.pass_threshold
    ):
        return False
    current_questions = list(
        assessment.questions.order_by('order', 'id').values(
            'prompt',
            'choices',
            'correct_choice',
            'learning_objective',
            'explanation',
            'order',
        )
    )
    return current_questions == [
        question_blueprint_payload(question) for question in blueprint.questions
    ]
