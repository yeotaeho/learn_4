"""LLM 설정 모듈."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class LLMProvider(str, Enum):
    """LLM 제공자 열거형."""

    OPENAI = "openai"
    LOCAL = "local"
    OLLAMA = "ollama"


class LLMConfig(BaseModel):
    """LLM 공통 설정."""

    provider: LLMProvider = Field(
        default=LLMProvider.OPENAI,
        description="LLM 제공자"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="생성 온도"
    )
    max_tokens: int = Field(
        default=1024,
        gt=0,
        description="최대 토큰 수"
    )


class OpenAIConfig(LLMConfig):
    """OpenAI 설정."""

    provider: LLMProvider = LLMProvider.OPENAI
    api_key: str = Field(..., description="OpenAI API 키")
    model_name: str = Field(
        default="gpt-3.5-turbo",
        description="모델 이름"
    )


class LocalModelConfig(LLMConfig):
    """로컬 모델 설정."""

    provider: LLMProvider = LLMProvider.LOCAL
    model_path: str = Field(..., description="모델 파일 경로")
    device: str = Field(
        default="auto",
        description="실행 장치 (cpu, cuda, auto)"
    )
    torch_dtype: str = Field(
        default="auto",
        description="Torch 데이터 타입 (float16, bfloat16, auto)"
    )
    trust_remote_code: bool = Field(
        default=False,
        description="원격 코드 신뢰 여부"
    )
    load_in_8bit: bool = Field(
        default=False,
        description="8bit 양자화 로드"
    )
    load_in_4bit: bool = Field(
        default=False,
        description="4bit 양자화 로드"
    )


class OllamaConfig(LLMConfig):
    """Ollama 설정."""

    provider: LLMProvider = LLMProvider.OLLAMA
    model_name: str = Field(
        default="llama2",
        description="Ollama 모델 이름"
    )
    base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama 서버 URL"
    )

