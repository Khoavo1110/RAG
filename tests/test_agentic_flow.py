import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Add current workspace root to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pydantic import BaseModel
from backend.app.schemas import Document, DocumentChunk
from backend.app.agents.critic import CriticResult
from backend.app.agents.router import (
    AgentState, 
    RouteChoice, 
    route_question_node, 
    retrieve_node, 
    generate_node, 
    critic_node, 
    should_continue,
    agentic_rag_app
)

# Mock models for structured output testing
class MockLLMResponse(BaseModel):
    route: str
    reason: str

class TestAgenticFlow(unittest.IsolatedAsyncioTestCase):
    
    @patch("backend.app.agents.router.get_llm")
    async def test_route_question_node_vector(self, mock_get_llm):
        # Setup mock LLM with structured output returning vector choice
        mock_llm = MagicMock()
        mock_structured_llm = AsyncMock()
        mock_structured_llm.ainvoke.return_value = RouteChoice(route="vector", reason="Looking for specific FPT report details.")
        mock_llm.with_structured_output.return_value = mock_structured_llm
        mock_get_llm.return_value = mock_llm

        state: AgentState = {
            "query": "CEO Phạm Minh Tuấn đã nói gì về GPU?",
            "tenant_id": "tenant_1",
            "route": "hybrid",
            "retrieved_contexts": [],
            "draft_answer": "",
            "critic_feedback": None,
            "refinement_query": None,
            "loop_count": 0,
            "final_answer": "",
            "thought_process": [],
            "sources": []
        }

        result = await route_question_node(state)
        self.assertEqual(result["route"], "vector")
        self.assertIn("Chọn hướng truy xuất: 'vector'", result["thought_process"][0])

    @patch("backend.app.agents.router.vector_search_tool")
    @patch("backend.app.agents.router.graph_search_tool")
    async def test_retrieve_node_hybrid(self, mock_graph_search, mock_vector_search):
        # Setup mock db session and search tools
        mock_db = MagicMock()
        
        mock_vector_search.return_value = [
            {
                "content": "FPT đầu tư 200 triệu USD mua GPU.",
                "document_id": "doc_1",
                "title": "Báo cáo FPT",
                "chunk_index": 0,
                "source_type": "vector"
            }
        ]
        
        mock_graph_search.return_value = {
            "context_string": "FACTS: FPT Software USES NVIDIA GPU",
            "raw_facts": [
                {
                    "fact": "FPT Software USES NVIDIA GPU",
                    "name": "USES",
                    "episodes": ["ep_1"]
                }
            ],
            "source_type": "graph"
        }

        state: AgentState = {
            "query": "FPT mua GPU của ai?",
            "tenant_id": "tenant_1",
            "route": "hybrid",
            "retrieved_contexts": [],
            "draft_answer": "",
            "critic_feedback": None,
            "refinement_query": None,
            "loop_count": 0,
            "final_answer": "",
            "thought_process": [],
            "sources": []
        }

        config = {"configurable": {"db": mock_db}}

        result = await retrieve_node(state, config=config)
        
        # Verify both channels are queried and contexts merged
        self.assertEqual(len(result["retrieved_contexts"]), 2)
        self.assertEqual(result["retrieved_contexts"][0]["source_type"], "vector")
        self.assertEqual(result["retrieved_contexts"][1]["source_type"], "graph")
        
        # Verify sources extraction
        self.assertEqual(len(result["sources"]), 2)
        self.assertEqual(result["sources"][0]["title"], "Báo cáo FPT")
        self.assertEqual(result["sources"][1]["fact"], "FPT Software USES NVIDIA GPU")

    @patch("backend.app.agents.router.get_llm")
    async def test_generate_node(self, mock_get_llm):
        # Setup mock response
        mock_llm = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "FPT Software đã ký hợp tác với NVIDIA."
        mock_llm.ainvoke.return_value = mock_response
        mock_get_llm.return_value = mock_llm

        state: AgentState = {
            "query": "FPT hợp tác với ai?",
            "tenant_id": None,
            "route": "vector",
            "retrieved_contexts": [
                {
                    "content": "FPT hợp tác với NVIDIA phát triển AI Factory.",
                    "document_id": "doc_1",
                    "title": "Báo cáo FPT",
                    "chunk_index": 0,
                    "source_type": "vector"
                }
            ],
            "draft_answer": "",
            "critic_feedback": None,
            "refinement_query": None,
            "loop_count": 0,
            "final_answer": "",
            "thought_process": [],
            "sources": []
        }

        result = await generate_node(state)
        self.assertEqual(result["draft_answer"], "FPT Software đã ký hợp tác với NVIDIA.")
        self.assertIn("Đã tạo dự thảo câu trả lời", result["thought_process"][0])

    @patch("backend.app.agents.router.critic_agent")
    async def test_critic_node_invalid(self, mock_critic):
        # Critic evaluates draft answer as incomplete and suggests refinement
        mock_critic.evaluate = AsyncMock(return_value=CriticResult(
            is_valid=False,
            feedback="Thiếu số tiền đầu tư mua chip GPU.",
            refinement_query="FPT đầu tư bao nhiêu tiền mua GPU NVIDIA?"
        ))

        state: AgentState = {
            "query": "FPT đầu tư bao nhiêu tiền mua GPU?",
            "tenant_id": None,
            "route": "hybrid",
            "retrieved_contexts": [],
            "draft_answer": "FPT đã ký hợp tác mua chip của NVIDIA.",
            "critic_feedback": None,
            "refinement_query": None,
            "loop_count": 0,
            "final_answer": "",
            "thought_process": [],
            "sources": []
        }

        result = await critic_node(state)
        self.assertEqual(result["final_answer"], "")
        self.assertEqual(result["refinement_query"], "FPT đầu tư bao nhiêu tiền mua GPU NVIDIA?")
        self.assertEqual(result["critic_feedback"], "Thiếu số tiền đầu tư mua chip GPU.")

    def test_should_continue_logic(self):
        # 1. Answer validated by critic -> Should END
        state_valid: AgentState = {
            "query": "query", "tenant_id": None, "route": "vector", "retrieved_contexts": [],
            "draft_answer": "answer", "critic_feedback": None, "refinement_query": None,
            "loop_count": 0, "final_answer": "answer", "thought_process": [], "sources": []
        }
        self.assertEqual(should_continue(state_valid), "end")

        # 2. Answer invalid but loop limit hit -> Should END
        state_limit: AgentState = {
            "query": "query", "tenant_id": None, "route": "vector", "retrieved_contexts": [],
            "draft_answer": "answer", "critic_feedback": "error", "refinement_query": "refine",
            "loop_count": 2, "final_answer": "", "thought_process": [], "sources": []
        }
        self.assertEqual(should_continue(state_limit), "end")

        # 3. Answer invalid and loop limit not hit -> Should CONTINUE
        state_continue: AgentState = {
            "query": "query", "tenant_id": None, "route": "vector", "retrieved_contexts": [],
            "draft_answer": "answer", "critic_feedback": "error", "refinement_query": "refine",
            "loop_count": 0, "final_answer": "", "thought_process": [], "sources": []
        }
        self.assertEqual(should_continue(state_continue), "continue")

    @patch("backend.app.agents.tools.graph_extractor")
    async def test_graph_search_tool_with_tenant(self, mock_graph_extractor):
        from backend.app.agents.tools import graph_search_tool
        
        # Setup mock db and query
        mock_db = MagicMock()
        mock_doc = MagicMock()
        mock_doc.metadata_json = {"graphiti_episode_uuid": "episode_fpt_123"}
        mock_db.query().filter().all.return_value = [mock_doc]

        # Setup mock Neo4j/Graphiti edges list return
        mock_edge = MagicMock()
        mock_edge.fact = "FPT Software USES NVIDIA GPU"
        mock_edge.name = "USES"
        mock_edge.episodes = ["episode_fpt_123"]
        mock_edge.valid_at = None
        mock_edge.invalid_at = None
        
        # Setup another edge that belongs to different tenant (should be filtered out!)
        mock_edge_other = MagicMock()
        mock_edge_other.fact = "Viettel USES Huawei"
        mock_edge_other.name = "USES"
        mock_edge_other.episodes = ["episode_viettel_456"]
        mock_edge_other.valid_at = None
        mock_edge_other.invalid_at = None

        mock_graph_extractor.graphiti.search = AsyncMock(return_value=[mock_edge, mock_edge_other])

        # Run tool
        result = await graph_search_tool(mock_db, "GPU partners", tenant_id="tenant_fpt_001")

        # Verify only mock_edge remains
        self.assertEqual(len(result["raw_facts"]), 1)
        self.assertEqual(result["raw_facts"][0]["fact"], "FPT Software USES NVIDIA GPU")
        self.assertIn("FPT Software USES NVIDIA GPU", result["context_string"])
        self.assertNotIn("Viettel USES Huawei", result["context_string"])
        
        # Verify graphiti.search was called with group_ids=[tenant_id]
        mock_graph_extractor.graphiti.search.assert_called_once_with("GPU partners", group_ids=["tenant_fpt_001"])

if __name__ == "__main__":
    unittest.main()
