import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    model_name: str = os.getenv("MODEL_NAME", "gpt-4o-mini")
    base_url: str | None = os.getenv("OPENAI_BASE_URL") or None
    api_key: str = os.getenv("OPENAI_API_KEY", "dummy")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
    retrieval_k: int = int(os.getenv("RETRIEVAL_K", "3"))
    max_searches: int = int(os.getenv("MAX_SEARCHES", "2"))
    llm_timeout: float = float(os.getenv("LLM_TIMEOUT", "60"))

    def __post_init__(self):
        if self.retrieval_k < 1 or self.max_searches < 1:
            raise ValueError("retrieval_k and max_searches must be >= 1")
