export default function Landing() {
  return (
    <div className="relative overflow-hidden">
      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Học Lập Trình Web <br />
            <span className="text-primary-600">Cùng Trợ Lý AI</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Nền tảng học lập trình web dành riêng cho học sinh cấp 2, 
            với giao diện thân thiện và AI hỗ trợ 24/7
          </p>
          <div className="flex justify-center space-x-4">
            <a href="/register" className="btn btn-primary text-lg px-8 py-3">
              Bắt đầu học ngay
            </a>
            <a href="/courses" className="btn btn-secondary text-lg px-8 py-3">
              Xem khóa học
            </a>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="bg-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center mb-12">Tính năng nổi bật</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">🤖</span>
              </div>
              <h3 className="text-xl font-semibold mb-2">Trợ lý AI</h3>
              <p className="text-gray-600">Giải đáp thắc mắc, hướng dẫn làm bài tập 24/7</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">📚</span>
              </div>
              <h3 className="text-xl font-semibold mb-2">Bài giảng sinh động</h3>
              <p className="text-gray-600">Video, hình ảnh, ví dụ thực tế dễ hiểu</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">💬</span>
              </div>
              <h3 className="text-xl font-semibold mb-2">Cộng đồng</h3>
              <p className="text-gray-600">Forum trao đổi, học hỏi cùng bạn bè</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
