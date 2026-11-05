from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── LLM Provider ──────────────────────────────────────────────────────────
    # Set LLM_PROVIDER to "gemini" or "groq" in your .env file.
    # Groq is free and has no strict daily quota — recommended when Gemini
    # free-tier is exhausted.
    llm_provider: str = "groq"

    # ── Gemini settings ───────────────────────────────────────────────────────
    gemini_api_key: str = ""
    llm_model: str = "llama-3.3-70b-versatile"   # overridden per provider below
    embedding_model: str = "models/gemini-embedding-001"
    embedding_batch_size: int = 100
    embedding_max_retries: int = 2
    embedding_retry_delay_seconds: int = 60

    # ── Groq settings ─────────────────────────────────────────────────────────
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"

    # ── RAG / Vector DB ───────────────────────────────────────────────────────
    vector_db_path: str = "./vector_db"
    chunk_size: int = 1200
    chunk_overlap: int = 100

    # ── MCP ───────────────────────────────────────────────────────────────────
    mcp_server_url: str = "http://localhost:3333"
    github_mcp_url: str = "https://api.githubcopilot.com/mcp/"
    github_mcp_token: str = ""

    # ── Loader ────────────────────────────────────────────────────────────────
    allowed_extensions: list[str] = [".py", ".js", ".ts", ".go", ".java", ".md"]
    max_file_size_kb: int = 1042

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
