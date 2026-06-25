import datetime
from graphiti_core import Graphiti
from graphiti_core.llm_client import LLMConfig
from graphiti_core.llm_client.openai_generic_client import OpenAIGenericClient
from graphiti_core.embedder import OpenAIEmbedder, OpenAIEmbedderConfig, EmbedderClient
from openai import AsyncOpenAI
from backend.app.config import settings

class GeminiGraphitiEmbedder(EmbedderClient):
    def __init__(self, api_key: str):
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=api_key
        )
        
        class MockConfig:
            embedding_dim = 768
            embedding_model = "models/text-embedding-004"
            
        self.config = MockConfig()

    async def create(self, input_data) -> list[float]:
        if isinstance(input_data, list):
            res = await self.embeddings.aembed_documents(input_data)
            return res[0]
        res = await self.embeddings.aembed_query(str(input_data))
        return res

    async def create_batch(self, input_data_list: list[str]) -> list[list[float]]:
        # langchain embeddings.aembed_documents returns async
        return await self.embeddings.aembed_documents(input_data_list)

class GraphExtractor:
    def __init__(self):
        # Create a single shared OpenAI client with high retry count (max_retries=12)
        # to safely handle GitHub Models rate limit (15 requests per 60s)
        self.shared_client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url="https://models.inference.ai.azure.com",
            max_retries=12
        )

        # 1. Configure OpenAIGenericClient pointed to GitHub Models for LLM tasks
        # This bypasses the beta structured output endpoint and uses standard JSON mode,
        # which is fully compatible with GitHub Models (GPT-4o-mini).
        self.llm_config = LLMConfig(
            api_key=settings.OPENAI_API_KEY,
            base_url="https://models.inference.ai.azure.com",
            model="gpt-4o-mini",
            small_model="gpt-4o-mini"
        )
        self.llm_client = OpenAIGenericClient(
            config=self.llm_config,
            client=self.shared_client,
            structured_output_mode="json_object"
        )
        
        # 2. Configure GeminiEmbedder for 768-dimension embeddings
        self.embedder = GeminiGraphitiEmbedder(api_key=settings.GEMINI_API_KEY)
        
        # 3. Setup Graphiti Instance
        self.graphiti = Graphiti(
            uri=settings.NEO4J_URI,
            user=settings.NEO4J_USERNAME,
            password=settings.NEO4J_PASSWORD,
            llm_client=self.llm_client,
            embedder=self.embedder,
            max_coroutines=2  # Reduce concurrent requests to avoid 15 RPM rate limit
        )

    async def initialize(self):
        """Build constraints and indices in Neo4j if they don't exist."""
        await self.graphiti.build_indices_and_constraints()

    async def add_episode(
        self,
        name: str,
        content: str,
        source_description: str = "document_ingestion",
        group_id: str | None = None
    ) -> str:
        """
        Add a document as an episode to the knowledge graph.
        Returns the created episode UUID.
        """
        res = await self.graphiti.add_episode(
            name=name,
            episode_body=content,
            source_description=source_description,
            reference_time=datetime.datetime.now(datetime.timezone.utc),
            group_id=group_id
        )
        return res.episode.uuid

    async def remove_episode(self, episode_uuid: str):
        """Remove an episode and clean up orphaned nodes/edges."""
        await self.graphiti.remove_episode(episode_uuid)

    async def close(self):
        """Close graph connections."""
        await self.graphiti.close()

# Singleton instance
graph_extractor = GraphExtractor()
