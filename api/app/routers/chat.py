"""채팅 API 라우터."""

from fastapi import APIRouter, HTTPException, BackgroundTasks

from ..core.config import settings
from ..core.deps import get_vectorstore, get_qlora_service
from ..models.chat import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    TrainingRequest,
    TrainingResponse,
)
from ..services.rag import RAGService, QLoRAService

router = APIRouter(prefix="/api", tags=["chat"])


@router.get("/health", response_model=HealthResponse)
def health_check():
    """헬스체크 엔드포인트.

    Returns:
        서버 및 벡터스토어 연결 상태
    """
    vectorstore = get_vectorstore()
    return HealthResponse(
        status="healthy",
        vectorstore_connected=vectorstore is not None,
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """RAG 방식으로 챗봇 응답을 생성합니다.

    Args:
        request: 챗봇 요청 (메시지, 히스토리)

    Returns:
        챗봇 응답

    Raises:
        HTTPException: 벡터스토어 연결 실패 또는 처리 오류
    """
    try:
        # 벡터스토어 가져오기
        vectorstore = get_vectorstore()
        if not vectorstore:
            raise HTTPException(
                status_code=503,
                detail="벡터스토어에 연결할 수 없습니다. PostgreSQL이 실행 중인지 확인하세요."
            )

        # RAG 서비스 생성 및 응답
        rag_service = RAGService(vectorstore)
        response = await rag_service.achat(request.message)

        return ChatResponse(response=response)

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"❌ 오류 발생: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"응답 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/qlora/chat", response_model=ChatResponse)
async def qlora_chat(request: ChatRequest):
    """QLoRA 모델로 챗봇 응답을 생성합니다.

    Args:
        request: 챗봇 요청 (메시지, 히스토리)

    Returns:
        챗봇 응답

    Raises:
        HTTPException: 모델 로드 실패 또는 처리 오류
    """
    try:
        # 전역 QLoRA 서비스 사용
        qlora_service = get_qlora_service()
        if qlora_service is None:
            raise HTTPException(
                status_code=503,
                detail="QLoRA 서비스가 초기화되지 않았습니다."
            )

        response = await qlora_service.achat(request.message)

        return ChatResponse(response=response)

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"❌ QLoRA 오류 발생: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"QLoRA 응답 생성 중 오류가 발생했습니다: {str(e)}"
        )


def _train_qlora_model(request: TrainingRequest) -> None:
    """백그라운드에서 QLoRA 모델 학습 실행."""
    try:
        # 전역 QLoRA 서비스 사용 또는 새로 생성
        qlora_service = get_qlora_service()
        if qlora_service is None:
            # 서비스가 없으면 새로 생성
            qlora_service = QLoRAService(
                model_path=settings.LOCAL_MODEL_PATH,
                adapter_path=None,
                device=settings.LOCAL_MODEL_DEVICE,
            )

        # 학습 데이터 포맷 변환
        training_data = [
            {
                "instruction": item.instruction,
                "input": item.input,
                "output": item.output,
            }
            for item in request.training_data
        ]

        # 학습 실행
        qlora_service.train(
            training_data=training_data,
            output_dir=request.output_dir,
            num_epochs=request.num_epochs,
            per_device_train_batch_size=request.per_device_train_batch_size,
            gradient_accumulation_steps=request.gradient_accumulation_steps,
            learning_rate=request.learning_rate,
            warmup_steps=request.warmup_steps,
            logging_steps=request.logging_steps,
            save_steps=request.save_steps,
            max_seq_length=request.max_seq_length,
        )
    except Exception as e:
        import traceback
        print(f"❌ QLoRA 학습 오류 발생: {str(e)}")
        traceback.print_exc()
        raise


@router.post("/qlora/train", response_model=TrainingResponse)
async def qlora_train(request: TrainingRequest, background_tasks: BackgroundTasks):
    """QLoRA 방식으로 모델 파인튜닝을 시작합니다.

    Args:
        request: 파인튜닝 요청
        background_tasks: 백그라운드 작업

    Returns:
        학습 시작 응답

    Raises:
        HTTPException: 요청 검증 실패
    """
    try:
        # 백그라운드에서 학습 시작
        background_tasks.add_task(_train_qlora_model, request)

        return TrainingResponse(
            status="started",
            message=f"QLoRA 파인튜닝이 시작되었습니다. 학습 데이터 수: {len(request.training_data)}",
            output_dir=request.output_dir,
        )

    except Exception as e:
        import traceback
        print(f"❌ QLoRA 학습 시작 오류: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"QLoRA 학습 시작 중 오류가 발생했습니다: {str(e)}"
        )

