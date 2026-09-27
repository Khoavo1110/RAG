# Nori frontend

React + TypeScript + Vite. Giao diện chat tiếng Việt, thư viện tài liệu, nguồn tham khảo, lịch sử hội thoại và giao diện sáng/tối.

Chạy từ thư mục frontend:

```powershell
npm ci
npm run dev
```

API được proxy đến `http://127.0.0.1:8000`. Có thể đặt `VITE_API_URL` nếu backend chạy ở địa chỉ khác. `npm run build` kiểm tra TypeScript và tạo bản build; `npm run lint` kiểm tra mã nguồn.
