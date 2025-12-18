# LangChain RAG Chatbot 프로젝트

RAG(Retrieval-Augmented Generation) 방식의 챗봇 애플리케이션입니다.

## 📋 프로젝트 구조

```
langchain/
├── ui/                    # Next.js 프론트엔드
│   ├── app/
│   ├── components/
│   └── package.json
├── api_server.py          # FastAPI 백엔드 서버
├── api_requirements.txt   # 백엔드 의존성
├── app.py                # 기존 LangChain 앱
├── .env                  # 환경변수 (OPENAI_API_KEY 포함)
└── Docker-compose.yaml   # Docker 설정
```

## 🚀 시작하기

### 1. 환경변수 설정

루트 디렉토리에 `.env` 파일을 생성하고 다음을 추가하세요:

```env
OPENAI_API_KEY=your_openai_api_key_here
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=postgres
```

### 2. 백엔드 서버 실행

```bash
# 의존성 설치
pip install -r api_requirements.txt

# 서버 실행
python api_server.py
```

서버는 `http://localhost:8000`에서 실행됩니다.

### 3. 프론트엔드 실행

```bash
cd ui
npm install
npm run dev
```

프론트엔드는 `http://localhost:3000`에서 실행됩니다.

## 🔧 Docker Compose로 전체 실행

```bash
# 모든 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

## 📝 API 엔드포인트

### POST /api/chat

챗봇에 메시지를 보냅니다.

**Request:**
```json
{
  "message": "벡터 검색이란 무엇인가요?",
  "history": [
    {"role": "user", "content": "안녕하세요"},
    {"role": "assistant", "content": "안녕하세요! 무엇을 도와드릴까요?"}
  ]
}
```

**Response:**
```json
{
  "response": "벡터 검색은 의미 기반 유사도 검색을 가능하게 합니다..."
}
```

### GET /health

서버 상태를 확인합니다.

**Response:**
```json
{
  "status": "healthy",
  "vectorstore_connected": true
}
```

## 🎯 RAG 동작 방식

1. **사용자 질문 입력** → 프론트엔드
2. **질문을 백엔드로 전송** → API 서버
3. **벡터 검색** → pgvector에서 관련 문서 검색
4. **컨텍스트 구성** → 검색된 문서 + 질문
5. **LLM 응답 생성** → OpenAI GPT 모델
6. **응답 반환** → 프론트엔드에 표시

## 🔍 문제 해결

### 벡터스토어 연결 실패

- PostgreSQL이 실행 중인지 확인
- `DB_HOST`, `DB_PORT` 등 환경변수 확인
- pgvector 확장이 설치되어 있는지 확인

### OpenAI API 오류

- `.env` 파일에 `OPENAI_API_KEY`가 올바르게 설정되었는지 확인
- API 키가 유효한지 확인
- API 사용량 제한 확인

### CORS 오류

- `api_server.py`의 `allow_origins`에 프론트엔드 URL이 포함되어 있는지 확인

## 📚 참고 자료

- [LangChain 문서](https://python.langchain.com/)
- [Next.js 문서](https://nextjs.org/docs)
- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [OpenAI API 문서](https://platform.openai.com/docs)


