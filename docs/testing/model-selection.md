# Chọn model Local / API trong Nori

Ngày kiểm tra: 26/09/2026.

## Sử dụng

Mở http://127.0.0.1:5173, chọn Local hoặc API phía trên ô nhập, sau đó chọn model. Mỗi hướng nhớ lựa chọn riêng. Chuyển model mở cuộc trò chuyện mới để không trộn lịch sử giữa các model.

Khởi động từ D:\RAG: `powershell -ExecutionPolicy Bypass -File .\start-nori.ps1`. Nếu ứng dụng đang chạy, dùng ngay cửa sổ hiện tại; không khởi động thêm trên cùng cổng. Dừng bằng `.\stop-nori.ps1`.

## Cấu hình và phạm vi

Backend đọc config.yaml và .env của Hermes tại HERMES_HOME, hoặc các thư mục Hermes tiêu chuẩn. Trên máy này là C:\Users\vodan\AppData\Local\hermes. Không sao chép khóa sang frontend và không chỉnh cấu hình Hermes. Muốn nạp lại cấu hình/khóa mới, khởi động lại backend.

Có bốn provider API: Gemini, NVIDIA, Groq, OpenRouter. Catalog hiện có 4 model local và 18 model API. Model không có trong catalog của provider hoặc thiếu khóa bị vô hiệu hóa; trạng thái được liệt kê không bảo đảm đủ hạn mức hay suy luận thành công.

Model được chọn áp dụng cho sinh câu trả lời, kiểm chứng và hiệu chỉnh của từng yêu cầu, được cô lập bằng ContextVar. Truy xuất PostgreSQL/Neo4j dùng chung. Ingestion/embedding vẫn giữ cấu hình cũ; Local ở đây chỉ nói đến model trả lời, không bảo đảm toàn bộ hệ thống chạy ngoại tuyến. API nhận câu hỏi và các đoạn tài liệu truy xuất. Không tự chuyển provider khi lỗi.

## Bằng chứng kiểm tra

- Quy trình: các checkpoint RED cho profile lạ, bảo mật khóa, lỗi provider, điều kiện/người thực hiện, cấu hình Gemini và cô lập ingestion; sau đó chạy GREEN.
- Cơ học: 58 kiểm thử trong test_model_selection.py, test_rag_upgrade.py, test_api.py đều đạt. Có một cảnh báo deprecation Starlette/httpx. Coverage phạm vi agents và models đạt 94%; không phải coverage toàn dự án.
- Frontend: npm run build và npm run lint đạt. Kiểm tra trình duyệt chọn hai hướng, nhớ model NVIDIA, gửi đúng model_profile và màn hình rộng 390px không tràn ngang.
- Bằng chứng API: artifacts/rag-upgrade/model-selection-live-check.json và model-selection-final-adapter-check.json. Các hội thoại thử nghiệm đã được xóa sau khi ghi bằng chứng.
- Ngữ nghĩa: NVIDIA Super từng trả lời được Atlas (tăng 180 triệu, chia 120/60 cho hai nhà cung cấp, Nguyễn Linh phê duyệt) và hóa đơn (đúng các vai trò, Trần Mai phê duyệt thanh toán). Một lượt trước đó đảo vai trò và đổi ngưỡng không quá 60 giây thành dưới 60 giây; đã bổ sung kiểm tra điều kiện số và người thực hiện, cùng kiểm thử hồi quy.
- Giới hạn: lần kiểm tra sau NVIDIA vẫn có lượt không vượt kiểm chứng và trả trích đoạn; Gemini/Groq có lỗi 429. Vì vậy không tuyên bố nâng model đã giải quyết toàn bộ độ chính xác. Bộ kiểm chứng dùng model có thể bỏ sót lỗi; các ràng buộc bổ sung là kiểm tra bảo thủ, không thay thế đánh giá độc lập.
- Kiểm tra con người: đã đọc thủ công hai câu NVIDIA nêu trên; người dùng cần đánh giá thêm bộ 20 câu theo nguồn trước khi coi đây là hệ thống nghiệp vụ đáng tin cậy.

Khi không xác minh được, ứng dụng trả đoạn nguồn và lý do lỗi nếu có, thay vì trình bày bản tổng hợp như đã được kiểm chứng. Cấu hình Gemini dùng reasoning_effort low và giới hạn đầu ra 8192 token nhằm dành ngân sách cho JSON; không bảo đảm hết lỗi quota/đầu ra.

Commit chức năng chỉ gồm các file liên quan tới bộ chọn model và kiểm chứng. Workspace đã có nhiều thay đổi dựng lại ứng dụng từ trước; checkpoint này không phải ảnh triển khai độc lập của toàn bộ dự án.
