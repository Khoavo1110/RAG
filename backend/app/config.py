from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
if BASE_DIR.name == '.nori-rebuild':
    BASE_DIR = BASE_DIR.parent
load_dotenv(BASE_DIR / '.env')

class Settings(BaseSettings):
    POSTGRES_USER: str = 'postgres'
    POSTGRES_PASSWORD: str = ''
    POSTGRES_DB: str = 'agentic_rag'
    POSTGRES_HOST: str = 'localhost'
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str | None = None
    NEO4J_URI: str = 'bolt://localhost:7687'
    NEO4J_USERNAME: str = 'neo4j'
    NEO4J_PASSWORD: str = ''
    REDIS_URL: str = 'redis://localhost:6379/0'
    LLM_PROVIDER: str = 'ollama'
    OLLAMA_BASE_URL: str = 'http://localhost:11434/v1'
    OLLAMA_MODEL: str = 'qwen2.5:3b'
    OLLAMA_NUM_CTX: int = 16384
    GEMINI_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    OPENROUTER_API_KEY: str | None = None
    OPENROUTER_MODEL: str = 'openai/gpt-4o-mini'
    GITHUB_MODELS_API_KEY: str | None = None
    GITHUB_MODELS_BASE_URL: str = 'https://models.github.ai/inference'
    GITHUB_MODELS_MODEL: str = 'gpt-4o-mini'
    LLM_MODEL: str = 'gemini-2.5-flash'
    EMBEDDING_MODEL: str = 'gemini-embedding-2'
    model_config = SettingsConfigDict(env_file=BASE_DIR / '.env', extra='ignore')

    @property
    def postgres_url(self):
        if self.DATABASE_URL:
            return self.DATABASE_URL.replace('postgresql://', 'postgresql+psycopg2://', 1)
        from sqlalchemy import URL
        return URL.create('postgresql+psycopg2', username=self.POSTGRES_USER,
                          password=self.POSTGRES_PASSWORD, host=self.POSTGRES_HOST,
                          port=self.POSTGRES_PORT, database=self.POSTGRES_DB)

settings = Settings()
