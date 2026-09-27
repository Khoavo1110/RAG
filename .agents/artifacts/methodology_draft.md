# BẢN THẢO CHƯƠNG PHƯƠNG PHÁP LUẬN (METHODOLOGY DRAFT v2.1)
## Kiến trúc Agentic RAG 2.0: Tích hợp Đồ thị Tri thức Động và Cơ sở Dữ liệu Vector Dưới Tiến trình Suy luận Đa tác nhân

**Vị trí lưu trữ:** `artifacts/methodology_draft.md`  
**Quy chuẩn áp dụng:** `workflows/academic-writing-integrity.md` (Stage 4A)  
**Tiêu chí biên tập:** Chuyển thể 100% sang văn xuôi học thuật liên tục (Prose Narrative), loại bỏ cấu trúc gạch đầu dòng chatbot, đa dạng hóa nhịp điệu câu (Burstiness), giải thích quyết định kỹ thuật thực tế và đối soát trực tiếp mã nguồn `backend/`.

---

### TÓM TẮT CHƯƠNG

Nghiên cứu này thiết lập phương pháp luận khoa học và mô tả kiến trúc kỹ thuật cho hệ thống Agentic RAG 2.0. Mục tiêu trọng tâm là khắc phục hai khiếm khuyết nền tảng của các hệ thống tăng cường truy xuất truyền thống: sự đứt gãy liên kết khi lập luận quan hệ đa chặng và sự mù mờ trước tính biến thiên theo thời gian của dữ liệu doanh nghiệp. Để giải quyết đồng thời hai thách thức này, nghiên cứu đề xuất một kiến trúc lai kết hợp cơ sở dữ liệu quan hệ vector hóa (PostgreSQL/PGVector) và đồ thị tri thức nhận biết thời gian (Neo4j/Graphiti). 

Tiến trình vận hành của hệ thống được điều khiển bởi một đồ thị trạng thái hữu hạn trên nền tảng LangGraph. Quy trình nạp dữ liệu được thiết kế tuần tự hai pha nhằm đảm bảo tính sẵn sàng cao, chấp nhận trạng thái nạp một phần khi bước trích xuất đồ thị gặp sự cố. Quá trình xử lý truy vấn được phân luồng chủ động qua ba kênh chuyên biệt thông qua tác nhân định tuyến ý định, kết hợp cùng một tác nhân phản biện độc lập nhằm kiểm tra tính trung thực và tính đầy đủ của câu trả lời trước khi chuyển giao cho người dùng. Toàn bộ phương pháp được đặt trong một giao thức thử nghiệm đối chuẩn phân tầng gồm bốn nhóm tác vụ độc lập, đi kèm ma trận chỉ số đa chiều và kế hoạch bóc tách thành phần có kiểm định thống kê.

---

### 1. ĐẶT VẤN ĐỀ VÀ CÂU HỎI NGHIÊN CỨU

Trong các bài toán xử lý tri thức chuyên sâu, việc dựa hoàn toàn vào các phép đo khoảng cách hình học cục bộ như khoảng cách Cosine hoặc Euclid trong không gian vector dày $\mathbb{R}^d$ bộc lộ những giới hạn rõ rệt. Khi một kho tài liệu được phân tách thành các khối văn bản độc lập, cấu trúc liên kết ngữ nghĩa giữa các thực thể nằm rải rác ở nhiều trang tài liệu khác nhau gần như bị triệt tiêu hoàn toàn. Nếu một câu hỏi đòi hỏi chuỗi suy luận bắc cầu qua nhiều thực thể trung gian mà câu hỏi đó chỉ đề cập đến thực thể đầu và thực thể cuối, vector nhúng của câu hỏi thường rơi vào vùng lân cận của một phân đoạn đơn lẻ và bỏ rơi các phân đoạn chứa mắt xích logic còn lại. Hậu quả là mô hình ngôn ngữ lớn nhận được một ngữ cảnh không đầy đủ, dẫn đến việc tự động suy diễn thông tin sai lệch ngoài tài liệu.

Bên cạnh sự đứt gãy liên kết quan hệ, các hệ thống vector truyền thống còn gặp phải điểm nghẽn về tính thời gian của thông tin. Dữ liệu thực tế của các tổ chức luôn vận động theo thời gian, nơi một điều khoản hợp đồng hay một vị trí nhân sự có thể bị sửa đổi hoặc thay thế sau một mốc thời gian cụ thể. Việc lưu trữ các khối văn bản tĩnh không kèm nhãn thời gian hiệu lực khiến giải thuật tìm kiếm vector dễ dàng trích xuất các dữ kiện cũ mâu thuẫn với thực tại. 

Để giải quyết các rào cản trên, nghiên cứu này xác lập ba câu hỏi nghiên cứu cụ thể gắn liền với các giả thuyết có thể kiểm chứng. Câu hỏi nghiên cứu thứ nhất ($RQ_1$) khảo sát xem việc bổ sung cấu trúc đồ thị động có cải thiện đáng kể độ phủ ngữ cảnh đối với các câu hỏi đa chặng và dữ liệu biến động hay không, với giả thuyết bác bỏ $H_{0,1}$ là độ phủ ngữ cảnh giữa hệ thống lai và hệ thống vector đơn thuần không có sự khác biệt có ý nghĩa thống kê ($p \ge 0.01$). Câu hỏi nghiên cứu thứ hai ($RQ_2$) đo lường khả năng triệt tiêu ảo giác của vòng lặp phản biện hai chiều, đặt giả thuyết $H_{0,2}$ rằng tỷ lệ phát biểu không có căn cứ giữa phiên bản có phản biện và không có phản biện là tương đương nhau. Cuối cùng, câu hỏi nghiên cứu thứ ba ($RQ_3$) phân tích sự đánh đổi kỹ thuật giữa thời gian phản hồi phân vị $P_{95}$, lượng token tiêu thụ và độ chính xác của câu trả lời trong điều kiện vận hành thực tế.

---

### 2. TỔNG QUAN TÀI LIỆU VÀ KHOẢNG TRỐNG KỸ THUẬT

Nền tảng của các phương pháp tăng cường truy xuất bắt nguồn từ công trình của Lewis và cộng sự (2020) [5], nơi ngữ cảnh được trích xuất dựa trên tích vô hướng giữa vector truy vấn và vector tài liệu. Dù khảo cứu của Gao và cộng sự (2023) [6] đã chỉ ra nhiều cải tiến trong kỹ thuật phân mảnh và tái xếp hạng, bản chất của không gian vector vẫn chỉ tối ưu cho các truy vấn đơn chặng mang tính tra cứu cục bộ. Khi đối mặt với nhu cầu tổng hợp tri thức toàn thể, Edge và cộng sự tại Microsoft Research (2024) [2] đã đề xuất GraphRAG, sử dụng mô hình ngôn ngữ để trích xuất thực thể toàn cục và phân cụm theo giải thuật Leiden nhằm tạo ra các bản tóm tắt cộng đồng phân cấp. Tuy nhiên, hướng tiếp cận này mang bản chất của một đồ thị tĩnh với chi phí tính toán ban đầu rất lớn, đòi hỏi hàng nghìn lượt gọi mô hình cho mỗi tài liệu và không có khả năng thích ứng khi dữ liệu phát sinh liên tục theo thời gian.

Để xử lý sự biến thiên thời gian, Rasmussen và cộng sự (2025) [1] giới thiệu kiến trúc Graphiti, tổ chức tri thức dưới dạng các chuỗi sự kiện được gắn nhãn thời gian rõ ràng và tự động chuẩn hóa thực thể. Các cạnh quan hệ trong Graphiti mang khoảng thời gian hiệu lực, giúp hệ thống phân biệt rạch ròi giữa trạng thái quá khứ và trạng thái hiện tại. Mặt khác, các nghiên cứu về khả năng tự phản biện như Self-RAG của Asai và cộng sự (2023) [3] hay CRAG của Yan và cộng sự (2024) [4] đã chứng minh rằng việc chèn thêm các bước đánh giá độc lập có thể nâng cao tính trung thực của câu trả lời. Dẫu vậy, Self-RAG đòi hỏi phải can thiệp vào trọng số mô hình thông qua quá trình tinh chỉnh các token đặc biệt, trong khi CRAG lại phụ thuộc vào nguồn tìm kiếm trên mạng công cộng khi thiếu dữ liệu nội bộ.

Từ bức tranh tổng quan trên, khoảng trống nghiên cứu của đồ án được xác lập rõ ràng: hiện chưa có một giải pháp mã nguồn mở nào kết hợp thành công tính năng lưu trữ kép có khả năng chịu lỗi giữa PostgreSQL (PGVector) và Neo4j (Graphiti), đồng thời vận hành một quy trình suy luận có điều kiện chặn biên an toàn mà không đòi hỏi phải thay đổi trọng số nội tại của mô hình ngôn ngữ.

---

### 3. MÔ HÌNH HÓA TOÁN HỌC VÀ KIẾN TRÚC HIỆN THỰC

Hệ thống quản lý dữ liệu trên hai cấu trúc biểu diễn không gian độc lập. Cấu trúc thứ nhất là không gian vector rời rạc $\mathcal{D}$, nơi văn bản được phân nhỏ thành tập hợp các khối $d_i = \langle c_i, \mathbf{v}_i, \text{id}_i \rangle$, với chuỗi ký tự $c_i$ và vector nhúng $\mathbf{v}_i \in \mathbb{R}^d$ được chỉ mục trên bảng `document_chunks` của PostgreSQL thông qua phần mở rộng `pgvector`. Cấu trúc thứ hai là đồ thị tri thức động $\mathcal{G} = (\mathcal{V}, \mathcal{E}, \mathcal{T})$ lưu trữ trên Neo4j, trong đó $\mathcal{V}$ là tập các thực thể chuẩn hóa, $\mathcal{T}$ là trục thời gian của các sự kiện, và $\mathcal{E}$ là tập các cạnh quan hệ có hướng $e = \langle u, v, r, t, \psi \rangle$ gắn liền với mã định danh sự kiện $\psi$ tại thời điểm $t$. Cả hai cấu trúc lưu trữ này đều đã được hiện thực hóa hoàn chỉnh trong mã nguồn dự án `[đã triển khai]`.

Quy trình nạp dữ liệu trong tệp `backend/app/ingestion/database_sync.py` được thiết kế theo cơ chế cam kết trạng thái hai pha có nhánh bảo vệ `[đã triển khai]`. Thay vì sử dụng cơ chế nạp đồng thời thiếu an toàn, hệ thống thực hiện ghi bản ghi tài liệu và các khối phân đoạn vào PostgreSQL trước, sau đó commit giao dịch kho dữ liệu vector. Sau khi dữ liệu vector đã được bảo toàn chắc chắn, hệ thống mới tiến hành gọi hàm bất đồng bộ sang Graphiti để trích xuất thực thể vào Neo4j. Trong trường hợp bước trích xuất đồ thị gặp sự cố do nghẽn mạng hoặc quá thời gian chờ, hệ thống chủ động bắt ngoại lệ, ghi log cảnh báo và giữ nguyên các bản ghi trong PostgreSQL. Quyết định kỹ thuật này chấp nhận trạng thái nạp một phần để bảo toàn tính khả dụng của dịch vụ, cho phép người dùng vẫn có thể tra cứu tài liệu ngay lập tức qua kênh tìm kiếm vector mà không bị mất dữ liệu.

Tiến trình suy luận của hệ thống được tổ chức dưới dạng một đồ thị trạng thái có hướng trên nền tảng LangGraph trong tệp `backend/app/agents/router.py` `[đã triển khai]`. Khi nhận câu hỏi từ người dùng, tác nhân định tuyến sẽ phân tích ngữ nghĩa với tham số nhiệt độ bằng 0 để quyết định hướng truy xuất: nhánh vector dành cho các câu hỏi tra cứu dữ kiện cục bộ, nhánh graph dành cho các câu hỏi phân tích mạng lưới liên kết, và nhánh hybrid dành cho các yêu cầu phức hợp cần cả mô tả văn bản lẫn quan hệ thực thể. Sau khi tác nhân sinh thiết lập dự thảo câu trả lời, tác nhân phản biện trong tệp `backend/app/agents/critic.py` sẽ thực hiện kiểm tra chéo hai chiều về tính trung thực và tính đầy đủ `[đã triển khai]`. Nếu dự thảo chưa đạt, tác nhân phản biện sẽ phát sinh câu truy vấn tinh chỉnh để tiến hành truy xuất bổ sung. Nhằm triệt tiêu rủi ro cạn kiệt tài nguyên do vòng lặp vô hạn, hệ thống đặt điều kiện chặn cứng: tiến trình tự động kết thúc và xuất bản thảo tốt nhất hiện có khi số chu kỳ lặp chạm ngưỡng 2, tương đương tối đa ba lượt truy xuất. Riêng công thức hàm chấm điểm lai đa biến $\mathcal{S}_{\text{hybrid}} = \alpha \cdot \text{Sim}_{\text{dense}} + \beta \cdot \text{Score}_{\text{graph}}$ nhằm tái sắp xếp các kết quả là hướng cải tiến giải thuật trong tương lai; mã nguồn hiện hành thực hiện gom tụ và ghép nối các chuỗi ngữ cảnh thô `[đề xuất]`.

---

### 4. GIAO THỨC ĐÁNH GIÁ ĐỐI CHUẨN

Để kiểm chứng tính ưu việt của phương pháp, một giao thức thử nghiệm phân tầng được thiết lập với tập dữ liệu kiểm chuẩn gồm $N=100$ câu hỏi được gán nhãn sự thật chuẩn. Tập dữ liệu này được phân chia thành bốn nhóm tác vụ độc lập: 30 câu hỏi tra cứu dữ kiện đơn chặng trong một phân đoạn văn bản; 35 câu hỏi lập luận đa chặng đòi hỏi bắc cầu qua chuỗi thực thể phân tán ở nhiều tài liệu; 20 câu hỏi liên quan đến sự biến động dữ liệu theo thời gian; và 15 câu hỏi không có căn cứ trong tài liệu hoặc chứa tiền đề sai nhằm thử thách khả năng phát hiện thiếu thông tin của tác nhân phản biện.

Chất lượng của hệ thống được lượng hóa qua năm thước đo chính, bao gồm độ chính xác ngữ cảnh ($CP$), độ phủ ngữ cảnh ($CR$), tính trung thực của phát ngôn ($\mathcal{F}$), độ liên quan của câu trả lời ($\mathcal{AR}$), và độ trễ vận hành phân vị $P_{50}, P_{95}$. Bốn cấu hình đối trọng được đưa vào thử nghiệm bóc tách thành phần trên cùng một môi trường phần cứng và mô hình ngôn ngữ nền tảng: cấu hình B1 chỉ dùng PGVector; cấu hình B2 chỉ dùng Neo4j Graphiti; cấu hình B3 lai ghép hai nguồn nhưng không có vòng phản biện; và cấu hình B4 là hệ thống Agentic RAG 2.0 hoàn chỉnh. 

Về mặt liêm chính học thuật, nghiên cứu ghi nhận rõ ràng rằng các số liệu so sánh giữa bốn cấu hình trong các báo cáo thiết kế hiện tại thể hiện ma trận đối chuẩn đề xuất và kỳ vọng lý thuyết; các số đo thực nghiệm chính xác sẽ được thu thập sau khi kích hoạt kịch bản kiểm thử tự động trên hạ tầng dịch vụ Docker `[chưa xác minh]`.

---

### 5. GIỚI HẠN VÀ THÁCH THỨC VẬN HÀNH

Nghiên cứu thừa nhận ba giới hạn kỹ thuật cần được cân nhắc trong quá trình triển khai thực tế. Giới hạn thứ nhất là sự gia tăng độ trễ: đối với các câu hỏi phức tạp kích hoạt trọn vẹn ba chu kỳ phản biện, thời gian xử lý toàn trình có thể kéo dài gấp hai đến ba lần so với kiến trúc RAG một lượt thông thường, đòi hỏi phải áp dụng cơ chế truyền dữ liệu dạng dòng trong các giao diện người dùng tương tác. Giới hạn thứ hai là sự phụ thuộc vào năng lực bóc tách của mô hình ngôn ngữ ở pha nạp ban đầu, nơi các tài liệu có cấu trúc bảng biểu phức tạp hoặc ngữ pháp không chuẩn có thể dẫn đến việc sinh các cạnh quan hệ không chính xác trên Neo4j. Giới hạn thứ ba là sự tồn tại của trạng thái nạp không đồng bộ cục bộ khi dịch vụ trích xuất đồ thị gặp sự cố, đòi hỏi hệ thống phải có các tiến trình quét bù định kỳ để đồng bộ hóa hoàn toàn hai kho dữ liệu.

---

### 6. TÀI LIỆU THAM KHẢO

[1] P. Rasmussen, P. Paliychuk, T. Beauvais, J. Ryan, và D. Chalef, "Zep: A Temporal Knowledge Graph Architecture for Agent Memory," *arXiv preprint arXiv:2501.13956*, 2025. https://doi.org/10.48550/arXiv.2501.13956.

[2] D. Edge et al., "From Local to Global: A Graph RAG Approach to Query-Focused Summarization," *arXiv preprint arXiv:2404.16130*, 2024. https://doi.org/10.48550/arXiv.2404.16130.

[3] A. Asai, Z. Wu, Y. Wang, A. Sil, và H. Hajishirzi, "Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection," *arXiv preprint arXiv:2310.11511*, 2023. https://doi.org/10.48550/arXiv.2310.11511.

[4] S.-Q. Yan, J.-C. Gu, Y. Zhu, và Z.-H. Ling, "Corrective Retrieval Augmented Generation," *arXiv preprint arXiv:2401.15884*, 2024. https://doi.org/10.48550/arXiv.2401.15884.

[5] P. Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks," trong *Advances in Neural Information Processing Systems (NeurIPS)*, tập 33, 2020, tr. 9459-9474.

[6] Y. Gao et al., "Retrieval-Augmented Generation for Large Language Models: A Survey," *arXiv preprint arXiv:2312.10997*, 2023. https://doi.org/10.48550/arXiv.2312.10997.

[7] S. Es, J. James, L. Espinosa-Anke, và S. Schockaert, "Ragas: Automated Evaluation of Retrieval Augmented Generation," *arXiv preprint arXiv:2309.15217*, 2023.
