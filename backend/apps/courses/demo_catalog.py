"""Additive demo content; never copies learner records or fabricated RAG state."""

from pathlib import Path

from .learning_corpus import compile_learning_corpus


PHP_LESSONS = (
    ('php-va-luong-request', 'PHP và luồng xử lý một trang web', '''Mục tiêu: phân biệt mã chạy trên máy chủ với nội dung trình duyệt nhận được.

PHP xử lý yêu cầu ở máy chủ. Trình duyệt gửi một HTTP request; máy chủ chạy chương trình PHP và gửi response về. Trang HTML nhận được có thể chứa kết quả do PHP tạo ra. Trình duyệt không cần đọc mã nguồn PHP để hiển thị kết quả.

Ví dụ tối giản trong tệp hello.php:
<?php
echo 'Xin chào Intaaneto!';

Khi học, hãy phân biệt ba thành phần: tệp mã nguồn, chương trình thực thi PHP và trình duyệt. Mở tệp PHP như một tệp văn bản không tương đương với gửi yêu cầu tới máy chủ có PHP.

Thực hành: vẽ sơ đồ Trình duyệt → Máy chủ → PHP → Response. Ghi nơi mã PHP được chạy và nơi kết quả được hiển thị. Sau đó thay lời chào bằng tên một khóa học.

Tự kiểm tra: tại sao sửa mã PHP thường cần tải lại trang để thấy kết quả? Nội dung response có nhất thiết là HTML không?

Tham khảo: https://www.php.net/manual/en/intro-whatis.php'''),
    ('bien-va-kieu-du-lieu', 'Biến, kiểu dữ liệu và phép toán', '''Mục tiêu: lưu dữ liệu có tên và phân biệt chuỗi, số, giá trị đúng/sai.

Tên biến PHP bắt đầu bằng ký hiệu $. Tên biến phân biệt chữ hoa và chữ thường: $price và $Price là hai tên khác nhau. Hãy khởi tạo biến trước khi dùng và chọn tên diễn đạt ý nghĩa.

Ví dụ tính tổng tiền cho một đơn hàng giả lập:
<?php
$unitPrice = 120;
$quantity = 3;
$total = $unitPrice * $quantity;
$courseName = 'PHP cơ bản';
$isPublished = true;
echo $total;

Kết quả của phép nhân là 360. Chuỗi nằm trong dấu nháy, còn true là giá trị boolean. Dấu chấm dùng để nối chuỗi, ví dụ 'Khóa học: ' . $courseName.

Thực hành: thay số lượng bằng 5 rồi dự đoán kết quả trước khi chạy. Tạo thêm biến $discount để tính giá sau giảm. Đây là ví dụ số học, không phải cách tính tiền cho ứng dụng thương mại thực tế.

Tự kiểm tra: nếu viết nhầm $Quantity thay cho $quantity thì điều gì thay đổi? Vì sao tên $total dễ hiểu hơn tên $x?

Tham khảo: https://www.php.net/manual/en/language.variables.basics.php'''),
    ('dieu-kien-va-vong-lap', 'Điều kiện và vòng lặp', '''Mục tiêu: chọn nhánh xử lý và lặp một công việc có điểm dừng.

if và else giúp chương trình lựa chọn hành động theo một điều kiện. Vòng lặp for phù hợp khi biết cách khởi tạo, điều kiện tiếp tục và bước cập nhật.

Ví dụ minh họa ngưỡng điểm trong một bài tập độc lập:
<?php
$score = 8;
if ($score >= 5) {
    echo 'Đạt';
} else {
    echo 'Cần ôn tập';
}
for ($lesson = 1; $lesson <= 3; $lesson++) {
    echo 'Bài ' . $lesson . PHP_EOL;
}

Ngưỡng 5 chỉ phục vụ ví dụ PHP, không phải quy tắc chấm điểm của Intaaneto. Khi thiết kế vòng lặp, luôn kiểm tra điều kiện dừng để tránh lặp vô hạn.

Thực hành: thử các điểm 4, 5 và 6 để kiểm tra hai nhánh và ranh giới. Đổi vòng lặp để in số bài từ 1 đến 5. Dự đoán điều gì xảy ra nếu thay <= bằng <.

Tự kiểm tra: tại sao cần thử giá trị đúng tại ngưỡng? Phần nào của for làm biến đếm thay đổi?

Tham khảo: https://www.php.net/manual/en/language.control-structures.php'''),
    ('mang-va-ham', 'Mảng và hàm: tổ chức dữ liệu khóa học', '''Mục tiêu: quản lý nhiều giá trị và tách một phép tính thành hàm dùng lại.

Mảng PHP liên kết khóa với giá trị. Một danh sách có thể dùng khóa số; mảng kết hợp có thể dùng khóa chuỗi để đặt tên cho dữ liệu. foreach lần lượt duyệt các phần tử.

Ví dụ dùng dữ liệu học tập giả lập:
<?php
$course = ['title' => 'PHP cơ bản', 'lessons' => 5];
$durations = [20, 25, 30];
function totalMinutes(array $values): int {
    $total = 0;
    foreach ($values as $minutes) {
        $total += $minutes;
    }
    return $total;
}
echo $course['title'];
echo totalMinutes($durations);

Hàm nhận một mảng thời lượng và trả về tổng. Với dữ liệu ví dụ, tổng là 75 phút. Việc trả về một giá trị cho phép phần khác của chương trình sử dụng kết quả mà không cần hàm tự hiển thị.

Thực hành: thêm một bài dài 15 phút, dự đoán tổng mới. Thử mảng rỗng và giải thích kết quả. Tạo hai khóa giả lập rồi mô tả khóa nào dùng để truy cập tiêu đề.

Tham khảo: https://www.php.net/manual/en/language.types.array.php
https://www.php.net/manual/en/functions.user-defined.php'''),
    ('bieu-mau-va-du-lieu-dau-vao', 'Biểu mẫu và kiểm tra dữ liệu đầu vào', '''Mục tiêu: nhận dữ liệu biểu mẫu và hiển thị chuỗi như văn bản trong HTML.

Một biểu mẫu gửi bằng POST có thể được đọc qua $_POST. Dữ liệu người dùng gửi tới máy chủ không tự trở thành dữ liệu hợp lệ. Cần kiểm tra kiểu, giới hạn độ dài và các quy tắc của trường trước khi sử dụng.

Ví dụ xử lý một lời chào, không ghi dữ liệu hay thực hiện hành động nhạy cảm:
<?php
$name = $_POST['name'] ?? '';
if (!is_string($name) || strlen($name) > 100) {
    http_response_code(400);
    exit('Tên không hợp lệ');
}
echo 'Xin chào ' . htmlspecialchars($name, ENT_QUOTES, 'UTF-8');

htmlspecialchars giúp hiển thị các ký tự đặc biệt dưới dạng văn bản trong ngữ cảnh HTML này. Hàm này không thay thế kiểm tra dữ liệu, phân quyền, bảo vệ CSRF hay truy vấn cơ sở dữ liệu có tham số.

Thực hành: thử tên thông thường, trường bị bỏ trống, ký tự < và chuỗi quá dài. Ghi lại khác biệt giữa việc từ chối dữ liệu không hợp lệ và mã hóa dữ liệu khi hiển thị.

Tham khảo: https://www.php.net/manual/en/tutorial.forms.php'''),
)


def catalog_courses(source_root):
    courses = []
    for compiled in compile_learning_corpus(source_root):
        definition = compiled.definition
        courses.append({
            'slug': definition.slug, 'title': definition.title,
            'description': definition.description, 'duration_hours': definition.duration_hours,
            'objectives': '\n'.join(definition.objectives), 'prerequisites': definition.prerequisites,
            'cover': 'networks' if definition.source_file == 'computer-networks.md' else 'web',
            'lessons': [dict(slug=item.definition.slug, title=item.definition.title,
                             content=item.content, duration_minutes=item.definition.duration_minutes)
                        for item in compiled.lessons],
        })
    courses.append({
        'slug': 'demo-php-co-ban', 'title': 'PHP cơ bản qua ví dụ',
        'description': 'Năm bài học ngắn với ví dụ và bài tự luyện: luồng request, biến, điều kiện, mảng, hàm và biểu mẫu.',
        'duration_hours': 2, 'objectives': 'Đọc được mã PHP cơ bản.\nTự luyện với dữ liệu giả lập.\nNhận biết ranh giới dữ liệu đầu vào.',
        'prerequisites': 'Biết thao tác với tệp văn bản và có kiến thức HTML cơ bản.',
        'cover': 'php',
        'lessons': [dict(slug=slug, title=title, content=content, duration_minutes=25)
                    for slug, title, content in PHP_LESSONS],
    })
    return courses


COVER_ROOT = Path(__file__).resolve().parents[2] / 'assets' / 'course_covers'
