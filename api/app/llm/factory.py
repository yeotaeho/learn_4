"""LLM 팩토리 - 모델 인스턴스 생성 및 관리."""

from typing import Optional, Union

from .base import BaseLLM
from .config import (
    LLMConfig,
    LLMProvider,
    LocalModelConfig,
    OllamaConfig,
    OpenAIConfig,
)
from .local_model import LocalLLM
from .ollama_model import OllamaLLM
from .openai_model import OpenAILLM

# 전역 LLM 인스턴스 캐시
_llm_instance: Optional[BaseLLM] = None


class LLMFactory:
    """LLM 팩토리 클래스.

    사용 예시:
        # OpenAI
        config = OpenAIConfig(api_key="sk-...")
        llm = LLMFactory.create(config)

        # 로컬 모델
        config = LocalModelConfig(model_path="./model_weights/my-model")
        llm = LLMFactory.create(config)
    """

    @staticmethod
    def create(
        config: Union[OpenAIConfig, LocalModelConfig, OllamaConfig]
    ) -> BaseLLM:
        """설정에 따라 적절한 LLM 인스턴스를 생성합니다.

        Args:
            config: LLM 설정 객체

        Returns:
            BaseLLM 구현체 인스턴스

        Raises:
            ValueError: 지원하지 않는 provider인 경우
        """
        if config.provider == LLMProvider.OPENAI:
            if not isinstance(config, OpenAIConfig):
                msg = "OpenAI provider는 OpenAIConfig가 필요합니다."
                raise ValueError(msg)
            return OpenAILLM(config)

        elif config.provider == LLMProvider.LOCAL:
            if not isinstance(config, LocalModelConfig):
                msg = "Local provider는 LocalModelConfig가 필요합니다."
                raise ValueError(msg)
            return LocalLLM(config)

        elif config.provider == LLMProvider.OLLAMA:
            if not isinstance(config, OllamaConfig):
                msg = "Ollama provider는 OllamaConfig가 필요합니다."
                raise ValueError(msg)
            return OllamaLLM(config)

        else:
            msg = f"지원하지 않는 LLM provider입니다: {config.provider}"
            raise ValueError(msg)


def get_llm() -> Optional[BaseLLM]:
    """전역 LLM 인스턴스를 반환합니다.

    Returns:
        캐시된 LLM 인스턴스 또는 None
    """
    return _llm_instance


def set_llm(llm: BaseLLM) -> None:
    """전역 LLM 인스턴스를 설정합니다.

    Args:
        llm: 설정할 LLM 인스턴스
    """
    global _llm_instance
    _llm_instance = llm


def reset_llm() -> None:
    """전역 LLM 인스턴스를 초기화합니다."""
    global _llm_instance
    if _llm_instance is not None:
        _llm_instance.unload()
    _llm_instance = None

