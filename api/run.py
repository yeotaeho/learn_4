"""로컬에서 FastAPI 서버를 실행하는 스크립트."""

import os
import sys
from pathlib import Path

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn

# Neon PostgreSQL 기본 URL
NEON_DATABASE_URL = (
    "postgresql://neondb_owner:npg_pzP8wiQDH1sk@"
    "ep-autumn-boat-a1wcjk8g-pooler.ap-southeast-1.aws.neon.tech/"
    "neondb?sslmode=require"
)

if __name__ == "__main__":
    # run.py 파일 기준으로 model_weights 경로 설정 (절대 경로)
    run_file_dir = Path(__file__).parent.absolute()
    model_weights_path = run_file_dir / "model_weights"

    # 환경변수 기본값 설정 (로컬 실행용)
    os.environ.setdefault("LLM_PROVIDER", "local")
    os.environ.setdefault("LOCAL_MODEL_PATH", str(model_weights_path))
    os.environ.setdefault("LOCAL_MODEL_DEVICE", "cuda")
    os.environ.setdefault("DATABASE_URL", NEON_DATABASE_URL)

    # 개발 모드 설정
    debug = os.getenv("DEBUG", "true").lower() == "true"

    print("🚀 로컬 서버 시작...")
    print(f"📦 LLM Provider: {os.getenv('LLM_PROVIDER')}")
    print(f"📂 Model Path: {os.getenv('LOCAL_MODEL_PATH')}")
    print(f"🗄️  Database: Neon PostgreSQL (ap-southeast-1)")
    print(f"🔧 Debug Mode: {debug}")
    print()

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=debug,
        log_level="info",
    )
