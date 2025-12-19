"""RAG 서비스 - LangChain RAG 체인 관리."""

import asyncio
import os
from pathlib import Path
from typing import Any, Optional

# QLoRA 관련 import는 조건부로 처리 (OpenAI 사용 시 불필요)
try:
    import torch
    from datasets import Dataset
    from peft import LoraConfig, PeftModel, get_peft_model, prepare_model_for_kbit_training
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        TrainingArguments,
        Trainer,
        DataCollatorForLanguageModeling,
    )
    QLORA_AVAILABLE = True
except ImportError:
    QLORA_AVAILABLE = False
    # QLoRA 관련 타입 힌트를 위한 더미 클래스
    torch = None  # type: ignore
    Dataset = None  # type: ignore
    LoraConfig = None  # type: ignore
    PeftModel = None  # type: ignore
    get_peft_model = None  # type: ignore
    prepare_model_for_kbit_training = None  # type: ignore
    AutoModelForCausalLM = None  # type: ignore
    AutoTokenizer = None  # type: ignore
    BitsAndBytesConfig = None  # type: ignore
    TrainingArguments = None  # type: ignore
    Trainer = None  # type: ignore
    DataCollatorForLanguageModeling = None  # type: ignore

from langchain_community.vectorstores import PGVector
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough

from ..core.config import settings
from ..core.deps import get_llm


class RAGService:
    """RAG(Retrieval-Augmented Generation) 서비스 클래스.

    로컬 LLM 또는 OpenAI를 사용하여 RAG 기반 응답을 생성합니다.
    """

    # RAG 프롬프트 템플릿 (로컬 모델용으로 최적화) - 추후 사용 예정
    # RAG_TEMPLATE = """다음 문맥을 기반으로 질문에 답하세요.
    # 문맥에 없는 정보는 추측하지 마세요.
    # 답변은 한국어로 간결하게 작성하세요.
    #
    # 문맥:
    # {context}
    #
    # 질문: {question}
    #
    # 답변:"""

    def __init__(self, vectorstore: PGVector, llm: Any = None) -> None:
        """RAG 서비스 초기화.

        Args:
            vectorstore: PGVector 벡터스토어 인스턴스
            llm: LangChain 호환 LLM 인스턴스 (None이면 자동 로드)
        """
        self.vectorstore = vectorstore
        self.llm = llm or get_llm()
        self.chain = self._create_chain()

    # 추후 사용 예정 - 프롬프트 템플릿 생성
    # def _create_prompt(self) -> PromptTemplate:
    #     """프롬프트 템플릿 생성."""
    #     return PromptTemplate(
    #         template=self.RAG_TEMPLATE,
    #         input_variables=["context", "question"],
    #     )

    # 추후 사용 예정 - 문서 포맷팅
    # @staticmethod
    # def _format_docs(docs: list) -> str:
    #     """검색된 문서들을 문자열로 변환.
    #
    #     Args:
    #         docs: 검색된 문서 리스트
    #
    #     Returns:
    #         포맷된 문서 문자열
    #     """
    #     if not docs:
    #         return "관련 문서를 찾을 수 없습니다."
    #     return "\n\n".join(doc.page_content for doc in docs)

    def _create_chain(self):
        """체인 생성 - 현재는 프롬프트와 문맥 없이 사용자 메시지만 전달."""
        # 추후 사용 예정 - RAG 체인 (프롬프트와 문맥 포함)
        # retriever = self.vectorstore.as_retriever(
        #     search_type="similarity",
        #     search_kwargs={"k": 3}
        # )
        #
        # prompt = self._create_prompt()
        #
        # chain = (
        #     {
        #         "context": retriever | self._format_docs,
        #         "question": RunnablePassthrough(),
        #     }
        #     | prompt
        #     | self.llm
        #     | StrOutputParser()
        # )

        # 현재: 프롬프트와 문맥 없이 사용자 메시지만 LLM에 전달
        chain = (
            RunnablePassthrough()
            | self.llm
            | StrOutputParser()
        )

        return chain

    def chat(self, message: str) -> str:
        """사용자 메시지에 대한 RAG 응답 생성.

        Args:
            message: 사용자 메시지

        Returns:
            RAG 기반 응답 문자열
        """
        return self.chain.invoke(message)

    async def achat(self, message: str) -> str:
        """비동기 RAG 응답 생성.

        Args:
            message: 사용자 메시지

        Returns:
            RAG 기반 응답 문자열
        """
        return await self.chain.ainvoke(message)


class QLoRAService:
    """QLoRA 기반 모델 서비스 클래스.

    PEFT의 QLoRA 방식을 사용하여 모델을 양자화하고 LoRA 어댑터를 추가합니다.
    대화 및 파인튜닝 기능을 제공합니다.
    """

    def __init__(
        self,
        model_path: str,
        adapter_path: Optional[str] = None,
        device: str = "cuda",
        lora_r: int = 16,
        lora_alpha: int = 32,
        lora_dropout: float = 0.05,
        target_modules: Optional[list[str]] = None,
    ) -> None:
        """QLoRA 서비스 초기화.

        Args:
            model_path: 베이스 모델 경로
            adapter_path: LoRA 어댑터 경로 (None이면 새로 학습)
            device: 사용할 디바이스 (cuda, cpu, auto)
            lora_r: LoRA rank
            lora_alpha: LoRA alpha
            lora_dropout: LoRA dropout
            target_modules: LoRA를 적용할 모듈 리스트 (None이면 자동 감지)
        """
        self.model_path = model_path
        self.adapter_path = adapter_path
        self.device = device
        self.lora_r = lora_r
        self.lora_alpha = lora_alpha
        self.lora_dropout = lora_dropout
        self.target_modules = target_modules

        self.model: Optional[Any] = None  # AutoModelForCausalLM 타입 힌트 (조건부 import)
        self.tokenizer: Optional[Any] = None  # AutoTokenizer 타입 힌트 (조건부 import)
        self._is_loaded = False

    def _load_model(self) -> None:
        """QLoRA 모델 로드."""
        if not QLORA_AVAILABLE:
            raise ImportError(
                "QLoRA 기능을 사용하려면 torch, transformers, peft, datasets 패키지가 필요합니다. "
                "pip install torch transformers peft datasets bitsandbytes"
            )
        if self._is_loaded:
            return

        print(f"🔄 QLoRA 모델 로딩 중: {self.model_path}")

        # 디바이스 설정
        if not QLORA_AVAILABLE or torch is None:
            raise ImportError("torch가 설치되지 않았습니다.")
        if self.device == "auto":
            device_map = "auto"
        elif self.device == "cuda" and torch.cuda.is_available():
            device_map = "cuda:0"
        else:
            device_map = "cpu"

        # 4-bit 양자화 설정
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
        )

        # 토크나이저 로드
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path,
            trust_remote_code=False,
        )

        # 패딩 토큰 설정
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

        # 모델 로드 (4-bit 양자화)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            quantization_config=bnb_config,
            device_map=device_map,
            trust_remote_code=False,
            torch_dtype=torch.bfloat16,
        )

        # LoRA 설정
        if self.target_modules is None:
            # 일반적인 모델 구조에 맞춰 자동 설정
            self.target_modules = ["q_proj", "k_proj", "v_proj", "o_proj"]

        lora_config = LoraConfig(
            r=self.lora_r,
            lora_alpha=self.lora_alpha,
            target_modules=self.target_modules,
            lora_dropout=self.lora_dropout,
            bias="none",
            task_type="CAUSAL_LM",
        )

        # 기존 어댑터가 있으면 로드, 없으면 새로 생성
        if self.adapter_path and Path(self.adapter_path).exists():
            print(f"📂 기존 LoRA 어댑터 로드: {self.adapter_path}")
            # 양자화된 모델 준비
            self.model = prepare_model_for_kbit_training(self.model)
            # 기존 어댑터 로드
            self.model = PeftModel.from_pretrained(
                self.model,
                self.adapter_path,
            )
        else:
            # 양자화된 모델 준비
            self.model = prepare_model_for_kbit_training(self.model)
            # 새 LoRA 어댑터 추가
            self.model = get_peft_model(self.model, lora_config)
            print("✅ 새 LoRA 어댑터 생성 완료")

        self._is_loaded = True
        print(f"✅ QLoRA 모델 로드 완료: {self.model_path}")

    def chat(self, message: str, max_new_tokens: int = 512, temperature: float = 0.7) -> str:
        """QLoRA 모델로 대화 생성.

        Args:
            message: 사용자 메시지
            max_new_tokens: 최대 생성 토큰 수
            temperature: 생성 온도

        Returns:
            생성된 응답 문자열
        """
        if not self._is_loaded:
            self._load_model()

        # 토큰화
        inputs = self.tokenizer(
            message,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=2048,
        )

        # 디바이스로 이동
        if not QLORA_AVAILABLE or torch is None:
            raise ImportError("torch가 설치되지 않았습니다.")
        if self.device == "cuda" and torch.cuda.is_available():
            inputs = {k: v.to("cuda") for k, v in inputs.items()}

        # 생성
        self.model.eval()
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.1,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )

        # 디코딩 (입력 프롬프트 제외하고 생성된 부분만)
        input_length = inputs["input_ids"].shape[1]
        generated_text = self.tokenizer.decode(
            outputs[0][input_length:],
            skip_special_tokens=True,
        )

        return generated_text.strip()

    async def achat(self, message: str, max_new_tokens: int = 512, temperature: float = 0.7) -> str:
        """비동기 QLoRA 모델로 대화 생성.

        Args:
            message: 사용자 메시지
            max_new_tokens: 최대 생성 토큰 수
            temperature: 생성 온도

        Returns:
            생성된 응답 문자열
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.chat(message, max_new_tokens, temperature)
        )

    def train(
        self,
        training_data: list[dict[str, str]],
        output_dir: str,
        num_epochs: int = 3,
        per_device_train_batch_size: int = 4,
        gradient_accumulation_steps: int = 4,
        learning_rate: float = 2e-4,
        warmup_steps: int = 100,
        logging_steps: int = 10,
        save_steps: int = 500,
        max_seq_length: int = 2048,
    ) -> None:
        """QLoRA 방식으로 모델 파인튜닝.

        Args:
            training_data: 학습 데이터 리스트 [{"instruction": "...", "input": "...", "output": "..."}]
            output_dir: 모델 저장 경로
            num_epochs: 학습 에포크 수
            per_device_train_batch_size: 디바이스당 배치 크기
            gradient_accumulation_steps: 그래디언트 누적 스텝
            learning_rate: 학습률
            warmup_steps: 워밍업 스텝
            logging_steps: 로깅 간격
            save_steps: 저장 간격
            max_seq_length: 최대 시퀀스 길이
        """
        if not self._is_loaded:
            self._load_model()

        print(f"🚀 QLoRA 파인튜닝 시작...", flush=True)
        print(f"📊 학습 데이터 수: {len(training_data)}", flush=True)

        # 데이터 포맷팅
        def format_prompt(example: dict[str, str]) -> dict[str, str]:
            """프롬프트 포맷팅."""
            instruction = example.get("instruction", "")
            input_text = example.get("input", "")
            output = example.get("output", "")

            if input_text:
                prompt = f"### Instruction:\n{instruction}\n\n### Input:\n{input_text}\n\n### Response:\n{output}"
            else:
                prompt = f"### Instruction:\n{instruction}\n\n### Response:\n{output}"

            return {"text": prompt}

        # 데이터셋 생성
        if not QLORA_AVAILABLE or Dataset is None:
            raise ImportError("datasets 패키지가 설치되지 않았습니다.")
        dataset = Dataset.from_list(training_data)
        dataset = dataset.map(format_prompt)

        # 토큰화 함수
        def tokenize_function(examples: dict[str, list[str]]) -> dict[str, list[list[int]]]:
            """토큰화 함수."""
            return self.tokenizer(
                examples["text"],
                truncation=True,
                max_length=max_seq_length,
                padding="max_length",
            )

        tokenized_dataset = dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=dataset.column_names,
        )

        # 데이터 콜레이터
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False,
        )

        # 학습 인자 설정
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=num_epochs,
            per_device_train_batch_size=per_device_train_batch_size,
            gradient_accumulation_steps=gradient_accumulation_steps,
            learning_rate=learning_rate,
            warmup_steps=warmup_steps,
            logging_steps=logging_steps,
            save_steps=save_steps,
            save_total_limit=3,
            fp16=True,
            optim="paged_adamw_8bit",
            lr_scheduler_type="cosine",
            report_to="none",
            remove_unused_columns=False,
        )

        # 트레이너 생성
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=tokenized_dataset,
            data_collator=data_collator,
        )

        # 학습 실행
        print("📚 학습 시작...")
        trainer.train()

        # 모델 저장
        print(f"💾 모델 저장 중: {output_dir}")
        trainer.save_model()
        self.tokenizer.save_pretrained(output_dir)
        print(f"✅ 학습 완료! 모델이 저장되었습니다: {output_dir}")

    def save_adapter(self, adapter_path: str) -> None:
        """LoRA 어댑터만 저장.

        Args:
            adapter_path: 어댑터 저장 경로
        """
        if not self._is_loaded:
            raise ValueError("모델이 로드되지 않았습니다. 먼저 _load_model()을 호출하세요.")

        if not QLORA_AVAILABLE or PeftModel is None:
            raise ImportError("peft 패키지가 설치되지 않았습니다.")
        if isinstance(self.model, PeftModel):
            self.model.save_pretrained(adapter_path)
            print(f"✅ LoRA 어댑터 저장 완료: {adapter_path}")
        else:
            raise ValueError("LoRA 어댑터가 없습니다.")

    def unload(self) -> None:
        """모델을 메모리에서 해제."""
        if self.model is not None:
            del self.model
            del self.tokenizer

            if QLORA_AVAILABLE and torch is not None and torch.cuda.is_available():
                torch.cuda.empty_cache()

            self.model = None
            self.tokenizer = None
            self._is_loaded = False
            print("🗑️ QLoRA 모델 메모리 해제 완료")
