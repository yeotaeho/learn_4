"""LLM 기본 인터페이스 정의."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseLLM(ABC):
    """LLM 추상 기본 클래스.

    모든 LLM 구현체는 이 클래스를 상속받아야 합니다.
    """

    def __init__(self, model_name: str, **kwargs: Any) -> None:
        """LLM 초기화.

        Args:
            model_name: 모델 이름 또는 경로
            **kwargs: 추가 설정
        """
        self.model_name = model_name
        self._model: Optional[Any] = None
        self._tokenizer: Optional[Any] = None

    @abstractmethod
    def load(self) -> None:
        """모델을 메모리에 로드합니다."""
        pass

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> str:
        """텍스트를 생성합니다.

        Args:
            prompt: 입력 프롬프트
            **kwargs: 생성 옵션 (temperature, max_tokens 등)

        Returns:
            생성된 텍스트
        """
        pass

    @abstractmethod
    async def agenerate(self, prompt: str, **kwargs: Any) -> str:
        """비동기로 텍스트를 생성합니다.

        Args:
            prompt: 입력 프롬프트
            **kwargs: 생성 옵션

        Returns:
            생성된 텍스트
        """
        pass

    @property
    def is_loaded(self) -> bool:
        """모델이 로드되었는지 확인."""
        return self._model is not None

    def unload(self) -> None:
        """모델을 메모리에서 해제합니다."""
        self._model = None
        self._tokenizer = None

    def to_langchain(self) -> Any:
        """LangChain 호환 LLM 객체로 변환.

        Returns:
            LangChain LLM 인스턴스
        """
        raise NotImplementedError("LangChain 변환이 구현되지 않았습니다.")

