import asyncio
from datetime import datetime, timezone
from backend.app.config import settings

class GraphExtractor:
    def __init__(self): self._graphiti=None
    @property
    def graphiti(self):
        if self._graphiti is None:
            from graphiti_core import Graphiti
            from graphiti_core.llm_client import LLMConfig
            from graphiti_core.llm_client.openai_generic_client import OpenAIGenericClient
            from graphiti_core.embedder import EmbedderClient
            from backend.app.agents.critic import default_provider_config
            from backend.app.ingestion.chunker import DocumentChunker
            from openai import AsyncOpenAI
            class GeminiEmbedder(EmbedderClient):
                async def create(self, input_data):
                    text=input_data[0] if isinstance(input_data,list) else str(input_data)
                    return (await asyncio.to_thread(DocumentChunker().generate_embeddings,[text]))[0]
                async def create_batch(self, input_data_list):
                    return await asyncio.to_thread(DocumentChunker().generate_embeddings,input_data_list)
            url,key,model=default_provider_config()
            llm=OpenAIGenericClient(config=LLMConfig(api_key=key,base_url=url,model=model,small_model=model),
                client=AsyncOpenAI(api_key=key,base_url=url,timeout=30,max_retries=0),structured_output_mode='json_object')
            self._graphiti=Graphiti(settings.NEO4J_URI,settings.NEO4J_USERNAME,settings.NEO4J_PASSWORD,
                llm_client=llm,embedder=GeminiEmbedder(),max_coroutines=2)
        return self._graphiti
    async def initialize(self): await self.graphiti.build_indices_and_constraints()
    async def add_episode(self,name,content,source_description='document',group_id=None):
        result=await self.graphiti.add_episode(name=name,episode_body=content,source_description=source_description,
            reference_time=datetime.now(timezone.utc),group_id=group_id)
        return result.episode.uuid
    async def remove_episode(self,uuid): await self.graphiti.remove_episode(uuid)
    async def close(self):
        if self._graphiti is not None:
            await self._graphiti.close()
            self._graphiti=None

graph_extractor=GraphExtractor()
