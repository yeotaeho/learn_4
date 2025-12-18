# LangChain RAG Chatbot API

FastAPI 기반 RAG(Retrieval-Augmented Generation) 챗봇 API 서버입니다.

## 📁 프로젝트 구조

```
api/
├── app/
│   ├── __init__.py           # 패키지 초기화
│   ├── main.py               # FastAPI 앱 팩토리
│   ├── core/                 # 핵심 설정
│   │   ├── __init__.py
│   │   ├── config.py         # 환경변수 및 설정
│   │   └── deps.py           # 의존성 주입
│   ├── data/                 # 데이터 모듈
│   │   ├── __init__.py
│   │   └── documents.py      # RAG 문서 데이터
│   ├── models/               # Pydantic 모델
│   │   ├── __init__.py
│   │   └── chat.py           # 채팅 스키마
│   ├── routers/              # API 라우터
│   │   ├── __init__.py
│   │   └── chat.py           # 채팅 엔드포인트
│   └── services/             # 비즈니스 로직
│       ├── __init__.py
│       └── rag.py            # RAG 서비스
├── run.py                    # 실행 스크립트
├── requirements.txt          # 의존성
└── README.md
```

## 🚀 시작하기

### 1. 환경 설정

루트 디렉토리에 `.env` 파일 생성:

```env
OPENAI_API_KEY=your_openai_api_key_here
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=postgres
```

### 2. 의존성 설치

```bash
cd api
pip install -r requirements.txt
```

### 3. 서버 실행

```bash
# 방법 1: run.py 사용 (개발 모드, 자동 리로드)
python run.py

# 방법 2: uvicorn 직접 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

서버: http://localhost:8000

## 📝 API 문서

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔌 API 엔드포인트

### GET /
루트 엔드포인트 - 서버 정보 반환

### GET /api/health
헬스체크 - 서버 및 벡터스토어 상태 확인

### POST /api/chat
RAG 챗봇 응답 생성

**Request:**
```json
{
  "message": "벡터 검색이란 무엇인가요?",
  "history": []
}
```

**Response:**
```json
{
  "response": "벡터 검색은 의미 기반 유사도 검색을 가능하게 합니다..."
}
```

## 🏗️ 아키텍처

```
[클라이언트 요청]
       ↓
[main.py] FastAPI 앱
       ↓
[routers/chat.py] 라우터
       ↓
[services/rag.py] RAG 서비스
       ↓
[core/deps.py] 벡터스토어
       ↓
[PostgreSQL + pgvector]
       ↓
[OpenAI GPT] → 응답 생성
```

## 🔧 설정 커스터마이징

`app/core/config.py`에서 설정 변경:

```python
class Settings(BaseSettings):
    OPENAI_MODEL: str = "gpt-4o"  # 모델 변경
    OPENAI_TEMPERATURE: float = 0.5  # 온도 조정
```

## 📚 주요 기술 스택

- **FastAPI**: 고성능 웹 프레임워크
- **LangChain**: LLM 애플리케이션 프레임워크
- **OpenAI**: GPT 모델 및 임베딩
- **PostgreSQL + pgvector**: 벡터 데이터베이스
- **Pydantic**: 데이터 검증

