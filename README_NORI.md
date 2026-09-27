# Nori — bản demo RAG mới

Backend và frontend được viết lại. Dữ liệu tiếp tục lưu trong PostgreSQL + pgvector của Docker hiện có. Neo4j cung cấp đồ thị tri thức; mô hình lấy từ `.env`, hiện dùng Ollama `qwen2.5:3b`. Không xóa volume và không thay `.env`.

## Chạy nhanh trên Windows

Mở Docker Desktop và Ollama. Tại `D:\RAG`:

```powershell
.\start-nori.ps1
```

Mở http://127.0.0.1:5173. API: http://127.0.0.1:8000/docs. Dừng hai ứng dụng bằng `.\stop-nori.ps1`; các container dữ liệu tiếp tục chạy.

Nếu cần cài lại thư viện:

```powershell
.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
cd frontend
npm ci
```

## Chạy cả ứng dụng trong Docker

```powershell
docker compose -f docker-compose.yml -f docker-compose.nori.yml up -d --build
```

Mở http://127.0.0.1:8080. Ollama phải đang chạy trên máy host và cho phép kết nối từ Docker; địa chỉ trong container là `host.docker.internal`. Chế độ local ở cổng 5173 và chế độ Docker cùng dùng cổng API 8000 nên hãy dừng ứng dụng local trước khi chạy Docker.

## Chức năng

- Chat dựa trên tài liệu, kết hợp truy xuất vector, văn bản và đồ thị khi có nguồn.
- Bộ kiểm chứng xem xét bản nháp; lỗi kiểm chứng được ghi rõ, không tự nhận đã kiểm chứng.
- Lịch sử hội thoại và tài liệu lưu trong PostgreSQL, có lọc theo không gian.
- Tải văn bản UTF-8 `.txt` / `.md` tối đa 1 MB. Vector và đồ thị được lập chỉ mục nền. Nếu embedding thất bại, tài liệu vẫn được lưu và tìm bằng văn bản.
- Xem nguồn, đọc tài liệu, tìm thư viện, xóa có xác nhận, giao diện sáng/tối và bố cục điện thoại.
- `cli.py` giữ nguyên các lệnh `ingest`, `query`, `chat` qua giao diện module tương thích mới.

Đây là demo cá nhân trên localhost. Bộ lọc không gian là phân vùng dữ liệu, không phải hệ thống xác thực/phân quyền nhiều người dùng. Chưa hỗ trợ đọc PDF/DOCX. Gemini embedding nhận nội dung văn bản khi lập chỉ mục, dù mô hình trả lời có thể chạy local qua Ollama. Redis hiện không được dùng cho hàng đợi; tác vụ lập chỉ mục chạy trong tiến trình API và chưa có cơ chế tự thử lại sau khi tiến trình dừng.

Neo4j đang có kết nối không có nghĩa là mọi tài liệu đã có đồ thị. Các tài liệu cũ thiếu `graphiti_episode_uuid` được tìm bằng pgvector/văn bản; tài liệu mới lưu UUID khi lập đồ thị thành công.

## Kiểm tra

```powershell
.venv\Scripts\python.exe -m pytest backend\tests -q
cd frontend
npm run build
npm run lint
```

Các kiểm thử dùng không gian riêng và dọn dữ liệu kiểm thử, không xóa tài liệu sẵn có. Các script trong `tests/` ở gốc là thí nghiệm lịch sử của phiên bản trước; dùng bộ kiểm thử mới trong `backend/tests` cho API Nori.
