"""챗봇 관련 Pydantic 모델."""

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """채팅 메시지 모델."""

    role: str = Field(..., description="메시지 역할 (user 또는 assistant)")
    content: str = Field(..., description="메시지 내용")


class ChatRequest(BaseModel):
    """챗봇 요청 모델."""

    message: str = Field(..., description="사용자 메시지")
    history: list[ChatMessage] = Field(
        default_factory=list,
        description="이전 대화 기록"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "벡터 검색이란 무엇인가요?",
                "history": [
                    {"role": "user", "content": "안녕하세요"},
                    {"role": "assistant", "content": "안녕하세요! 무엇을 도와드릴까요?"}
                ]
            }
        }


class ChatResponse(BaseModel):
    """챗봇 응답 모델."""

    response: str = Field(..., description="챗봇 응답")

    class Config:
        json_schema_extra = {
            "example": {
                "response": "벡터 검색은 의미 기반 유사도 검색을 가능하게 합니다."
            }
        }


class HealthResponse(BaseModel):
    """헬스체크 응답 모델."""

    status: str = Field(..., description="서버 상태")
    vectorstore_connected: bool = Field(..., description="벡터스토어 연결 상태")


class TrainingDataItem(BaseModel):
    """학습 데이터 항목."""

    instruction: str = Field(..., description="지시사항")
    input: str = Field(default="", description="입력 (선택사항)")
    output: str = Field(..., description="출력")


class TrainingRequest(BaseModel):
    """QLoRA 파인튜닝 요청 모델."""

    training_data: list[TrainingDataItem] = Field(..., description="학습 데이터")
    output_dir: str = Field(..., description="모델 저장 경로")
    num_epochs: int = Field(default=3, description="학습 에포크 수")
    per_device_train_batch_size: int = Field(default=4, description="디바이스당 배치 크기")
    gradient_accumulation_steps: int = Field(default=4, description="그래디언트 누적 스텝")
    learning_rate: float = Field(default=2e-4, description="학습률")
    warmup_steps: int = Field(default=100, description="워밍업 스텝")
    logging_steps: int = Field(default=10, description="로깅 간격")
    save_steps: int = Field(default=500, description="저장 간격")
    max_seq_length: int = Field(default=2048, description="최대 시퀀스 길이")


class TrainingResponse(BaseModel):
    """QLoRA 파인튜닝 응답 모델."""

    status: str = Field(..., description="학습 상태")
    message: str = Field(..., description="상세 메시지")
    output_dir: str = Field(..., description="모델 저장 경로")
