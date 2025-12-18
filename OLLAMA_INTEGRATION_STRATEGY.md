# Ollama 통합 전략

## 📋 목차
1. [아키텍처 개요](#아키텍처-개요)
2. [Docker Compose 구성](#docker-compose-구성)
3. [애플리케이션 코드 수정](#애플리케이션-코드-수정)
4. [구현 단계](#구현-단계)
5. [모델 선택 가이드](#모델-선택-가이드)
6. [성능 최적화](#성능-최적화)
7. [구현 체크리스트](#구현-체크리스트)

---

## 🎯 아키텍처 개요

### 현재 구조
```
┌─────────────────┐     ┌──────────────┐
│ langchain-app   │────▶│  postgres    │
│ (Python)        │     │  (pgvector)  │
└─────────────────┘     └──────────────┘
```

### Ollama 추가 후 구조
```
┌─────────────────┐     ┌──────────────┐
│ langchain-app   │────▶│  postgres    │
│ (Python + LLM)  │     │  (pgvector)  │
└────────┬────────┘     └──────────────┘
         │
         ▼
┌─────────────────┐
│    ollama       │
│  (LLM Server)   │
└─────────────────┘
```

**통합 목적:**
- pgvector에 저장된 문서를 검색 (Retrieval)
- 검색된 문서를 컨텍스트로 Ollama LLM에 전달
- LLM이 컨텍스트를 기반으로 질문에 답변 (RAG 패턴)

---

## 🐳 Docker Compose 구성

### Option A: 기본 Ollama 서비스

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: langchain-ollama
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "11434:11434"
    networks:
      - langchain-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  postgres_data:
  ollama_data:  # 새로 추가
```

### Option B: GPU 지원 (NVIDIA GPU 있을 경우)

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: langchain-ollama
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "11434:11434"
    networks:
      - langchain-network
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
```

### langchain-app 서비스 수정

```yaml
langchain-app:
  build: .
  container_name: langchain-app
  restart: unless-stopped
  depends_on:
    postgres:
      condition: service_healthy
    ollama:
      condition: service_healthy  # 새로 추가
  environment:
    DB_HOST: postgres
    DB_PORT: 5432
    DB_USER: postgres
    DB_PASSWORD: postgres
    DB_NAME: postgres
    OLLAMA_BASE_URL: http://ollama:11434  # 새로 추가
  networks:
    - langchain-network
```

---

## 💻 애플리케이션 코드 수정

### 1. requirements.txt 업데이트

```txt
langchain-core>=0.1.0
langchain-community>=0.0.20
langchain-ollama>=0.0.1  # 새로 추가
psycopg2-binary>=2.9.0
pgvector>=0.2.0
```

### 2. app.py 수정 - Import 추가

```python
"""간단한 LangChain Hello World 앱 - pgvector와 Ollama 연동."""

import os
import time
from langchain_core.documents import Document
from langchain_core.embeddings import FakeEmbeddings
from langchain_community.vectorstores import PGVector
from langchain_ollama import OllamaLLM  # 새로 추가
from langchain_core.prompts import PromptTemplate  # 새로 추가
from langchain_core.output_parsers import StrOutputParser  # 새로 추가
from langchain_core.runnables import RunnablePassthrough  # 새로 추가
```

### 3. Ollama 연결 테스트 함수

```python
def test_ollama_connection(base_url: str = "http://ollama:11434") -> bool:
    """Ollama 서버 연결을 테스트합니다."""
    print("🔍 Ollama 연결 테스트 중...")
    max_retries = 30

    for i in range(max_retries):
        try:
            llm = OllamaLLM(
                model="llama2",
                base_url=base_url,
                timeout=10
            )
            response = llm.invoke("Hello")
            print("✅ Ollama 연결 성공!")
            return True
        except Exception as e:
            if i < max_retries - 1:
                print(f"⏳ Ollama 연결 시도 {i + 1}/{max_retries}: {str(e)}")
                time.sleep(2)
            else:
                print(f"❌ Ollama 연결 실패: {str(e)}")
                return False

    return False
```

### 4. RAG 체인 구성

```python
def create_rag_chain(vectorstore, llm):
    """RAG (Retrieval-Augmented Generation) 체인을 생성합니다."""

    # 프롬프트 템플릿 정의
    template = """다음 문맥을 기반으로 질문에 답하세요.
    문맥에 없는 정보는 추측하지 마세요.

문맥: {context}

질문: {question}

답변:"""

    prompt = PromptTemplate.from_template(template)

    # Retriever 생성
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 2}  # 상위 2개 문서 검색
    )

    # 문서를 문자열로 변환하는 함수
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # RAG 체인 구성
    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain
```

### 5. main 함수에 통합

```python
def main() -> None:
    """메인 함수: pgvector와 Ollama를 연동하여 RAG 구현."""
    print("🚀 LangChain + Ollama Hello World 앱 시작!")

    # 환경변수 읽기
    ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://ollama:11434')

    # PostgreSQL 연결 (기존 코드)
    # ... vectorstore 생성 코드 ...

    # Ollama 연결 테스트
    if not test_ollama_connection(ollama_base_url):
        print("⚠️ Ollama 없이 계속 진행합니다.")
        # Ollama 없이 기본 동작만 수행
        return

    # Ollama LLM 초기화
    print("\n🤖 Ollama LLM 초기화 중...")
    llm = OllamaLLM(
        model="llama2",  # 또는 mistral, phi3 등
        base_url=ollama_base_url,
        temperature=0.7
    )

    # RAG 체인 생성
    print("🔗 RAG 체인 생성 중...")
    rag_chain = create_rag_chain(vectorstore, llm)

    # RAG 테스트
    print("\n🧠 RAG 테스트 중...")
    question = "벡터 검색이란 무엇인가요?"
    print(f"질문: {question}")

    response = rag_chain.invoke(question)
    print(f"\n🤖 LLM 응답:\n{response}")

    print("\n🎉 RAG 앱 실행 완료!")
```

---

## 📝 구현 단계

### Phase 1: 기본 Ollama 통합 (30분)

1. **Docker Compose 수정**
   - ollama 서비스 추가
   - volumes 추가
   - langchain-app의 depends_on 수정

2. **컨테이너 시작**
   ```bash
   docker-compose up -d
   ```

3. **모델 다운로드**
   ```bash
   docker exec -it langchain-ollama ollama pull llama2
   # 또는
   docker exec -it langchain-ollama ollama pull phi3
   ```

4. **연결 테스트**
   ```bash
   curl http://localhost:11434/api/tags
   ```

### Phase 2: RAG 구현 (1시간)

1. **requirements.txt 업데이트**
   - langchain-ollama 추가

2. **app.py 수정**
   - Import 추가
   - Ollama 연결 함수 추가
   - RAG 체인 생성 함수 추가
   - main 함수 수정

3. **재빌드 및 테스트**
   ```bash
   docker-compose build langchain-app
   docker-compose up -d
   docker-compose logs -f langchain-app
   ```

### Phase 3: 고도화 (선택사항)

1. **대화 히스토리 추가**
   ```python
   from langchain.memory import ConversationBufferMemory
   ```

2. **스트리밍 응답**
   ```python
   for chunk in rag_chain.stream(question):
       print(chunk, end="", flush=True)
   ```

3. **다중 모델 지원**
   ```python
   model_name = os.getenv('OLLAMA_MODEL', 'llama2')
   ```

---

## 🎯 모델 선택 가이드

| 모델 | 크기 | 특징 | RAM 요구사항 | 추천 용도 |
|------|------|------|-------------|-----------|
| **llama2** | 7B | 범용, 안정적 | ~8GB | 일반 대화, QA |
| **llama3** | 8B | 최신, 성능 향상 | ~8GB | 일반 대화, QA |
| **mistral** | 7B | 빠른 응답 | ~8GB | 빠른 응답 필요 시 |
| **phi3** | 3.8B | 경량, 빠름 | ~4GB | 리소스 제한 환경 |
| **gemma** | 2B-7B | Google 모델 | ~4-8GB | 다양한 크기 선택 |
| **codellama** | 7B | 코드 특화 | ~8GB | 코드 생성/설명 |

### 모델 다운로드 명령어

```bash
# 기본 모델
docker exec -it langchain-ollama ollama pull llama2

# 경량 모델 (빠른 테스트용)
docker exec -it langchain-ollama ollama pull phi3

# 최신 모델
docker exec -it langchain-ollama ollama pull llama3

# 코드 전용
docker exec -it langchain-ollama ollama pull codellama
```

### 모델 확인

```bash
# 다운로드된 모델 리스트
docker exec -it langchain-ollama ollama list

# 특정 모델 테스트
docker exec -it langchain-ollama ollama run llama2 "Hello!"
```

---

## ⚡ 성능 최적화

### 1. 리소스 제한 설정

```yaml
ollama:
  deploy:
    resources:
      limits:
        cpus: '4'
        memory: 8G
      reservations:
        cpus: '2'
        memory: 4G
```

### 2. Ollama 설정 최적화

```python
llm = OllamaLLM(
    model="llama2",
    base_url=ollama_base_url,
    temperature=0.7,      # 창의성 조절 (0-1)
    top_k=40,             # 다양성 조절
    top_p=0.9,            # 확률 임계값
    num_ctx=2048,         # 컨텍스트 윈도우 크기
    repeat_penalty=1.1,   # 반복 방지
)
```

### 3. 캐싱 전략

```python
# 모델을 메모리에 유지 (keep_alive)
llm = OllamaLLM(
    model="llama2",
    base_url=ollama_base_url,
    keep_alive="5m"  # 5분간 메모리 유지
)
```

### 4. 스트리밍 응답

```python
def stream_response(chain, question):
    """스트리밍 방식으로 응답 출력"""
    print("🤖 응답: ", end="", flush=True)
    for chunk in chain.stream(question):
        print(chunk, end="", flush=True)
    print()
```

---

## 🔍 디버깅 및 모니터링

### Ollama 로그 확인

```bash
# Ollama 로그
docker logs langchain-ollama

# 실시간 로그
docker logs -f langchain-ollama
```

### API 엔드포인트 테스트

```bash
# 헬스체크
curl http://localhost:11434/api/tags

# 모델 정보
curl http://localhost:11434/api/show -d '{
  "name": "llama2"
}'

# 간단한 생성 테스트
curl http://localhost:11434/api/generate -d '{
  "model": "llama2",
  "prompt": "Why is the sky blue?",
  "stream": false
}'
```

### Python 디버깅 코드

```python
def debug_ollama():
    """Ollama 상태를 자세히 확인"""
    import requests

    base_url = "http://ollama:11434"

    try:
        # 1. 서버 상태
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        print(f"✅ 서버 상태: {response.status_code}")
        print(f"📋 모델 리스트: {response.json()}")

        # 2. 간단한 생성 테스트
        response = requests.post(
            f"{base_url}/api/generate",
            json={"model": "llama2", "prompt": "Hi", "stream": False},
            timeout=30
        )
        print(f"✅ 생성 테스트: {response.json()}")

    except Exception as e:
        print(f"❌ 오류: {e}")
```

---

## ✅ 구현 체크리스트

### 준비 단계
- [ ] 시스템 리소스 확인 (최소 8GB RAM 권장)
- [ ] Docker 및 Docker Compose 설치 확인
- [ ] GPU 사용 여부 결정 (선택사항)

### Docker 설정
- [ ] `Docker-compose.yaml`에 ollama 서비스 추가
- [ ] ollama_data 볼륨 추가
- [ ] langchain-app의 depends_on에 ollama 추가
- [ ] 환경변수 OLLAMA_BASE_URL 추가
- [ ] 헬스체크 설정 추가

### 애플리케이션 수정
- [ ] `requirements.txt`에 langchain-ollama 추가
- [ ] `app.py`에 필요한 import 추가
- [ ] Ollama 연결 테스트 함수 작성
- [ ] RAG 체인 생성 함수 작성
- [ ] main 함수에 RAG 로직 통합

### 테스트
- [ ] 컨테이너 빌드 및 시작
- [ ] Ollama 모델 다운로드 (llama2 또는 phi3)
- [ ] 모델 다운로드 확인 (`ollama list`)
- [ ] 연결 테스트 (curl 또는 Python)
- [ ] RAG 체인 동작 확인
- [ ] 로그 확인 및 디버깅

### 최적화 (선택사항)
- [ ] 리소스 제한 설정
- [ ] Ollama 파라미터 튜닝
- [ ] 스트리밍 응답 구현
- [ ] 에러 처리 강화
- [ ] 모니터링 추가

---

## 📚 참고 자료

### 공식 문서
- [Ollama 공식 문서](https://ollama.ai/)
- [LangChain Ollama 통합](https://python.langchain.com/docs/integrations/llms/ollama)
- [LangChain RAG 가이드](https://python.langchain.com/docs/use_cases/question_answering/)

### 모델 정보
- [Ollama 모델 라이브러리](https://ollama.ai/library)
- [Llama 2 정보](https://ai.meta.com/llama/)
- [Mistral AI](https://mistral.ai/)

### Docker 관련
- [Ollama Docker Hub](https://hub.docker.com/r/ollama/ollama)
- [Docker Compose 문서](https://docs.docker.com/compose/)

---

## 🚀 시작하기

```bash
# 1. 컨테이너 시작
docker-compose up -d

# 2. Ollama 로그 확인
docker logs -f langchain-ollama

# 3. 모델 다운로드 (새 터미널)
docker exec -it langchain-ollama ollama pull llama2

# 4. 앱 로그 확인
docker-compose logs -f langchain-app

# 5. 테스트
curl http://localhost:11434/api/tags
```

---

**작성일:** 2024-12-16
**버전:** 1.0
**다음 단계:** Phase 1부터 순차적으로 구현 시작

