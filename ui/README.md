# LangChain RAG Chatbot UI

Next.js를 사용한 RAG 방식 챗봇 프론트엔드 애플리케이션입니다.

## 🚀 시작하기

### 1. 의존성 설치

```bash
cd ui
npm install
```

### 2. 개발 서버 실행

```bash
npm run dev
```

브라우저에서 [http://localhost:3000](http://localhost:3000)을 열어 확인하세요.

## 📁 프로젝트 구조

```
ui/
├── app/
│   ├── layout.tsx      # 루트 레이아웃
│   ├── page.tsx        # 메인 페이지
│   └── globals.css     # 전역 스타일
├── components/
│   └── Chat.tsx        # 챗봇 컴포넌트
├── package.json
├── tsconfig.json
└── next.config.js
```

## 🔧 환경변수

루트 디렉토리의 `.env` 파일에 다음을 설정하세요:

```env
OPENAI_API_KEY=your_openai_api_key_here
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=postgres
```

백엔드 API 서버는 `http://localhost:8000`에서 실행되어야 합니다.

## 🏗️ 빌드

```bash
npm run build
npm start
```

## 📝 주요 기능

- 💬 실시간 채팅 인터페이스
- 🔍 RAG 방식 질의응답
- 📱 반응형 디자인
- ⚡ 빠른 응답 속도


