# 🏗️ Kiến trúc dự án — Bạn Cùng Học

## Tổng quan

MVP là một **Single Page Application (SPA) không dùng framework**, toàn bộ nằm trong `ban-cung-hoc-mvp.html`. Điều hướng thực hiện bằng cách show/hide các `<div class="view">` thay vì routing thật.

---

## 📁 Cấu trúc HTML Views

```
#view-home           → Trang chủ (bài viết nổi bật + khóa học)
#view-articles       → Danh sách bài viết
#view-article-reader → Đọc bài viết đơn
#view-courses        → Danh sách khóa học
#view-course-detail  → Chi tiết khóa học + danh sách bài học
#view-lesson         → Đọc bài học (2 cột: nội dung + sidebar)
#view-assessment     → Kiểm tra cuối khóa (MCQ)
#view-certificate    → Chứng chỉ hoàn thành

#notebook-drawer     → Drawer sổ tay (overlay từ phải)
.fab                 → Floating Action Button mở sổ tay
```

### Điều hướng

```js
go(viewName)         // Switch view đang active
openArticle(id)      // Mở bài viết theo ID
openCourse(id)       // Mở trang chi tiết khóa học
openLesson(cId, lId) // Mở bài học (set currentCourse + currentLesson)
startAssessment(cId) // Bắt đầu quiz cuối khóa
openCert(cId)        // Hiển thị chứng chỉ
```

---

## 🎨 Design Tokens (CSS Variables)

```css
/* Nền & mặt phẳng */
--bg: #f7f4ef          /* Cream ấm — background toàn trang */
--ink: #1a1814         /* Đen ấm — text chính */
--surface: #fff        /* Card/panel */
--surface2: #f0ece4    /* Surface thứ cấp */
--border: #ddd8cc
--border2: #c8c0b0
--muted: #9a9080       /* Text phụ nhạt */
--muted2: #6a6050      /* Text phụ đậm hơn */

/* Accent — Dược học */
--green: #1e4d38
--green-bg: #eaf4ee
--green-mid: #2d7a58   /* CTA chính */
--green-border: #aed4c0
--green-text: #143628

/* Accent — Tâm lý học */
--blue: #2a3f72
--blue-bg: #edf0f9
--blue-mid: #3d5fba
--blue-border: #b0c0e4
--blue-text: #1a2848

/* Accent — Premium/Chứng chỉ */
--purple: #5c2d70
--purple-bg: #f4eefa
--purple-mid: #8a4ab0
--purple-border: #d0b0e4
--purple-text: #3a1a48

/* Trạng thái */
--gold: #c07818        /* Warning / explain */
--gold-bg: #fdf5e4
--gold-border: #e8d090
--red: #b83c20         /* Sai / lỗi */
--red-bg: #fdf0ea

/* Layout */
--r: 10px              /* Border radius chuẩn */
--sh: 0 2px 12px rgba(26,24,20,.07)  /* Shadow card */
```

---

## 📊 Data Model

### Article

```js
{
  id: 'a1',
  tag: 'Dược học',
  tagClass: 'tag-green',        // tag-green | tag-blue | tag-purple
  title: 'Tiêu đề bài viết',
  excerpt: 'Tóm tắt ngắn...',
  readTime: '5 phút',
  date: '2024-01-15',
  content: `<HTML nội dung đầy đủ>`
}
```

### Course

```js
{
  id: 'c1',
  icon: '💊',
  iconClass: 'icon-green',      // icon-green | icon-blue
  tag: 'Dược học',
  tagClass: 'tag-green',
  title: 'Tên khóa học',
  desc: 'Mô tả ngắn',
  lessonCount: 3,
  lessons: [ /* xem Lesson bên dưới */ ],
  assessment: {
    questions: [ /* xem Question bên dưới */ ]
  }
}
```

### Lesson

```js
{
  id: 'l1',
  title: 'Tên bài học',
  duration: '12 phút',
  free: true,                   // false = Premium (khóa)
  essences: [
    { id: 'e1', text: 'Key point...' }
  ],
  quiz: [
    {
      q: 'Câu hỏi?',
      opts: ['A', 'B', 'C', 'D'],
      correct: 1,               // index 0-based
      explain: 'Giải thích HTML...'
    }
  ],
  content: `<HTML nội dung bài học>`
}
```

### Assessment Question

```js
{
  q: 'Câu hỏi?',
  opts: ['A', 'B', 'C', 'D'],
  correct: 2
}
```

---

## 🧠 State Management

Tất cả state dùng biến JS đơn giản — không có store/flux:

```js
// Tiến độ học
let completedLessons = new Set()     // Set<lessonId>
let savedEssences   = new Set()      // Set<essenceId>
let assessmentPassed = new Set()     // Set<courseId>
let lessonQuizScores = {}            // { lessonId: { correct, total } }

// Navigation
let currentCourseId  = null
let currentLessonId  = null
let currentArticleId = null

// Assessment quiz state
let quizQ = 0, quizCorrect = 0, quizAnswered = false
let quizQuestions = [], quizCourseId = null

// Lesson quiz state
let lq = { q: 0, correct: 0, answered: false, questions: [], lessonId: null }
```

---

## 🧩 Lesson View Layout

```
┌─────────────────────────────────────────────┐
│  ← Quay lại   [Tên khóa học]               │
├─────────────────────────┬───────────────────┤
│                         │  SIDEBAR (sticky) │
│  LESSON CONTENT         │                   │
│  ─ Tiêu đề bài          │  💡 Key Essences  │
│  ─ Nội dung HTML        │  [Lưu vào sổ tay] │
│                         │                   │
│  💡 Key Essence blocks  │  📊 Tiến độ       │
│  [Lưu] callout inline   │  khóa học         │
│                         │                   │
│  🧪 Kiểm tra nhanh      │                   │
│  3 MCQ cuối bài         │                   │
│                         │                   │
│  ← Prev   [Mark done]   │                   │
│                 Next →  │                   │
└─────────────────────────┴───────────────────┘
```

---

## 🔑 Key Essence System

Đây là tính năng phân biệt của nền tảng:

1. **Inline callout** — mỗi bài học có các block `.essence-block` có thể lưu
2. **Toggle** — `toggleEssence(id, lessonTitle, courseTitle)` — add/remove khỏi `savedEssences`
3. **Notebook drawer** — FAB `📋 Sổ tay` mở drawer bên phải liệt kê mọi essence đã lưu, phân nhóm theo khóa học
4. **Persistence** — hiện tại chỉ in-memory (mất khi reload); v0.2 sẽ lưu localStorage/backend

---

## 📝 Assessment Flow

```
openCourse()
  └─ canAssess = tất cả bài free đã completed?
       ├─ Chưa → button disabled
       └─ Rồi → startAssessment(courseId)
                  └─ renderQuestion2() → pickAnswer() → nextQ()
                       └─ showResult()
                            ├─ score < 80% → retry
                            └─ score ≥ 80% → assessmentPassed.add(courseId)
                                               └─ openCert(courseId)
```

---

## 🔮 Hướng phát triển kỹ thuật (v0.2+)

| Hạng mục | Hướng đề xuất |
|---|---|
| Framework | React hoặc SvelteKit (SSR cho SEO) |
| Backend | Supabase (Auth + DB + Storage) |
| Styling | Tailwind CSS với design tokens hiện tại |
| State | Zustand hoặc Svelte stores |
| Content | MDX hoặc Notion API làm CMS |
| Payments | Stripe (gói Premium) |
| Mobile | React Native hoặc PWA |
