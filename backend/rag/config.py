"""
RAG 시스템 설정 파일
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드 (프로젝트 루트에서)
PROJECT_ROOT = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# Gemini API 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")

# ChromaDB 설정
CHROMA_PERSIST_DIRECTORY = os.getenv(
    "CHROMA_PERSIST_DIRECTORY",
    str(PROJECT_ROOT / "backend" / "chroma_db")
)
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "pc_components")

# 임베딩 모델 설정
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/text-embedding-004")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "768"))

# 생성 모델 설정
# 기본값: gemini-2.5-pro (2025년 11월 최신 - 코딩/추론/복잡한 작업에 최적)
# 환경변수로 변경 가능 (.env 파일에서 GENERATION_MODEL 설정)
# 사용 가능한 모델: gemini-3-pro, gemini-2.5-pro, gemini-2.5-flash, gemini-2.5-flash-lite
GENERATION_MODEL = os.getenv("GENERATION_MODEL", "gemini-2.5-pro")

# RAG 설정
TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "5"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))

# 데이터베이스 경로
SQL_DUMP_PATH = PROJECT_ROOT / "backend" / "data" / "pc_data_dump.sql"

# 로깅 설정
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

