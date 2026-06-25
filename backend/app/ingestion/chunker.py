from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from backend.app.config import settings

class DocumentChunker:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
        )
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=settings.OPENAI_API_KEY,
            openai_api_base="https://models.inference.ai.azure.com"
        )

    def split_text(self, text: str) -> list[str]:
        """Split text into chunks."""
        return self.splitter.split_text(text)

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        return self.embeddings.embed_documents(texts)

    def chunk_and_embed(self, text: str) -> list[dict]:
        """Split text into chunks and generate embeddings for each."""
        chunks = self.split_text(text)
        if not chunks:
            return []
            
        embeddings = self.generate_embeddings(chunks)
        
        chunk_data = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_data.append({
                "content": chunk,
                "chunk_index": i,
                "embedding": embedding
            })
            
        return chunk_data
