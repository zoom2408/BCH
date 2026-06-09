# 🗺️ Roadmap — Bạn Cùng Học

## Tầm nhìn

Xây dựng nền tảng học tập thông minh nhất dành cho sinh viên y dược và tâm lý tại Việt Nam — nơi kiến thức được **hấp thụ sâu**, không chỉ đọc qua.

---

## 📍 Trạng thái hiện tại

**MVP v0.1 — Single-file prototype** ✅

---

## 🏁 Changelog

### v0.1.0 — MVP Launch *(2025-06)*

**Được xây dựng:**

- [x] Giao diện tổng thể: trang chủ, điều hướng, design system
- [x] Module **Bài viết**: danh sách + đọc bài đơn
- [x] Module **Khóa học**: danh sách khóa học theo chủ đề
- [x] **Trang chi tiết khóa học**: tiến độ, danh sách bài học, trạng thái mở khóa
- [x] **Bài học**: layout 2 cột (nội dung + sidebar), điều hướng prev/next
- [x] **Key Essence System**: inline callout lưu tinh hoa bài học → sổ tay
- [x] **Sổ tay (Notebook Drawer)**: FAB + drawer, phân nhóm theo khóa học
- [x] **Quiz cuối bài học**: 3 MCQ với giải thích, không tính điểm tổng
- [x] **Kiểm tra cuối khóa**: MCQ có điểm, pass ≥80%
- [x] **Chứng chỉ**: hiển thị sau khi vượt qua kiểm tra
- [x] Nội dung mẫu: 2 khóa học (Dược lý + Tâm lý), 6 bài học, 2 bài viết

---

## 🚀 Lộ trình phát triển

### v0.2 — Foundation *(Q3 2025)*

**Mục tiêu:** Chuyển từ prototype sang sản phẩm thực, có người dùng thật.

- [ ] **Tài khoản người dùng** (đăng ký / đăng nhập)
- [ ] **Lưu tiến độ** vào database (không mất khi reload)
- [ ] **Trang hồ sơ**: tiến độ khóa học, essences đã lưu, chứng chỉ
- [ ] Nội dung thật: 1 khóa học Dược lý hoàn chỉnh (10+ bài)
- [ ] Mobile responsive cải thiện
- [ ] Analytics cơ bản (bài nào được đọc nhiều nhất)

**Tech:** Supabase Auth + PostgreSQL, Next.js hoặc SvelteKit

---

### v0.3 — Growth *(Q4 2025)*

**Mục tiêu:** Monetization và mở rộng nội dung.

- [ ] **Gói Premium**: thanh toán qua Stripe / MoMo / ZaloPay
- [ ] Mở khóa bài Premium sau khi đăng ký
- [ ] Thêm 2–3 khóa học mới (Dược lâm sàng, Tâm lý lâm sàng)
- [ ] **Spaced Repetition**: nhắc ôn lại essence theo chu kỳ Leitner
- [ ] **Leaderboard** / điểm kinh nghiệm (XP) nhẹ
- [ ] Email digest hàng tuần: "Bạn chưa ôn 3 bài này"

---

### v0.4 — Community *(Q1 2026)*

**Mục tiêu:** Tạo cộng đồng học tập.

- [ ] **Bình luận** dưới bài học
- [ ] **Chia sẻ essence**: public/private notebook
- [ ] **Study group**: học cùng bạn bè, chia sẻ tiến độ
- [ ] Hệ thống **thăng cấp** (Level up sau khi hoàn thành khóa) ← *được đề xuất bởi user*
- [ ] **Badge / Achievement**: chứng chỉ theo kỹ năng
- [ ] Forum hỏi đáp theo chủ đề

---

### v1.0 — Scale *(Q2–Q3 2026)*

**Mục tiêu:** Trở thành nền tảng chuẩn mực cho sinh viên y dược Việt Nam.

- [ ] **Mobile app** (React Native / Flutter)
- [ ] **Offline mode**: tải bài học xuống học không cần mạng
- [ ] **AI Tutor**: chatbot giải thích dựa trên nội dung khóa học
- [ ] Liên kết với **trường đại học** (tín chỉ, chứng chỉ chính thức)
- [ ] **Marketplace nội dung**: giảng viên tự upload khóa học
- [ ] Hỗ trợ **tiếng Anh** (cho sinh viên thi USMLE, BPharm)

---

## 💡 Backlog / Ý tưởng

Các tính năng đang được cân nhắc, chưa xếp vào phase cụ thể:

- Flashcard tích hợp với Anki
- Podcast / audio bài học
- Case study tương tác (bệnh nhân ảo)
- Thi thử đề cương quốc gia
- Tích hợp PubMed / tài liệu y khoa

---

## 📏 Định nghĩa "Done" cho mỗi feature

| Tiêu chí | Mô tả |
|---|---|
| ✅ Functional | Tính năng hoạt động đúng với mọi edge case |
| ✅ Mobile-ready | Hiển thị tốt trên màn hình 375px+ |
| ✅ Accessible | Keyboard navigable, contrast ratio ≥ 4.5:1 |
| ✅ Tested | Ít nhất 1 user test thực tế |
| ✅ Documented | Cập nhật ARCHITECTURE.md nếu thay đổi data model |
