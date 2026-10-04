# ClassHub Frontend

Giao diện ClassHub được xây dựng bằng Vue 3, Vue Router và Vite. Frontend gọi REST API của backend và nhận cập nhật trạng thái tủ theo thời gian thực qua SignalR.

## Yêu cầu

- Node.js và npm
- ClassHub API có thể truy cập được từ trình duyệt

## Cài đặt và chạy

```sh
npm install
npm run dev
```

Các lệnh khác:

```sh
npm run build
npm run preview
```

`build` tạo bản triển khai trong `dist/`; `preview` phục vụ bản build đó để xem trước.

## Cấu hình API

Mặc định frontend dùng `http://localhost:5146/api` cho REST API; URL SignalR mặc định được suy ra từ URL API. Có thể cấu hình qua biến môi trường Vite:

```env
VITE_API_URL=http://localhost:5146/api
# Chỉ đặt khi SignalR Hub được host ở địa chỉ riêng:
# VITE_HUB_URL=http://localhost:5146
```

Tham khảo `.env.example`. Các biến `VITE_*` được đưa vào bundle frontend, vì vậy không đặt bí mật trong các biến này.

## Cấu trúc mã nguồn

- `index.html`: HTML shell; nạp `src/main.js`.
- `src/main.js`: khởi tạo Vue, router, CSS toàn cục và Font Awesome.
- `src/router.js`: khai báo route và kiểm tra phiên/quyền truy cập.
- `src/App.vue`: component gốc, hiển thị trang hiện hành qua `router-view`.
- `src/views/client/`: các trang dành cho người dùng.
- `src/views/admin/`: các trang quản trị.
- `src/views/auth/`: các trang đăng nhập và đăng ký.
- `src/views/NotFoundView.vue`: trang dự phòng cho route không tồn tại.
- `src/components/shared/`: component giao diện dùng chung giữa các trang.
- `src/components/admin/`: component dùng chung riêng trong khu vực quản trị, gồm layout và sidebar.
- `src/services/`: client REST, xử lý lỗi, phiên đăng nhập và kết nối SignalR.
- `src/config/`: cấu hình URL runtime.
- `src/assets/`: asset được import từ mã nguồn; `public/` chứa tài nguyên tĩnh được tham chiếu bằng đường dẫn gốc.
- `vite.config.js`: cấu hình Vite, plugin Vue/Tailwind và alias `@` trỏ tới `src/`.

## Route chính

- Người dùng: `/`, `/history`, `/info`, `/login`, `/register`.
- Quản trị: `/admin`, `/admin/cabinets`, `/admin/accounts`, `/admin/buildings`, `/admin/history`, `/admin/statistics`.

Các trang quản trị yêu cầu quyền `ADMIN`; các route được bảo vệ sẽ chuyển người dùng chưa đăng nhập tới `/login`.
