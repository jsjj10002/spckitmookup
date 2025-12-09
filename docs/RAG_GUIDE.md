# RAG 시스템 사용 가이드

PC 부품 추천을 위한 RAG (Retrieval-Augmented Generation) 시스템 완전 가이드입니다.

## 📋 목차

1. [시스템 개요](#시스템-개요)
2. [빠른 시작](#빠른-시작)
3. [사용 예시](#사용-예시)
4. [API 레퍼런스](#api-레퍼런스)
5. [고급 사용법](#고급-사용법)
6. [문제 해결](#문제-해결)

## 시스템 개요

### 아키텍처

```
사용자 쿼리
    ↓
[1] 임베딩 생성 (Gemini Embedding API)
    ↓
[2] 벡터 검색 (ChromaDB)
    ↓
[3] 관련 부품 추출
    ↓
[4] 컨텍스트 구성
    ↓
[5] 추천 생성 (Gemini Generation API)
    ↓
결과 반환
```

### 주요 컴포넌트

1. **Embedder**: 텍스트를 768차원 벡터로 변환
2. **Vector Store**: ChromaDB에 부품 정보 저장 및 검색
3. **Data Parser**: SQL 덤프에서 부품 정보 추출
4. **Retriever**: 의미 기반 부품 검색
5. **Generator**: AI 추천 생성
6. **Pipeline**: 전체 워크플로우 통합

## 빠른 시작

### 1. 의존성 설치

```bash
cd backend
uv pip install -e .
```

### 2. 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집
# GEMINI_API_KEY=your_actual_api_key_here
```

### 3. 벡터 DB 초기화

```bash
# 처음 실행 (약 10-30분 소요)
python backend/scripts/init_database.py

# 진행 상황 확인
python backend/scripts/init_database.py --log-level INFO
```

### 4. 테스트

```bash
python backend/scripts/test_rag.py
```

### 5. API 서버 실행

```bash
cd backend/api
uvicorn main:app --reload --port 8000
```

브라우저에서 확인: http://localhost:8000/docs

## 사용 예시

### 예시 1: 기본 쿼리

```python
from backend.rag.pipeline import RAGPipeline

# 파이프라인 초기화
pipeline = RAGPipeline()

# 쿼리 실행
result = pipeline.query(
    user_query="게임용 고성능 그래픽카드 추천해줘",
    top_k=5
)

print(result["recommendation"])
```

**출력 예시:**
```json
{
  "analysis": "게임용 고성능 그래픽카드를 찾고 계시네요...",
  "components": [
    {
      "category": "gpu",
      "name": "NVIDIA RTX 4090",
      "price": "250",
      "features": ["4K 게이밍", "레이트레이싱", "DLSS 3.0"],
      "why_recommended": "최고 성능의 게임용 그래픽카드"
    }
  ],
  "total_price": "250",
  "additional_notes": "충분한 파워 서플라이가 필요합니다"
}
```

### 예시 2: 사양 기반 검색

```python
# 예산과 목적으로 검색
result = pipeline.query_by_specs(
    requirements={
        "budget": 150,
        "purpose": "게임",
        "categories": ["cpu", "gpu", "memory", "motherboard"],
        "preferences": "조용하고 전력 효율이 좋은 부품"
    },
    top_k=3
)

print(result["recommendation"])
```

### 예시 3: 카테고리 필터링

```python
# GPU만 검색
result = pipeline.query(
    user_query="RTX 4000 시리즈",
    category="gpu",
    top_k=10
)
```

### 예시 4: 부품 비교

```python
# 특정 부품들 비교
result = pipeline.compare_components(
    component_ids=["gpu_1", "gpu_2", "gpu_3"]
)

print(result["comparison"])
```

## API 레퍼런스

### REST API 엔드포인트

#### POST /query
기본 쿼리 검색

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "게임용 CPU 추천",
    "top_k": 5,
    "category": null,
    "include_context": false
  }'
```

**응답:**
```json
{
  "query": "게임용 CPU 추천",
  "recommendation": {
    "analysis": "...",
    "components": [...]
  },
  "retrieved_count": 5
}
```

#### POST /query-by-specs
사양 기반 검색

```bash
curl -X POST "http://localhost:8000/query-by-specs" \
  -H "Content-Type: application/json" \
  -d '{
    "budget": 150,
    "purpose": "게임",
    "categories": ["cpu", "gpu"],
    "top_k": 3
  }'
```

#### POST /compare
부품 비교

```bash
curl -X POST "http://localhost:8000/compare" \
  -H "Content-Type: application/json" \
  -d '{
    "component_ids": ["cpu_1", "cpu_2"]
  }'
```

#### GET /stats
시스템 통계

```bash
curl "http://localhost:8000/stats"
```

**응답:**
```json
{
  "total_documents": 5234,
  "collection_name": "pc_components",
  "categories_sample": {
    "cpu": 234,
    "gpu": 189,
    "memory": 456
  }
}
```

## 고급 사용법

### 커스텀 임베더 사용

```python
from backend.rag.embedder import GeminiEmbedder
from backend.rag.vector_store import PCComponentVectorStore

# 커스텀 설정으로 임베더 생성
embedder = GeminiEmbedder(
    model="models/text-embedding-004",
    task_type="RETRIEVAL_DOCUMENT",
    max_retries=5
)

# 벡터 스토어에 연결
vector_store = PCComponentVectorStore(embedder=embedder)
```

### 배치 처리

```python
# 여러 쿼리를 배치로 처리
queries = [
    "게임용 CPU",
    "영상 편집용 GPU",
    "가성비 메모리"
]

results = []
for query in queries:
    result = pipeline.query(user_query=query, top_k=3)
    results.append(result)
```

### 유사도 필터링

```python
from backend.rag.retriever import PCComponentRetriever

retriever = PCComponentRetriever(vector_store)

# 최소 유사도 0.7 이상만 검색
results = retriever.retrieve(
    query="고성능 그래픽카드",
    top_k=10,
    min_similarity=0.7
)
```

### 데이터 재구축

```bash
# 기존 데이터 삭제 후 재구축
python backend/scripts/init_database.py --force

# 다른 SQL 파일 사용
python backend/scripts/init_database.py --sql-file path/to/other.sql
```

## 문제 해결

### Q1: "GEMINI_API_KEY가 설정되지 않았습니다" 오류

**해결:**
```bash
# .env 파일에 API 키 추가
echo 'GEMINI_API_KEY=your_api_key_here' > backend/.env
```

### Q2: ChromaDB 초기화 실패

**해결:**
```bash
# ChromaDB 디렉토리 삭제
rm -rf backend/chroma_db

# 재초기화
python backend/scripts/init_database.py
```

### Q3: "검색된 부품이 없습니다" 응답

**원인:** 벡터 DB가 비어있거나 쿼리와 관련된 부품이 없음

**해결:**
1. DB 통계 확인: `curl http://localhost:8000/stats`
2. DB 재초기화: `python backend/scripts/init_database.py --force`
3. 더 일반적인 쿼리 사용

### Q4: API 응답이 느림

**해결:**
- `top_k` 값을 줄이기 (5 이하 권장)
- 카테고리 필터 사용하여 검색 범위 축소
- Gemini API 할당량 확인

### Q5: Import 에러

**해결:**
```bash
# 프로젝트 루트에서 실행
cd /path/to/SpckitAI

# Python 경로 확인
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 스크립트 실행
python backend/scripts/test_rag.py
```

## 성능 최적화

### 1. 임베딩 캐싱

```python
# 자주 사용하는 쿼리는 결과를 캐시
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_query(query_str):
    return pipeline.query(user_query=query_str)
```

### 2. 배치 크기 조정

```python
# 대량 데이터 처리 시 배치 크기 증가
vector_store.add_documents(documents, batch_size=200)
```

### 3. 인덱스 최적화

ChromaDB는 HNSW 인덱스를 사용합니다. 더 많은 데이터가 추가될수록 검색 속도가 느려질 수 있습니다.

```python
# 컬렉션 재생성으로 인덱스 최적화
vector_store.delete_collection()
pipeline.initialize_database()
```

## 모니터링

### 시스템 통계 확인

```python
stats = pipeline.get_stats()
print(f"총 문서 수: {stats['total_documents']}")
print(f"카테고리별 분포: {stats['categories_sample']}")
```

### 로그 레벨 설정

```python
from loguru import logger
import sys

logger.remove()
logger.add(sys.stdout, level="DEBUG")
```

## 다음 단계

1. 프론트엔드와 연동
2. 부품 호환성 체크 추가
3. 사용자 피드백 시스템 구축
4. A/B 테스트 구현
5. 프롬프트 최적화

## 참고 자료

- [Gemini API 문서](https://ai.google.dev/gemini-api/docs)
- [ChromaDB 문서](https://docs.trychroma.com/)
- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [RAG 개념 설명](https://www.pinecone.io/learn/retrieval-augmented-generation/)

