"""애플리케이션 설정 및 환경변수 관리."""

import os
from enum import Enum
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# 루트 디렉토리의 .env 파일 로드
load_dotenv()

# Neon PostgreSQL 기본 URL
DEFAULT_DATABASE_URL = (
    "postgresql://neondb_owner:npg_pzP8wiQDH1sk@"
    "ep-autumn-boat-a1wcjk8g-pooler.ap-southeast-1.aws.neon.tech/"
    "neondb?sslmode=require"
)


class LLMProvider(str, Enum):
    """LLM 제공자 열거형."""

    OPENAI = "openai"
    LOCAL = "local"


class Settings(BaseSettings):
    """애플리케이션 설정."""

    # API 정보
    APP_NAME: str = "LangChain RAG Chatbot API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # LLM 설정
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")  # "openai" 또는 "local"

    # OpenAI 설정 (LLM_PROVIDER=openai일 때 사용)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))

    # 로컬 모델 설정 (LLM_PROVIDER=local일 때 사용)
    LOCAL_MODEL_PATH: str = os.getenv(
        "LOCAL_MODEL_PATH",
        str(Path(__file__).parent.parent.parent / "model_weights")
    )
    LOCAL_MODEL_DEVICE: str = os.getenv("LOCAL_MODEL_DEVICE", "cuda")  # cpu, cuda, auto
    LOCAL_MODEL_MAX_NEW_TOKENS: int = int(os.getenv("LOCAL_MODEL_MAX_NEW_TOKENS", "512"))
    LOCAL_MODEL_TEMPERATURE: float = float(os.getenv("LOCAL_MODEL_TEMPERATURE", "0.7"))

    # 데이터베이스 설정 (Neon PostgreSQL)
    DATABASE_URL: str = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

    # CORS 설정
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
    ]

    @property
    def database_url(self) -> str:
        """PostgreSQL 연결 문자열 반환."""
        return self.DATABASE_URL

    @property
    def is_local_llm(self) -> bool:
        """로컬 LLM 사용 여부."""
        return self.LLM_PROVIDER.lower() == "local"

    def validate_config(self) -> None:
        """설정 유효성 검사."""
        if self.is_local_llm:
            model_path = Path(self.LOCAL_MODEL_PATH)
            if not model_path.exists():
                msg = f"로컬 모델 경로가 존재하지 않습니다: {self.LOCAL_MODEL_PATH}"
                raise ValueError(msg)
            if not (model_path / "config.json").exists():
                msg = f"모델 config.json이 없습니다: {self.LOCAL_MODEL_PATH}"
                raise ValueError(msg)
        else:
            if not self.OPENAI_API_KEY:
                msg = "OPENAI_API_KEY 환경변수가 설정되지 않았습니다."
                raise ValueError(msg)

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    """설정 싱글톤 인스턴스 반환."""
    return Settings()


# 전역 설정 인스턴스
settings = get_settings()
