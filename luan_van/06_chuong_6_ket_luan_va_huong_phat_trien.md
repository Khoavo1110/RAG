# CHƯƠNG 6: KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN

---

## 6.1. TỔNG KẾT CÁC KẾT QUẢ ĐẠT ĐƯỢC

Luận văn đã nghiên cứu, thiết kế và hiện thực hóa thành công hệ thống **Agentic RAG 2.0** — một kiến trúc Tăng cường Truy xuất Sinh thế hệ mới kết hợp hài hòa giữa Cơ sở dữ liệu Vector quan hệ (PostgreSQL/PGVector) và Đồ thị Tri thức Động nhận biết thời gian (Neo4j Graphiti), được điều khiển bởi máy trạng thái suy luận LangGraph có tác nhân phản biện độc lập. 

Các kết quả khoa học và kỹ thuật nổi bật mà đề tài đã đạt được bao gồm:

1. **Về mặt Kiến trúc & Lưu trữ Không gian Kép:**  
   Thiết lập thành công quy trình nạp dữ liệu tuần tự hai pha chịu lỗi (**Two-Phase Fault-Tolerant Ingestion**). Bằng việc ghi nhận dữ liệu vector vào PostgreSQL trước khi đồng bộ sang Neo4j Graphiti, hệ thống bảo đảm 100% tính sẵn sàng truy vấn của tầng dữ liệu ngay cả khi quá trình trích xuất thực thể đồ thị gặp sự cố gián đoạn API, loại bỏ hoàn toàn rủi ro nghẽn giao dịch phân tán.

2. **Về mặt Điều phối Suy luận & Khử Ảo giác:**  
   Xây dựng hoàn chỉnh đồ thị trạng thái LangGraph với 4 tác nhân chuyên trách (`Router`, `Retriever`, `Generator`, `Critic`). Cơ chế kiểm tra chéo hai chiều (Faithfulness & Completeness) của `CriticAgent` kết hợp cùng điều kiện chặn biên cứng toán học ($loop\_count \le 2$) đã triệt tiêu hoàn toàn nguy cơ bùng nổ vòng lặp vô hạn, nâng tỷ lệ trung thực phát ngôn đạt mức **94.1%** (+23.5% so với mô hình không có phản biện).

3. **Về mặt Nhận thức Thời gian & Khử Dữ kiện Quá hạn:**  
   Ứng dụng thành công cấu trúc cạnh sự kiện (`episodes`) với các thuộc tính khoảng thời gian hiệu lực $[t_{\text{valid}}, t_{\text{invalid}})$ và định dạng chuẩn hóa `<FACTS>`, giúp hệ thống giảm thiểu tỷ lệ phát ngôn sai lệch do dữ kiện cũ (*stale facts*) từ **28.4% xuống còn 4.6%**.

4. **Về mặt Hiệu năng & Giá trị Thực nghiệm:**  
   Thực nghiệm định lượng trên 100 câu hỏi phức tạp đã chứng minh hệ thống đạt độ phủ ngữ cảnh **89.4%** trên các truy vấn đa chặng (tăng gấp đôi so với 50.8% của Naive Vector RAG), khống chế thành công độ trễ phân vị thứ 95 ở mức **5.42 giây** ($P_{95} \le 5.8\text{s}$) và tiêu thụ lượng token thấp hơn **3.16 lần** so với kiến trúc tóm tắt cộng đồng của Static GraphRAG. Toàn bộ 3 câu hỏi nghiên cứu ($RQ_1, RQ_2, RQ_3$) đều được kiểm định bằng phương pháp thống kê với độ tin cậy vượt trội ($p < 0.001$).

---

## 6.2. CÁC GIỚI HẠN KỸ THUẬT CỦA NGHIÊN CỨU

Bên cạnh những đóng góp vượt bậc, nghiên cứu cũng thẳng thắn ghi nhận một số giới hạn kỹ thuật cần được cải tiến:

1. **Sự gia tăng độ trễ ở các truy vấn biên:**  
   Đối với khoảng 7% các câu hỏi phức tạp kích hoạt trọn vẹn cả 2 chu kỳ phản biện, thời gian xử lý toàn trình kéo dài đến 5.4 giây. Trong các ứng dụng web tương tác người dùng, thời gian chờ này đòi hỏi giao diện phải triển khai cơ chế truyền dữ liệu dạng dòng (streaming Server-Sent Events) kèm hiển thị dòng suy nghĩ động (Thought Process timeline) để tối ưu trải nghiệm tương tác.
2. **Hiện tượng bất đối xứng cục bộ trong trạng thái nạp một phần:**  
   Khi khâu nạp đồ thị Graphiti gặp sự cố ngoại lệ (trả về trạng thái `partial_success`), dữ liệu chỉ sẵn sàng trên PGVector mà chưa có mặt trên Neo4j. Mặc dù hệ thống không bị sập, nhưng các truy vấn đa chặng liên quan đến tài liệu này tạm thời chỉ có thể dựa vào tìm kiếm ngữ nghĩa mờ cho đến khi tiến trình đồng bộ quét bù chạy lại.
3. **Phụ thuộc vào năng lực bóc tách của mô hình nhúng đầu vào:**  
   Đối với các tài liệu kỹ thuật chứa các bảng biểu đan xen phức tạp hoặc văn bản scan có độ nhiễu cao, khâu nhận diện thực thể tự động của Graphiti đôi khi có thể bỏ sót các quan hệ ngầm định nếu không có bộ tiền xử lý chuyên biệt theo định dạng văn bản.

---

## 6.3. HƯỚNG PHÁT TRIỂN TRONG TƯƠNG LAI

Để phát triển hệ sinh thái **Agentic RAG 2.0** lên mức độ hoàn thiện sản phẩm công nghiệp quy mô lớn, các hướng nghiên cứu mở rộng tiếp theo bao gồm:

1. **Tích hợp Tầng Tái xếp hạng Đa biến (Neural Cross-Encoder Reranker):**  
   Nghiên cứu áp dụng mô hình tái xếp hạng BGE-Reranker hoặc Cohere Rerank trực tiếp sau bước ghép ngữ cảnh `<FACTS>`, kết hợp cùng trọng số hàm suy giảm thời gian của Chronofy (Syed et al., 2026) để tối ưu hóa thứ tự ưu tiên của các đoạn trích trước khi đưa vào Generator.
2. **Ứng dụng Bộ nhớ Đệm Ngữ nghĩa Đồ thị (Graph Semantic Caching với Redis):**  
   Triển khai cơ chế lưu đệm ngữ nghĩa trên cụm Redis hiện có nhằm ghi nhớ các đồ thị con (subgraphs) và chuỗi suy luận của các câu hỏi thường gặp, giúp kéo giảm độ trễ phân vị $P_{50}$ xuống dưới **1.0 giây** và tiết kiệm đến 40% chi phí API LLM.
3. **Mở rộng Kiến trúc Tự học Liên tục theo Thời gian thực (Continuous Learning):**  
   Ứng dụng các nguyên lý mạng bộ nhớ sự kiện động DYNA (Sarabadani & Tajvidiyan, 2026) để cho phép hệ thống tự động ghi nhận phản hồi của người dùng (human-in-the-loop feedback) thành các episode tri thức mới, giúp đồ thị tri thức tự tiến hóa và nâng cao độ chính xác theo thời gian vận hành.
