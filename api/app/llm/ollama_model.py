"""Ollama 모델 래퍼."""

import asyncio
from typing import Any

from .base import BaseLLM
from .config import OllamaConfig


class OllamaLLM(BaseLLM):
    """Ollama LLM 클래스.

    사용 예시:
        config = OllamaConfig(model_name="llama2", base_url="http://localhost:11434")
        llm = OllamaLLM(config)
        llm.load()
        response = llm.generate("안녕하세요")
    """

    def __init__(self, config: OllamaConfig) -> None:
        """Ollama LLM 초기화.

        Args:
            config: Ollama 설정
        """
        super().__init__(model_name=config.model_name)
        self.config = config

    def load(self) -> None:
        """Ollama LLM 인스턴스를 생성합니다.

        langchain-community 필요:
            pip install langchain-community
        """
        # TODO: 사용자가 직접 구현하거나 아래 코드 활성화
        #
        # from langchain_community.llms import Ollama
        #
        # self._model = Ollama(
        #     model=self.config.model_name,
        #     base_url=self.config.base_url,
        #     temperature=self.config.temperature,
        # )
        raise NotImplementedError("load() 메서드를 구현해주세요.")

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """텍스트를 생성합니다.

        Args:
            prompt: 입력 프롬프트
            **kwargs: 생성 옵션

        Returns:
            생성된 텍스트
        """
        if not self.is_loaded:
            self.load()

        return self._model.invoke(prompt)

    async def agenerate(self, prompt: str, **kwargs: Any) -> str:
        """비동기로 텍스트를 생성합니다.

        Args:
            prompt: 입력 프롬프트
            **kwargs: 생성 옵션

        Returns:
            생성된 텍스트
        """
        if not self.is_loaded:
            self.load()

        return await self._model.ainvoke(prompt)

    def to_langchain(self) -> Any:
        """LangChain 호환 LLM 객체로 변환.

        Returns:
            Ollama 인스턴스
        """
        if not self.is_loaded:
            self.load()
        return self._model

