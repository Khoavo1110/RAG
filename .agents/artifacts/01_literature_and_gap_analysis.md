# 📑 GIAI ĐOẠN 1: CƠ SỞ LÝ THUYẾT & PHÂN TÍCH KHOẢNG TRỐNG NGHIÊN CỨU
## Literature Grounding & Research Gap Analysis for Agentic RAG 2.0

**Dự án:** Agentic RAG 2.0 (PGVector + Neo4j Graphiti + Multi-Agent Reasoning Loop)  
**Tác giả / Hệ thống:** Antigravity Master Control Hub (`.agents/AGENTS.md` v2.1)  
**Trạng thái kiểm chứng:** Đã xác thực qua MCP `browser-use` trên Google Chrome cổng 9222 và kho lưu trữ khoa học chính thức `arXiv.org`.  
**Quy chuẩn chứng cứ:** `[đã triển khai]` | `[đã đo]` | `[đề xuất]` | `[chưa xác minh]`  

---

### 1. ĐẶT VẤN ĐỀ VÀ BỐI CẢNH KHOA HỌC

Trong kỷ nguyên của các Mô hình Ngôn ngữ Lớn (Large Language Models - LLMs), việc áp dụng LLM vào các hệ thống tri thức doanh nghiệp đòi hỏi giải quyết hai vấn đề nội tại cố hữu: hiện tượng ảo giác (hallucination) và sự lạc hậu của tri thức tham số tĩnh (static parametric memory). Kỹ thuật Tăng cường Truy xuất Sinh (Retrieval-Augmented Generation - RAG) do Lewis và cộng sự (2020) khởi xướng đã trở thành tiêu chuẩn công nghiệp nhằm cung cấp dữ liệu ngữ cảnh thời gian thực cho mô hình ngôn ngữ.

Tuy nhiên, thế hệ RAG truyền thống dựa trên việc tìm kiếm tương đồng vector dày (Dense Vector Search) bộc lộ những giới hạn toán học và cấu trúc nghiêm trọng:

1. **Sự đứt gãy liên kết quan hệ đa chặng (Multi-hop Relational Disconnection):**
   Phép đo khoảng cách cosine hoặc dot-product trong không gian vector dày $\mathbb{R}^d$ hoàn toàn cô lập các khối văn bản (text chunks). Khi một câu hỏi đòi hỏi chuỗi suy luận bắc cầu qua nhiều thực thể nằm phân tán ở các tài liệu khác nhau (ví dụ: $e_1 \xrightarrow{r_1} e_2 \xrightarrow{r_2} e_3$), nhưng câu hỏi chỉ chứa thực thể đầu $e_1$ và đích $e_3$, vector embedding của câu hỏi sẽ không có độ tương đồng đủ cao với các chunk chứa thực thể trung gian $e_2$. Kết quả là Top-$K$ vector retrieval bỏ sót mắt xích tri thức then chốt.

2. **Sự mù mờ trước tính biến thiên theo thời gian (Temporal Blindness & Stale Facts):**
   Dữ liệu tổ chức luôn biến đổi: các quyết định bổ nhiệm nhân sự, thỏa thuận hợp đồng hay điều chỉnh tài chính diễn ra liên tục theo các mốc thời gian. Không gian vector tĩnh không lưu giữ tính thứ tự thời gian và thời gian hiệu lực của các quan hệ (`valid_at`, `invalid_at`). Khi truy vấn thông tin hiện tại, hệ thống vector thường trích xuất các dữ kiện cũ trong quá khứ chỉ vì chúng có độ khớp từ vựng cao, gây ra hiện tượng mâu thuẫn tri thức.

3. **Cơ chế truy xuất thụ động một lượt (Passive Single-shot Retrieval):**
   Hầu hết các pipeline RAG hiện hành vận hành theo cơ cấu tuyến tính một chiều: $\text{Query} \to \text{Retrieve} \to \text{Generate}$. Mô hình sinh buộc phải chấp nhận mọi ngữ cảnh mà bộ truy xuất trả về mà không có cơ hội tự phản biện (self-critique) về tính đầy đủ hoặc tính trung thực, dẫn đến suy diễn sai nếu bước truy xuất ban đầu bị nhiễu hoặc thiếu thông tin.

---

### 2. CÂU HỎI NGHIÊN CỨU & GIẢ THUYẾT BÁC BỎ (RESEARCH QUESTIONS & HYPOTHESES)

Để định lượng hóa và kiểm chứng giải pháp đề xuất, nghiên cứu này xác lập 3 câu hỏi nghiên cứu cốt lõi ($RQ$) cùng các giả thuyết không ($H_0$) có thể bác bỏ thông qua thực nghiệm:

- **Câu hỏi Nghiên cứu 1 ($RQ_1$ - Biểu diễn Lai Không gian Kép):**
  *Việc kết hợp cấu trúc Đồ thị Tri thức Động nhận biết thời gian (Neo4j Graphiti) với Cơ sở dữ liệu Vector (PostgreSQL/PGVector) có nâng cao đáng kể độ phủ ngữ cảnh ($CR$) và độ chính xác ngữ cảnh ($CP$) trên các truy vấn đa chặng và dữ liệu biến động so với việc chỉ dùng đơn lẻ một trong hai nguồn hay không?*
  - **Giả thuyết Không $H_{0,1}$:** Độ phủ ngữ cảnh trung bình của hệ sinh thái lai ($CR_{\text{hybrid}}$) không có sự khác biệt có ý nghĩa thống kê so với hệ thống vector đơn thuần ($CR_{\text{vector}}$) trên tập câu hỏi đa chặng: $\mu(CR_{\text{hybrid}}) - \mu(CR_{\text{vector}}) \le 0$ với ngưỡng ý nghĩa $p \ge 0.01$.

- **Câu hỏi Nghiên cứu 2 ($RQ_2$ - Động lực học Tự Phản biện Bị Chặn):**
  *Cơ chế định tuyến ý định kết hợp vòng lặp kiểm tra chéo hai chiều (Faithfulness & Completeness) của tác nhân phản biện (Critic Agent) với giới hạn chặn cứng tối đa 3 chu kỳ lặp ($loop\_count \le 2$) có triệt tiêu hiệu quả hiện tượng ảo giác và cải thiện độ trung thực phát ngôn ($\mathcal{F}$) mà không gây bùng nổ vòng lặp vô hạn hay không?*
  - **Giả thuyết Không $H_{0,2}$:** Tỷ lệ trung thực $\mathcal{F}$ của hệ thống khi có tác nhân Critic không vượt trội hơn phiên bản lai không có Critic: $\mu(\mathcal{F}_{\text{critic}}) - \mu(\mathcal{F}_{\text{no\_critic}}) \le 0$ với $p \ge 0.01$.

- **Câu hỏi Nghiên cứu 3 ($RQ_3$ - Đánh đổi Hiệu năng & Khả thi Vận hành):**
  *Sự gia tăng về thời gian phản hồi phân vị $P_{95}$ và lượng token tiêu thụ khi vận hành vòng lặp đa tác nhân có duy trì được trong ngưỡng chấp nhận vận hành doanh nghiệp ($P_{95} \le 6.0\text{s}$) và tương xứng với mức cải thiện chất lượng thông tin hay không?*
  - **Giả thuyết Không $H_{0,3}$:** Thời gian trễ $P_{95}$ của vòng lặp tác nhân vượt ngưỡng giới hạn vận hành tương tác ($> 6.0\text{s}$) hoặc chi phí token tăng không tuyến tính so với chất lượng thông tin mang lại.

---

### 3. MA TRẬN TÀI LIỆU KHOA HỌC ĐỐI CHUẨN (LITERATURE MATRIX)

Toàn bộ tài liệu được khảo cứu và đối chiếu siêu dữ liệu chính thức qua kho lưu trữ `arXiv.org` và các hội nghị AI hàng đầu (NeurIPS) thông qua công cụ tự động hóa `browser-use`:

| STT | Công trình & Tác giả | Định danh & Năm | Đóng góp Kỹ thuật Nền tảng | Giới hạn so với Kiến trúc Agentic RAG 2.0 |
| :---: | :--- | :--- | :--- | :--- |
| **1** | **Zep / Graphiti**<br>(Rasmussen et al.) | `arXiv:2501.13956`<br>(2025) | Thiết lập Graphiti: Mô hình đồ thị tri thức nhận biết thời gian (Temporally-aware KG) cho bộ nhớ tác nhân, bảo toàn các cạnh sự kiện (`episodes`) với khoảng hiệu lực thời gian. | Tập trung vào bộ nhớ hội thoại người dùng (User-Agent Memory); chưa tích hợp song song với hệ quản trị CSDL quan hệ vector chuẩn doanh nghiệp (PostgreSQL/PGVector) và chưa có bộ định tuyến đa nhánh động. |
| **2** | **Microsoft GraphRAG**<br>(Edge et al.) | `arXiv:2404.16130`<br>(2024) | Trích xuất đồ thị thực thể từ toàn bộ kho tài liệu và tiền tổng hợp tóm tắt cộng đồng phân cấp qua thuật toán Leiden để phục vụ tóm tắt tập trung theo truy vấn (QFS). | Đồ thị tĩnh (Static Graph); chi phí nạp cực cao (tiêu tốn hàng ngàn API call cho mỗi tài liệu); không hỗ trợ dữ liệu biến thiên theo thời gian thực; không có cơ chế tự phản biện động theo thời gian thực. |
| **3** | **Self-RAG**<br>(Asai et al.) | `arXiv:2310.11511`<br>(2023) | Đào tạo mô hình ngôn ngữ có khả năng tự phản ánh thông qua việc tinh chỉnh (fine-tuning) các reflection tokens đặc biệt để kiểm soát truy xuất và phản biện. | Phụ thuộc vào việc huấn luyện mô hình mở (Llama 7B/13B); không thể áp dụng trực tiếp cho các mô hình thương mại đóng (Gemini, Claude, GPT-4o); chỉ hoạt động trên không gian vector phẳng. |
| **4** | **Corrective RAG (CRAG)**<br>(Yan et al.) | `arXiv:2401.15884`<br>(2024) | Thiết kế bộ đánh giá truy xuất nhẹ để tính điểm tin cậy; tự động kích hoạt tìm kiếm web ngoài khi tài liệu nội bộ không đủ thông tin. | Phụ thuộc vào dữ liệu tìm kiếm công cộng (Web Search); không xây dựng được tầng tri thức quan hệ nội bộ doanh nghiệp dưới dạng đồ thị có cấu trúc. |
| **5** | **Foundations of RAG**<br>(Lewis et al.; Gao et al.) | `NeurIPS 2020`<br>`arXiv:2312.10997` | Đặt nền móng toán học cho việc truy xuất vector dày dựa trên tích vô hướng và hàm phạt xác suất sinh có điều kiện. | Bộc lộ điểm nghẽn nghiêm trọng khi truy vấn đòi hỏi liên kết bắc cầu nhiều thực thể không cùng nằm trong một chunk văn bản đơn lẻ. |
| **6** | **Ragas Metric Framework**<br>(Es et al.) | `arXiv:2309.15217`<br>(2023) | Xây dựng bộ chỉ số đánh giá phi tham số chuẩn hóa cho RAG bao gồm: Faithfulness, Answer Relevance, Context Precision, và Context Recall. | Là công cụ đánh giá tĩnh (evaluation framework), không tham gia vào vòng lặp điều phối thời gian thực của tác nhân. |

---

### 4. PHÂN TÍCH TOÁN HỌC VỀ ĐIỂM NGHẼN CỦA DENSE RETRIEVAL & STATIC GRAPHRAG

#### 4.1. Giới hạn Hình học của Phép Tìm kiếm Vector Dày
Xét không gian nhúng $\mathbb{R}^d$ với mạng nơ-ron mã hóa $E: \Sigma^* \to \mathbb{R}^d$. Cho tập tài liệu nguồn được chia thành $N$ khối văn bản $\mathcal{D} = \{d_1, d_2, \dots, d_N\}$. Phép tìm kiếm $k$ láng giềng gần nhất theo khoảng cách Cosine:
$$\text{Top-}K(q) = \arg\max_{d_i \in \mathcal{D}}^{(K)} \frac{\langle E(q), E(d_i) \rangle}{\|E(q)\|_2 \|E(d_i)\|_2}$$

*Mệnh đề đứt gãy quan hệ:* Giả sử câu truy vấn $q$ chứa cặp thực thể $(e_A, e_C)$ với mối quan hệ bắc cầu $e_A \xrightarrow{r_1} e_B \xrightarrow{r_2} e_C$. Chunk $d_1$ chứa $(e_A, r_1, e_B)$ và chunk $d_2$ chứa $(e_B, r_2, e_C)$.
Do $q$ không xuất hiện từ vựng $e_B$, tích vô hướng $\langle E(q), E(d_1) \rangle$ và $\langle E(q), E(d_2) \rangle$ bị suy giảm bởi sự xuất hiện của các từ không liên quan trong chunk. Khi đó:
$$\max_{i \in \{1, 2\}} \cos(E(q), E(d_i)) < \tau_K$$
trong đó $\tau_K$ là ngưỡng cosine của phần tử thứ $K$ trong kho dữ liệu lớn. Kết quả là cả $d_1$ và $d_2$ đều bị loại khỏi tập ứng viên, khiến LLM mất hoàn toàn căn cứ logic để trả lời.

#### 4.2. Hạn chế của Đồ thị Tĩnh Microsoft GraphRAG
Mô hình GraphRAG của Microsoft dựa trên việc xây dựng đồ thị tĩnh trước khi truy vấn và thực hiện thuật toán phân cụm Leiden:
$$\mathcal{C}_{\text{communities}} = \text{LeidenPartition}(\mathcal{V}, \mathcal{E})$$
Mô hình này gặp hai rào cản chí tử trong môi trường ứng dụng động:
1. **Độ phức tạp tính toán và chi phí nạp:** Mỗi lần nạp một tài liệu mới đòi hỏi quét toàn bộ corpus để tái phân cụm cộng đồng, tiêu tốn lượng token LLM khổng lồ ($\mathcal{O}(|\mathcal{V}| \times \text{Tokens}_{\text{summary}})$).
2. **Thiếu khả năng nhận biết thời gian:** Cạnh quan hệ giữa hai thực thể $(u, v)$ trong GraphRAG là vô hướng hoặc tĩnh, không có nhãn khoảng thời gian hiệu lực $[t_{\text{valid}}, t_{\text{invalid}})$. Khi một quan hệ bị hủy bỏ trong thực tế, đồ thị tĩnh không thể tự động vô hiệu hóa nếu không tái chỉ mục toàn bộ.

---

### 5. KHOẢNG TRỐNG KỸ THUẬT & ĐÓNG GÓP CỦA ĐỒ ÁN (THE RESEARCH GAP)

Dựa trên phân tích tài liệu và thực nghiệm, khoảng trống kỹ thuật được xác lập rõ ràng:
*Hiện chưa có một hệ thống mã nguồn mở hoàn chỉnh nào tích hợp kiến trúc lưu trữ kép chịu lỗi giữa PostgreSQL (PGVector) và Neo4j (Graphiti), đồng thời điều khiển quá trình truy xuất bằng một đồ thị trạng thái hữu hạn LangGraph với tác nhân phản biện độc lập có điều kiện chặn biên mà không cần can thiệp tinh chỉnh trọng số LLM.*

Đồ án **Agentic RAG 2.0** giải quyết trọn vẹn khoảng trống này với 3 đóng góp khoa học chính:
1. **Kiến trúc Lưu trữ Kép Tuần tự Hai Pha (Fault-Tolerant Dual-Store Ingestion):** Ghi nhận dữ liệu vector vào PostgreSQL trước nhằm đảm bảo 100% tính sẵn sàng truy vấn, sau đó mới nạp tri thức đồ thị vào Neo4j Graphiti; chấp nhận trạng thái nạp một phần an toàn khi bước đồ thị gặp sự cố `[đã triển khai]`.
2. **Bộ Định tuyến Ý định & Tích hợp Ngữ cảnh Đa Kênh:** Phân loại thông minh truy vấn thành 3 luồng chuyên biệt (`vector`, `graph`, `hybrid`) và chuẩn hóa facts đồ thị nhận biết thời gian theo cú pháp `<FACTS>` `[đã triển khai]`.
3. **Vòng lặp Suy luận Đa tác nhân có Điều kiện Chặn Biên Tuyệt đối:** Vòng lặp phản biện hai chiều (Faithfulness & Completeness) với cơ chế tự động tinh chỉnh câu hỏi (`refinement_query`) và chặn cứng ở chu kỳ lặp thứ 2 ($loop\_count \le 2$), triệt tiêu hoàn toàn nguy cơ lặp vô hạn `[đã triển khai]`.
