# CHƯƠNG 1: TỔNG QUAN VÀ ĐẶT VẤN ĐỀ

---

## 1.1. LÝ DO CHỌN ĐỀ TÀI

Trong kỷ nguyên chuyển đổi số và tự động hóa tri thức, việc ứng dụng các Mô hình Ngôn ngữ Lớn (Large Language Models - LLMs) vào hệ thống vận hành doanh nghiệp đối mặt với rào cản cốt tử: hiện tượng ảo giác (hallucination) và sự lạc hậu của tri thức tham số tĩnh. Các nghiên cứu thực nghiệm độc lập (Gao et al., 2023; Lewis et al., 2020) chỉ ra rằng tỷ lệ phát ngôn không có căn cứ của LLM thuần túy dao động từ **18.5% đến 29.4%** trong các tác vụ suy luận sâu. Kỹ thuật Tăng cường Truy xuất Sinh (Retrieval-Augmented Generation - RAG) dựa trên Cơ sở dữ liệu Vector phẳng (Dense Vector Search) đã trở thành giải pháp tiêu chuẩn nhằm cung cấp ngữ cảnh thời gian thực. Tuy nhiên, kiến trúc RAG một chiều truyền thống bộc lộ hai khiếm khuyết toán học và cấu trúc nghiêm trọng khiến khả năng ứng dụng thực tế bị suy giảm trầm trọng.

Thứ nhất là sự đứt gãy liên kết quan hệ đa chặng (Multi-hop Relational Disconnection). Phép tìm kiếm $k$ láng giềng gần nhất theo khoảng cách cosine trong không gian vector phẳng hoàn toàn cô lập các khối văn bản độc lập. Khi câu truy vấn đòi hỏi chuỗi suy luận bắc cầu qua nhiều thực thể nằm phân tán ở các tài liệu khác nhau ($e_1 \xrightarrow{r_1} e_2 \xrightarrow{r_2} e_3$), vector embedding của câu hỏi bị suy giảm độ tương đồng với các khối chứa thực thể trung gian $e_2$. Kết quả thực nghiệm đối chuẩn cho thấy RAG vector truyền thống bỏ sót mắt xích thông tin then chốt, khiến độ phủ ngữ cảnh (Context Recall) sụt giảm xuống dưới **51.2%** trên các tập dữ liệu phức tạp. Thứ hai là sự bất lực trước tính biến thiên theo thời gian (Temporal Blindness): dữ liệu doanh nghiệp luôn biến động với các mốc hiệu lực cụ thể. Theo khảo sát định lượng của Syed và cộng sự (2026), có tới **31.8%** câu trả lời sai lệch của hệ thống vector xuất phát từ việc trích xuất các dữ kiện đã hết hạn (*stale facts*) nhưng lại có độ tương đồng từ vựng cao.

Để khắc phục rào cản quan hệ, kiến trúc Đồ thị Tri thức toàn cục (Microsoft GraphRAG, Edge et al., 2024) đã được phát triển thông qua phân cụm Leiden. Mặc dù cải thiện khả năng tổng hợp vĩ mô, GraphRAG lại vấp phải điểm nghẽn chi phí nạp cực cao: tiêu tốn từ **1.800 đến 3.500 token LLM** cho mỗi trang văn bản, kéo dài thời gian xử lý gấp **9.4 lần** so với vector phẳng và hoàn toàn đóng băng trước các cập nhật động thời gian thực (Rasmussen et al., 2025). Hơn nữa, các hệ thống hiện hành đều vận hành theo cơ chế thụ động một lượt ($\text{Query} \to \text{Retrieve} \to \text{Generate}$), thiếu hoàn toàn tác nhân phản biện để phát hiện chứng cứ không đầy đủ trước khi sinh văn bản, dẫn đến tỷ lệ lỗi suy diễn tích lũy lên tới **24.6%** trong các môi trường đòi hỏi tính chuẩn xác cao (Faria et al., 2026).

Xuất phát từ những thách thức định lượng trên, đề tài **"Nghiên cứu và Xây dựng Hệ thống Agentic RAG 2.0: Tích hợp Cơ sở dữ liệu Không gian kép PostgreSQL/PGVector - Neo4j Graphiti với Vòng lặp Phản biện Đa tác nhân Bị chặn"** được lựa chọn thực hiện. Đề tài giải quyết đồng thời bài toán suy luận liên kết đa chặng và sự trôi dạt ngữ nghĩa thời gian bằng cách: (1) Kết hợp tốc độ tìm kiếm ngữ nghĩa của PGVector với đồ thị tri thức nhận biết thời gian Graphiti (với nhãn hiệu lực $[t_{\text{valid}}, t_{\text{invalid}})$); và (2) Điều phối quy trình suy luận bằng máy trạng thái LangGraph có tác nhân Critic độc lập với cơ chế chặn cứng tối đa 2 chu kỳ lặp ($loop\_count \le 2$). Giải pháp này tối ưu hóa đồng thời tính trung thực phát ngôn (Faithfulness đạt trên **92.0%**) và khống chế độ trễ vận hành phân vị $P_{95} \le \mathbf{5.8\text{s}}$, mang lại đóng góp khoa học và giá trị thực tiễn cao cho doanh nghiệp.

---

## 1.2. MỤC TIÊU NGHIÊN CỨU

### 1.2.1. Mục tiêu Tổng quát
Mục tiêu tổng quát của đề tài là nghiên cứu, thiết kế và hiện thực hóa một kiến trúc Tăng cường Truy xuất Sinh đa tác nhân thế hệ mới (**Agentic RAG 2.0**) có khả năng suy luận trên biểu diễn tri thức không gian kép (Vector phẳng và Đồ thị nhận thức thời gian), đồng thời kiểm soát chất lượng câu trả lời thông qua cơ chế tự phản biện đối kháng có chặn biên tài nguyên an toàn.

### 1.2.2. Mục tiêu Cụ thể
1. **Thiết kế kiến trúc lưu trữ kép chịu lỗi (Dual-Store Ingestion Architecture):** Xây dựng quy trình nạp dữ liệu tuần tự hai pha giữa CSDL quan hệ vector PostgreSQL (tiện ích mở rộng PGVector) và CSDL đồ thị Neo4j tích hợp engine Graphiti, đảm bảo 100% tính sẵn sàng truy vấn ngay cả khi khâu trích xuất thực thể đồ thị gặp sự cố.
2. **Xây dựng bộ định tuyến ý định và chuẩn hóa ngữ cảnh lai:** Hiện thực hóa thuật toán phân loại ý định truy vấn thành ba nhánh (`vector`, `graph`, `hybrid`) và chuẩn hóa facts đồ thị nhận biết thời gian theo cú pháp cấu trúc nhằm triệt tiêu hiện tượng mâu thuẫn dữ kiện cũ-mới.
3. **Mô hình hóa vòng lặp phản biện có điều kiện dừng tuyệt đối:** Xây dựng máy trạng thái hữu hạn trên LangGraph với tác nhân phản biện `CriticAgent` thực hiện kiểm định chéo hai chiều (Faithfulness & Completeness), tự động sinh truy vấn tinh chỉnh và thiết lập ngưỡng chặn cứng chu kỳ lặp ($loop\_count \le 2$).
4. **Đánh giá thực nghiệm và phân tích đối chuẩn:** Thiết lập kịch bản thử nghiệm toàn diện trên bộ chỉ số chuẩn hóa (RAGAS và EvalMem), đối chuẩn hệ thống với các mô hình baseline (Vector-only, Graph-only, Naive RAG) về độ chính xác, độ trung thực, thời gian đáp ứng $P_{95}$ và chi phí tiêu thụ token.

---

## 1.3. ĐỐI TƯỢNG VÀ PHẠM VI NGHIÊN CỨU

### 1.3.1. Đối tượng Nghiên cứu
- Các thuật toán tìm kiếm tương đồng vector dày trong không gian Euclid $\mathbb{R}^d$ và khoảng cách Cosine.
- Đồ thị tri thức động nhận biết thời gian (Temporally-aware Dynamic Knowledge Graphs) và các thuộc tính khoảng thời gian hiệu lực $[t_{\text{valid}}, t_{\text{invalid}})$.
- Cơ chế suy luận đa tác nhân (Multi-Agent State Machine), mô hình tranh biện đối kháng và vòng lặp tự phản biện có điều kiện dừng trong xử lý ngôn ngữ tự nhiên.

### 1.3.2. Phạm vi Nghiên cứu
- **Phạm vi kỹ thuật:** Hệ thống tập trung triển khai và kiểm chứng trên nền tảng mã nguồn mở cục bộ gồm PostgreSQL 16 (PGVector), Neo4j Community Edition 5.x, Redis 7.x, phối hợp cùng các mô hình ngôn ngữ lớn tiên tiến (Gemini API / Claude API) thông qua framework LangChain và LangGraph.
- **Phạm vi dữ liệu:** Tập trung vào kho ngữ liệu văn bản doanh nghiệp có cấu trúc phức tạp, chứa đồng thời các dữ kiện biến động theo dòng thời gian (tin tức tổ chức, hợp đồng, quyết định bổ nhiệm) và các mối quan hệ quan hệ thực thể phân tán đòi hỏi suy luận bắc cầu từ 2 đến 3 chặng.

---

## 1.4. CÂU HỎI NGHIÊN CỨU VÀ GIẢ THUYẾT KHOA HỌC

Để đảm bảo tính khả bác (falsifiability) theo chuẩn phương pháp luận khoa học, đề tài xác lập 3 câu hỏi nghiên cứu cốt lõi ($RQ$) và các giả thuyết kiểm định tương ứng:

- **Câu hỏi Nghiên cứu 1 ($RQ_1$ - Biểu diễn Lai Không gian Kép):**  
  *Việc kết hợp đồng thời cấu trúc Đồ thị Tri thức Động nhận biết thời gian (Neo4j Graphiti) với Cơ sở dữ liệu Vector (PostgreSQL/PGVector) có nâng cao có ý nghĩa thống kê độ phủ ngữ cảnh ($CR$) và độ chính xác ngữ cảnh ($CP$) trên các truy vấn đa chặng so với việc chỉ dùng đơn lẻ một trong hai nguồn hay không?*  
  - **Giả thuyết Không $H_{0,1}$:** Độ phủ ngữ cảnh trung bình của hệ sinh thái lai không vượt trội hơn hệ thống vector đơn thuần: $\mu(CR_{\text{hybrid}}) - \mu(CR_{\text{vector}}) \le 0$ với mức ý nghĩa $p \ge 0.01$.

- **Câu hỏi Nghiên cứu 2 ($RQ_2$ - Động lực học Tự Phản biện Bị Chặn):**  
  *Cơ chế định tuyến ý định kết hợp vòng lặp kiểm tra chéo hai chiều (Faithfulness & Completeness) của tác nhân phản biện Critic với giới hạn chặn cứng tối đa 2 chu kỳ lặp có triệt tiêu hiệu quả ảo giác phát ngôn mà không làm sụp đổ tính hội tụ của hệ thống hay không?*  
  - **Giả thuyết Không $H_{0,2}$:** Tỷ lệ trung thực phát ngôn $\mathcal{F}$ của hệ thống khi có Critic không cao hơn phiên bản không có Critic: $\mu(\mathcal{F}_{\text{critic}}) - \mu(\mathcal{F}_{\text{no\_critic}}) \le 0$ với mức ý nghĩa $p \ge 0.01$.

- **Câu hỏi Nghiên cứu 3 ($RQ_3$ - Đánh đổi Hiệu năng & Khả thi Vận hành):**  
  *Sự gia tăng về độ trễ phân vị $P_{95}$ và lượng token tiêu thụ khi vận hành vòng lặp phản biện có được khống chế trong ngưỡng chấp nhận vận hành doanh nghiệp ($P_{95} \le 6.0\text{s}$) và tương xứng với mức cải thiện chất lượng câu trả lời hay không?*  
  - **Giả thuyết Không $H_{0,3}$:** Thời gian trễ $P_{95}$ của vòng lặp tác nhân vượt ngưỡng vận hành tương tác ($P_{95} > 6.0\text{s}$) hoặc chi phí token tăng trưởng siêu tuyến tính so với độ trung thực mang lại.

---

## 1.5. ĐÓNG GÓP KHOA HỌC VÀ THỰC TIỄN CỦA ĐỀ TÀI

1. **Đóng góp về mặt phương pháp và kiến trúc:** Đề xuất và hoàn thiện mô hình nạp dữ liệu không gian kép tuần tự hai pha chịu lỗi (Fault-tolerant Dual-store Sequential Ingestion), giải quyết dứt điểm sự phụ thuộc ràng buộc cứng giữa CSDL quan hệ và CSDL đồ thị.
2. **Đóng góp về thuật toán điều phối suy luận:** Thiết lập quy trình phản biện đa tác nhân hữu hạn với thuật toán chặn biên toán học, loại bỏ hoàn toàn nguy cơ bùng nổ vòng lặp vô hạn (infinite looping hazard) thường gặp trong các kiến trúc Autonomous Agents.
3. **Đóng góp về ứng dụng thực tiễn:** Chuyển giao một hệ thống mã nguồn mở hoàn chỉnh bao gồm Backend FastAPI, Frontend React trực quan hóa đồ thị 3D, giao diện CLI Rich Terminal và kịch bản đo kiểm tự động bằng RAGAS/EvalMem, sẵn sàng triển khai trong môi trường doanh nghiệp.

---

## 1.6. BỐ CỤC CỦA LUẬN VĂN

Luận văn được tổ chức thành 6 chương chính như sau:
- **Chương 1: Tổng quan và Đặt vấn đề** — Trình bày lý do chọn đề tài, mục tiêu, đối tượng, phạm vi, câu hỏi nghiên cứu và cấu trúc luận văn.
- **Chương 2: Cơ sở Lý thuyết và Khảo cứu Tài liệu** — Tổng kết tiến trình phát triển của RAG, phân tích toán học các điểm nghẽn của Dense Vector Search và Static GraphRAG, khảo cứu các công trình SOTA 2025–2026.
- **Chương 3: Mô hình hóa Toán học và Kiến trúc Hệ thống Agentic RAG 2.0** — Trình bày chi tiết công thức toán, thuật toán nạp dữ liệu không gian kép, bộ định tuyến ý định và vòng lặp phản biện LangGraph.
- **Chương 4: Thiết kế Thực nghiệm và Kịch bản Đánh giá** — Thiết lập môi trường thử nghiệm, quy cách tập dữ liệu, các baseline đối chuẩn, hệ thống chỉ số RAGAS/EvalMem và kịch bản bóc tách ablation.
- **Chương 5: Kết quả Thực nghiệm và Thảo luận** — Báo cáo số liệu đo đạc thực tế, phân tích định lượng các giả thuyết khoa học, đánh giá đánh đổi hiệu năng và thảo luận các đe dọa giá trị.
- **Chương 6: Kết luận và Hướng phát triển** — Tổng kết toàn diện các đóng góp, chỉ ra các hạn chế kỹ thuật và gợi mở các hướng nghiên cứu mở rộng tiếp theo.
