"""의존성 주입 모듈."""

from typing import Any, Optional

from langchain_community.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings

from .config import settings
from ..data.documents import RAG_DOCUMENTS

# 벡터스토어 캐시
_vectorstore: Optional[PGVector] = None

# LLM 캐시
_llm: Optional[Any] = None

# QLoRA 서비스 캐시
_qlora_service: Optional[Any] = None


def get_embeddings() -> OpenAIEmbeddings:
    """OpenAI 임베딩 인스턴스 반환.

    OpenAI API를 사용하여 텍스트 임베딩 생성.
    """
    return OpenAIEmbeddings(
        model=settings.OPENAI_EMBEDDING_MODEL,
        openai_api_key=settings.OPENAI_API_KEY,
    )


def get_vectorstore() -> Optional[PGVector]:
    """PGVector 벡터스토어를 초기화하고 반환합니다.

    Returns:
        초기화된 PGVector 인스턴스 또는 None
    """
    global _vectorstore

    if _vectorstore is not None:
        return _vectorstore

    try:
        embeddings = get_embeddings()
        _vectorstore = PGVector.from_documents(
            documents=RAG_DOCUMENTS,
            embedding=embeddings,
            connection_string=settings.database_url,
            use_jsonb=True,
        )
        print("✅ 벡터스토어 초기화 성공!")
        return _vectorstore
    except Exception as e:
        print(f"⚠️ 벡터스토어 초기화 실패: {e}")
        return None


def reset_vectorstore() -> None:
    """벡터스토어 캐시 초기화."""
    global _vectorstore
    _vectorstore = None


def get_llm() -> Any:
    """LLM 인스턴스를 반환합니다.

    설정에 따라 로컬 모델 또는 OpenAI를 사용합니다.

    Returns:
        LangChain 호환 LLM 인스턴스
    """
    global _llm

    if _llm is not None:
        return _llm

    if settings.is_local_llm:
        # 로컬 Mi:dm 모델 사용
        from ..llm.config import LocalModelConfig
        from ..llm.local_model import LocalLLM

        config = LocalModelConfig(
            model_path=settings.LOCAL_MODEL_PATH,
            device=settings.LOCAL_MODEL_DEVICE,
            max_tokens=settings.LOCAL_MODEL_MAX_NEW_TOKENS,
            temperature=settings.LOCAL_MODEL_TEMPERATURE,
            torch_dtype="bfloat16",  # Mi:dm은 bfloat16 사용
            trust_remote_code=False,
        )
        local_llm = LocalLLM(config)
        local_llm.load()
        _llm = local_llm.to_langchain()
        print(f"✅ 로컬 LLM 로드 완료: {settings.LOCAL_MODEL_PATH}")
    else:
        # OpenAI 사용
        from langchain_openai import ChatOpenAI

        _llm = ChatOpenAI(
            model_name=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE,
            openai_api_key=settings.OPENAI_API_KEY,
        )
        print(f"✅ OpenAI LLM 초기화: {settings.OPENAI_MODEL}")

    return _llm


def reset_llm() -> None:
    """LLM 캐시 초기화."""
    global _llm
    _llm = None


def get_qlora_service() -> Optional[Any]:
    """QLoRA 서비스 인스턴스를 반환합니다.

    Returns:
        QLoRAService 인스턴스 또는 None
    """
    global _qlora_service
    return _qlora_service


def set_qlora_service(service: Any) -> None:
    """QLoRA 서비스 인스턴스를 설정합니다.

    Args:
        service: QLoRAService 인스턴스
    """
    global _qlora_service
    _qlora_service = service


def reset_qlora_service() -> None:
    """QLoRA 서비스 캐시 초기화."""
    global _qlora_service
    if _qlora_service is not None:
        try:
            _qlora_service.unload()
        except Exception:
            pass
    _qlora_service = None
