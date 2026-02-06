export default function Landing() {
  return (
    <div className="fixed inset-0 overflow-auto">
      {/* Background Image */}
      <div 
        className="fixed inset-0 bg-cover bg-center bg-no-repeat -z-10"
        style={{ backgroundImage: 'url(/images/background2.png)' }}
      ></div>

      {/* Content */}
      <div className="relative z-10 min-h-screen">
        {/* Hero Section */}
        <main className="px-8">
          <div className="max-w-7xl mx-auto min-h-screen flex flex-col justify-center items-center text-center pt-32">
            <h1 className="text-7xl md:text-8xl font-black text-white mb-12 tracking-tight leading-none">
              INTAANETO
            </h1>
            <p className="text-2xl md:text-3xl font-light text-white mb-4 tracking-wide animate-typing overflow-hidden whitespace-nowrap border-r-4 border-orange-500 pr-2 inline-block" 
               style={{ 
                 textShadow: '0 0 20px rgba(249,115,22,0.8), 0 0 40px rgba(249,115,22,0.5), 0 0 60px rgba(249,115,22,0.3)',
                 animation: 'typing 8s ease-in-out infinite, blink-caret 0.75s step-end infinite'
               }}>
              Nền tảng Học Lập Trình Trực Tuyến
            </p>

            {/* Feature Cards */}
            <div className="grid md:grid-cols-2 gap-6 mt-12 w-full max-w-4xl">
              {/* Organization Card */}
              <div className="group relative">
                <div className="absolute -inset-0.5 bg-gradient-to-r from-pink-600 to-purple-600 rounded-2xl blur opacity-30 group-hover:opacity-50 transition"></div>
                <div className="relative p-8 bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl hover:bg-white/20 transition-all">
                  <div className="flex items-center gap-4 mb-3">
                    <div className="w-12 h-12 rounded-lg bg-white/20 flex items-center justify-center">
                      <span className="text-2xl">🎓</span>
                    </div>
                    <div className="text-left">
                      <p className="text-sm text-white/70 mb-1">Nền tảng</p>
                      <p className="text-xl font-bold text-white">Học Tập Online</p>
                    </div>
                  </div>
                  <p className="text-white/80 text-left">
                    Khóa học từ cơ bản đến nâng cao với lộ trình rõ ràng
                  </p>
                </div>
              </div>

              {/* Partners Card */}
              <div className="group relative">
                <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-600 to-cyan-600 rounded-2xl blur opacity-30 group-hover:opacity-50 transition"></div>
                <div className="relative p-8 bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl hover:bg-white/20 transition-all">
                  <div className="flex items-center gap-4 mb-3">
                    <div className="w-12 h-12 rounded-lg bg-white/20 flex items-center justify-center">
                      <span className="text-2xl">🤖</span>
                    </div>
                    <div className="text-left">
                      <p className="text-sm text-white/70 mb-1">Công nghệ</p>
                      <p className="text-xl font-bold text-white">AI Assistant</p>
                    </div>
                  </div>
                  <p className="text-white/80 text-left">
                    Trợ lý AI hỗ trợ học tập 24/7 thông minh và hiệu quả
                  </p>
                </div>
              </div>
            </div>

            {/* CTA Button */}
            <div className="mt-16">
              <a 
                href="/register" 
                className="inline-block px-12 py-4 rounded-full bg-white text-gray-900 hover:bg-gray-100 transition-all font-bold text-lg shadow-2xl hover:shadow-3xl transform hover:scale-105"
              >
                Bắt đầu học ngay
              </a>
            </div>
          </div>

          {/* Features Section */}
          <div className="max-w-7xl mx-auto py-20">
            <h2 className="text-4xl font-bold text-white text-center mb-16">
              Tính năng nổi bật
            </h2>
            <div className="grid md:grid-cols-3 gap-8">
              {[
                {
                  title: 'Khóa học chất lượng',
                  description: 'Nội dung được biên soạn bài bản, cập nhật liên tục',
                  icon: '📚',
                  gradient: 'from-orange-500 to-red-500'
                },
                {
                  title: 'Bài tập thực hành',
                  description: 'Hệ thống bài tập đa dạng, kiểm tra tự động',
                  icon: '💻',
                  gradient: 'from-purple-500 to-pink-500'
                },
                {
                  title: 'Cộng đồng sôi động',
                  description: 'Diễn đàn thảo luận và chia sẻ kiến thức',
                  icon: '👥',
                  gradient: 'from-blue-500 to-cyan-500'
                }
              ].map((feature, idx) => (
                <div key={idx} className="group relative">
                  <div className={`absolute -inset-0.5 bg-gradient-to-r ${feature.gradient} rounded-2xl blur opacity-20 group-hover:opacity-40 transition`}></div>
                  <div className="relative p-8 bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl hover:bg-white/15 transition-all text-center">
                    <div className="text-5xl mb-4">{feature.icon}</div>
                    <h3 className="text-2xl font-bold text-white mb-3">{feature.title}</h3>
                    <p className="text-white/80">{feature.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </main>

        {/* Footer */}
        <footer className="px-8 py-8 border-t border-white/10">
          <div className="max-w-7xl mx-auto text-center">
            <p className="text-white/60">&copy; 2026 Intaaneto. All rights reserved.</p>
          </div>
        </footer>
      </div>
    </div>
  )
}
