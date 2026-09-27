# Báo cáo rà soát và biên tập luận văn

Ngày biên tập: 27/09/2026. Tệp được chỉnh: `LUAN_VAN_AGENTIC_RAG_2.0_HOAN_CHINH.md`. Phạm vi: bố cục, phương pháp, số liệu, diễn đạt học thuật và trích dẫn APA 7; không sửa mã hoặc chạy lại benchmark.

## 1. Những lỗi đã xử lý

| Vị trí bản gốc | Vấn đề | Quyết định biên tập |
|---|---|---|
| Mục lục và thân bài | Thiếu Chương 2; thiếu đầu Chương 3; Chương 4 xuất hiện trước mục 3.2 và bị lặp | Sắp lại đủ sáu chương, các mục theo đúng thứ tự |
| Bìa và tóm tắt | Đưa tên công cụ điều phối, APA và CLI vào thông tin học thuật/từ khóa; còn từ ngoại ngữ “construido” | Dùng thông tin tác giả cần bổ sung, tóm tắt theo mục tiêu–phương pháp–kết quả–giới hạn |
| Chương 1, 2, 6 | Nhiều khẳng định tuyệt đối: đầu tiên, triệt tiêu hoàn toàn, 100% sẵn sàng | Chuyển thành mệnh đề có điều kiện và phạm vi kiểm chứng |
| Chương 3 | LangGraph, định tuyến ba nhánh, chia đoạn 1000/200, 7 lần gọi LLM, P95 suy từ trung bình không khớp luồng phục vụ | Viết lại từ mã; phân biệt hàm tương thích với luồng thực thi |
| Chương 4, 5 | 100 câu, hai chuyên gia, κ=0,87, bốn baseline không có hồ sơ tương ứng | Bỏ khỏi kết quả đã đạt; dùng bộ 22 tài liệu hư cấu và 20 ca đã lưu |
| Chương 5 | Điểm RAGAS khớp mock_metrics; bảng còn không khớp chính tệp được dẫn | Không dùng làm số đo thực |
| Chương 5 | t-test, p-value, router 94%, token và lỗi stale facts thiếu dữ liệu nguồn | Loại khỏi kết luận; mô tả kế hoạch đánh giá tiếp |
| Chương 5, 6 | Xem phản hồi trích đoạn như tổng hợp thành công | Báo cáo riêng 0/20 verified, 20/20 extractive tại mốc lịch sử |
| Toàn bài | Câu dài, nhiều tính từ quảng cáo, nhịp liệt kê và thuật ngữ đổi liên tục | Biên tập theo chức năng đoạn; dùng thuật ngữ nhất quán |

Tên đề tài được rút gọn để phản ánh đúng nội dung được bảo vệ. Nếu đã đăng ký tên đề tài chính thức, tác giả cần đối chiếu với hồ sơ của trường.

## 2. Kiểm tra số liệu đã giữ

Tính lại bằng đọc JSON, không gọi API. Lệnh hoàn tất với mã thoát 0:

- T01–T18: mean source recall 0,7500 → 0,9675925926; số ca đủ nguồn 8/18 → 16/18.
- T15 thiếu INV-BS-041; T17 thiếu FIN-POL-01.
- `after.json`: 20 ca; verified=0; extractive=20; no_evidence=0.
- Trung vị thời gian 27,51 giây; lớn nhất 111,00 giây. T20 gồm hai lượt hội thoại.
- API mốc riêng: T03 23,31 giây/12 nguồn; T06 79,00 giây/12 nguồn; T19 1,47 giây/0 nguồn; cả ba HTTP 200.

Recall ở đây kiểm tra mã tài liệu trong tiêu đề, khác Context Recall của RAGAS. Hai cấu hình khác ngân sách. Tệp evaluate.py truyền danh sách vector và graph rỗng trong phép đo nguồn. Không suy ra tác dụng riêng vector/RRF/Graphiti hoặc độ đúng câu trả lời.

## 3. Rà soát tài liệu tham khảo

Đã đối chiếu siêu dữ liệu và nội dung liên quan từ nguồn chính thức: arXiv, ACL Anthology, NeurIPS và bài gốc RRF. Bản sửa giữ bảy tài liệu thực sự được trích trong nội dung, sắp theo tên tác giả, ghi đầy đủ danh sách tác giả và DOI/URL.

- Self-RAG: sửa Wu, Y. thành Wu, Z.
- RAGAS: sửa tác giả thành Es, James, Espinosa Anke, Schockaert; dùng bản hội nghị EACL 2024, DOI 10.18653/v1/2024.eacl-demo.16.
- GraphRAG: ghi đủ 10 tác giả, kết thúc bằng Larson, J.
- Zep/Graphiti: dùng Rasmussen et al. (2025), arXiv:2501.13956; mã 2506.08742 trong bản gốc trỏ tới bài toán học.
- Corrective RAG: sửa đầy đủ tác giả Yan, Gu, Zhu, Ling.

Các mục dưới đây bị loại vì mã được dẫn không khớp tên bài:
- LabourCrew, 2603.01245: trang arXiv là *Insights for an AI Whistleblower Office from 30 Case Studies*.
- EvalMem, 2609.04521: trang arXiv là *A Polymatroidal Perspective on Random Contraction*.
- Khảo sát Agentic RAG, 2501.09876: trang arXiv là *Geometry-Preserving Encoder/Decoder in Latent Generative Models*.
- Chronofy, 2607.02134: trang arXiv là *Coding-agents can replicate scientific machine learning papers*.
- Truy xuất tài chính, 2609.01892: trang arXiv là bài về SUSY và LZ.

Kết luận trên chỉ nói mã định danh trong bản gốc sai, không khẳng định không tồn tại bất kỳ công trình nào có tên tương tự.

## 4. Phân biệt phiên bản

Trong lúc rà soát, mã nguồn được thay đổi bên ngoài lượt biên tập luận văn. Cuối lượt đọc ghi nhận:

| Tệp | SHA-256 |
|---|---|
| backend/app/agents/tools.py | D0788650D575379776342F07A61BBDFBA74CD42FE45DF5955C29E332DF3566A4 |
| backend/app/agents/router.py | 18D643BC5BBFE7607D562316311A7322FA9E00ABD98E66E9355A685F9493AF87 |
| backend/app/agents/critic.py | 8E4EDA545A6882FE32A392CF1D722826A3EA96AE62F32D2DF27DF62E3361499D |

Bản mới thêm ưu tiên sửa đổi 1,3, danh sách thực thể, đối sánh quote mềm và unverified_draft. Hàm tương thích LangGraph đã có, nhưng agentic_rag_app vẫn là AgenticRAG. Chương 3 mô tả rõ các đặc điểm này; Chương 5 không gán kết quả cũ cho chúng. Nếu mã tiếp tục đổi sau mốc trên, cần đối chiếu lại trước khi nộp.

## 5. Kiểm tra theo năm lớp

1. Quy trình: xác định tệp và phạm vi, đọc kỹ năng học thuật, lập bản sửa trước khi ghi.
2. Cơ học: kiểm tra thứ tự chương/mục, bảng, khối mã, số liệu và liên kết tệp.
3. Bằng chứng: đối chiếu JSON, script, mã nguồn và siêu dữ liệu tài liệu tham khảo.
4. Ngữ nghĩa: tách truy xuất khỏi tổng hợp; tách mã hiện tại khỏi lượt đo; giữ kết quả không đạt và giới hạn.
5. Con người: còn cần tác giả bổ sung thông tin bìa, xác nhận tên đề tài và kiểm tra mẫu trường trước nộp.

Bản Markdown đã chuẩn hóa nội dung trích dẫn APA 7. Nó chưa tự xác lập lề, phông, giãn dòng, số trang, thụt treo hoặc mục lục tự động của bản Word/PDF. Khi dàn trang, dùng mẫu trường; danh mục tham khảo cần thụt treo 1,27 cm. Chưa chạy Turnitin và không tuyên bố đã kiểm tra tương đồng hoặc qua bộ phát hiện AI.

Chỉ chỉnh tệp tổng hợp được yêu cầu. Các tệp chương rời 01–07 và tệp phương pháp luận cũ chưa được đồng bộ, không dùng để ghép lại đè lên bản sửa.

## 6. Các điểm tác giả cần hoàn thiện

- [CẦN KIỂM CHỨNG] Tên đề tài đã đăng ký, loại luận văn và quy định trường/khoa.
- [CẦN KIỂM CHỨNG] Cấu hình máy và môi trường của từng lượt thực nghiệm nếu muốn bổ sung.
- [CẦN KIỂM CHỨNG] Phiên bản dữ liệu, prompt, model digest và snapshot mã nếu tái chạy.
- [CẦN NGUỒN] Nhật ký gán nhãn/chấm độc lập trước khi tuyên bố đáp án chuẩn chuyên gia.
- [CẦN KIỂM CHỨNG] Quy định công bố việc sử dụng công cụ hỗ trợ biên tập của trường.

Không điền các thông tin còn thiếu bằng dữ liệu giả định.

## 7. Kết quả kiểm tra sau khi lưu

Đã đọc lại tệp trên đĩa: đủ sáu chương, bảy mục tham khảo khớp trích dẫn, khối mã cân bằng và các đường dẫn bằng chứng tồn tại. Mã băm bản sao khớp bản gốc; mã băm ba tệp nguồn tại thời điểm lưu khớp mốc đã mô tả. Hai lượt rà soát cuối về kiến trúc và số liệu không phát hiện sai lệch nghiêm trọng. Đã sửa ba chỗ diễn đạt nhỏ về thứ tự số liệu, cách gọi trạng thái và phạm vi mở rộng tham chiếu. Các phép kiểm tra chỉ đọc và tính lại JSON hoàn tất với mã thoát 0.
