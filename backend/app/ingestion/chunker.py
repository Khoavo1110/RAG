from backend.app.config import settings

class DocumentChunker:
    def __init__(self, chunk_size=900, chunk_overlap=100):
        self.chunk_size, self.chunk_overlap = chunk_size, chunk_overlap
    def split_text(self, text):
        return [text[i:i+self.chunk_size] for i in range(0, len(text), self.chunk_size-self.chunk_overlap) if text[i:i+self.chunk_size].strip()]
    def generate_embeddings(self, texts):
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        if not settings.GEMINI_API_KEY: raise RuntimeError('Embedding provider is not configured')
        client = GoogleGenerativeAIEmbeddings(model=settings.EMBEDDING_MODEL, google_api_key=settings.GEMINI_API_KEY)
        result = client.embed_documents(texts)
        if any(len(v) != 3072 for v in result): raise ValueError('Expected 3072-dimensional embeddings for existing database')
        return result
    def chunk_and_embed(self, text):
        chunks=self.split_text(text)
        return [dict(content=c, embedding=e, chunk_index=i) for i,(c,e) in enumerate(zip(chunks,self.generate_embeddings(chunks)))]
