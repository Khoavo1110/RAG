# LUẬN VĂN

## Nghiên cứu và xây dựng hệ thống Agentic RAG 2.0: Truy xuất tài liệu kết hợp và kiểm chứng câu trả lời có giới hạn

**Học viên:** [Bổ sung họ và tên]  
**Mã học viên:** [Bổ sung mã học viên]  
**Ngành/chuyên ngành:** [Bổ sung ngành/chuyên ngành]  
**Cơ sở đào tạo:** [Bổ sung tên trường và khoa]  
**Người hướng dẫn:** [Bổ sung họ tên, học hàm/học vị theo mẫu của trường]  
**Thời điểm biên tập:** Tháng 9 năm 2026

## Tóm tắt

Luận văn nghiên cứu việc xây dựng hệ thống hỏi đáp trên tài liệu tiếng Việt có thông tin phân tán, tham chiếu chéo và các văn bản điều chỉnh. Hệ thống Agentic RAG 2.0 lưu tài liệu gốc trong PostgreSQL, kết hợp tìm kiếm từ vựng với pgvector và bổ sung khả năng tìm nguồn qua Neo4j/Graphiti. Câu trả lời được tạo theo cấu trúc nhận định, trích đoạn và mã nguồn; sau đó được kiểm tra và cho phép sửa tối đa một lần. Ở phiên bản được đánh giá, bản tổng hợp chưa đạt kiểm chứng được thay bằng bằng chứng gốc; khi không có nguồn, hệ thống thông báo thiếu thông tin. Phương pháp nghiên cứu gồm phân tích yêu cầu, xây dựng nguyên mẫu và phân tích lại các bản ghi đánh giá đã lưu trong dự án. Bộ dữ liệu gồm 22 tài liệu doanh nghiệp hư cấu và 20 ca kiểm tra. Trên 18 câu hỏi độc lập, tỷ lệ mã tài liệu tham chiếu tìm được trung bình tăng từ 0,7500 lên 0,9676 sau mở rộng tham chiếu. Tuy nhiên, hai cấu hình sử dụng ngân sách khác nhau nên kết quả chưa xác định được tác động riêng của từng thành phần. Lượt đánh giá với qwen2.5:3b ghi nhận 0/20 bản tổng hợp đạt kiểm chứng và 20/20 phản hồi chuyển sang trích đoạn nguồn. Kết quả cho thấy truy xuất được đủ nguồn chưa đồng nghĩa với tổng hợp đúng và đủ. Đóng góp của luận văn nằm ở thiết kế quy trình có thể truy vết nguồn, giới hạn số lần sửa và nhận diện các điểm chưa đạt của nguyên mẫu. Chưa có căn cứ kết luận hệ thống vượt trội về độ đúng câu trả lời, xử lý thời gian hoặc độ trễ so với các phương pháp đối chứng.

*Từ khóa:* sinh tăng cường truy xuất, truy xuất kết hợp, bằng chứng nguồn, kiểm chứng câu trả lời, PostgreSQL, Graphiti.

## Mục lục

- Chương 1. Tổng quan và vấn đề nghiên cứu
  - 1.1. Bối cảnh và lý do chọn đề tài
  - 1.2. Mục tiêu nghiên cứu
  - 1.3. Câu hỏi nghiên cứu
  - 1.4. Đối tượng, phạm vi và cách tiếp cận
  - 1.5. Đóng góp và giới hạn của đóng góp
  - 1.6. Cấu trúc luận văn
- Chương 2. Cơ sở lý thuyết và nghiên cứu liên quan
  - 2.1. Sinh tăng cường truy xuất
  - 2.2. Kết hợp truy xuất từ vựng và vector
  - 2.3. Đồ thị tri thức và thông tin thời gian
  - 2.4. Tự phản hồi và kiểm chứng câu trả lời
  - 2.5. Các khía cạnh đánh giá
  - 2.6. Định vị nghiên cứu
- Chương 3. Phương pháp nghiên cứu và thiết kế hệ thống
  - 3.1. Bài toán và nguyên tắc thiết kế
  - 3.2. Kiến trúc tổng thể
  - 3.3. Lưu tài liệu và lập chỉ mục
  - 3.4. Truy xuất và mở rộng bằng chứng
  - 3.5. Sinh, kiểm chứng và sửa câu trả lời
  - 3.6. Giới hạn thực thi và xử lý lỗi
  - 3.7. Phạm vi hỗ trợ thời gian và khác biệt giao diện
- Chương 4. Dữ liệu và phương pháp đánh giá
  - 4.1. Nguồn bằng chứng và phiên bản thực nghiệm
  - 4.2. Bộ dữ liệu Minh An
  - 4.3. Các cấu hình được so sánh
  - 4.4. Định nghĩa chỉ số
  - 4.5. Quy trình phân tích và khả năng tái lập
  - 4.6. Thiết kế đánh giá bổ sung
- Chương 5. Kết quả và thảo luận
  - 5.1. Kết quả truy xuất nguồn
  - 5.2. Kết quả sinh và kiểm chứng
  - 5.3. Thời gian xử lý và kiểm tra API
  - 5.4. Phân tích trường hợp
  - 5.5. Trả lời câu hỏi nghiên cứu
  - 5.6. Các đe dọa đến tính hợp lệ
- Chương 6. Kết luận và hướng phát triển
  - 6.1. Kết luận
  - 6.2. Những vấn đề chưa giải quyết
  - 6.3. Hướng phát triển
- Tài liệu tham khảo
- Phụ lục A. Danh mục bằng chứng trong dự án
- Phụ lục B. Quy tắc kiểm tra số liệu

## Danh mục từ viết tắt

| Viết tắt | Diễn giải |
|---|---|
| API | Giao diện lập trình ứng dụng |
| CLI | Giao diện dòng lệnh |
| LLM | Mô hình ngôn ngữ lớn |
| RAG | Retrieval-augmented generation; sinh tăng cường truy xuất |
| RRF | Reciprocal rank fusion; hợp nhất thứ hạng nghịch đảo |
| JSON | Định dạng trao đổi dữ liệu có cấu trúc |
| HTTP | Giao thức truyền tải siêu văn bản |

# Chương 1. Tổng quan và vấn đề nghiên cứu

## 1.1. Bối cảnh và lý do chọn đề tài

Một câu hỏi về hồ sơ doanh nghiệp thường cần nhiều hơn một đoạn văn bản. Chẳng hạn, để xác định nhà cung cấp được thanh toán bao nhiêu và ai có thẩm quyền phê duyệt, người đọc có thể phải đối chiếu hợp đồng, phụ lục, hóa đơn và quy định nội bộ. Khó khăn không chỉ là tìm tài liệu có từ khóa giống câu hỏi mà còn là phân biệt số tiền cam kết với số tiền đã chi, kế hoạch với kết quả và quy định cũ với quyết định thay thế.

RAG đưa thông tin từ kho tài liệu vào quá trình sinh câu trả lời. Công trình của Lewis et al. (2020) kết hợp thành phần truy xuất với mô hình sinh để xử lý các nhiệm vụ cần tri thức bên ngoài. Cách tiếp cận này là nền tảng cho việc xây dựng hệ thống hỏi đáp có nguồn tham chiếu. Tuy nhiên, việc đưa tài liệu vào đầu vào chưa tự bảo đảm rằng câu trả lời sử dụng đúng tài liệu đó.

Trong phạm vi dự án này, hai yêu cầu cần được xem xét cùng nhau. Trước hết, hệ thống phải tìm đủ hồ sơ liên quan, kể cả khi một hồ sơ chỉ được nhắc gián tiếp qua mã tham chiếu. Tiếp theo, câu trả lời phải giữ được chủ thể, số liệu, phủ định và điều kiện trong nguồn. Một bản tổng hợp ngắn nhưng gán sai người phê duyệt vẫn không đáp ứng yêu cầu, dù danh sách nguồn kèm theo có chứa tài liệu đúng.

Đề tài vì vậy tập trung vào một nguyên mẫu có khả năng truy vết bằng chứng và phản hồi rõ khi chưa xác nhận được bản tổng hợp. Việc kết hợp PostgreSQL/pgvector với Neo4j/Graphiti được xem là lựa chọn thiết kế cần đánh giá. Hiệu quả của lựa chọn này phải được xác định bằng dữ liệu đo, thay vì suy ra từ tên công nghệ hoặc mức độ phức tạp của kiến trúc.

## 1.2. Mục tiêu nghiên cứu

Mục tiêu tổng quát là xây dựng và đánh giá bước đầu một hệ thống hỏi đáp tài liệu tiếng Việt, trong đó quá trình tìm nguồn, sinh câu trả lời và kiểm chứng có thể được phân biệt và kiểm tra riêng.

Các mục tiêu cụ thể gồm:

1. Lưu giữ tài liệu gốc và tổ chức các đường truy xuất bổ sung, để vẫn có thể tìm kiếm văn bản khi một thành phần lập chỉ mục chưa khả dụng.
2. Kết hợp ứng viên truy xuất và mở rộng tham chiếu trong một ngân sách ngữ cảnh xác định.
3. Ràng buộc mỗi nhận định với trích đoạn nguồn, kiểm tra bản nháp và giới hạn số lần sửa.
4. Đánh giá mức tìm được nguồn, trạng thái trả lời và thời gian xử lý từ các bản ghi có thể kiểm tra; nêu rõ phần chưa đủ dữ liệu để kết luận.

## 1.3. Câu hỏi nghiên cứu

**RQ1.** Trong bộ hồ sơ thử nghiệm, mở rộng tham chiếu tài liệu làm thay đổi mức tìm được các nguồn cần thiết như thế nào so với lấy sáu đoạn đầu từ tìm kiếm từ vựng?

**RQ2.** Với mô hình và cấu hình đã được chạy, quy trình sinh kèm kiểm chứng tạo được bao nhiêu bản tổng hợp vượt qua các điều kiện kiểm tra nội bộ, và xử lý ra sao khi chưa đạt?

**RQ3.** Thời gian xử lý được ghi nhận ở mức nào, và bằng chứng hiện có cho phép nhận định đến đâu về khả năng sử dụng tương tác?

Ba câu hỏi trên có phạm vi phù hợp với dữ liệu hiện có. RQ1 là so sánh mô tả giữa hai cấu hình khác ngân sách. RQ2 là đánh giá hành vi của một cấu hình, chưa phải thí nghiệm tách riêng tác dụng của bộ kiểm chứng. RQ3 không đặt trước một cam kết độ trễ đã đạt.

Các bản ghi được thu thập trước lượt biên tập này, nên cách đặt câu hỏi và phân tích ở đây có tính chất hồi cứu. Luận văn không trình bày chúng như một nghiên cứu đã đăng ký trước giả thuyết. Thiết kế đối chứng cần thực hiện tiếp được nêu ở mục 4.6.

## 1.4. Đối tượng, phạm vi và cách tiếp cận

Đối tượng nghiên cứu là quy trình hỏi đáp trên tài liệu văn bản: lưu trữ, tìm kiếm, lựa chọn bằng chứng, sinh câu trả lời và kiểm chứng. Phạm vi triển khai gồm backend Python, API và giao diện CLI cùng gọi một thành phần xử lý chính. PostgreSQL lưu tài liệu và dữ liệu hội thoại; pgvector hỗ trợ tìm kiếm vector; Graphiti kết nối kho đồ thị Neo4j.

Phạm vi dữ liệu là 22 hồ sơ hư cấu bằng tiếng Việt của Minh An Supply. Bộ câu hỏi gồm 20 ca được xây dựng để kiểm tra thông tin phân tán, thay đổi hồ sơ, điều kiện nghiệp vụ, thiếu bằng chứng và hội thoại tiếp nối. Đây là bộ dữ liệu kiểm tra nguyên mẫu, không đại diện cho toàn bộ doanh nghiệp hoặc mọi dạng câu hỏi tiếng Việt.

Nghiên cứu được trình bày theo hướng thiết kế hệ thống và đánh giá thăm dò. Bằng chứng gồm mã nguồn đang đọc, cấu hình khai báo, tài liệu mô tả dữ liệu và kết quả chạy đã lưu. Những loại bằng chứng này có chức năng khác nhau: mã cho biết hệ thống được thiết kế để làm gì; bản ghi chạy cho biết điều gì đã xảy ra trong một lần chạy cụ thể. Một tính năng mới trong mã không tự động có kết quả thực nghiệm từ bản ghi cũ.

## 1.5. Đóng góp và giới hạn của đóng góp

Đóng góp kỹ thuật của đề tài là tổ chức quy trình trả lời có truy vết: ưu tiên tài liệu gốc, đưa trích đoạn vào hợp đồng sinh, kiểm tra bản sửa và chuyển sang phản hồi bằng chứng khi chưa xác nhận được tổng hợp. Giới hạn một lần sửa giúp kiểm soát số bước xử lý, nhưng không phải bằng chứng về tính đúng của câu trả lời.

Đóng góp thực nghiệm là phân tích riêng kết quả truy xuất và kết quả tổng hợp. Hồ sơ đánh giá cho phép nhận diện một tình huống đáng chú ý: mức tìm được nguồn tăng nhưng bộ sinh vẫn chưa đạt yêu cầu kiểm chứng. Kết quả này hữu ích để lựa chọn bước cải tiến tiếp theo.

Luận văn không tuyên bố phát minh RAG, RRF, đồ thị thời gian hoặc cơ chế tự phản hồi. Các kỹ thuật nền đã có trong nghiên cứu trước. Phần đóng góp ở đây thuộc về cách tích hợp, quy tắc xử lý lỗi và phân tích giới hạn của nguyên mẫu trong một bối cảnh cụ thể.

## 1.6. Cấu trúc luận văn

Chương 2 trình bày cơ sở lý thuyết và vị trí của đề tài so với nghiên cứu liên quan. Chương 3 mô tả phương pháp và hiện thực. Chương 4 xác định dữ liệu, chỉ số và giới hạn của thiết kế đánh giá. Chương 5 phân tích kết quả đã lưu và trả lời các câu hỏi nghiên cứu. Chương 6 tổng kết các kết luận có thể bảo vệ bằng bằng chứng và xác định công việc tiếp theo.

# Chương 2. Cơ sở lý thuyết và nghiên cứu liên quan

## 2.1. Sinh tăng cường truy xuất

Cho câu hỏi $q$ và kho tài liệu $\mathcal{D}$, một quy trình RAG lựa chọn tập ngữ cảnh $\mathcal{C}\subseteq\mathcal{D}$ rồi sinh câu trả lời $y$ dựa trên $q$ và $\mathcal{C}$. Cách viết khái quát là:

$$
\mathcal{C}=R(q,\mathcal{D}),\qquad y=G(q,\mathcal{C}).
$$

Ở đây, $R$ là quy trình truy xuất và $G$ là thành phần sinh. Ký hiệu này mô tả phân công chức năng trong hệ thống của luận văn; không khẳng định đây là hiện thực lại toàn bộ mô hình huấn luyện của Lewis et al. (2020).

Tách hai thành phần cho phép phân tích lỗi rõ hơn. Nếu tài liệu cần thiết không có trong $\mathcal{C}$, sửa cách diễn đạt câu trả lời thường không đủ. Nếu $\mathcal{C}$ đã chứa bằng chứng mà $y$ vẫn nhầm số tiền hoặc vai trò, vấn đề nằm ở việc sử dụng ngữ cảnh. Hai tình huống cần cách khắc phục khác nhau.

Một đoạn có độ tương đồng cao với câu hỏi có thể chưa chứa đủ điều kiện để trả lời. Ví dụ, hợp đồng nêu số tiền nhưng phụ lục mới quyết định mức điều chỉnh. Đây là tình huống có thể xảy ra khi thông tin phân tán, không phải một định lý rằng tìm kiếm vector luôn thất bại với câu hỏi nhiều tài liệu.

## 2.2. Kết hợp truy xuất từ vựng và vector

Tìm kiếm từ vựng dựa vào các từ hoặc mã xuất hiện trong văn bản. Nó phù hợp với những truy vấn có mã hồ sơ như CR-07 hoặc INV-BS-042. Tìm kiếm vector sử dụng biểu diễn nhúng để tìm nội dung gần nghĩa, kể cả khi câu hỏi và tài liệu không dùng cùng cách diễn đạt. Hai đường truy xuất có thể bổ sung cho nhau nhưng cũng có thể cùng trả về nội dung không cần thiết.

Với hai vector khác không $\mathbf{u}$ và $\mathbf{v}$, độ tương đồng cosine được tính bằng:

$$
\operatorname{cos}(\mathbf{u},\mathbf{v})
=\frac{\mathbf{u}^{\mathsf T}\mathbf{v}}
{\|\mathbf{u}\|_2\|\mathbf{v}\|_2}.
$$

Điểm tương đồng này phục vụ xếp hạng. Nó không phải xác suất rằng một tài liệu đủ để trả lời câu hỏi.

RRF hợp nhất nhiều danh sách dựa trên vị trí xếp hạng, thay vì yêu cầu điểm của các bộ tìm kiếm nằm trên cùng một thang đo. Cormack et al. (2009) trình bày phương pháp cộng các giá trị nghịch đảo của thứ hạng đã cộng một hằng số. Luận văn dùng nguyên tắc này trong hiện thực, với cách xử lý tài liệu trùng và các quy tắc bổ sung được mô tả tại mục 3.4. Việc áp dụng RRF chưa tự chứng minh tốt hơn một đường truy xuất riêng lẻ; kết luận đó cần thí nghiệm cùng ngân sách.

## 2.3. Đồ thị tri thức và thông tin thời gian

Edge et al. (2024) xây dựng GraphRAG cho câu hỏi tổng hợp ở phạm vi kho dữ liệu, thông qua đồ thị thực thể và các bản tóm tắt cộng đồng. Công trình này cung cấp một hướng tổ chức thông tin quan hệ cho truy xuất và tổng hợp. Tuy nhiên, nhiệm vụ tổng quan toàn kho khác với việc tìm chính xác hồ sơ cần để trả lời một câu hỏi nghiệp vụ. Do đó, không thể chỉ dựa vào tên GraphRAG để chọn một cấu hình làm đối chứng phù hợp.

Rasmussen et al. (2025) mô tả Zep với Graphiti là thành phần đồ thị nhận biết thời gian, hướng tới lưu trữ và cập nhật tri thức cho tác nhân. Khả năng lưu lịch sử quan hệ tạo cơ sở để phân biệt thông tin ở các thời điểm khác nhau. Dù vậy, hiệu quả của một ứng dụng cụ thể còn phụ thuộc vào cách trích xuất, lưu nhãn thời gian và lọc dữ kiện khi truy xuất.

Cần phân biệt thời điểm một bản ghi được nạp với thời điểm dữ kiện trong bản ghi có hiệu lực. Quyết định được nạp ngày 25/9 có thể quy định hiệu lực từ ngày 1/10. Nếu ứng dụng chỉ biết ngày nạp, nó chưa có đủ thông tin để xác định quyết định đã áp dụng tại ngày 27/9 hay chưa.

Trong hệ thống của luận văn, quan hệ đồ thị được dùng để tìm lại tài liệu gốc qua liên kết episode. Phần đánh giá hiện có chưa kiểm tra riêng độ đúng của việc lọc theo khoảng hiệu lực. Vì vậy, “có tích hợp Graphiti” và “đã xử lý đúng mọi câu hỏi thời gian” là hai mức tuyên bố khác nhau.

## 2.4. Tự phản hồi và kiểm chứng câu trả lời

Self-RAG huấn luyện mô hình sử dụng các dấu hiệu phản hồi để điều khiển truy xuất và đánh giá quá trình sinh (Asai et al., 2023). Corrective RAG bổ sung bước đánh giá chất lượng truy xuất, từ đó lựa chọn hành động xử lý tiếp theo (Yan et al., 2024). Hai công trình cho thấy phản hồi có thể được đặt tại nhiều vị trí trong quy trình, với đầu vào và mục đích khác nhau.

Nguyên mẫu của luận văn đặt bước kiểm chứng sau khi đã có bản nháp. Bộ kiểm chứng nhận câu hỏi, ngữ cảnh và câu trả lời để đánh giá mức được nguồn hỗ trợ và phần thông tin còn thiếu. Bản sửa, nếu có, dùng lại tập ngữ cảnh đã chọn. Đây là sửa câu trả lời có giới hạn, chưa phải cơ chế tự quyết định truy xuất lại.

Thành phần sinh và thành phần kiểm chứng sử dụng cùng hồ sơ mô hình được chọn. Chúng khác vai trò và yêu cầu đầu ra nhưng không độc lập về sai lệch mô hình. Một phản hồi “đạt” từ bộ kiểm chứng chỉ là kết quả của cơ chế kiểm tra nội bộ. Muốn đánh giá chất lượng, vẫn cần đối chiếu với đáp án hoặc người chấm độc lập.

## 2.5. Các khía cạnh đánh giá

RAGAS phân biệt chất lượng truy xuất, mức bám nguồn và chất lượng câu trả lời; đồng thời cung cấp cách tự động hóa một số phép đánh giá (Es et al., 2024). Sự phân biệt này quan trọng vì một hệ thống có thể tìm đúng tài liệu nhưng sinh sai, hoặc sinh một câu đúng nhưng không trả lời đủ yêu cầu.

Luận văn dùng ba nhóm quan sát: nguồn nào được tìm thấy, hệ thống trả lời theo trạng thái nào và mất bao lâu. Chỉ số tìm được mã tài liệu trong nghiên cứu này không được gọi là Context Recall của RAGAS. Tương tự, tỷ lệ nhãn `verified` không được đổi tên thành Faithfulness hay độ chính xác.

Nếu một lần chạy không tạo được đầu ra hợp lệ, trường hợp đó phải được giữ lại trong báo cáo. Thay bằng điểm minh họa sẽ làm mất khả năng phân biệt lỗi vận hành với chất lượng đo được.

## 2.6. Định vị nghiên cứu

**Bảng 1**  
*Quan hệ giữa nghiên cứu liên quan và phạm vi của đề tài*

| Hướng tiếp cận | Vấn đề chính | Liên hệ với đề tài |
|---|---|---|
| RAG (Lewis et al., 2020) | Đưa tri thức truy xuất vào quá trình sinh | Cơ sở phân tách truy xuất và sinh |
| RRF (Cormack et al., 2009) | Hợp nhất nhiều danh sách xếp hạng | Thành phần hợp nhất ứng viên |
| GraphRAG (Edge et al., 2024) | Tổng hợp dựa trên tổ chức đồ thị | Cơ sở tham khảo, chưa có đối chứng thực nghiệm trong dự án |
| Graphiti/Zep (Rasmussen et al., 2025) | Tổ chức tri thức có thông tin thời gian | Hỗ trợ tìm nguồn qua episode; chưa đánh giá riêng suy luận thời gian |
| Self-RAG; Corrective RAG | Phản hồi để điều chỉnh truy xuất hoặc sinh | Cơ sở tham khảo cho bước đánh giá chất lượng |
| RAGAS (Es et al., 2024) | Đánh giá nhiều khía cạnh của RAG | Giúp phân biệt loại chỉ số, chưa cung cấp điểm hợp lệ cho lần đánh giá đang báo cáo |

*Ghi chú.* Bảng tổng hợp mục đích liên quan, không phải bảng xếp hạng hiệu quả. Self-RAG và Corrective RAG tương ứng với Asai et al. (2023) và Yan et al. (2024).

Vấn đề được lựa chọn trong luận văn là tổ chức một quy trình có thể truy vết từ câu trả lời về hồ sơ, đồng thời xử lý minh bạch các trường hợp tổng hợp chưa đạt. Tính phù hợp của thiết kế được xem xét trên bộ tài liệu thử nghiệm đã mô tả. Phạm vi khảo cứu này không đủ để khẳng định chưa từng có hệ thống nào kết hợp các kỹ thuật tương tự.

# Chương 3. Phương pháp nghiên cứu và thiết kế hệ thống

## 3.1. Bài toán và nguyên tắc thiết kế

Đầu vào của hệ thống gồm câu hỏi $q$, mã không gian tài liệu $w$ và lịch sử hội thoại $h$ nếu có. Đầu ra gồm nội dung phản hồi, danh sách nguồn và trạng thái xử lý. Kho tài liệu sử dụng cho một yêu cầu là $\mathcal{D}_w$, được chọn theo `tenant_id`.

Mỗi nguồn cần giữ được định danh tài liệu, tiêu đề và nội dung. Thông tin suy ra từ đồ thị được dùng để tìm tài liệu gốc, thay vì mặc nhiên trở thành căn cứ đúng. Lịch sử hội thoại có thể giúp xác định đại từ trong câu hỏi tiếp nối, nhưng không thay thế tài liệu làm bằng chứng.

Chương này mô tả luồng phục vụ của `AgenticRAG._ainvoke` cùng các thành phần liên quan được đọc ngày 27/9/2026. Các thay đổi mới được phân biệt với phiên bản tạo ra kết quả ở Chương 5. Mã băm của các tệp chính được lưu trong hồ sơ biên tập kèm luận văn; một kết quả chạy cũ không được xem là phép đo của toàn bộ mã hiện tại.

## 3.2. Kiến trúc tổng thể

Hệ thống gồm ba nhóm chức năng: nạp và lưu tài liệu, truy xuất bằng chứng, xử lý câu trả lời. API nhận yêu cầu và gọi backend; CLI cũng sử dụng backend này nhưng có khác biệt về truyền lịch sử và chọn cấu hình mô hình.

**Hình 1**  
*Luồng xử lý chính của phiên bản mã nguồn được rà soát*

~~~mermaid
flowchart TD
    D["Tài liệu"] --> P["Lưu bản gốc trong PostgreSQL"]
    P --> I["Thử lập chỉ mục vector"]
    I --> J["Thử tạo episode Graphiti"]
    J --> N["Neo4j"]
    Q["Câu hỏi, không gian, lịch sử"] --> H["Xác định tham chiếu hội thoại"]
    H --> L["Tìm kiếm từ vựng"]
    H --> V["Tìm kiếm vector"]
    H --> G["Tìm qua Graphiti khi chọn hybrid"]
    L --> R["Hợp nhất và mở rộng nguồn"]
    V --> R
    G --> R
    P -. "Văn bản gốc" .-> R
    N -. "Episode liên quan" .-> G
    R --> E{"Có nguồn phù hợp?"}
    E -->|Không| X["Thông báo thiếu bằng chứng"]
    E -->|Có| A["Sinh nhận định và trích đoạn"]
    A --> C["Kiểm tra cấu trúc và kiểm chứng"]
    C -->|Đạt| O["Trả bản tổng hợp"]
    C -->|Chưa đạt, còn lượt sửa| B["Sửa một lần với cùng ngữ cảnh"]
    B --> C2["Kiểm chứng lại"]
    C -->|Lỗi hoặc hết khả năng sửa| F["Xử lý phản hồi chưa kiểm chứng"]
    C2 -->|Đạt| O
    C2 -->|Chưa đạt| F
~~~

*Ghi chú.* Ở phiên bản đánh giá cũ, nhánh chưa đạt trả trích đoạn nguồn. Mã hiện tại còn có trạng thái `unverified_draft`, được giải thích tại mục 3.5. Sơ đồ mô tả luồng ứng dụng, không biểu diễn một đồ thị LangGraph đã biên dịch.

PostgreSQL và Neo4j là hai kho có vai trò khác nhau. PostgreSQL giữ bản gốc dùng để đối chiếu. Neo4j/Graphiti cung cấp liên kết để bổ sung nguồn. Vì vậy, luận văn dùng thuật ngữ “lưu trữ kết hợp”, tránh diễn giải hai kho như một cơ chế giao dịch phân tán có bảo đảm nhất quán nguyên tử.

## 3.3. Lưu tài liệu và lập chỉ mục

Trong `backend/app/ingestion/database_sync.py`, `ingest_document` ghi tài liệu gốc vào PostgreSQL trước khi lập chỉ mục. Hàm `index_document` thử tạo embedding và lưu các đoạn, sau đó thử thêm episode vào Graphiti. Hai khối xử lý bắt lỗi riêng. Trạng thái vector và trạng thái đồ thị được ghi vào metadata.

Lựa chọn lưu bản gốc trước cho phép tìm kiếm từ vựng khi việc tạo embedding thất bại. Nếu Graphiti chưa khả dụng, dữ liệu đã lưu trong PostgreSQL không bị xóa để hoàn tác toàn bộ quy trình. Tuy nhiên, điều này chỉ giúp ứng dụng có một đường xử lý dự phòng. Nó không bảo đảm tính sẵn sàng nếu PostgreSQL lỗi, dữ liệu chưa được lưu hoặc ứng dụng không nhận được yêu cầu.

`DocumentChunker` chia văn bản bằng cửa sổ cố định 900 ký tự, chồng lấn 100 ký tự. Bước dịch là 800 ký tự. Cách chia này đơn giản, dễ kiểm tra, nhưng có thể cắt ngang câu, bảng hoặc điều kiện nằm cuối đoạn. Hiện thực không phải bộ chia đệ quy theo cấu trúc văn bản.

Bộ tạo embedding được khai báo qua cấu hình. Mã hiện tại yêu cầu mỗi vector có 3.072 chiều; cấu hình mặc định là `gemini-embedding-2`. Đây là mô tả cấu hình mã nguồn, không phải xác nhận mô hình nhúng đã được ghi lại đầy đủ cho mọi lần chạy lịch sử. Chưa có căn cứ từ ORM để khẳng định đang sử dụng HNSW hoặc IVFFlat trong cơ sở dữ liệu thực tế.

API có thể lập chỉ mục nền sau khi lưu tài liệu. Ngược lại, CLI có bước khởi tạo Graphiti trước quy trình nạp. Sự khác nhau này cần được kiểm thử riêng khi đánh giá khả năng tiếp tục hoạt động lúc đồ thị không khả dụng.

## 3.4. Truy xuất và mở rộng bằng chứng

### 3.4.1. Chọn không gian và chuẩn bị câu hỏi

Luồng API hỗ trợ `documents` và `hybrid`. Cả hai thực hiện tìm kiếm từ vựng và vector; chế độ `hybrid` bổ sung Graphiti. Đây là chế độ do yêu cầu lựa chọn, không phải kết quả của một lần phân loại ý định bằng LLM trong luồng `_ainvoke`.

Khi phát hiện một số cách hỏi tiếp nối, chẳng hạn “người đó” hoặc “dự án đó”, hàm `retrieval_query` bổ sung thông tin từ hội thoại trước để xác định đối tượng. Đây là một quy tắc nhận dạng mẫu, chưa phải bộ giải quyết đồng tham chiếu tổng quát. Việc diễn giải sai lượt trước có thể ảnh hưởng truy vấn tiếp theo.

Lọc theo không gian giới hạn tài liệu được sử dụng. Cơ chế này chưa đủ để kết luận hệ thống đã có đầy đủ xác thực hoặc phân quyền người dùng.

### 3.4.2. Tìm kiếm và hợp nhất thứ hạng

Tìm kiếm từ vựng chuẩn hóa chữ thường, dấu tiếng Việt và một danh sách từ dừng, sau đó chấm điểm theo công thức dạng BM25. Hàm hiện tại đọc tài liệu của không gian và tính thống kê từ vựng theo yêu cầu. Với bộ nhỏ, cách này dễ kiểm tra. Khi dữ liệu tăng, chi phí đọc và tính lại là một hạn chế cần đo.

Tìm kiếm vector sắp xếp theo khoảng cách cosine, lấy tối đa 12 ứng viên và giữ các kết quả có khoảng cách nhỏ hơn 0,65. Tìm kiếm từ vựng cũng lấy tối đa 12 ứng viên. Ngưỡng khoảng cách là tham số hiện thực, chưa có thí nghiệm trong hồ sơ chứng minh đó là ngưỡng tối ưu.

Trong `fuse_sources`, các ứng viên được hợp nhất theo `document_id`. Một tài liệu chỉ đóng góp một lần trong mỗi danh sách. Với $r_j(d)$ là thứ hạng lần xuất hiện đầu của tài liệu $d$ trong danh sách $j$, điểm cơ sở là:

$$
s_{\mathrm{RRF}}(d)=\sum_{j:d\in L_j}\frac{1}{60+r_j(d)}.
$$

Mã được đọc ở cuối lượt rà soát còn nhân điểm với 1,3 nếu tài liệu có dấu hiệu sửa đổi hoặc ngày được trích xuất từ ngày 1/9/2026 trở đi:

$$
s(d)=b(d)\,s_{\mathrm{RRF}}(d),\qquad b(d)\in\{1;\,1,3\}.
$$

Ngày được lấy từ tiêu đề và phần đầu nội dung; nếu thiếu năm, mã mặc định dùng 2026. Đây là quy tắc ưu tiên gắn với bộ minh họa, chưa phải mô hình hiệu lực thời gian. Các kết quả truy xuất đã lưu trong Chương 5 không đánh giá riêng hệ số 1,3 hoặc ngưỡng ngày này.

### 3.4.3. Mở rộng tham chiếu

Hệ thống chọn nguồn hạt giống rồi mở rộng các liên kết mã hồ sơ theo hai chiều: tài liệu đang đọc nhắc đến hồ sơ khác, hoặc hồ sơ khác nhắc đến tài liệu đang đọc. Số bước tối đa là hai, số tài liệu tối đa là 12 và ngân sách nội dung khoảng 24.000 ký tự. Giới hạn ký tự không phải giới hạn token và chưa bao gồm toàn bộ phần chỉ dẫn của prompt.

Phiên bản hiện tại còn bổ sung neo ban đầu dựa trên tên riêng và một danh sách thực thể khai báo sẵn. Phần mở rộng qua hai bước dựa trên mã tham chiếu. Các quy tắc như vậy có thể hữu ích cho hồ sơ có mã rõ ràng nhưng cần đánh giá lại trên dữ liệu khác. Không nên mô tả chúng như khả năng suy luận đồ thị tổng quát.

Ở chế độ có đồ thị, các episode được đối chiếu với tài liệu cùng không gian. Quan hệ tìm thấy giúp chọn tài liệu gốc; prompt sinh nhận nội dung tài liệu với nhãn nguồn `[n]`. Lớp này không đưa một khối `<FACTS>` được bảo đảm đúng về thời gian vào quá trình sinh.

## 3.5. Sinh, kiểm chứng và sửa câu trả lời

Bộ sinh được yêu cầu trả JSON gồm danh sách `claims`. Mỗi phần tử chứa `quote`, `source_id` và `text`, lần lượt là trích đoạn, mã nguồn và nhận định. Danh sách `missing_information` ghi phần câu hỏi chưa có dữ liệu.

Backend kiểm tra định dạng, phạm vi mã nguồn và một số ràng buộc ngôn ngữ. Ví dụ, điều kiện “không quá 60 giây” không nên bị đổi thành “dưới 60 giây”, vì hai khoảng giá trị khác nhau tại đúng 60 giây. Các quy tắc về người và hành động cũng nhằm hạn chế đổi vai trò chủ thể. Chúng là kiểm tra theo mẫu, không phải chứng minh hình thức cho mọi câu tiếng Việt.

Bộ kiểm chứng tiếp tục đánh giá các nhận định và mức đầy đủ của câu trả lời. Nếu chưa đạt, luồng chính cho phép một lần sửa bằng cùng tập bằng chứng, rồi kiểm chứng bản sửa. Luồng này không quay lại tìm tài liệu mới.

Cần phân biệt hai hợp đồng phản hồi:

- **Phiên bản được mô tả trong hồ sơ đánh giá cũ:** khi chưa xác nhận được bản tổng hợp, phản hồi chuyển sang trích đoạn nguồn. Các bản ghi 20 ca ở Chương 5 thuộc phiên bản này.
- **Phiên bản mã hiện tại:** `is_quote_supported` chấp nhận nhiều mức đối sánh, bao gồm tỷ lệ từ của quote có trong nguồn đạt ít nhất 75% trong điều kiện được mã quy định. Nhánh chưa đạt có thể giữ một bản nháp dài hơn 20 ký tự và gắn trạng thái `unverified_draft` cùng chú thích chưa kiểm chứng đầy đủ. Khi không có bản nháp phù hợp hoặc bước sinh lỗi, hệ thống dùng trích đoạn nguồn.

Đối sánh từ không bảo đảm giữ nguyên thứ tự, phủ định hay quan hệ giữa các thực thể. Vì vậy, không thể mô tả phiên bản hiện tại là bắt buộc mọi quote phải khớp nguyên văn, dù prompt vẫn yêu cầu như vậy. Tương tự, bản nháp có chú thích chưa kiểm chứng không được tính như câu trả lời đã đạt.

Sinh và kiểm chứng cùng dùng hồ sơ mô hình được chọn. Sự phân vai hỗ trợ tổ chức quy trình, nhưng chưa tạo ra hai người đánh giá độc lập. Nhãn `verified` chỉ có nghĩa là đã qua các điều kiện của hệ thống tại phiên bản đó.

## 3.6. Giới hạn thực thi và xử lý lỗi

Luồng `_ainvoke` có tối đa hai lần kiểm chứng và một lần sửa. Nếu tính riêng các lời gọi ở tầng sinh và kiểm chứng, số lời gọi tối đa là:

$$
N_{\mathrm{LLM}}\leq 1_{\mathrm{sinh}}+1_{\mathrm{kiểm\ chứng}}
+1_{\mathrm{sửa}}+1_{\mathrm{kiểm\ chứng\ lại}}=4.
$$

Giới hạn này không bao gồm embedding, truy vấn Graphiti hoặc các lời gọi khi lập chỉ mục. Nó giới hạn số bước của luồng, không chứng minh câu trả lời hội tụ đến đáp án đúng.

Thời gian toàn trình gồm thời gian tìm kiếm, chuẩn bị ngữ cảnh, suy luận, truyền thông và xử lý lỗi. Không thể lấy thời gian trung bình của một lời gọi rồi nhân số lời gọi để suy ra phân vị $P_{95}$. Độ trễ phải được đo trên các yêu cầu có cấu hình và điều kiện vận hành xác định.

API hiện có hạn tổng theo loại hồ sơ mô hình, trong khi CLI không có cùng lớp hạn tổng. Một timeout ở coroutine cũng không mặc nhiên chứng minh mọi công việc nền đã dừng. Do đó, đánh giá giới hạn tài nguyên cần đo thêm bộ nhớ, yêu cầu còn chạy và tác động khi nhiều người dùng đồng thời.

## 3.7. Phạm vi hỗ trợ thời gian và khác biệt giao diện

Mã hiện tại ưu tiên văn bản được nhận diện là sửa đổi và chứa chỉ dẫn về văn bản mới hơn. Tuy nhiên, ngày mới hơn không luôn đồng nghĩa với thay thế pháp lý hoặc nghiệp vụ. Cần biết phạm vi điều chỉnh, thời điểm hiệu lực và điều kiện áp dụng. Hiện chưa có phép đo độc lập cho những trường hợp này.

Một số ví dụ trong prompt và danh sách thực thể lấy trực tiếp từ bộ Minh An. Điều đó làm tăng mức chuyên biệt của nguyên mẫu. Nếu tiếp tục dùng cùng bộ câu hỏi để điều chỉnh rồi báo cáo kết quả cuối, không thể coi bộ đó là tập kiểm tra độc lập.

Trong mã có các lớp và hàm tương thích mang tên `AgentState`, `CriticAgent` và các nút định tuyến. Tuy nhiên, đối tượng được gọi là `agentic_rag_app = AgenticRAG()`. Sự hiện diện của các tên này chưa chứng minh luồng đang chạy là một `StateGraph` được biên dịch hoặc đã dùng định tuyến LLM ba nhánh.

API truyền lịch sử hội thoại và hỗ trợ chọn hồ sơ mô hình; CLI hiện gọi chung backend nhưng không truyền lịch sử tương đương. Vì thế, kết quả hội thoại của API không được dùng làm bằng chứng rằng CLI đã đạt cùng hành vi. Những khác biệt này được giữ trong phạm vi hạn chế của hiện thực.

# Chương 4. Dữ liệu và phương pháp đánh giá

## 4.1. Nguồn bằng chứng và phiên bản thực nghiệm

Phần thực nghiệm sử dụng các bản ghi đã có trong dự án, không phải một lượt chạy mới được tạo trong quá trình biên tập. Dữ liệu được đọc lại để tính các thống kê mô tả và kiểm tra tính nhất quán. Luận văn phân biệt ba mốc ở Bảng 2.

**Bảng 2**  
*Phân biệt các mốc mã nguồn và kết quả*

| Mốc | Bằng chứng | Phạm vi sử dụng |
|---|---|---|
| A: lượt đánh giá ứng viên | `after.json`, `retrieval.json`, `summary.json` | Báo cáo 20 ca; phân tích truy xuất trên T01–T18 |
| B: kiểm tra API sau một số chỉnh sửa | `final-api-check.json` | Xem riêng T03, T06 và T19; không gộp với A |
| C: mã đọc ngày 27/9/2026 | `router.py`, `critic.py`, `tools.py` và mã băm kèm theo | Mô tả hiện thực, gồm các thay đổi chưa được A hoặc B đánh giá |

*Ghi chú.* Các tệp JSON trong bảng nằm tại `artifacts/rag-upgrade/`. “Sau chỉnh sửa” chỉ diễn tả quan hệ phiên bản được ghi trong hồ sơ, không có nghĩa mốc B là phiên bản cuối của toàn dự án.

`summary.json` ghi rõ lượt A diễn ra trước các thay đổi về timeout, chặn bỏ qua hợp đồng quote, trình bày phản hồi dự phòng và từ chối thực thể ngoài dữ liệu. Trong quá trình rà soát, mã nguồn còn thay đổi tiếp sang mốc C. Vì vậy, phân tích cần giữ nguyên phạm vi của từng mốc.

Bản cấu hình khai báo PostgreSQL 16 qua ảnh `pgvector/pgvector:pg16`, Neo4j 5 và Redis 7. Chưa có căn cứ rằng Redis tham gia đường xử lý câu hỏi hiện tại. Lượt A sử dụng Ollama với qwen2.5:3b theo báo cáo thực nghiệm của dự án. Tài liệu lưu chưa đủ để xác nhận đầy đủ CPU, RAM, phiên bản runtime, mã định danh trọng số và mọi tham số vận hành tại thời điểm chạy. Luận văn không điền những thông tin này bằng cấu hình dự kiến.

## 4.2. Bộ dữ liệu Minh An

Theo `data/demo-doanh-nghiep/minh-an/README.md`, bộ dữ liệu gồm 22 tài liệu hư cấu, chốt thông tin ngày 25/9/2026. Nội dung mô phỏng tổ chức, nhân sự, dự án, nhà cung cấp, hợp đồng, hóa đơn, sự cố và quyết định điều chỉnh. Không được diễn giải các số tiền, tên người hoặc hoạt động trong bộ này như dữ liệu doanh nghiệp thật.

Các tệp thuộc `documents/` là tài liệu nguồn để nạp RAG. Câu hỏi, đáp án và mã nguồn đối chiếu nằm trong `evaluation/cases.json`. Theo quy trình dữ liệu, thư mục đánh giá cùng README và manifest không được nạp như tài liệu trả lời, nhằm tránh đưa đáp án vào kho truy xuất. Quy định này là thiết kế chống rò rỉ, không thay thế kiểm toán độc lập toàn bộ quá trình nạp.

Bộ kiểm tra có 20 ca, ký hiệu T01–T20. T01–T18 được dùng cho thống kê tìm nguồn ở cấp câu hỏi độc lập. T19 kiểm tra phản hồi với nội dung ngoài không gian tài liệu. T20 là hội thoại tiếp nối, nên không được xem như một truy vấn độc lập cùng điều kiện với 18 câu đầu.

Bộ dữ liệu cung cấp đáp án và danh sách nguồn để đối chiếu. Chưa có nhật ký gán nhãn của hai chuyên gia hoặc phép tính độ đồng thuận giữa người chấm. Vì vậy, danh sách này được gọi là “nguồn đối chiếu của bộ kiểm tra”, không phải chuẩn vàng đã được chuyên gia độc lập xác nhận.

README cũng ghi nhận một phần đầu vào Graphiti sử dụng các bản tóm tắt quan hệ chọn lọc trong `graph_inputs.json`. Chúng không được nạp làm văn bản trả lời, nhưng cách chuẩn bị này có thể ảnh hưởng chất lượng đồ thị. Kết quả từ bộ demo không đủ để suy ra chất lượng trích xuất Graphiti trực tiếp từ toàn văn.

## 4.3. Các cấu hình được so sánh

Phép so sánh truy xuất đã lưu gồm:

- **Cấu hình cơ sở:** lấy sáu đoạn đầu từ kết quả tìm kiếm từ vựng.
- **Cấu hình mở rộng:** dùng kết quả từ vựng làm đầu vào hợp nhất, sau đó mở rộng tham chiếu để lấy tối đa 12 tài liệu.

Trong đoạn đo này của `artifacts/rag-upgrade/evaluate.py`, danh sách vector và danh sách facts đồ thị được truyền rỗng. Do đó, phép đo không tách được hiệu quả của vector, Neo4j hay Graphiti. Đơn vị đầu ra còn khác nhau: một phía là đoạn văn, phía kia là tài liệu. Chênh lệch mức tìm được nguồn có thể đến từ cả cơ chế mở rộng lẫn ngân sách lớn hơn.

Phần đánh giá đầu cuối gọi `AgenticRAG` ở chế độ `documents` với 20 ca. Nó quan sát hành vi của hệ thống kết hợp tìm kiếm tài liệu và kiểm chứng, nhưng không phải so sánh với bốn hệ thống đối chứng độc lập. Trong hồ sơ được dùng cho luận văn, chưa có một thực nghiệm cùng điều kiện cho Static GraphRAG, Graph-only hoặc Hybrid không kiểm chứng.

## 4.4. Định nghĩa chỉ số

### 4.4.1. Tỷ lệ tìm được nguồn đối chiếu

Với câu hỏi $i$, gọi $G_i$ là tập mã tài liệu đối chiếu và $\widehat{G}_i$ là các mã được xác định từ tiêu đề nguồn truy xuất. Chỉ số dùng trong phân tích là:

$$
R_i=\frac{|G_i\cap\widehat{G}_i|}{|G_i|},
\qquad
\overline{R}=\frac{1}{n}\sum_{i=1}^{n}R_i.
$$

Đây là trung bình theo câu hỏi, không phải tỷ lệ gộp tất cả tài liệu của mọi câu. Script lưu kết quả bằng cách kiểm tra mã đối chiếu có xuất hiện trong tiêu đề nguồn hay không. Cách đo phụ thuộc vào quy ước đặt tiêu đề và chưa kiểm tra trực tiếp đoạn nguồn có chứa đúng dữ kiện cần dùng.

Một chỉ số bổ sung là số câu tìm đủ toàn bộ mã đối chiếu:

$$
N_{\mathrm{đủ}}=\sum_{i=1}^{n}\mathbb{I}(R_i=1).
$$

Hai chỉ số không phạt việc lấy thêm nhiều tài liệu không liên quan. Vì vậy, chúng phải được đọc cùng ngân sách truy xuất; không thay thế độ chính xác nguồn hoặc chất lượng câu trả lời.

### 4.4.2. Trạng thái trả lời

Phân tích lượt A phân loại phản hồi theo ba trạng thái `verified`, `extractive` và `no_evidence`. Trạng thái thứ nhất cho biết bản tổng hợp đã qua kiểm tra nội bộ. Trạng thái thứ hai cho biết hệ thống trả bằng chứng gốc. Trạng thái thứ ba cho biết chưa tìm được nguồn phù hợp.

Tỷ lệ `verified` phản ánh khả năng hoàn thành hợp đồng của hệ thống trong lần chạy. Nó không phải tỷ lệ trả lời đúng được đánh giá độc lập. Một phản hồi `extractive` có thể chứa thông tin hữu ích nhưng vẫn chưa hoàn thành nhiệm vụ tổng hợp. Trạng thái `unverified_draft` ở mã hiện tại là một loại riêng và chưa có số liệu trong lượt A.

### 4.4.3. Thời gian xử lý

Thời gian được lấy từ trường `seconds` trong từng bản ghi. Luận văn báo cáo trung vị và giá trị lớn nhất của lượt A, đồng thời trình bày từng phép kiểm tra API ở mốc B.

Đối với T20, script tính thời gian từ trước lượt hỏi mở đầu và bao gồm cả lượt hỏi tiếp nối. Vì vậy, trung vị của 20 ca mô tả thời gian hoàn thành ca kiểm tra; không hoàn toàn tương đương độ trễ của một yêu cầu đơn lẻ. Không dùng giá trị lớn nhất thay cho $P_{95}$.

Hồ sơ hiện có không lưu đầy đủ token đầu vào/đầu ra cho từng ca và mọi lời gọi liên quan. Luận văn vì thế không báo cáo chi phí token trung bình hoặc chi phí tiền tệ.

## 4.5. Quy trình phân tích và khả năng tái lập

Các thống kê trong Chương 5 được tính lại bằng cách đọc JSON, không gọi LLM hoặc truy cập cơ sở dữ liệu. Quy trình gồm đếm số bản ghi, lọc đúng tập câu hỏi, tính trung bình theo câu, đếm trạng thái và đối chiếu thời gian. Mã kiểm tra nằm ở Phụ lục B.

Bảng `tests/evaluation_results.md` không được dùng làm bằng chứng chất lượng. Script `tests/run_evaluation.py` chỉ định nghĩa ba câu hỏi và có nhánh gán sẵn điểm khi không đánh giá được. Bảng kết quả khớp các điểm gán sẵn, nhưng không lưu nguồn đo trực tiếp hay mô phỏng của từng giá trị. Vì vậy, chưa thể xác minh đó là một phép chấm RAGAS trên đầu ra thật.

Việc tính lại thống kê từ JSON xác nhận sự nhất quán của số liệu được lưu, không xác nhận độc lập quá trình tạo ra từng bản ghi. Để tái chạy đầy đủ, cần đóng băng mã, dữ liệu, prompt, mô hình và phụ thuộc; đồng thời ghi cấu hình máy, điều kiện tải và trạng thái dịch vụ. Cây làm việc hiện tại có thay đổi chưa được gắn thành một phiên bản thực nghiệm duy nhất, nên chỉ một mã commit chưa đủ mô tả toàn bộ môi trường.

## 4.6. Thiết kế đánh giá bổ sung

Một nghiên cứu tiếp theo nên giữ cùng dữ liệu nguồn, mô hình sinh, giới hạn ngữ cảnh và quy trình chấm khi so sánh các thành phần. Có thể thiết kế các cấu hình lần lượt sử dụng từ vựng, vector, hợp nhất hai nguồn, mở rộng tham chiếu và bổ sung đồ thị. Muốn đo tác dụng của kiểm chứng, cần so sánh có và không có bước này trên cùng tập nguồn truy xuất.

Việc bổ sung kiểm chứng làm tăng số lời gọi. Do đó, ngoài chất lượng câu trả lời, cần báo cáo độ trễ và chi phí thực tế. Không nên tắt mọi giới hạn vòng lặp để tạo một đối chứng không kiểm soát; có thể so sánh các mức số lần sửa hữu hạn đã xác định trước.

Tập dùng để điều chỉnh quy tắc cần tách khỏi tập kiểm tra cuối. Các mã tài liệu, tên tổ chức và ví dụ trong prompt phải được rà soát để tránh thiết kế quá sát đáp án. Cần thêm tài liệu có tên và cấu trúc khác, câu hỏi diễn đạt lại, trường hợp phủ định, dữ kiện mâu thuẫn và câu thiếu bằng chứng.

Khi có điểm chất lượng theo từng câu từ một quy trình chấm độc lập, có thể phân tích chênh lệch ghép cặp, khoảng tin cậy và kích thước ảnh hưởng. Phương pháp thống kê phải phù hợp phân bố, cấu trúc phụ thuộc giữa câu hỏi và số phép so sánh. Không suy ra kiểm định $t$, giá trị $p$ hay hệ số đồng thuận chỉ từ một bảng điểm trung bình. Đây là kế hoạch cần thực hiện, chưa phải kết quả của luận văn.

# Chương 5. Kết quả và thảo luận

## 5.1. Kết quả truy xuất nguồn

Tính lại các bản ghi T01–T18 trong `retrieval.json` cho kết quả ở Bảng 3.

**Bảng 3**  
*Kết quả tìm nguồn đối chiếu trên 18 câu hỏi độc lập*

| Chỉ số | Sáu đoạn từ vựng | Mở rộng tham chiếu, tối đa 12 tài liệu |
|---|---:|---:|
| Số câu được phân tích | 18 | 18 |
| Tỷ lệ mã nguồn tìm được trung bình | 0,7500 | 0,9676 |
| Số câu tìm đủ toàn bộ mã đối chiếu | 8/18 | 16/18 |
| Tỷ lệ câu tìm đủ toàn bộ mã đối chiếu | 44,44% | 88,89% |

*Ghi chú.* Nguồn: `artifacts/rag-upgrade/retrieval.json`; cách tính được trình bày ở mục 4.4. Chỉ số dùng mã tài liệu trong tiêu đề, không phải Context Recall của RAGAS. Hai cấu hình khác ngân sách và đơn vị nguồn.

Chênh lệch trung bình là 0,2176, tương ứng khoảng 21,76 điểm phần trăm. Kết quả cho thấy cấu hình mở rộng tìm được nhiều mã nguồn đối chiếu hơn trong bộ này. Tuy nhiên, một phần cải thiện có thể do số nguồn tối đa tăng và việc lấy lại tài liệu thay cho đoạn ngắn. Chưa thể quy toàn bộ chênh lệch cho thuật toán mở rộng.

Hai trường hợp chưa tìm đủ nguồn là T15 và T17. T15 tìm được 2/3 mã đối chiếu, còn thiếu INV-BS-041. T17 tìm được 3/4 mã, còn thiếu FIN-POL-01. Chỉ một tài liệu bị thiếu vẫn có thể làm câu trả lời không đủ căn cứ nếu tài liệu đó chứa số tiền đã thanh toán hoặc điều kiện phê duyệt. Vì vậy, điểm trung bình cao cần được đọc cùng phân tích từng câu.

## 5.2. Kết quả sinh và kiểm chứng

**Bảng 4**  
*Trạng thái phản hồi của lượt đánh giá ứng viên với qwen2.5:3b*

| Trạng thái | Số ca | Tỷ lệ |
|---|---:|---:|
| `verified`: tổng hợp đạt kiểm tra nội bộ | 0 | 0% |
| `extractive`: trả trích đoạn nguồn | 20 | 100% |
| `no_evidence`: không có nguồn phù hợp | 0 | 0% |
| Tổng | 20 | 100% |

*Ghi chú.* Nguồn: `artifacts/rag-upgrade/after.json`, đối chiếu `summary.json`. Đây là mốc A, trước các chỉnh sửa được nêu ở mục 4.1. Trạng thái `unverified_draft` của mã mới không thuộc mẫu này.

Lượt chạy chưa đạt mục tiêu tạo bản tổng hợp vượt qua kiểm chứng. Không được xem việc trả 20 phản hồi bằng chứng là 20 câu trả lời tổng hợp đúng. Kết quả cũng không có nghĩa mọi bản nháp đều sai về nội dung: một bản nháp có thể bị loại vì không tuân thủ cấu trúc, không cung cấp đủ chứng cứ hoặc vì bộ kiểm chứng chưa trả kết quả hợp lệ.

Bảng 4 kết hợp với Bảng 3 cho thấy việc tìm được nguồn và việc tạo bản tổng hợp đạt yêu cầu là hai điểm cần cải tiến riêng. Tuy nhiên, hai phép đo không hoàn toàn đồng nhất: phép đo nguồn chỉ dùng nhánh từ vựng và mở rộng; lượt đầu cuối còn có đường vector và xử lý mô hình. Vì vậy, không dùng hai bảng để suy ra quan hệ nhân quả chính xác giữa độ phủ nguồn và chất lượng sinh.

Chưa có chấm độc lập từng bản nháp để phân biệt lỗi nội dung với lỗi hợp đồng. Kết luận phù hợp nhất là cấu hình được chạy chưa hoàn thành yêu cầu tổng hợp theo cơ chế kiểm tra tại thời điểm đó. Cần giữ kết quả không đạt này trong báo cáo để tránh đánh giá quá mức nguyên mẫu.

## 5.3. Thời gian xử lý và kiểm tra API

Lượt A có trung vị thời gian hoàn thành ca kiểm tra là **27,51 giây**, giá trị lớn nhất là **111,00 giây**. Đây là thống kê tính từ 20 giá trị `seconds` trong `after.json`. Riêng T20 gồm hai lượt hỏi như đã nêu ở mục 4.4.3. Các số liệu không hỗ trợ tuyên bố độ trễ $P_{95}$ chỉ khoảng 5–6 giây.

Ba kiểm tra API tại mốc B được trình bày riêng.

**Bảng 5**  
*Kết quả ba ca kiểm tra API được lưu sau lượt đánh giá ứng viên*

| Ca | Mã HTTP | Thời gian (giây) | Số nguồn trả về | Nội dung quan sát |
|---|---:|---:|---:|---|
| T03 | 200 | 23,31 | 12 | Trả bằng chứng gốc; chưa phải tổng hợp đạt kiểm chứng |
| T06 | 200 | 79,00 | 12 | Trả bằng chứng gốc; chưa phải tổng hợp đạt kiểm chứng |
| T19 | 200 | 1,47 | 0 | Thông báo không tìm thấy thông tin phù hợp trong không gian |

*Ghi chú.* Nguồn: `artifacts/rag-upgrade/final-api-check.json`. Mã HTTP 200 biểu thị yêu cầu được xử lý ở tầng giao thức, không xác nhận độ đúng của câu trả lời. Không gộp ba ca này vào mẫu 20 ca ở Bảng 4.

T19 ở mốc A còn nhận phản hồi trích đoạn, trong khi mốc B không trả nguồn và thông báo thiếu dữ liệu. Khác biệt này phù hợp với việc có thay đổi quy tắc từ chối giữa các phiên bản. Một ca kiểm tra thành công chưa chứng minh khả năng từ chối tổng quát hoặc cách ly dữ liệu trong mọi tình huống.

Các lần chạy đơn lẻ chưa mô tả được phân bố độ trễ khi nhiều người dùng đồng thời, ảnh hưởng của khởi động mô hình hoặc mức dao động giữa các lần lặp. Hiệu năng hiện tại cần được xem là bằng chứng thăm dò, chưa phải cam kết vận hành.

## 5.4. Phân tích trường hợp

### 5.4.1. T03: Tập hợp nguồn về nhà cung cấp và khoản điều chỉnh

Theo danh sách đối chiếu, T03 cần các nguồn về nhà cung cấp và điều chỉnh liên quan. Bản ghi truy xuất cho thấy cấu hình mở rộng tìm đủ các mã yêu cầu. Tuy nhiên, kiểm tra API ở mốc B vẫn trả bằng chứng gốc thay vì một bản tổng hợp đạt kiểm chứng.

Trường hợp này cho thấy danh sách nguồn đầy đủ chưa giải quyết xong nhiệm vụ. Bộ sinh còn phải xác định đúng phần tiền nào thuộc hợp đồng gốc, phần nào được bổ sung và ai thực hiện vai trò tương ứng. Không thể gán nguyên nhân thất bại chỉ cho truy xuất.

### 5.4.2. T06: Giữ đủ người và điều kiện

T06 kiểm tra thông tin phân tán về trách nhiệm và điều kiện nghiệp vụ. Hồ sơ nâng cấp ghi nhận bản trả lời cũ bỏ sót Vũ Anh. Ở phép đo nguồn sau mở rộng, các mã tài liệu đối chiếu được tìm đủ, nhưng phản hồi API vẫn sử dụng đoạn nguồn.

Một đánh giá hữu ích ở cấp nhận định cần kiểm tra cả danh sách người và quan hệ giữa người với hành động. Đếm số tên xuất hiện trong câu trả lời chưa đủ: “người đề nghị” và “người phê duyệt” có thể cùng nằm trong một tài liệu nhưng không được hoán đổi.

### 5.4.3. T19: Không trả dữ liệu ngoài không gian

T19 đặt câu hỏi về FPT và GPU trong không gian `minh_an_demo`. Bản ghi mốc B trả danh sách nguồn rỗng và thông báo thiếu thông tin, thay vì đưa số liệu từ tài liệu khác vào câu trả lời.

Quan sát này hỗ trợ kết luận hẹp rằng ca kiểm tra đã có hành vi từ chối phù hợp tại mốc B. Muốn đánh giá rộng hơn, cần thêm nhiều thực thể ngoài kho, cách diễn đạt không chứa tên viết tắt và các tình huống có từ khóa trùng nhưng khác chủ thể.

### 5.4.4. T15 và T17: Vì sao cần xem từng nguồn bị thiếu

T15 thiếu một hồ sơ hóa đơn; T17 thiếu quy định phê duyệt. Cả hai minh họa hạn chế của việc chỉ nhìn điểm trung bình. Hồ sơ bị thiếu có thể chứa điều kiện quyết định câu trả lời, dù số lượng tài liệu đã tìm được khá lớn.

Cần kiểm tra các nguồn thiếu do không được xếp hạng đủ cao, không có liên kết tham chiếu phù hợp hay bị giới hạn ngân sách. Dữ liệu tổng hợp hiện có chưa phân loại nguyên nhân đầy đủ, nên luận văn không chọn một nguyên nhân duy nhất để giải thích.

## 5.5. Trả lời câu hỏi nghiên cứu

**RQ1:** Trong 18 câu hỏi độc lập, cấu hình mở rộng nâng tỷ lệ mã nguồn tìm được trung bình từ 0,7500 lên 0,9676 và số câu đủ nguồn từ 8 lên 16. Đây là cải thiện quan sát được trong điều kiện đã chạy. Do khác ngân sách, chưa xác định được hiệu quả riêng của mở rộng tham chiếu, RRF, vector hoặc đồ thị.

**RQ2:** Với lượt đánh giá qwen2.5:3b, không bản tổng hợp nào trong 20 ca vượt qua kiểm tra nội bộ; toàn bộ chuyển sang trích đoạn nguồn. Kết quả chứng minh hành vi dự phòng đã xuất hiện trong lượt chạy, nhưng chưa chứng minh rằng kiểm chứng làm tăng độ đúng so với không kiểm chứng.

**RQ3:** Trung vị thời gian ca kiểm tra là 27,51 giây, lớn nhất 111,00 giây. Ba ca API sau đó có thời gian khác nhau đáng kể. Bằng chứng chưa đủ để xác lập độ trễ tương tác ổn định, và không hỗ trợ ngưỡng $P_{95}\leq6$ giây.

Luận văn không bác bỏ giả thuyết thống kê nào từ các bảng trên. Dữ liệu nguồn, cách chọn mẫu và thiết kế đối chứng hiện chưa hỗ trợ các kết luận nhân quả hoặc tuyên bố ưu thế có ý nghĩa thống kê.

## 5.6. Các đe dọa đến tính hợp lệ

**Khác biệt cấu hình và phiên bản.** Ngân sách nguồn không đồng nhất; mã được sửa nhiều lần; các bản ghi không đóng băng đầy đủ môi trường. Gộp chúng có thể tạo một kết quả không thuộc về bất kỳ cấu hình thực tế nào.

**Thiết kế bộ kiểm tra.** Dữ liệu hư cấu có mã hồ sơ và quan hệ được chuẩn bị để thử hệ thống. Quy tắc và prompt hiện tại còn chứa các thực thể của bộ này. Hiệu quả trên dữ liệu cùng kiểu có thể không chuyển sang tài liệu doanh nghiệp khác.

**Giới hạn thước đo.** Tìm thấy mã nguồn trong tiêu đề không chứng minh câu trả lời sử dụng đúng nội dung. Nhãn `verified` phụ thuộc hợp đồng kiểm tra; việc nới điều kiện quote hoặc giữ bản nháp làm thay đổi ý nghĩa vận hành của các trạng thái. Không so sánh trực tiếp các tỷ lệ này qua phiên bản mà bỏ qua thay đổi hợp đồng.

**Thiếu chấm độc lập.** Đáp án đối chiếu và hệ thống chưa được đánh giá bằng một quy trình người chấm có ghi nhận độ đồng thuận. Sinh và kiểm chứng cùng hồ sơ mô hình cũng có thể mắc lỗi tương quan.

**Phạm vi dữ liệu và vận hành.** Hai mươi ca không đủ đại diện cho mọi cấu trúc câu hỏi. Bộ đánh giá chưa bao phủ tải đồng thời, tài liệu rất dài, bảng phức tạp hoặc cập nhật thời gian có mâu thuẫn. Tìm kiếm từ vựng và mở rộng nguồn hiện còn đọc toàn bộ tài liệu trong không gian, nên chưa có bằng chứng về khả năng mở rộng lớn.

Những giới hạn này không làm mất giá trị của việc xây dựng nguyên mẫu, nhưng xác định rõ mức kết luận có thể rút ra: kết quả thăm dò trên bộ hồ sơ nhỏ, có khả năng truy vết và còn nhiều vấn đề cần kiểm tra tiếp.

# Chương 6. Kết luận và hướng phát triển

## 6.1. Kết luận

Luận văn đã trình bày thiết kế và đánh giá bước đầu hệ thống Agentic RAG 2.0 cho hỏi đáp tài liệu tiếng Việt. Nguyên mẫu giữ tài liệu gốc trong PostgreSQL, sử dụng các đường truy xuất bổ sung và tổ chức bước sinh, kiểm chứng, sửa câu trả lời với số lượt hữu hạn. Việc giữ nguồn đối chiếu giúp kiểm tra phản hồi và nhận diện các phần chưa đủ bằng chứng.

Phân tích 18 câu hỏi độc lập cho thấy cấu hình mở rộng tham chiếu tìm được nhiều mã nguồn đối chiếu hơn cấu hình sáu đoạn từ vựng: trung bình 0,9676 so với 0,7500. Số câu tìm đủ nguồn tăng từ 8/18 lên 16/18. Kết quả này có giá trị mô tả trong bộ Minh An, nhưng còn chịu ảnh hưởng của ngân sách nguồn khác nhau.

Ở tầng tổng hợp, lượt đánh giá qwen2.5:3b ghi nhận 0/20 bản tổng hợp vượt qua kiểm tra nội bộ và 20/20 phản hồi trích đoạn. Đây là giới hạn quan trọng của cấu hình đã chạy. Hệ thống đã có hành vi dự phòng, nhưng chưa đạt yêu cầu tổng hợp trong lượt đánh giá đó.

Thời gian xử lý trung vị 27,51 giây và lớn nhất 111,00 giây chưa hỗ trợ cam kết tương tác với độ trễ thấp. Chưa có phép đo hợp lệ để kết luận về Faithfulness, Context Precision, Context Recall theo RAGAS hoặc hiệu quả riêng của đồ thị thời gian.

Từ các kết quả trên, bài học thiết kế chính là cần đánh giá riêng khả năng tìm nguồn, tuân thủ hợp đồng sinh và độ đúng nội dung. Cải thiện một tầng chưa đủ để xác nhận chất lượng toàn hệ thống.

## 6.2. Những vấn đề chưa giải quyết

Bộ kiểm tra còn nhỏ, hư cấu và chưa có quy trình người chấm độc lập. Dữ liệu đã tham gia quá trình điều chỉnh quy tắc, nên không đủ làm tập kiểm tra cuối cho khả năng khái quát. Hiện chưa có thí nghiệm cùng ngân sách để tách tác dụng của từng đường truy xuất và bước kiểm chứng.

Quy tắc ưu tiên văn bản sửa đổi chưa mô hình hóa đầy đủ hiệu lực thời gian. Tên thực thể và ví dụ nghiệp vụ khai báo sẵn làm nguyên mẫu phụ thuộc bộ minh họa. Mã hiện tại còn nới điều kiện đối sánh quote và giữ bản nháp chưa kiểm chứng; những thay đổi này cần một lượt đánh giá riêng.

Cơ chế tìm kiếm từ vựng và mở rộng tham chiếu chưa được kiểm tra ở quy mô lớn. Lọc không gian tài liệu chưa thay thế đầy đủ quản lý quyền truy cập. Khác biệt giữa API và CLI cũng làm hạn chế khả năng suy rộng kết quả từ một giao diện sang giao diện còn lại.

Các hạn chế này cần được giải quyết trước khi tuyên bố hệ thống phù hợp vận hành doanh nghiệp hoặc có ưu thế so với các hệ thống đối chứng.

## 6.3. Hướng phát triển

Ưu tiên tiếp theo là đóng băng một phiên bản mã và hợp đồng đầu ra, rồi đánh giá trên dữ liệu chưa dùng để điều chỉnh. Mỗi nhận định cần được chấm theo độ đúng, mức được nguồn hỗ trợ và độ đầy đủ. Các phản hồi trích đoạn, bản nháp chưa kiểm chứng và thông báo thiếu dữ liệu cần được ghi riêng.

Ở tầng truy xuất, cần so sánh cùng ngân sách ký tự hoặc token, bổ sung phép đo nguồn không liên quan và kiểm tra nguyên nhân bỏ sót T15/T17. Sau đó mới đánh giá riêng đóng góp của vector, RRF, tham chiếu và Graphiti. Với hồ sơ dài, có thể thử cách chia theo cấu trúc và lựa chọn đoạn phù hợp hơn, nhưng phải giữ điều kiện đối chứng.

Ở tầng sinh, cần kiểm tra xem lỗi đến từ tuân thủ JSON, cách ghép ngữ cảnh, giới hạn mô hình hay độ nghiêm của bộ kiểm chứng. Thử mô hình khác là một hướng thí nghiệm, chưa phải giải pháp đã được xác nhận. Việc nới điều kiện kiểm tra cần được đánh giá cùng nguy cơ chấp nhận nhận định sai, thay vì chỉ theo tỷ lệ qua kiểm chứng.

Đối với thời gian, cần tách ngày nạp, ngày ban hành, ngày hiệu lực và quan hệ thay thế. Bộ kiểm tra nên có câu hỏi lịch sử, văn bản mới nhưng chưa có hiệu lực và các quyết định chỉ điều chỉnh một phần. Khi mở rộng vận hành, cần đo tải đồng thời, chi phí, bảo vệ dữ liệu và khả năng hủy tác vụ.

# Tài liệu tham khảo

Asai, A., Wu, Z., Wang, Y., Sil, A., & Hajishirzi, H. (2023). *Self-RAG: Learning to retrieve, generate, and critique through self-reflection* [Bản tiền công bố]. arXiv. https://doi.org/10.48550/arXiv.2310.11511

Cormack, G. V., Clarke, C. L. A., & Büttcher, S. (2009). Reciprocal rank fusion outperforms Condorcet and individual rank learning methods. In *Proceedings of the 32nd international ACM SIGIR conference on research and development in information retrieval* (pp. 758–759). Association for Computing Machinery. https://doi.org/10.1145/1571941.1572114

Edge, D., Trinh, H., Cheng, N., Bradley, J., Chao, A., Mody, A., Truitt, S., Metropolitansky, D., Ness, R. O., & Larson, J. (2024). *From local to global: A graph RAG approach to query-focused summarization* [Bản tiền công bố]. arXiv. https://doi.org/10.48550/arXiv.2404.16130

Es, S., James, J., Espinosa Anke, L., & Schockaert, S. (2024). RAGAs: Automated evaluation of retrieval augmented generation. In N. Aletras & O. De Clercq (Eds.), *Proceedings of the 18th Conference of the European Chapter of the Association for Computational Linguistics: System demonstrations* (pp. 150–158). Association for Computational Linguistics. https://doi.org/10.18653/v1/2024.eacl-demo.16

Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W.-t., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. *Advances in Neural Information Processing Systems, 33*, 9459–9474. https://papers.nips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html

Rasmussen, P., Paliychuk, P., Beauvais, T., Ryan, J., & Chalef, D. (2025). *Zep: A temporal knowledge graph architecture for agent memory* [Bản tiền công bố]. arXiv. https://doi.org/10.48550/arXiv.2501.13956

Yan, S.-Q., Gu, J.-C., Zhu, Y., & Ling, Z.-H. (2024). *Corrective retrieval augmented generation* [Bản tiền công bố]. arXiv. https://doi.org/10.48550/arXiv.2401.15884

# Phụ lục A. Danh mục bằng chứng trong dự án

Các đường dẫn dưới đây là hồ sơ nội bộ hỗ trợ tái lập nguyên mẫu, không được trình bày như bài báo đã công bố.

**Bảng A1**  
*Đối chiếu nội dung luận văn với hồ sơ dự án*

| Nội dung | Tệp hoặc thành phần đối chiếu | Phạm vi chứng cứ |
|---|---|---|
| Dữ liệu hư cấu và cách chuẩn bị Graphiti | `data/demo-doanh-nghiep/minh-an/README.md` | Nguồn và giới hạn bộ dữ liệu |
| Câu hỏi, đáp án, mã nguồn yêu cầu | `data/demo-doanh-nghiep/minh-an/evaluation/cases.json` | 20 ca; chưa có xác nhận gán nhãn độc lập |
| Lập chỉ mục vector và đồ thị | `backend/app/ingestion/database_sync.py` | Thứ tự lưu, trạng thái, xử lý lỗi |
| Chia đoạn và yêu cầu chiều embedding | `backend/app/ingestion/chunker.py` | Cấu hình mã nguồn |
| Tìm kiếm và mở rộng nguồn | `backend/app/agents/tools.py` | Thuật toán hiện tại; không tự chứng minh hiệu quả |
| Luồng sinh và sửa | `backend/app/agents/router.py` | Luồng phục vụ hiện tại |
| Kiểm chứng và đối sánh quote | `backend/app/agents/critic.py` | Hợp đồng hiện tại |
| Cách chạy phép đo nguồn và đầu cuối | `artifacts/rag-upgrade/evaluate.py` | Thủ tục của lượt đã lưu |
| Tỷ lệ tìm nguồn theo câu | `artifacts/rag-upgrade/retrieval.json` | Kết quả nguồn ở mốc A |
| Trạng thái và thời gian 20 ca | `artifacts/rag-upgrade/after.json` | Kết quả đầu cuối ở mốc A |
| Tổng hợp cùng cảnh báo phiên bản | `artifacts/rag-upgrade/summary.json` | Đối chiếu thống kê |
| Ba ca API sau chỉnh sửa | `artifacts/rag-upgrade/final-api-check.json` | Kết quả mốc B |
| Mô tả giới hạn của lượt nâng cấp | `docs/testing/rag-architecture-upgrade.md` | Báo cáo kỹ thuật; đối chiếu với JSON |
| Kịch bản có nhánh gán điểm sẵn | `tests/run_evaluation.py` | Lý do không sử dụng bảng RAGAS cũ làm kết quả thật |

*Ghi chú.* Không suy ra trạng thái dịch vụ đang hoạt động hôm nay chỉ từ một bản ghi sức khỏe lịch sử. Mã băm các nguồn và danh sách nội dung đã sửa nằm trong `BAO_CAO_RASOAT_LUAN_VAN_APA7.md` và `HO_SO_BIEN_TAP_LUAN_VAN.json` kèm bản thảo.

# Phụ lục B. Quy tắc kiểm tra số liệu

Đoạn mã dưới đây chỉ đọc các bản ghi đã lưu. Nó không chạy hệ thống RAG, không gọi dịch vụ mô hình và không ghi kết quả mới. Thư mục làm việc là gốc dự án `D:\RAG`.

~~~python
import json
import statistics
from pathlib import Path

root = Path("artifacts/rag-upgrade")
retrieval = json.loads((root / "retrieval.json").read_text(encoding="utf-8"))
answers = json.loads((root / "after.json").read_text(encoding="utf-8"))
api = json.loads((root / "final-api-check.json").read_text(encoding="utf-8"))

eligible = [item for item in retrieval if item["case"] not in {"T19", "T20"}]
assert len(eligible) == 18
assert len(answers) == 20

before = statistics.mean(item["before_recall"] for item in eligible)
after = statistics.mean(item["after_recall"] for item in eligible)
complete_before = sum(item["before_recall"] == 1 for item in eligible)
complete_after = sum(item["after_recall"] == 1 for item in eligible)

modes = {
    mode: sum(item["result"].get("answer_mode") == mode for item in answers)
    for mode in ["verified", "extractive", "no_evidence"]
}
durations = [item["seconds"] for item in answers]

print("Tỷ lệ mã nguồn trung bình:", before, after)
print("Số câu tìm đủ nguồn:", complete_before, complete_after)
print("Trạng thái:", modes)
print("Trung vị và thời gian lớn nhất:",
      statistics.median(durations), max(durations))
print("API:", [
    (item["case"], item["status"], item["seconds"],
     len(item["response"].get("sources", [])))
    for item in api["results"]
])
~~~

Khi tái chạy một phiên bản hệ thống mới, cần lưu một bộ kết quả khác với thông tin phiên bản và hợp đồng chấm. Không ghi đè các bản ghi đang hỗ trợ kết luận của luận văn.
