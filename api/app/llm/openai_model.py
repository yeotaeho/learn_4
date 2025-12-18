"""OpenAI 모델 래퍼."""

import asyncio
from typing import Any

from langchain_openai import ChatOpenAI

from .base import BaseLLM
from .config import OpenAIConfig


class OpenAILLM(BaseLLM):
    """OpenAI LLM 클래스.

    사용 예시:
        config = OpenAIConfig(api_key="sk-...", model_name="gpt-3.5-turbo")
        llm = OpenAILLM(config)
        llm.load()
        response = llm.generate("안녕하세요")
    """

    def __init__(self, config: OpenAIConfig) -> None:
        """OpenAI LLM 초기화.

        Args:
            config: OpenAI 설정
        """
        super().__init__(model_name=config.model_name)
        self.config = config
        self._chat_model: ChatOpenAI | None = None

    def load(self) -> None:
        """ChatOpenAI 인스턴스를 생성합니다."""
        self._chat_model = ChatOpenAI(
            model_name=self.config.model_name,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            openai_api_key=self.config.api_key,
        )
        self._model = self._chat_model  # is_loaded 체크용

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

        response = self._chat_model.invoke(prompt)
        return response.content

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

        response = await self._chat_model.ainvoke(prompt)
        return response.content

    def to_langchain(self) -> ChatOpenAI:
        """LangChain 호환 LLM 객체로 변환.

        Returns:
            ChatOpenAI 인스턴스
        """
        if not self.is_loaded:
            self.load()
        return self._chat_model

