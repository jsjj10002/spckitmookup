# RAG (Retrieval-Augmented Generation) 모듈

> Gemini API + ChromaDB 기반 PC 부품 검색 및 추천 시스템

---

## 목차

- [개요](#개요)
- [아키텍처](#아키텍처)
- [파일 구조](#파일-구조)
- [핵심 컴포넌트](#핵심-컴포넌트)
- [데이터 흐름](#데이터-흐름)
- [Step-by-Step 파이프라인](#step-by-step-파이프라인)
- [설정 (Config)](#설정-config)
- [사용법](#사용법)
- [API 연동](#api-연동)

---

## 개요

### 목표

SQL 데이터베이스에 저장된 **135,660개 PC 부품 정보**를 벡터화하여 자연어 검색 및 AI 추천을 제공.

### 핵심 기술

| 기술 | 역할 |
|------|------|
| **Gemini API** | 임베딩 생성 (text-embedding-004) + 추천 생성 (gemini-3-flash-preview) |
| **ChromaDB** | 벡터 데이터베이스 (코사인 유사도 검색) |
| **Pydantic** | 데이터 검증 및 스키마 정의 |

---

## 아키텍처

### 전체 시스템 흐름

```
사용자 쿼리
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          RAGPipeline                                 │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    1. Query Processing                          │ │
│  │  [사용자 쿼리] → [GeminiEmbedder] → [쿼리 벡터]                │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              │                                       │
│                              ▼                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    2. Retrieval                                  │ │
│  │  [쿼리 벡터] → [ChromaDB] → [유사 부품 검색]                   │ │
│  │                 ↓                                                │ │
│  │  [PCComponentRetriever]                                          │ │
│  │   - 카테고리 필터링                                              │ │
│  │   - 유사도 기반 정렬                                             │ │
│  │   - 메타데이터 필터 (소켓, 가격 등)                             │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              │                                       │
│                              ▼                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    3. Generation                                 │ │
│  │  [검색 결과] + [사용자 쿼리] → [Gemini LLM] → [추천 응답]      │ │
│  │                 ↓                                                │ │
│  │  [PCRecommendationGenerator]                                     │ │
│  │   - 시스템 프롬프트 적용                                         │ │
│  │   - 부품 컨텍스트 구성                                           │ │
│  │   - 한국어 응답 생성                                             │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
추천 응답 (부품 목록 + 설명)
```

---

## 파일 구조

```
rag/
├── __init__.py          # 모듈 초기화 및 exports
├── config.py            # 환경변수 및 설정 관리
├── data_parser.py       # SQL 덤프 파싱
├── embedder.py          # Gemini 임베딩 생성기
├── vector_store.py      # ChromaDB 벡터 데이터베이스
├── retriever.py         # 부품 검색 및 필터링
├── generator.py         # AI 추천 응답 생성
├── pipeline.py          # 전체 시스템 통합 파이프라인
├── step_by_step.py      # 단계별 부품 선택 파이프라인
└── README.md            # 이 문서
```

### 파일별 역할

| 파일 | 역할 | 주요 클래스 |
|------|------|-------------|
| `config.py` | 환경변수, API 키, 모델 설정 | - |
| `data_parser.py` | SQL INSERT문 → 부품 문서 변환 | `PCDataParser` |
| `embedder.py` | 텍스트 → 벡터 변환 (Gemini API) | `GeminiEmbedder` |
| `vector_store.py` | ChromaDB CRUD 작업 | `PCComponentVectorStore` |
| `retriever.py` | 유사도 검색 + 필터링 | `PCComponentRetriever` |
| `generator.py` | LLM 기반 추천 응답 생성 | `PCRecommendationGenerator` |
| `pipeline.py` | 위 모듈 통합 (기본 검색) | `RAGPipeline` |
| `step_by_step.py` | 단계별 부품 선택 (CPU→GPU→...) | `StepByStepRAGPipeline` |

---

## 핵심 컴포넌트

### 1. PCDataParser (data_parser.py)

SQL 덤프 파일에서 PC 부품 정보를 추출하여 RAG용 문서로 변환.

```python
class PCDataParser:
    """
    입력: SQL INSERT 문 (pc_data_dump.sql)
    출력: List[Dict] - 부품 문서 리스트
    
    문서 구조:
    {
        "text": "RTX 4070 NVIDIA GPU 게임용 그래픽카드 650000원",
        "metadata": {
            "category": "gpu",
            "name": "RTX 4070",
            "price": 650000,
            "brand": "NVIDIA",
            ...
        }
    }
    """
```

### 2. GeminiEmbedder (embedder.py)

Gemini API를 사용하여 텍스트를 768차원 벡터로 변환.

```python
class GeminiEmbedder:
    """
    모델: text-embedding-004
    차원: 768
    태스크 타입:
        - RETRIEVAL_DOCUMENT: 문서 임베딩 (DB 저장용)
        - RETRIEVAL_QUERY: 쿼리 임베딩 (검색용)
    
    메서드:
        embed_text(text) → List[float]        # 단일 텍스트
        embed_batch(texts) → List[List[float]] # 배치 처리
        embed_query(query) → List[float]      # 검색 쿼리용
    """
```

### 3. PCComponentVectorStore (vector_store.py)

ChromaDB를 사용한 벡터 데이터베이스 관리.

```python
class PCComponentVectorStore:
    """
    저장소: ChromaDB (영구 저장)
    유사도: 코사인 유사도
    
    메서드:
        add_documents(documents)   # 문서 추가
        search(query, top_k)       # 유사도 검색
        get_by_category(category)  # 카테고리별 조회
        get_stats()                # 통계 조회
    """
```

### 4. PCComponentRetriever (retriever.py)

벡터 검색 결과에 추가 필터링 적용.

```python
class PCComponentRetriever:
    """
    기능:
        - 유사도 기반 검색
        - 카테고리 필터링
        - 메타데이터 필터 (소켓, 가격대 등)
        - 호환 부품 검색
    
    메서드:
        retrieve(query, category) → List[Dict]
        retrieve_by_specs(requirements) → Dict[category, List[Dict]]
        retrieve_compatible_components(base, target_category) → List[Dict]
    """
```

### 5. PCRecommendationGenerator (generator.py)

검색 결과를 기반으로 AI 추천 응답 생성.

```python
class PCRecommendationGenerator:
    """
    모델: gemini-3-flash-preview
    
    기능:
        - 부품 컨텍스트 기반 추천 생성
        - 시스템 프롬프트 적용
        - 부품 비교 분석
    
    메서드:
        generate_recommendation(query, components) → Dict
        generate_comparison(components) → Dict
    """
```

### 6. RAGPipeline (pipeline.py)

위 컴포넌트들을 통합하는 메인 파이프라인.

```python
class RAGPipeline:
    """
    통합 메서드:
        initialize_database(sql_path)  # DB 초기화
        query(user_query)              # 추천 생성
        query_by_specs(requirements)   # 사양 기반 추천
        compare_components(ids)        # 부품 비교
        get_stats()                    # 시스템 통계
    """
```

---

## 데이터 흐름

### 1. 데이터베이스 초기화 (한 번만 실행)

```
pc_data_dump.sql
    │
    ▼ PCDataParser.parse_sql_dump()
테이블별 레코드 추출
    │
    ▼ PCDataParser.create_component_documents()
부품 문서 리스트 (text + metadata)
    │
    ▼ GeminiEmbedder.embed_batch()
벡터 임베딩 생성
    │
    ▼ PCComponentVectorStore.add_documents()
ChromaDB 저장 (135,660개 부품)
```

### 2. 검색 및 추천 (매 요청마다)

```
"150만원 게임용 PC"
    │
    ▼ GeminiEmbedder.embed_query()
쿼리 벡터 [768차원]
    │
    ▼ PCComponentVectorStore.search()
유사 부품 검색 (ChromaDB)
    │
    ▼ PCComponentRetriever.retrieve()
필터링 및 정렬
    │
    ▼ PCRecommendationGenerator.generate_recommendation()
AI 추천 응답 생성
    │
    ▼
{
    "recommendation": "...",
    "components": [...],
    "total_price": 1450000
}
```

---

## Step-by-Step 파이프라인

### 개요

부품을 **카테고리별로 단계적으로 선택**하는 방식의 RAG 파이프라인.

```
CPU(1단계) → 메인보드(2단계) → 메모리(3단계) → GPU(4단계)
    → 저장장치(5단계) → PSU(6단계) → 쿨러(7단계) → 케이스(8단계)
```

### StepByStepRAGPipeline

```python
class StepByStepRAGPipeline:
    """
    세션 기반 단계별 부품 선택
    
    메서드:
        start_session(budget, purpose) → SelectionSession
        get_step_candidates(session_id, step) → StepResult
        select_component(session_id, step, component_id) → bool
        get_summary(session_id) → Dict
    
    특징:
        - 이전 선택 기반 호환성 필터링
        - 단계별 예산 배분
        - 세션 상태 관리
    """
```

### 단계별 처리

| 단계 | 카테고리 | 예산 비율 | 호환성 참조 |
|------|----------|----------|-------------|
| 1 | CPU | 20-25% | - |
| 2 | 메인보드 | 10-15% | CPU 소켓 |
| 3 | 메모리 | 8-10% | 메인보드 DDR 타입 |
| 4 | GPU | 30-40% | - |
| 5 | 저장장치 | 8-12% | - |
| 6 | PSU | 5-8% | 총 TDP 기준 |
| 7 | CPU 쿨러 | 3-5% | CPU 소켓 |
| 8 | 케이스 | 5-8% | 메인보드 폼팩터 |

---

## 설정 (Config)

### config.py 환경변수

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| `GEMINI_API_KEY` | (필수) | Gemini API 키 |
| `CHROMA_PERSIST_DIRECTORY` | `backend/chroma_db` | ChromaDB 저장 경로 |
| `CHROMA_COLLECTION_NAME` | `pc_components` | 컬렉션 이름 |
| `EMBEDDING_MODEL` | `text-embedding-004` | 임베딩 모델 |
| `EMBEDDING_DIMENSION` | `768` | 임베딩 차원 |
| `GENERATION_MODEL` | `gemini-3-flash-preview` | 생성 모델 |
| `TOP_K_RESULTS` | `5` | 기본 검색 결과 수 |

### .env 파일 예시

```env
GEMINI_API_KEY=your_api_key_here
GENERATION_MODEL=gemini-3-flash-preview
TOP_K_RESULTS=5
LOG_LEVEL=INFO
```

---

## 사용법

### 기본 사용

```python
from backend.rag import RAGPipeline

# 파이프라인 초기화
pipeline = RAGPipeline()

# (최초 1회) 데이터베이스 구축
pipeline.initialize_database()

# 추천 요청
result = pipeline.query("150만원으로 게임용 PC 추천해줘")
print(result["recommendation"])
```

### 카테고리별 검색

```python
from backend.rag import PCComponentRetriever, PCComponentVectorStore

vector_store = PCComponentVectorStore()
retriever = PCComponentRetriever(vector_store)

# GPU 검색
gpus = retriever.retrieve(
    query="RTX 4070 게임용",
    category="gpu",
    top_k=5
)
```

### Step-by-Step 사용

```python
from backend.rag import StepByStepRAGPipeline

pipeline = StepByStepRAGPipeline()

# 세션 시작
session = pipeline.start_session(budget=1500000, purpose="gaming")

# 1단계: CPU 후보 조회
cpu_result = pipeline.get_step_candidates(session.session_id, step=1)

# CPU 선택
pipeline.select_component(
    session_id=session.session_id,
    step=1,
    component_id=cpu_result.candidates[0].component_id
)

# 2단계: (선택한 CPU와 호환되는) 메인보드 후보 조회
mb_result = pipeline.get_step_candidates(session.session_id, step=2)
```

---

## API 연동

### FastAPI 엔드포인트

| Method | Path | 설명 | 모듈 |
|--------|------|------|------|
| `POST` | `/query` | 기본 추천 | `RAGPipeline.query()` |
| `POST` | `/query-by-specs` | 사양 기반 추천 | `RAGPipeline.query_by_specs()` |
| `POST` | `/compare` | 부품 비교 | `RAGPipeline.compare_components()` |
| `POST` | `/step/start` | 단계별 시작 | `StepByStepRAGPipeline.start_session()` |
| `POST` | `/step/{step}/candidates` | 후보 조회 | `StepByStepRAGPipeline.get_step_candidates()` |
| `POST` | `/step/{step}/select` | 부품 선택 | `StepByStepRAGPipeline.select_component()` |
| `GET` | `/stats` | 시스템 통계 | `RAGPipeline.get_stats()` |

---

## 주의사항

1. **API Rate Limit**: Gemini API 호출 시 Rate Limit 주의 (배치 처리 권장)
2. **초기화 시간**: 135,660개 부품 임베딩 생성에 상당한 시간 소요 (최초 1회)
3. **메모리 사용**: ChromaDB는 메모리 사용량이 클 수 있음

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2025-12-31 | 1.0.0 | 초기 RAG 파이프라인 구현 |
| 2026-01-03 | 1.1.0 | Step-by-Step 파이프라인 추가 |
| 2026-01-08 | 1.2.0 | 기술 문서 작성 |
