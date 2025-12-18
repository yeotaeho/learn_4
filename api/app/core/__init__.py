"""Core 모듈 - 설정 및 의존성."""

from .config import settings
from .deps import get_vectorstore

__all__ = ["settings", "get_vectorstore"]

