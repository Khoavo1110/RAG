# BÁO CÁO KIỂM TRA TỔNG QUÁT KIẾN TRÚC & KẾ HOẠCH TỐI ƯU HÓA AGENTIC RAG 2.0

> **Thời điểm lập:** 26/09/2026 — 23:50  
> **Dự án:** Agentic RAG 2.0 (PostgreSQL/PGVector + Neo4j Graphiti + LangGraph Reasoning Loop)  
> **Dữ liệu thực nghiệm kiểm chứng:** `data/demo-doanh-nghiep/minh-an/` (22 tài liệu, 20 ca kiểm thử `CAU_HOI_TEST.md`)  
> **Mã lưu trữ bộ nhớ dài hạn:** `agentmemory` (`mem_muimjvpq_f999d6cc45e3`)

---

## 1. TỔNG QUAN KIẾN TRÚC HIỆN TẠI (CURRENT ARCHITECTURE)

Hệ thống hiện tại gồm 4 tầng chức năng:
1. **Tầng Lưu trữ kép (Dual-Store Ingestion):**
   - **PostgreSQL 16 (PGVector):** Lưu trữ toàn văn chia chunk 1.000 ký tự (overlap 200 ký tự).
   - **Neo4j 5 (Graphiti):** Trích xuất đồ thị tri thức động (Temporal Knowledge Graph - TKGs) theo episodes.
2. **Tầng Truy xuất tích hợp (Hybrid Retrieval & Expansion):**
   - Tìm kiếm từ khóa BM25 (`lexical_search`) + Tìm kiếm ngữ nghĩa vector (`vector_search_tool` với cosine distance < 0.65).
   - Hợp nhất điểm xếp hạng theo công thức Reciprocal Rank Fusion (`fuse_sources`).
   - Mở rộng ngữ cảnh tham chiếu chéo tối đa 2 bước nhảy (`expand_evidence`).
3. **Tầng Sinh câu trả lời (Grounded Generator):**
   - Prompt yêu cầu LLM trích dẫn nguyên văn bằng cấu trúc JSON:
     `{"claims": [{"quote": "...", "source_id": 1, "text": "..."}], "missing_information": []}`
4. **Tầng Kiểm duyệt hai chiều (Critic Verification):**
   - Hàm `render_grounded_answer` kiểm tra tính hợp lệ của quote và câu chữ.
   - Hàm `verify_answer` gọi LLM độc lập kiểm tra `is_valid` và `complete`.
   - Cơ chế cứu hộ: Fallback về `extractive_answer` nếu kiểm duyệt không đạt qua 2 lần thử.

---

## 2. BẢNG TỔNG HỢP CÁC LỖI KỸ THUẬT & SAI SÓT LOGIC ĐÃ XÁC THỰC

Qua thực nghiệm chạy thử trên câu hỏi thực tế của bộ hồ sơ Minh An Supply, hệ thống bộc lộ **6 điểm nghẽn cốt tử** sau:

| STT | Vị trí Module | Loại lỗi | Hiện tượng thực tế | Nguyên nhân kỹ thuật cụ thể |
| :---: | :--- | :---: | :--- | :--- |
| **1** | `backend/app/agents/router.py`<br>(dòng 74, 79–80) | **BUG KỸ THUẬT NGHIÊM TRỌNG** | RAG tìm đúng tài liệu, LLM trả lời đúng người phụ trách, nhưng màn hình hiển thị: *"Tôi chưa xác nhận được bản tổng hợp..."* | `render_grounded_answer` bắt buộc trường `text`. Khi LLM chỉ trả về `quote` và `source_id` thì `text is None` $\rightarrow$ hàm return `None` $\rightarrow$ vứt bỏ toàn bộ câu trả lời đúng của LLM. |
| **2** | `backend/app/agents/router.py`<br>(dòng 77) | **Cơ chế so khớp quá cứng nhắc** | Câu trả lời đúng bị đánh rớt nếu LLM tổng hợp nhiều ý thành một câu. | Lệnh `normalize(quote) not in normalize(...)` bắt buộc chuỗi con phải trùng khớp 100% từng ký tự. Khi LLM nối 2 câu trong tài liệu lại với nhau, hàm báo `False`. |
| **3** | `backend/app/agents/router.py`<br>(dòng 205–208) | **Lỗi cơ chế Fallback** | Trải nghiệm người dùng bị hỏng; RAG trông như bị "đơ" hoặc "từ chối trả lời". | Khi khâu kiểm duyệt không đạt qua 2 chu kỳ, code tự động kích hoạt `extractive_answer` ném ra nguyên văn văn bản thô thay vì hiển thị câu trả lời đã tổng hợp. |
| **4** | `backend/app/agents/tools.py`<br>(dòng 58, 121) | **Điểm nghẽn Truy xuất (Retrieval)** | Các câu hỏi tự nhiên không có mã viết hoa gạch ngang (như `CR-07`, `PRJ-AT-01`) bị thiếu ngữ cảnh trầm trọng. | Regex `CODE = re.compile(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\b")` chỉ bắt mã văn bản. Nếu người dùng hỏi tên người hoặc câu hỏi thông thường, bộ neo `anchors` trả về rỗng, làm đứt gãy chuỗi logic đa chặng. |
| **5** | `backend/app/agents/tools.py`<br>& `router.py` | **Lỗi Logic Thời gian (Temporal Inversion)** | Câu T02 trả lời sai mốc vận hành: lấy ngày cũ 15/10/2026 thay vì ngày mới 21/10/2026. | Cả BM25 và Vector đều không có trọng số thời gian (Recency Weighting). Văn bản điều lệ gốc dài hơn, lặp lại nhiều từ khóa hơn nên được xếp trước văn bản thay đổi `CR-07` và `STEER-09`. |
| **6** | `backend/app/agents/router.py`<br>(Prompt Instruction) | **Lỗi Ảo giác & Tính toán số học** | - Câu T15 (hỏi lương Lê Quang, lợi nhuận) bị trả lời mò mẫm.<br>- Câu T03, T04 bị cộng trùng số tiền (double-counting). | - Prompt thiếu lệnh cấm suy đoán dứt khoát đối với thông tin không có trong tài liệu.<br>- LLM không có công cụ tính toán số học (Calculator) nên tự nhẩm số tiền bị sai. |

---

## 3. LỘ TRÌNH TỐI ƯU HÓA HOÀN HẢO (ACTIONABLE FIX ROADMAP CHO NGÀY MAI)

### Pha 1: Khắc phục sự cố tắc nghẽn Kiểm duyệt (Ưu tiên cao nhất — 15 phút)
- **Tệp:** `backend/app/agents/router.py`
- **Hành động:**
  1. Trong `render_grounded_answer`: Nếu `text is None` hoặc rỗng, tự động gán `text = quote`.
  2. Nới lỏng so khớp chuỗi: Thay vì `quote not in content` 100%, sử dụng tỷ lệ trùng khớp từ vựng (token overlap $\ge 75\%$) hoặc cho phép so khớp theo từng cụm câu.
  3. Xóa bỏ hoặc làm mềm hàm `extractive_answer`: Khi verification bị fail nhẹ hoặc timeout, **vẫn xuất ra câu trả lời tổng hợp** kèm nhãn chú thích `[chưa kiểm chứng toàn phần]` thay vì xóa sạch câu trả lời và ném text thô.

### Pha 2: Cải tiến Bộ định tuyến & Trọng số Thời gian (Temporal Override — 30 phút)
- **Tệp:** `backend/app/agents/tools.py`
- **Hành động:**
  1. **Trích xuất mốc thời gian văn bản:** Nhận diện các mốc ngày tháng trong tiêu đề/đầu tệp (ví dụ `CR-07` ngày 18/09, `STEER-09` ngày 22/09 > `PRJ-AT-01` ngày 15/08).
  2. **Thêm hệ số Recency Boost:** Khi xếp hạng tài liệu cùng chủ đề, tài liệu có ngày hiệu lực mới nhất được nhân hệ số ưu tiên $1.3 \times$ để luôn nằm ở vị trí `[1]`, `[2]` trong context.
  3. Bổ sung nhận diện tên riêng thực thể (Named Entities: "Phạm Huy", "Lê Quang", "Mai Vy", "Bắc Sao Tech") vào `expand_evidence` chứ không chỉ bắt mỗi mã viết hoa gạch ngang.

### Pha 3: Tinh chỉnh Prompt Chống Ảo giác & Chống Bẫy Tiền đề (20 phút)
- **Tệp:** `backend/app/agents/router.py` (Prompt `instruction`)
- **Hành động:**
  1. **Quy tắc Vàng về Thiếu dữ liệu (Missing Data Rule):**
     *"Nếu thực thể hoặc số liệu được hỏi (như tiền lương nhân sự, lợi nhuận công ty) hoàn toàn không có văn bản nào đề cập, BẮT BUỘC ghi vào missing_information hoặc trả lời rõ ràng: 'Tài liệu không cung cấp thông tin này', TUYỆT ĐỐI KHÔNG ĐƯỢC TỰ Ý SUY ĐOÁN."* (Giải quyết dứt điểm câu T15, T16, T17).
  2. **Quy tắc Chống Bẫy Tiền đề sai (False Premise Rule):**
     *"Kiểm tra mốc thời gian của nguyên nhân và kết quả. Nếu câu hỏi gán ghép sự kiện xảy ra sau làm nguyên nhân cho sự kiện xảy ra trước (ví dụ sự cố tháng 9 gây giảm chỉ số tháng 8), PHẢI BÁC BỎ TIỀN ĐỀ CỦA CÂU HỎI."* (Giải quyết câu T11).
  3. **Quy tắc Tính toán & Tránh cộng trùng (Math & No Double-Counting):**
     *"Khi tính tổng ngân sách, kiểm tra xem số tiền thay đổi (CR) đã được gộp vào ngân sách điều chỉnh hay chưa. Nếu đã gộp, không được cộng lặp lại lần 2."* (Giải quyết câu T03, T04).

---

## 4. Ý NGHĨA KHOA HỌC ĐỐI VỚI LUẬN VĂN & HỘI ĐỒNG IUH

Việc chúng ta tìm ra đúng các lỗi này và có kế hoạch khắc phục bài bản là một **lợi thế học thuật khổng lồ**:
1. **Chứng minh năng lực kiểm thử thực tế:** Khác với các đồ án chỉ chạy thử câu hỏi dễ rồi "vẽ" số liệu đẹp, đề tài của bạn có một bộ **Stress Test thực tế 20 ca kiểm thử chuyên sâu của doanh nghiệp**.
2. **Liêm chính khoa học:** Luận văn có hẳn một chương phân tích các dạng lỗi thất bại (Failure Modes) và quá trình tinh chỉnh khắc phục (Refinement & Optimization). Đây chính là tiêu chí để giảng viên chấm điểm A+ tối đa!
