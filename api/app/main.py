"""FastAPI 애플리케이션 메인 모듈."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .core.deps import (
    get_llm,
    get_vectorstore,
    reset_llm,
    reset_vectorstore,
    set_qlora_service,
    reset_qlora_service,
)
from .routers import chat_router
from .services.rag import QLoRAService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리.

    시작 시 벡터스토어/LLM 초기화, 종료 시 정리.
    """
    # 시작 시
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 시작...")
    print(f"📦 LLM Provider: {settings.LLM_PROVIDER}")

    # 설정 검증
    settings.validate_config()

    # 벡터스토어 초기화 (미리 로드)
    get_vectorstore()

    # LLM 초기화 (미리 로드)
    get_llm()

    # QLoRA 서비스 초기화 (로컬 모델 사용 시에만)
    if settings.is_local_llm:
        try:
            print("🔄 QLoRA 서비스 초기화 중...", flush=True)
            qlora_service = QLoRAService(
                model_path=settings.LOCAL_MODEL_PATH,
                adapter_path=None,
                device=settings.LOCAL_MODEL_DEVICE,
            )
            # 모델 로드 (출력이 나오도록)
            qlora_service._load_model()
            set_qlora_service(qlora_service)
            print("✅ QLoRA 서비스 초기화 완료", flush=True)

        except Exception as e:
            print(f"⚠️ QLoRA 서비스 초기화 실패: {e}", flush=True)
            print("   QLoRA 기능은 사용할 수 없습니다.", flush=True)
            set_qlora_service(None)
    else:
        print("ℹ️  QLoRA 서비스는 로컬 모델 사용 시에만 사용 가능합니다.", flush=True)
        set_qlora_service(None)

    yield

    # 종료 시
    print("👋 서버를 종료합니다...")
    reset_qlora_service()
    reset_llm()
    reset_vectorstore()


def create_app() -> FastAPI:
    """FastAPI 애플리케이션 팩토리.

    Returns:
        구성된 FastAPI 인스턴스
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="RAG 방식의 챗봇 API 서버 (OpenAI 및 로컬 LLM 지원)",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS 미들웨어 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 라우터 등록
    app.include_router(chat_router)

    # 루트 엔드포인트
    @app.get("/", tags=["root"])
    def root():
        """루트 엔드포인트."""
        return {
            "message": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "running",
            "llm_provider": settings.LLM_PROVIDER,
            "docs": "/docs",
        }

    return app


# 애플리케이션 인스턴스
app = create_app()
