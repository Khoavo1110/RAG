# CHƯƠNG 2: CƠ SỞ LÝ THUYẾT VÀ TỔNG QUAN TÀI LIỆU

---

## 2.1. TIẾN TRÌNH PHÁT TRIỂN CỦA KỸ THUẬT TĂNG CƯỜNG TRUY XUẤT SINH (RAG)

### 2.1.1. Nền tảng Toán học của Dense Vector Retrieval
Kỹ thuật Tăng cường Truy xuất Sinh (Retrieval-Augmented Generation - RAG) do Lewis và cộng sự (2020) khởi xướng nhằm khắc phục giới hạn bộ nhớ tham số tĩnh của các Mô hình Ngôn ngữ Lớn. Về mặt toán học, cho trước một câu truy vấn $q \in \mathcal{Q}$ và kho ngữ liệu văn bản $\mathcal{D} = \{d_1, d_2, \dots, d_N\}$ được chia thành $N$ khối văn bản (text chunks). Một mạng nơ-ron mã hóa dày (Dense Embedding Model) $E: \Sigma^* \to \mathbb{R}^d$ ánh xạ câu hỏi và các đoạn văn bản thành các vector biểu diễn trong không gian Euclid $d$ chiều:
$$\mathbf{v}_q = E(q), \quad \mathbf{v}_{d_i} = E(d_i) \quad \forall d_i \in \mathcal{D}$$

Quá trình truy xuất $K$ đoạn văn bản liên quan nhất được định nghĩa thông qua độ đo khoảng cách Cosine hoặc tích vô hướng được chuẩn hóa:
$$\text{Top-}K(q) = \arg\max_{d_i \in \mathcal{D}}^{(K)} \text{sim}(\mathbf{v}_q, \mathbf{v}_{d_i}) = \arg\max_{d_i \in \mathcal{D}}^{(K)} \frac{\langle \mathbf{v}_q, \mathbf{v}_{d_i} \rangle}{\|\mathbf{v}_q\|_2 \|\mathbf{v}_{d_i}\|_2}$$

Sau bước truy xuất, tập ngữ cảnh được chọn $\mathcal{C}_K = \{d_{(1)}, \dots, d_{(K)}\}$ được ghép nối cùng câu hỏi để làm điều kiện cho mô hình sinh tính toán xác suất chuỗi từ mục tiêu $\mathbf{y} = (y_1, \dots, y_M)$:
$$P(\mathbf{y} \mid q, \mathcal{C}_K) = \prod_{m=1}^M P(y_m \mid y_{<m}, q, \mathcal{C}_K)$$

Theo Gao và cộng sự (2023), kiến trúc RAG vector phẳng tiêu chuẩn đã giải quyết xuất sắc các câu hỏi tra cứu dữ kiện trực tiếp (single-hop factual QA). Tuy nhiên, kiến trúc này bộc lộ những khiếm khuyết cơ học không thể khắc phục khi đối mặt với dữ liệu phức tạp trong thế giới thực.

### 2.1.2. Giới hạn Hình học và Điểm nghẽn Đứt gãy Quan hệ Đa chặng
Xét bài toán suy luận bắc cầu qua đồ thị thực thể gồm ba nút $e_A, e_B, e_C$ với quan hệ $e_A \xrightarrow{r_1} e_B$ và $e_B \xrightarrow{r_2} e_C$. Giả sử thông tin phân bố ở hai chunk độc lập:
$$d_1 \supset (e_A, r_1, e_B), \quad d_2 \supset (e_B, r_2, e_C)$$
Câu hỏi của người dùng chỉ chứa hai thực thể biên: $q = \text{"Mối liên hệ giữa } e_A \text{ và } e_C \text{ là gì?"}$. 

*Mệnh đề đứt gãy quan hệ:* Do $q$ hoàn toàn không chứa từ vựng hay ngữ nghĩa trực tiếp của thực thể trung gian $e_B$, độ tương đồng ngữ nghĩa giữa $\mathbf{v}_q$ và $\mathbf{v}_{d_1}$ hoặc $\mathbf{v}_{d_2}$ bị suy giảm bởi sự xuất hiện của các từ phụ trợ khác trong văn bản. Khi kho ngữ liệu $\mathcal{D}$ có quy mô lớn ($N \gg 10^5$), tồn tại vô số chunk gây nhiễu $d_{\text{noise}}$ chứa các từ vựng trùng khớp ngẫu nhiên với $q$, khiến:
$$\max \{\text{sim}(\mathbf{v}_q, \mathbf{v}_{d_1}), \text{sim}(\mathbf{v}_q, \mathbf{v}_{d_2})\} < \tau_K$$
trong đó $\tau_K$ là ngưỡng tương đồng của phần tử thứ $K$ trả về. Kết quả là cả $d_1$ và $d_2$ đều bị loại khỏi tập Top-$K$, khiến mô hình sinh mất hoàn toàn căn cứ logic để suy luận.

---

## 2.2. ĐỒ THỊ TRI THỨC TOÀN CỤC VÀ HẠN CHẾ CỦA MICROSOFT GRAPHRAG

Để vượt qua hạn chế của việc trích xuất văn bản phẳng, Microsoft Research đã công bố kiến trúc GraphRAG (Edge et al., 2024). Phương pháp này tiếp cận bài toán theo hướng tổng hợp toàn cục:
1. Sử dụng LLM để trích xuất toàn bộ thực thể ($\mathcal{V}$), quan hệ ($\mathcal{E}$) và các mô tả từ kho tài liệu.
2. Xây dựng đồ thị tri thức tổng thể $\mathcal{G} = (\mathcal{V}, \mathcal{E})$ và áp dụng thuật toán phân cụm cộng đồng Leiden (Leiden Community Detection) để nhóm các thực thể có tính kết nối cao thành cấu trúc phân cấp:
   $$\mathcal{C}_{\text{communities}} = \text{LeidenPartition}(\mathcal{V}, \mathcal{E})$$
3. Tạo tóm tắt cộng đồng từ dưới lên (Bottom-up Community Summaries) bằng LLM nhằm phục vụ các câu hỏi tổng quan toàn bộ kho dữ liệu (Query-Focused Summarization - QFS).

Mặc dù giải quyết được bài toán hiểu bao quát, nghiên cứu thực nghiệm và phân tích hệ thống chỉ ra GraphRAG vấp phải ba rào cản chí tử:
- **Chi phí nạp khổng lồ:** Việc quét toàn bộ corpus và chạy lặp hàng loạt prompt LLM để trích xuất thực thể và tóm tắt cộng đồng tiêu tốn từ 1.800 đến 3.500 token cho mỗi trang tài liệu, khiến chi phí tăng theo cấp số nhân khi dữ liệu mở rộng.
- **Tính đóng băng tĩnh (Static Graph Freeze):** Đồ thị và các bản tóm tắt cộng đồng được tính toán trước ngoại tuyến. Khi có tài liệu mới nạp vào, hệ thống không thể cập nhật cục bộ mà buộc phải tái chỉ mục toàn bộ đồ thị để phân cụm lại cộng đồng Leiden ($\mathcal{O}(|\mathcal{V}| \times \text{Cost}_{\text{LLM}})$).
- **Mù mờ về tính biến thiên thời gian:** Các cạnh quan hệ trong GraphRAG không lưu giữ thông tin khoảng thời gian hiệu lực, dẫn đến việc hòa trộn dữ kiện lịch sử cũ với thực trạng hiện tại.

---

## 2.3. ĐỒ THỊ TRI THỨC ĐỘNG NHẬN BIẾT THỜI GIAN (TEMPORAL KNOWLEDGE GRAPHS - TKG)

### 2.3.1. Kiến trúc Zep / Graphiti cho Bộ nhớ Tác nhân
Khác với phương pháp đồ thị tĩnh của Microsoft, Rasmussen và cộng sự (2025) thuộc Zep AI đã đề xuất engine **Graphiti**. Graphiti mô hình hóa đồ thị tri thức nhận biết thời gian (Temporally-aware Knowledge Graph) thông qua khái niệm sự kiện hội thoại (`episodes`). Mỗi tri thức trích xuất ra được gán nhãn mốc thời gian xuất hiện $t_{\text{created}}$, cùng hai thuộc tính hiệu lực thời gian quan trọng:
$$e = (u \xrightarrow{r} v; [t_{\text{valid}}, t_{\text{invalid}}))$$
trong đó $t_{\text{valid}}$ là mốc thời gian dữ kiện bắt đầu có hiệu lực và $t_{\text{invalid}}$ là mốc thời gian dữ kiện bị phủ quyết bởi một dữ kiện mới mâu thuẫn. Khi một episode mới ghi nhận sự thay đổi (ví dụ: bổ nhiệm vị trí mới), Graphiti tự động cập nhật $t_{\text{invalid}}$ của quan hệ cũ mà không cần tái cấu trúc toàn bộ đồ thị.

### 2.3.2. Mô hình Suy giảm Logic Thời gian (Chronofy, 2026)
Trong nghiên cứu đột phá xuất bản tháng 7/2026, Syed và cộng sự đã giới thiệu kiến trúc **Chronofy**, chỉ ra rằng các hệ thống RAG hiện tại đánh đồng trọng số của mọi dữ kiện bất kể niên đại xuất hiện. Chronofy thiết lập hàm suy giảm hợp lệ logic theo thời gian $\Lambda(t)$ đối với mỗi dữ kiện truy xuất:
$$\Lambda(t, t_q) = \exp\left(-\lambda \cdot \max(0, t_q - t_{\text{valid}})\right) \times \mathbb{I}(t_q < t_{\text{invalid}})$$
trong đó $t_q$ là mốc thời gian của truy vấn, $\lambda$ là hệ số phân rã theo miền nghiệp vụ, và $\mathbb{I}(\cdot)$ là hàm chỉ thị kiểm tra tính chưa hết hạn. Việc tích hợp hàm suy giảm thời gian đã giúp giảm thiểu 31.8% lỗi phát ngôn sai lệch trong các hệ thống RAG doanh nghiệp.

### 2.3.3. Mạng Bộ nhớ Sự kiện Động (DYNA, 2026)
Nghiên cứu của Sarabadani và Tajvidiyan (tháng 6/2026) về kiến trúc **DYNA** (Dynamic Episodic Memory Networks) đã củng cố vững chắc nền tảng lý thuyết cho việc kết hợp LLM đóng băng với Đồ thị Tri thức Động theo sự kiện. DYNA chứng minh rằng việc biểu diễn các sự kiện thành các nút động liên kết tuần tự theo thời gian cho phép mô hình ngôn ngữ cập nhật tri thức liên tục mà không gặp hiện tượng quên thảm khốc (catastrophic forgetting) và loại bỏ hoàn toàn nhu cầu tái tinh chỉnh trọng số (fine-tuning) tốn kém.

### 2.3.4. Truy xuất Hồi ức Sự kiện Đa chặng (Agent Memory, 2026)
Xu và cộng sự (tháng 9/2026) trong công trình về bộ nhớ tác nhân tài chính đã chỉ ra rằng cơ chế truy xuất hồi ức sự kiện (Episodic Retrieval) vượt trội hơn hẳn so với Dense Retrieval phẳng: khi các dữ kiện được tổ chức thành các chuỗi episode có gắn nhãn thời gian và định danh nguồn, độ chính xác của các quyết định đa chặng tăng thêm 27.4% nhờ loại bỏ các thực thể nhiễu không cùng ngữ cảnh sự kiện.

---

## 2.4. CƠ CHẾ TỰ PHẢN BIỆN VÀ TRANH BIỆN ĐỐI KHÁNG ĐA TÁC NHÂN

### 2.4.1. Self-RAG và Corrective RAG (CRAG)
Nhằm khắc phục tính thụ động của quy trình truy xuất một lượt, hai mô hình tiền đề đã được đề xuất:
- **Self-RAG (Asai et al., 2023):** Tinh chỉnh mô hình ngôn ngữ mở để sinh các thẻ phản chiếu đặc biệt (`[Retrieve]`, `[IsRel]`, `[IsSup]`, `[IsUse]`), cho phép mô hình tự quyết định khi nào cần truy xuất và đánh giá chất lượng đoạn văn bản. Hạn chế của Self-RAG là phụ thuộc hoàn toàn vào mô hình nguồn mở được huấn luyện riêng (Llama-7B/13B), không thể áp dụng cho các API thương mại đóng như Gemini 1.5 Pro hay Claude 3.5 Sonnet.
- **Corrective RAG - CRAG (Yan et al., 2024):** Bổ sung một bộ đánh giá truy xuất nhẹ (Retrieval Evaluator) để tính toán độ tin cậy của tập ngữ cảnh. Nếu độ tin cậy thấp, CRAG chuyển hướng sang tìm kiếm Web ngoài. Tuy nhiên, CRAG phụ thuộc vào nguồn dữ liệu công cộng mở và không có cơ chế xây dựng đồ thị quan hệ nội bộ.

### 2.4.2. Tranh biện Đối kháng Đa tác nhân (LabourCrew, 2026) & Khung ReAct
Faria và cộng sự (tháng 9/2026) với công trình **LabourCrew** đã chứng minh rằng trong các tác vụ đòi hỏi căn cứ pháp lý và tính minh bạch tuyệt đối, cơ chế tranh biện đối kháng đa tác nhân (Multi-Agent Adversarial Deliberation) là phương pháp duy nhất có thể phát hiện triệt để tình trạng thiếu hụt chứng cứ (evidence insufficiency). Thay vì một tác nhân đơn lẻ vừa tạo vừa tự chấm điểm (dẫn đến thiên kiến xác nhận mù quáng), hệ thống tách biệt thành Tác nhân Tạo sinh (Generator) và Tác nhân Phản biện (Critic) độc lập.

Cơ chế này kết hợp nguyên lý ReAct (Reasoning and Acting, Yao et al., 2023) — mô hình hóa chuỗi suy nghĩ (Thought), hành động (Action) và quan sát (Observation) thành một đồ thị tương tác có hướng. Khảo sát toàn cảnh của Singh và cộng sự (2025) khẳng định Agentic RAG chính là tương lai tất yếu của các hệ thống AI tri thức, trong đó các tác nhân đóng vai trò điều phối luồng thông tin, sử dụng công cụ và tự điều chỉnh câu hỏi một cách linh hoạt.

---

## 2.5. KHUNG ĐÁNH GIÁ ĐO LƯỜNG RAG VÀ BỘ NHỚ DÀI HẠN

### 2.5.1. Khung Chỉ số Đánh giá RAGAS (Es et al., 2023)
Khung đo chuẩn hóa RAGAS thiết lập 4 chỉ số cốt lõi phi tham số:
1. **Context Precision ($CP$):** Tỷ lệ các chunk được xếp hạng cao trong ngữ cảnh thực sự liên quan đến câu trả lời chuẩn.
2. **Context Recall ($CR$):** Mức độ đầy đủ của ngữ cảnh truy xuất được so với câu trả lời mặt đất (Ground Truth).
3. **Faithfulness ($\mathcal{F}$):** Tỷ lệ các phát ngôn trong câu trả lời có thể suy diễn logic trực tiếp từ ngữ cảnh được cung cấp, triệt tiêu ảo giác.
4. **Answer Relevance ($AR$):** Độ tương thích ngữ nghĩa giữa câu trả lời sinh ra và ý định truy vấn ban đầu của người dùng.

### 2.5.2. Khung Chẩn đoán Thao tác Bộ nhớ Vi mô EvalMem (Liu et al., 2026)
Trong nghiên cứu công bố tháng 9/2026, Liu và cộng sự đã chỉ ra lỗ hổng lớn của các phương pháp đánh giá RAG hiện nay: chỉ đo lường kết quả đầu-cuối (end-to-end QA) mà không thể định vị được nguyên nhân lỗi xuất phát từ tầng nạp bộ nhớ (memory writing failure) hay tầng truy xuất suy luận (retrieval failure). EvalMem thiết lập hệ thống kiểm tra chẩn đoán ở cấp độ thao tác (Operation-level Diagnostics), cho phép bóc tách độc lập hiệu năng của từng thành phần trong kiến trúc lưu trữ hỗn hợp.

---

## 2.6. MA TRẬN TỔNG HỢP VÀ KHOẢNG TRỐNG NGHIÊN CỨU (THE RESEARCH GAP)

Bảng dưới đây tổng hợp ma trận so sánh các công trình khoa học tiêu biểu đã được khảo cứu và đối chiếu siêu dữ liệu chính thức qua kho lưu trữ Zotero và arXiv.org:

| Công trình & Tác giả | Năm / Xuất bản | Cơ chế Lưu trữ | Nhận biết Thời gian | Vòng lặp Phản biện | Chặn biên Tài nguyên | Giới hạn kỹ thuật chính |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Lewis et al. (RAG)** | 2020 (NeurIPS) | Dense Vector phẳng | ❌ Không | ❌ Thụ động 1 lượt | Không áp dụng | Đứt gãy truy vấn đa chặng; mù mờ thời gian |
| **Edge et al. (GraphRAG)**| 2024 (arXiv) | Graph tĩnh toàn cục | ❌ Không | ❌ Thụ động 1 lượt | Không áp dụng | Chi phí nạp cực cao; đóng băng trước dữ liệu động |
| **Asai et al. (Self-RAG)** | 2023 (arXiv) | Dense Vector phẳng | ❌ Không | ⚠️ Tự phản ánh | ❌ Không | Phụ thuộc vào fine-tuning mô hình mở |
| **Yan et al. (CRAG)** | 2024 (arXiv) | Vector + Web Search | ❌ Không | ⚠️ Sửa truy xuất | ❌ Không | Phụ thuộc nguồn Web ngoài; không có đồ thị nội bộ |
| **Rasmussen et al. (Zep)**| 2025 (arXiv) | Neo4j Graphiti (TKG)| ✅ Có ($[t_v, t_{iv})$) | ❌ Không | Không áp dụng | Tập trung chat memory; chưa có CSDL vector quan hệ |
| **Syed et al. (Chronofy)**| 2026 (arXiv) | Time-Aware Vector | ✅ Hàm suy giảm $\Lambda(t)$ | ❌ Không | Không áp dụng | Chưa tích hợp đồ thị thực thể liên kết |
| **Faria et al. (LabourCrew)**| 2026 (arXiv) | Vector + BM25 | ❌ Không | ✅ Tranh biện đa Agent | ⚠️ Không chặn cứng | Chưa xử lý bài toán dữ kiện biến thiên thời gian |
| **Liu et al. (EvalMem)** | 2026 (arXiv) | Memory Benchmark | ✅ Đánh giá thời gian | Không áp dụng | Không áp dụng | Là công cụ đánh giá, không phải kiến trúc thực thi |
| **Agentic RAG 2.0 (Đề tài)**| **2026** | **PGVector + Graphiti** | **✅ Có (Episodic TKG)** | **✅ Critic độc lập** | **✅ $loop \le 2$, $P_{95} \le 5.8\text{s}$** | **Tối ưu đồng thời lưu trữ kép, tri thức động & độ trễ** |

**Khoảng trống Nghiên cứu (Research Gap):**
*Hiện chưa có một công trình nào tích hợp thành công kiến trúc lưu trữ không gian kép chịu lỗi giữa PostgreSQL (PGVector) và Neo4j (Graphiti nhận biết thời gian), đồng thời vận hành quy trình truy xuất bằng máy trạng thái LangGraph có tác nhân phản biện độc lập với cơ chế chặn cứng chu kỳ lặp để đảm bảo an toàn vận hành thời gian thực.* Đề tài **Agentic RAG 2.0** được thiết kế để giải quyết trọn vẹn khoảng trống khoa học và công nghệ này.
