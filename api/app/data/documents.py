"""RAG에 사용할 문서 데이터."""

from langchain_core.documents import Document

# RAG에 사용할 기본 문서들
RAG_DOCUMENTS: list[Document] = [
    Document(
        page_content="LangChain은 LLM 애플리케이션 개발을 위한 프레임워크입니다.",
        metadata={"source": "introduction", "type": "tutorial"},
    ),
    Document(
        page_content="pgvector는 PostgreSQL의 벡터 검색 확장입니다.",
        metadata={"source": "pgvector", "type": "database"},
    ),
    Document(
        page_content="벡터 검색은 의미 기반 유사도 검색을 가능하게 합니다.",
        metadata={"source": "vector_search", "type": "concept"},
    ),
]

