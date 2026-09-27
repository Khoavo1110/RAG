# Quy trình viết văn học thuật và liêm chính bản thảo

**Áp dụng cho:** Chương phương pháp luận Agentic RAG 2.0 sau khi đã có nguồn, câu hỏi nghiên cứu và khung phương pháp. Đầu ra là bản thảo `artifacts/methodology_draft.md` (tính từ `.agents/`) và nhật ký rà soát trong báo cáo phản biện. Dùng `academic-paper` ở chế độ viết/chỉnh sửa, cùng [văn phong học thuật](../skills/academic-paper/references/academic_writing_style.md), [kiểm tra chất lượng văn bản](../skills/academic-paper/references/writing_quality_check.md), [đánh giá lập luận](../skills/academic-paper/references/writing_judgment_framework.md) và [ngăn nội dung thiếu nguồn](../skills/academic-paper/references/anti_leakage_protocol.md). Dùng [quy trình sàng lọc tính nguyên gốc](../skills/academic-pipeline/references/plagiarism_detection_protocol.md) cho bước rà soát trùng lặp.

**Mức áp dụng mặc định: bài môn học.** Không cần mua iThenticate, lập báo cáo liêm chính dài hoặc chạy sàng lọc web theo tỷ lệ mẫu cố định. Ưu tiên yêu cầu của giảng viên/trường nếu có. Quy trình tối thiểu: (1) rà từng đoạn vay mượn ý xem có trích nguồn ngay tại ý đó; (2) tìm thử bằng dấu ngoặc kép một vài câu đặc thù hoặc đoạn nghi ngờ trên công cụ tìm kiếm; (3) nếu môn học có Turnitin, xem các đoạn được đánh dấu và sửa theo ngữ cảnh; (4) kiểm tra lần cuối danh mục tài liệu tham khảo. Chỉ chuyển sang kiểm tra chuyên sâu ở mục 4 khi thấy đoạn khớp dài, nguồn khó xác minh hoặc giảng viên yêu cầu.

## 0. Hợp đồng người viết

Trước khi tạo câu văn, người viết nhận bốn đầu vào: (1) dàn ý với mục đích của từng tiểu mục; (2) ma trận tuyên bố và chứng cứ; (3) dấu vết triển khai, thí nghiệm và giới hạn thật của dự án; (4) chuẩn trích dẫn và quy định của nơi nộp. Nếu tác giả có 1–2 trang đã tự viết và muốn giữ giọng văn đó, rút ra **đặc điểm biên tập** như cách đặt câu, mức độ dùng thuật ngữ và cách nối ý. Không sao chép câu chữ từ mẫu, không giả tạo trải nghiệm cá nhân. Nếu chưa có mẫu, mặc định dùng tiếng Việt học thuật trực tiếp, chính xác và dễ đọc.

**Đầu ra bắt buộc của lượt viết:** bản nháp theo tiểu mục, danh sách `[CẦN NGUỒN]`/`[CẦN KIỂM CHỨNG]`, và bảng ngắn `đoạn → ý chính → chứng cứ → quyết định của tác giả`. Nhiệm vụ của `draft_writer_agent` trong `academic-paper` là viết đoạn hoàn chỉnh; người điều phối không được coi dàn ý, bullet list hay bản dịch sát nguồn là bản nháp đã hoàn thành.

**Ưu tiên riêng cho chương phương pháp:** Các quy tắc TEEL, độ dài đoạn, số câu dẫn chứng và nhịp câu trong skill `academic-paper` là gợi ý, không phải khuôn bắt buộc. Đoạn mô tả thủ tục có thể ngắn; đoạn biện minh một lựa chọn thiết kế có thể dài hơn. Không kéo dài đoạn để đủ chữ hoặc chèn câu chuyển ý không mang thông tin.

## 1. Viết từ luận điểm và chứng cứ

Trước mỗi tiểu mục, ghi một câu trả lời cho ba câu hỏi: *Phần này giúp trả lời câu hỏi nghiên cứu thế nào? Người đọc cần biết điều gì để tái lập? Bằng chứng nằm ở đâu?* Chia khung thành các tiểu mục theo luồng thực tế: dữ liệu và tiền xử lý; nạp hai kho; định tuyến và truy xuất; sinh câu trả lời và Critic; giao thức đánh giá; giới hạn.

Với mỗi đoạn, đi theo chuỗi sau. Đây là dụng cụ kiểm tra, không phải mẫu câu cứng:

1. **Ý chính:** Một mệnh đề cụ thể, đúng phạm vi của đoạn.
2. **Căn cứ:** Nguồn học thuật, vị trí mã, cấu hình, dữ liệu hoặc kết quả đo hỗ trợ mệnh đề.
3. **Giải thích:** Căn cứ đó hỗ trợ điều gì, trong điều kiện nào và chưa chứng minh điều gì.
4. **Liên kết:** Cho biết đoạn này phục vụ bước phương pháp hoặc giả thuyết nào.

Viết bản nháp từ ghi chú và ma trận nguồn bằng lời của mình. Sau đó mở lại nguồn để kiểm tra ý nghĩa, số liệu và ngữ cảnh; không diễn đạt lại bằng cách thay vài từ đồng nghĩa trên một câu gốc. Nếu nguồn không đủ, đặt nhãn `[CẦN NGUỒN]` hoặc `[CẦN KIỂM CHỨNG]`; không điền bằng suy đoán của mô hình.

**Ví dụ từ mã dự án:** Thay câu mơ hồ “Hệ thống nạp đồng thời dữ liệu vào hai kho để bảo đảm tính nhất quán” bằng “Quy trình nạp ghi tài liệu và các chunk vào PostgreSQL trước, sau đó gọi Graphiti để thêm episode. Nếu bước Graphiti thất bại, tài liệu vẫn tồn tại trong PostgreSQL; vì vậy chương phương pháp cần nêu rõ trạng thái nạp một phần và cách nhận biết nó (`backend/app/ingestion/database_sync.py`).” Câu thứ hai mô tả luồng quan sát được và chỉ ra giới hạn, không biến một đặc điểm chưa triển khai thành ưu điểm đã chứng minh.

## 2. Giữ ranh giới giữa tiếng nói tác giả và tài liệu tham khảo

| Loại nội dung | Cách viết | Yêu cầu truy vết |
| :--- | :--- | :--- |
| Kết quả hoặc ý tưởng của công trình khác | Tóm tắt trung thành, nêu tác giả và điểm liên quan | Trích dẫn ngay tại mệnh đề; kiểm tra tài liệu gốc |
| Thiết kế, mã và lựa chọn của dự án | Nói rõ “hệ thống hiện tại” hoặc “nghiên cứu này” | Đường dẫn mã, cấu hình, dữ liệu hoặc nhật ký thực nghiệm |
| Diễn giải hay suy luận của tác giả | Nêu cơ sở và mức chắc chắn | Phân biệt suy luận với điều nguồn khẳng định trực tiếp |
| Đề xuất chưa triển khai | Dùng thì dự kiến, nêu giả định và phép thử | Gắn nhãn `đề xuất`; không dùng động từ hàm ý đã đo |

Trích nguyên văn chỉ khi cách diễn đạt gốc tự nó cần phân tích; đặt trong ngoặc kép hoặc khối trích dẫn, ghi trang/vị trí nếu chuẩn trích dẫn yêu cầu. Bảng, hình, thuật toán, công thức, dữ liệu và bản dịch ý từ nguồn khác cũng cần ghi nguồn. Trích dẫn đúng nguồn không hợp thức hóa việc chép dài câu chữ; việc chuyển ngữ gần nguyên văn vẫn cần kiểm tra và ghi nguồn.

## 3. Chỉnh văn theo ba lượt

1. **Lượt cấu trúc:** Mỗi đoạn có chức năng rõ; các tiểu mục đi theo thứ tự xử lý và nêu đủ thông tin để tái lập. Cắt đoạn không làm thay đổi lập luận. Không lặp phần tổng quan trong chương phương pháp.
2. **Lượt nội dung:** Đối chiếu từng mệnh đề với nguồn và mã; kiểm tra thuật ngữ, điều kiện áp dụng, đơn vị đo, tên biến, hình/bảng và sự thống nhất của ký hiệu. Mức độ khẳng định phải tương ứng sức mạnh bằng chứng.
3. **Lượt câu chữ:** Ưu tiên câu ngắn, chủ thể và hành động rõ, thuật ngữ nhất quán. Bỏ câu mở đầu sáo rỗng, tính từ quảng cáo, đoạn chỉ liệt kê nguồn và câu quá dài. Đọc lại thành tiếng để tìm chỗ khó hiểu; sửa vì độ rõ, không vì mục tiêu qua bộ phát hiện AI.

### Biên tập để văn có tiếng nói nghiên cứu

Với mỗi tiểu mục, yêu cầu người viết trả lời bằng câu văn: **vì sao chọn cách này**, **đã làm cụ thể thế nào**, **lựa chọn đó đánh đổi điều gì**, và **điều kiện nào khiến cách làm có thể thất bại**. Chỉ viết điều có dấu vết trong tài liệu, mã hoặc thí nghiệm. Các quyết định thực như nạp PostgreSQL trước Graphiti, đường lỗi khi Graphiti thất bại, định tuyến ba nhánh và giới hạn vòng Critic tạo nên giọng riêng của nghiên cứu; tính từ “đột phá”, “toàn diện”, “tối ưu” không thay thế được chúng.

Khi một đoạn bị nhận xét là “giống văn AI”, sửa theo **chẩn đoán có vị trí**, không sửa bằng cách đổi từ hàng loạt:

| Dấu hiệu ở đoạn cụ thể | Cách sửa có ích |
| :--- | :--- |
| Câu đầu chỉ nói “trong bối cảnh phát triển mạnh mẽ…” | Mở bằng đối tượng, thao tác hoặc quyết định nghiên cứu cụ thể |
| Ba câu liên tiếp chỉ ca ngợi lợi ích chung | Giữ mệnh đề kiểm chứng được, thêm căn cứ và nêu điều kiện/giới hạn |
| Mỗi đoạn cùng nhịp “trước hết, tiếp theo, cuối cùng” | Sắp ý theo quan hệ nhân quả hoặc thứ tự xử lý thật; chỉ dùng từ nối khi cần |
| Đoạn nào cũng một độ dài và cùng mẫu luận điểm–dẫn chứng–kết luận | Cho mỗi đoạn một chức năng; gộp hoặc tách theo nội dung, không theo số chữ |
| Thuật ngữ bị thay liên tục bằng từ đồng nghĩa | Dùng một thuật ngữ nhất quán và định nghĩa một lần |
| Trích dẫn nhiều nhưng không thấy quyết định của tác giả | Viết rõ nguồn nào dẫn tới lựa chọn nào, và vì sao lựa chọn ấy phù hợp hệ thống này |

Sau lượt biên tập, tác giả đọc như người phản biện: gạch dưới câu nào mình không thể giải thích hoặc chỉ ra nguồn/mã; câu đó phải được sửa hoặc bỏ. Không hứa văn bản sẽ được công cụ gắn nhãn “do người viết”, vì nhãn ấy không đo trực tiếp chất lượng hay quyền tác giả.

## 4. Rà soát nguy cơ đạo văn và trùng lặp

Ở mức bài môn học, áp dụng cho **toàn bộ bản thảo** ở mức kiểm kê nguồn; kiểm tra sâu những đoạn có trích dẫn, định nghĩa đặc thù, số liệu, mô tả thuật toán, bảng/hình và đoạn được diễn đạt lại từ một nguồn. Chỉ cần ghi ngắn `vị trí đoạn → nguồn đối chiếu → hành động sửa` cho các đoạn thực sự có vấn đề. Quy trình chi tiết dưới đây dùng khi phát hiện rủi ro cụ thể hoặc nơi nộp yêu cầu.

- **Sao chép nguyên văn chưa đánh dấu:** Trích dẫn đúng quy cách nếu thật sự cần nguyên văn; nếu không, viết lại từ ý hiểu và vẫn trích nguồn.
- **Diễn đạt lại quá sát:** Đổi cấu trúc lập luận dựa trên sự hiểu đúng nội dung, không chỉ thay từ; kiểm tra lại ý và trích nguồn.
- **Mượn ý nhưng không ghi nguồn:** Bổ sung trích dẫn tại mệnh đề, không dồn một trích dẫn chung cuối nhiều đoạn.
- **Trùng với bài cũ của chính tác giả:** Ghi nguồn công trình trước, mô tả phần dùng lại và phần mới; kiểm tra quy định của cơ sở đào tạo/tạp chí về tái sử dụng văn bản, bảng và dữ liệu.
- **Nguồn thứ cấp:** Nếu chưa đọc tài liệu gốc, ghi đúng là trích dẫn thứ cấp theo chuẩn được yêu cầu hoặc tìm lại nguồn gốc trước khi dùng.

Kết quả tìm kiếm web, công cụ kiểm tra tương đồng hoặc phần mềm chuyên dụng là **tín hiệu để mở đoạn và so sánh ngữ cảnh**, không phải phán quyết tự động. Không đặt ngưỡng phần trăm giống nhau như tiêu chuẩn phổ quát: tài liệu tham khảo, tên kỹ thuật và mô tả thủ tục có thể tạo tương đồng hợp lệ, trong khi đạo ý tưởng có thể không hiện thành trùng chữ. Nếu dùng phần mềm của trường/tạp chí, lưu phiên bản báo cáo và xử lý từng vị trí bị đánh dấu. Không tuyên bố “không đạo văn” khi chưa có kiểm tra tương ứng.

## 5. Cổng hoàn thành bản thảo

- Mỗi đoạn có vai trò trong lập luận; mô tả phương pháp khớp mã hoặc ghi rõ là đề xuất.
- Mỗi ý vay mượn, dữ kiện và trích nguyên văn có nguồn đúng vị trí; các mục tài liệu tham khảo khớp trích dẫn trong bài.
- Không còn đoạn sao chép chưa đánh dấu, diễn đạt lại quá sát hoặc nguồn không xác minh được.
- Với bài môn học, chỉ cần ghi lại các đoạn trùng đáng kể đã sửa và điểm cần hỏi giảng viên; không cần báo cáo kiểm toán riêng nếu không được yêu cầu.
- Quy định của cơ sở đào tạo hoặc nơi nộp về trích dẫn, dùng AI và công bố việc dùng AI được kiểm tra trước khi nộp. Người viết chịu trách nhiệm cuối cùng về nội dung và tính nguyên gốc.
