"""로컬 HuggingFace 모델 로더 - Mi:dm 2.0 Mini 지원."""

import asyncio
from typing import Any, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

from .base import BaseLLM
from .config import LocalModelConfig


class LocalLLM(BaseLLM):
    """로컬 HuggingFace 모델 클래스.

    Mi:dm 2.0 Mini 및 LlamaForCausalLM 기반 모델 지원.

    사용 예시:
        config = LocalModelConfig(model_path="./model_weights")
        llm = LocalLLM(config)
        llm.load()
        response = llm.generate("안녕하세요")
    """

    def __init__(self, config: LocalModelConfig) -> None:
        """로컬 LLM 초기화.

        Args:
            config: 로컬 모델 설정
        """
        super().__init__(model_name=config.model_path)
        self.config = config
        self._pipeline: Optional[Any] = None

    def load(self) -> None:
        """모델을 메모리에 로드합니다."""
        print(f"🔄 모델 로딩 중: {self.config.model_path}")

        # 디바이스 설정
        if self.config.device == "auto":
            device_map = "auto"
        elif self.config.device == "cuda":
            device_map = "cuda:0"
        else:
            device_map = "cpu"

        # torch dtype 설정
        if self.config.torch_dtype == "float16":
            torch_dtype = torch.float16
        elif self.config.torch_dtype == "bfloat16":
            torch_dtype = torch.bfloat16
        else:
            torch_dtype = torch.float32

        # 토크나이저 로드
        self._tokenizer = AutoTokenizer.from_pretrained(
            self.config.model_path,
            trust_remote_code=self.config.trust_remote_code,
        )

        # 패딩 토큰 설정 (없으면 EOS 토큰 사용)
        if self._tokenizer.pad_token is None:
            self._tokenizer.pad_token = self._tokenizer.eos_token

        # 모델 로드
        load_kwargs = {
            "pretrained_model_name_or_path": self.config.model_path,
            "trust_remote_code": self.config.trust_remote_code,
            "torch_dtype": torch_dtype,
        }

        # 양자화 설정
        if self.config.load_in_4bit:
            from transformers import BitsAndBytesConfig
            load_kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch_dtype,
            )
        elif self.config.load_in_8bit:
            from transformers import BitsAndBytesConfig
            load_kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_8bit=True,
            )
        else:
            load_kwargs["device_map"] = device_map

        self._model = AutoModelForCausalLM.from_pretrained(**load_kwargs)

        # 파이프라인 생성
        self._pipeline = pipeline(
            "text-generation",
            model=self._model,
            tokenizer=self._tokenizer,
            max_new_tokens=self.config.max_tokens,
            do_sample=True,
            temperature=self.config.temperature,
            top_p=0.9,
            repetition_penalty=1.1,
            pad_token_id=self._tokenizer.pad_token_id,
        )

        print(f"✅ 모델 로드 완료: {self.config.model_path}")

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

        # 생성 파라미터 오버라이드
        max_new_tokens = kwargs.get("max_tokens", self.config.max_tokens)
        temperature = kwargs.get("temperature", self.config.temperature)

        # 파이프라인 실행
        outputs = self._pipeline(
            prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            return_full_text=False,  # 프롬프트 제외하고 생성된 텍스트만 반환
        )

        return outputs[0]["generated_text"].strip()

    async def agenerate(self, prompt: str, **kwargs: Any) -> str:
        """비동기로 텍스트를 생성합니다.

        Args:
            prompt: 입력 프롬프트
            **kwargs: 생성 옵션

        Returns:
            생성된 텍스트
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.generate(prompt, **kwargs)
        )

    def to_langchain(self) -> Any:
        """LangChain 호환 LLM 객체로 변환.

        Returns:
            LangChain HuggingFacePipeline 인스턴스
        """
        if not self.is_loaded:
            self.load()

        from langchain_huggingface import HuggingFacePipeline

        return HuggingFacePipeline(pipeline=self._pipeline)

    def unload(self) -> None:
        """모델을 메모리에서 해제합니다."""
        if self._model is not None:
            del self._model
            del self._tokenizer
            del self._pipeline

            # GPU 메모리 정리
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            self._model = None
            self._tokenizer = None
            self._pipeline = None
            print("🗑️ 모델 메모리 해제 완료")
