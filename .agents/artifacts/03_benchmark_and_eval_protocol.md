# 📊 GIAI ĐOẠN 3: THIẾT KẾ KHUNG THỬ NGHIỆM & THANG ĐO ĐỐI CHUẨN
## Experimental Protocol & Benchmark Metrics for Agentic RAG 2.0

**Đề tài:** Agentic RAG 2.0: Tích hợp Đồ thị Tri thức Động (Neo4j Graphiti) và Cơ sở Dữ liệu Vector (PGVector) với Vòng lặp Suy luận Đa tác nhân (Multi-Agent Reasoning Loop)  
**Tiêu chuẩn áp dụng:** Ragas Evaluation Framework + MLOps Production Gateways  

---

### 1. THIẾT KẾ TẬP DỮ LIỆU ĐỐI CHUẨN (BENCHMARK DATASET DESIGN)

Để đánh giá toàn diện năng lực của hệ thống theo 3 câu hỏi nghiên cứu ($RQ_1, RQ_2, RQ_3$), bộ dữ liệu thử nghiệm được thiết kế theo cấu trúc phân tầng với tổng cộng $N = 100$ câu hỏi mẫu được gán nhãn chuẩn (Gold Standards), chia thành 4 nhóm tác vụ cụ thể:

| Nhóm Tác vụ | Ký hiệu | Số lượng mẫu | Đặc tính truy vấn & Thách thức kỹ thuật | Ví dụ minh họa |
| :--- | :---: | :---: | :--- | :--- |
| **Tra cứu Đơn chặng (Single-hop Lookup)** | $\mathcal{D}_{\text{single}}$ | 30 | Thông tin nằm trọn trong 1 chunk văn bản đơn lẻ; kiểm tra tốc độ và độ khớp từ khóa/ngữ nghĩa của Vector DB. | *"FPT và NVIDIA đã công bố hợp tác xây dựng AI Factory vào thời gian nào?"* |
| **Lập luận Đa chặng (Multi-hop Relational)** | $\mathcal{D}_{\text{multi}}$ | 35 | Câu trả lời đòi hỏi bắc cầu qua $\ge 2$ thực thể phân tán ở các tài liệu khác nhau mà phép tìm kiếm vector đơn thuần không thể tìm thấy trong Top-K. | *"Công ty nào là đối tác đầu tư chiến lược của đơn vị đang cung cấp hạ tầng GPU cho FPT?"* |
| **Xung đột Thời gian (Temporal Dynamic)** | $\mathcal{D}_{\text{temp}}$ | 20 | Dữ liệu chứa thông tin biến động qua các mốc thời gian (ví dụ: chức danh lãnh đạo cũ/mới, giá trị vốn hóa theo quý). Kiểm tra khả năng phân biệt sự kiện mới nhất dựa trên nhãn thời gian của Graphiti. | *"Ai hiện đang là Giám đốc phụ trách mảng Điện toán đám mây sau đợt tái cấu trúc tháng 6/2024?"* |
| **Thiếu thông tin / Ngoài phạm vi (Unanswerable / Boundary)** | $\mathcal{D}_{\text{unans}}$ | 15 | Thông tin hoàn toàn không có trong kho tài liệu hoặc câu hỏi chứa tiền đề sai. Kiểm tra khả năng từ chối trả lời của Critic Agent nhằm ngăn chặn ảo giác. | *"Ngân sách chi tiết của dự án hợp tác giữa FPT và OpenAI trong năm 2022 là bao nhiêu?"* *(Dự án không có thật)* |

---

### 2. HỆ THỐNG CHỈ SỐ ĐÁNH GIÁ (EVALUATION METRICS MATRIX)

Hệ thống đo lường được chuẩn hóa thành 3 nhóm chỉ số định lượng:

#### 2.1. Nhóm Chất lượng Truy xuất (Retrieval Quality Metrics)
1. **Context Precision ($CP$):** Tỷ lệ các chunk/facts liên quan trực tiếp đến câu trả lời nằm ở vị trí ưu tiên trong ngữ cảnh được trích xuất:
   $$CP@K = \frac{\sum_{k=1}^K \text{Precision}@k \times \mathbb{I}(\text{chunk}_k \text{ is relevant})}{\text{Tổng số chunk liên quan}}$$
2. **Context Recall ($CR$):** Mức độ bao phủ của ngữ cảnh được trích xuất so với toàn bộ sự thật cần thiết trong nhãn chuẩn (Ground Truth $y^*$):
   $$CR = \frac{|\text{Facts}(C) \cap \text{Facts}(y^*)|}{|\text{Facts}(y^*)|}$$
3. **Hit Rate @ $K$ ($HR@K$):** Tỷ lệ phần trăm câu truy vấn mà trong đó Top-$K$ tài liệu/facts trích xuất chứa ít nhất một thông tin trả lời được câu hỏi.

#### 2.2. Nhóm Độ chính xác Sinh & Lập luận (Generation & Reasoning Metrics)
1. **Tính trung thực (Faithfulness / Groundedness - $F$):** Tỷ lệ các phát biểu (claims) trong câu trả lời $y$ được suy diễn trực tiếp từ ngữ cảnh trích xuất $\mathcal{C}$, không chứa ảo giác:
   $$F(y, \mathcal{C}) = \frac{|\{c \in \text{Claims}(y) \mid \mathcal{C} \models c\}|}{|\text{Claims}(y)|} \in [0, 1]$$
2. **Độ phù hợp Câu trả lời (Answer Relevance - $AR$):** Độ tương đồng ngữ nghĩa giữa câu trả lời sinh ra và ý định thực sự của câu hỏi $q$:
   $$AR = \cos(E(y), E(q))$$
3. **Tỷ lệ Khử Ảo giác khi Thiếu Ngữ cảnh (Rejection Rate on $\mathcal{D}_{\text{unans}}$):** Tỷ lệ hệ thống phát hiện thông tin không đủ và từ chối sinh thông tin bịa đặt.

#### 2.3. Nhóm Hiệu năng Kỹ thuật & Chi phí (System Performance & Resource Consumption)
1. **Độ trễ phản hồi (End-to-End Latency):** Thời gian đo đạc từ khi nhận truy vấn đến khi xuất câu trả lời hoàn tất, ghi nhận tại phân vị $P_{50}, P_{90}, P_{95}$ (đơn vị: mili-giây ms).
2. **Tiêu hao Token (Token Consumption per Query):** Số lượng token đầu vào (prompt tokens) và token đầu ra (completion tokens) tiêu thụ trên toàn bộ các chu kỳ lặp của Agentic Loop.
3. **Tần suất Lặp của Critic (Average Critic Loop Iterations):** Số chu kỳ lặp trung bình $\bar{c}_{\text{loop}} = \frac{1}{|Q|} \sum_{i=1}^{|Q|} c_{\text{loop}}^{(i)} \in [0, 2]$.

---

### 3. CÁC MÔ HÌNH ĐỐI TRỌNG (BASELINE MODELS FOR COMPARISON)

Để kiểm chứng tính khả bác và tính ưu việt của phương pháp đề xuất, 4 biến thể hệ thống được đưa vào thử nghiệm đối đầu trên cùng một môi trường phần cứng, cùng mô hình nhúng và cùng LLM (`gemini-2.0-flash` hoặc `qwen2.5:3b`):

```
[B1: PGVector Only]  ──┐
[B2: Graphiti Only]  ──┼──> [Tập Đánh giá N=100] ──> [So sánh: Ragas + Latency + Token Cost]
[B3: Hybrid No-Critic] ─┤
[B4: Proposed System] ─┘
```

1. **Baseline 1: Dense Vector RAG (PGVector-Only):**
   - Chỉ sử dụng tìm kiếm cosine trên bảng `document_chunks`.
   - Sinh câu trả lời một lần (Single-pass Generation) không có Critic.
2. **Baseline 2: Knowledge Graph RAG (Graphiti-Only):**
   - Chỉ sử dụng tìm kiếm quan hệ thực thể trên Neo4j qua `graph_search_tool`.
   - Không có ngữ cảnh văn bản thô từ PGVector; không có Critic.
3. **Baseline 3: Hybrid Retrieval không có Critic (Ablation: No-Critic Hybrid):**
   - Định tuyến ý định qua Router và truy xuất đồng thời từ cả PGVector lẫn Neo4j Graphiti.
   - Ghép ngữ cảnh và sinh câu trả lời một lần duy nhất; bỏ qua nút `critic_node` (không có cơ chế tự sửa lỗi).
4. **Proposed Architecture: Agentic RAG 2.0 (Full Pipeline):**
   - Đầy đủ 4 thành phần: Intent Router $\to$ Hybrid Retriever $\to$ Generator $\to$ Critic Agent kèm tái tạo truy vấn ($loop\_count \le 2$).

---

### 4. KẾ HOẠCH PHÂN TÍCH BÓC TÁCH (ABLATION STUDY PLAN)

Thử nghiệm bóc tách thành phần (Ablation Analysis) được thiết kế để trả lời trực diện vai trò của từng cơ chế:

| Phép thử bóc tách | Thành phần loại bỏ | Mục tiêu kiểm chứng | Kỳ vọng thực nghiệm |
| :--- | :--- | :--- | :--- |
| **Ablation 1** | Loại bỏ Neo4j Graphiti (về B1) | Đo lường mức độ suy giảm của Context Recall và Answer Accuracy trên tập $\mathcal{D}_{\text{multi}}$ và $\mathcal{D}_{\text{temp}}$. | Nếu không có Đồ thị, $CR$ trên $\mathcal{D}_{\text{multi}}$ dự kiến giảm $\ge 30\%$. |
| **Ablation 2** | Loại bỏ PGVector (về B2) | Đo lường khả năng giải quyết các câu hỏi chi tiết cục bộ trên tập $\mathcal{D}_{\text{single}}$. | Nếu chỉ dùng Đồ thị, độ trễ trích xuất tăng và độ đầy đủ của chi tiết văn bản giảm. |
| **Ablation 3** | Loại bỏ Critic Agent (về B3) | Đo lường tỷ lệ ảo giác (Hallucination Rate) và số lượng câu trả lời bị thiếu thông tin. | Khi có Critic, Faithfulness dự kiến tăng từ $\approx 75\%$ lên $\ge 92\%$, bù lại bằng việc tăng độ trễ $P_{95}$. |

---

### 5. KIỂM SOÁT ĐỘ HỢP LỆ & KHẢ NĂNG TÁI LẬP (REPRODUCIBILITY & VALIDITY CONTROLS)

1. **Kiểm soát rò rỉ dữ liệu (Data Leakage Control):** Toàn bộ các câu hỏi trong tập Benchmark được biên soạn độc lập với quy trình chunking của tài liệu; các câu hỏi không chứa nguyên văn các chuỗi ký tự (exact string matches) có trong văn bản nguồn.
2. **Cố định tham số ngẫu nhiên (Determinism & Seeds):** Tham số nhiệt độ của Router và Critic được cố định tại $\text{temperature} = 0.0$ để loại bỏ tính bất định; Generator đặt $\text{temperature} = 0.3$.
3. **Ý nghĩa Thống kê (Statistical Significance):** Mọi phép so sánh giữa Agentic RAG 2.0 và các baselines đều được kiểm định bằng kiểm định Student's $t$-test cặp (Paired $t$-test) với ngưỡng tin cậy $p < 0.01$.

---

### 6. KẾT LUẬN GIAI ĐOẠN 3 (STAGE 3 ARTIFACT SIGN-OFF)
- **Tình trạng:** Khung đánh giá được thiết kế chặt chẽ, đầy đủ định nghĩa toán học của các chỉ số, kịch bản bóc tách và baselines công bằng.
- **Chuyển giao:** Đầu vào cho **Giai đoạn 4: Thẩm định Phản biện Khoa học, Kiểm tra Đạo văn & Tổng hợp Báo cáo Hoàn chỉnh**.
