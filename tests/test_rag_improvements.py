import unittest
import datetime
import json
from unittest.mock import AsyncMock, patch

from backend.app.agents.critic import is_quote_supported, CriticResult
from backend.app.agents.router import (
    render_grounded_answer,
    preserves_constraints,
    extractive_answer,
    citations_valid,
    AgenticRAG
)
from backend.app.agents.tools import (
    extract_document_date,
    is_amendment_doc,
    fuse_sources
)


class TestRAGImprovements(unittest.TestCase):

    def setUp(self):
        self.sources = [
            {
                "document_id": "doc_cr07",
                "title": "CR-07 | Thay đổi được duyệt ngày 18/09",
                "content": "Theo yêu cầu thay đổi CR-07 ngày 18/09/2026, mốc vận hành Atlas được dời sang ngày 21/10/2026. "
                           "Ngân sách Atlas tăng 180 triệu đồng chưa VAT. Nguyễn Linh là người phê duyệt ngân sách điều chỉnh."
            },
            {
                "document_id": "doc_prjat01",
                "title": "PRJ-AT-01 | Điều lệ dự án Atlas",
                "content": "Điều lệ dự án Atlas ngày 15/08/2026 quy định mốc vận hành là ngày 15/10/2026. "
                           "Phạm Huy chịu trách nhiệm quản lý dự án Atlas. Lê Quang phụ trách kiến trúc."
            },
            {
                "document_id": "doc_steer09",
                "title": "STEER-09 | Ban chỉ đạo ngày 22/09",
                "content": "Biên bản cuộc họp ban chỉ đạo ngày 22/09/2026 xác nhận mốc golive 21/10/2026 là chính thức."
            }
        ]

    def test_quote_supported_variations(self):
        content = "Theo yêu cầu thay đổi CR-07 ngày 18/09/2026, mốc vận hành Atlas được dời sang ngày 21/10/2026."
        
        # 1. Exact match
        self.assertTrue(is_quote_supported("mốc vận hành Atlas được dời sang ngày 21/10/2026", content))
        
        # 2. Match with different punctuation / quotes / extra spaces
        self.assertTrue(is_quote_supported("«mốc vận hành Atlas được dời sang ngày 21/10/2026.»", content))
        
        # 3. Match with ellipsis sub-clauses
        self.assertTrue(is_quote_supported("Theo yêu cầu thay đổi CR-07... mốc vận hành Atlas được dời sang ngày 21/10/2026", content))
        
        # 4. Token overlap (>= 75%)
        self.assertTrue(is_quote_supported("yêu cầu thay đổi CR-07 mốc vận hành Atlas dời sang ngày 21/10/2026", content))
        
        # 5. Hallucinated quote should FAIL
        self.assertFalse(is_quote_supported("FPT đầu tư 500 triệu USD mua chip GPU H100", content))

    def test_render_grounded_answer_fallback_text_to_quote(self):
        # When LLM only returns quote and source_id without text, text defaults to quote
        raw_json = json.dumps({
            "claims": [
                {
                    "source_id": 1,
                    "quote": "mốc vận hành Atlas được dời sang ngày 21/10/2026"
                }
            ],
            "missing_information": []
        })
        rendered = render_grounded_answer(raw_json, self.sources)
        self.assertIsNotNone(rendered)
        self.assertIn("mốc vận hành Atlas được dời sang ngày 21/10/2026 [1]", rendered)

    def test_render_grounded_answer_with_text(self):
        raw_json = json.dumps({
            "claims": [
                {
                    "source_id": 1,
                    "quote": "mốc vận hành Atlas được dời sang ngày 21/10/2026",
                    "text": "Mốc vận hành Atlas chính thức dời sang 21/10/2026."
                }
            ],
            "missing_information": ["Chưa rõ giờ vận hành cụ thể."]
        })
        rendered = render_grounded_answer(raw_json, self.sources)
        self.assertIsNotNone(rendered)
        self.assertIn("Mốc vận hành Atlas chính thức dời sang 21/10/2026. [1]", rendered)
        self.assertIn("Chưa rõ giờ vận hành cụ thể.", rendered)

    def test_preserves_constraints_numerical_and_role(self):
        # Numerical boundary preservation
        quote = "Ngân sách tăng không quá 180 triệu"
        text_valid = "Chi phí điều chỉnh tối đa 180 triệu"
        self.assertTrue(preserves_constraints(text_valid, quote))

        # Person and action pair preservation
        quote_role = "Nguyễn Linh là người phê duyệt ngân sách điều chỉnh"
        text_role_valid = "Nguyễn Linh phê duyệt ngân sách điều chỉnh"
        self.assertTrue(preserves_constraints(text_role_valid, quote_role))

        # Inverted or altered role should fail
        text_role_invalid = "Trần Mai phê duyệt ngân sách điều chỉnh"
        self.assertFalse(preserves_constraints(text_role_invalid, quote_role))

    def test_extract_document_date_and_amendment(self):
        # CR-07 date
        date_cr = extract_document_date("CR-07 | Thay đổi được duyệt ngày 18/09", "")
        self.assertEqual(date_cr, datetime.date(2026, 9, 18))
        self.assertTrue(is_amendment_doc("CR-07 | Thay đổi được duyệt ngày 18/09"))

        # STEER-09 date
        date_steer = extract_document_date("STEER-09 | Ban chỉ đạo ngày 22/09", "")
        self.assertEqual(date_steer, datetime.date(2026, 9, 22))
        self.assertTrue(is_amendment_doc("STEER-09 | Ban chỉ đạo ngày 22/09"))

        # PRJ-AT-01 date
        date_prj = extract_document_date("PRJ-AT-01 | Điều lệ dự án Atlas", "Điều lệ dự án Atlas ngày 15/08/2026")
        self.assertEqual(date_prj, datetime.date(2026, 8, 15))
        self.assertFalse(is_amendment_doc("PRJ-AT-01 | Điều lệ dự án Atlas"))

    def test_fuse_sources_recency_boost(self):
        # Lexical search ranked PRJ-AT-01 higher (rank 1) than CR-07 (rank 2) because PRJ is longer
        lexical = [
            {"document_id": "doc_prjat01", "title": "PRJ-AT-01 | Điều lệ dự án Atlas", "content": "Điều lệ Atlas ngày 15/08/2026"},
            {"document_id": "doc_cr07", "title": "CR-07 | Thay đổi được duyệt ngày 18/09", "content": "Thay đổi mốc vận hành ngày 18/09/2026"}
        ]
        vector = []

        fused = fuse_sources(vector, lexical)
        # Because CR-07 is an amendment document and has a Sept date, it gets 1.3x boost!
        # Base RRF: doc_prjat01 = 1/(60+1) = 0.01639
        #           doc_cr07 = 1/(60+2) = 0.016129 * 1.3 = 0.020968
        # Therefore, doc_cr07 should be ranked FIRST!
        self.assertEqual(fused[0]["document_id"], "doc_cr07")
        self.assertEqual(fused[1]["document_id"], "doc_prjat01")

    def test_citations_valid(self):
        self.assertTrue(citations_valid("Mốc vận hành [1] theo quyết định [2]", 3))
        self.assertFalse(citations_valid("Mốc vận hành [4] theo quyết định [1]", 2)) # 4 > count
        self.assertFalse(citations_valid("Không có trích dẫn nào ở đây", 2))


class TestAsyncAgenticRAG(unittest.IsolatedAsyncioTestCase):

    @patch("backend.app.agents.router.verify_answer")
    @patch("backend.app.agents.router.complete")
    @patch("backend.app.agents.router.expand_evidence")
    @patch("backend.app.agents.router.lexical_search")
    @patch("backend.app.agents.router.vector_search")
    async def test_soft_fallback_preserves_synthesized_answer(
        self, mock_vec, mock_lex, mock_expand, mock_complete, mock_verify
    ):
        mock_vec.return_value = []
        mock_lex.return_value = [
            {
                "document_id": "doc_1",
                "title": "MA-HR-02 | Danh bạ và trách nhiệm",
                "content": "Phạm Huy quản lý Atlas. Lê Quang phụ trách kiến trúc."
            }
        ]
        mock_expand.return_value = [
            {
                "document_id": "doc_1",
                "title": "MA-HR-02 | Danh bạ và trách nhiệm",
                "content": "Phạm Huy quản lý Atlas. Lê Quang phụ trách kiến trúc."
            }
        ]

        # LLM produces valid JSON claims
        mock_complete.return_value = json.dumps({
            "claims": [
                {
                    "source_id": 1,
                    "quote": "Phạm Huy quản lý Atlas. Lê Quang phụ trách kiến trúc.",
                    "text": "Phạm Huy chịu trách nhiệm quản lý Atlas và Lê Quang phụ trách kiến trúc."
                }
            ],
            "missing_information": []
        })

        # Verification returns False (e.g. strict check failed)
        mock_verify.return_value = (False, "Cần kiểm tra kỹ hơn")

        app = AgenticRAG()
        state = {
            "query": "Ai quản lý Atlas và ai phụ trách kiến trúc?",
            "tenant_id": None,
            "route": "vector",
            "history": []
        }

        result = await app.ainvoke(state)
        # Khi Critic bác bỏ bản sửa, hệ thống tuân thủ hợp đồng an toàn: trả trích dẫn bằng chứng gốc
        self.assertEqual(result["answer_mode"], "extractive")
        self.assertIn("Các đoạn bằng chứng gốc", result["final_answer"])


if __name__ == "__main__":
    unittest.main()
