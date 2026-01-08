# Spckit AI 서비스 아키텍처 및 모듈 현황

> 모듈 개발 현황, 프론트엔드 연결, 사용자 서빙 방식에 대한 종합 문서

---

## 목차

1. [현재 상태 요약](#1-현재-상태-요약)
2. [서비스 전체 구조](#2-서비스-전체-구조)
3. [모듈별 개발 현황 및 Main Task](#3-모듈별-개발-현황-및-main-task)
4. [프론트엔드 연결 계획](#4-프론트엔드-연결-계획)
5. [사용자 시나리오별 서비스 흐름](#5-사용자-시나리오별-서비스-흐름)
6. [API 엔드포인트 설계](#6-api-엔드포인트-설계)
7. [개발 우선순위 및 일정](#7-개발-우선순위-및-일정)

---

## 1. 현재 상태 요약

### 완성된 것

| 항목 | 상태 | 설명 |
|------|------|------|
| RAG 파이프라인 | **완성** | 부품 검색 및 AI 추천 생성 동작 |
| 벡터 DB | **완성** | 135,660개 부품 데이터 임베딩 |
| API 서버 | **완성** | FastAPI 기반, `/query` 엔드포인트 |
| 프론트엔드 연동 | **완성** | 기본 추천 기능 연결됨 |

### 뼈대만 구축된 것 (개발 필요)

| 모듈 | 상태 | 설명 |
|------|------|------|
| 멀티 에이전트 | **뼈대** | 클래스 구조, 인터페이스 정의됨 |
| PC 사양 진단 | **뼈대** | 데이터 모델, 로직 흐름 정의됨 |
| 가격 예측 | **뼈대** | 모델 구조, 입출력 정의됨 |
| GNN 추천 | **뼈대** | 그래프 구조, 모델 정의됨 |
| 호환성 검사 | **뼈대** | 규칙, 온톨로지 구조 정의됨 |
| Step-by-Step RAG | **뼈대** | 단계별 흐름 정의됨 |

> **뼈대 = 클래스/함수 시그니처 + 상세 주석/가이드 + Pydantic 모델 + 테스트 파일 템플릿**  
> **실제 로직은 placeholder 또는 더미 구현 상태**

---

## 2. 서비스 전체 구조

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              사용자 (브라우저)                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         프론트엔드 (Vite + JS)                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐    │
│  │ landing.html│  │ builder.html│  │   api.js    │  │   builder.js    │    │
│  │ (랜딩 페이지)│  │ (PC 빌더)  │  │ (API 통신) │  │  (UI 로직)      │    │
│  └─────────────┘  └─────────────┘  └──────┬──────┘  └─────────────────┘    │
└────────────────────────────────────────────┼────────────────────────────────┘
                                             │ HTTP/JSON
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          백엔드 API (FastAPI)                                │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         api/main.py (라우터)                          │  │
│  │  POST /query          - 기본 추천 [완성]                             │  │
│  │  POST /query-by-specs - 사양 기반 추천 [완성]                        │  │
│  │  POST /compare        - 부품 비교 [완성]                             │  │
│  │  ────────────────────────────────────────────────────                │  │
│  │  POST /diagnose       - 내 사양 진단 [미구현]                        │  │
│  │  POST /predict-price  - 가격 예측 [미구현]                           │  │
│  │  POST /recommend      - 개인화 추천 [미구현]                         │  │
│  │  POST /compatibility  - 호환성 검사 [미구현]                         │  │
│  │  POST /step/*         - 단계별 선택 [미구현]                         │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                     │                                        │
│                                     ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      모듈 레이어                                      │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────────┐ │  │
│  │  │    RAG     │ │ 멀티에이전트│ │  PC 진단   │ │    가격 예측       │ │  │
│  │  │  [완성]    │ │  [뼈대]    │ │  [뼈대]    │ │     [뼈대]         │ │  │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────────────┘ │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐                        │  │
│  │  │ GNN 추천   │ │ 호환성검사 │ │ Step-by-  │                        │  │
│  │  │  [뼈대]    │ │  [뼈대]    │ │ Step RAG  │                        │  │
│  │  │            │ │            │ │  [뼈대]    │                        │  │
│  │  └────────────┘ └────────────┘ └────────────┘                        │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                     │                                        │
│                                     ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                     데이터 레이어                                     │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐ │  │
│  │  │ ChromaDB       │  │  SQL 데이터     │  │  가격 이력 DB          │ │  │
│  │  │ (벡터 검색)    │  │  (부품 정보)   │  │  [구축 필요]           │ │  │
│  │  │ [완성]         │  │  [완성]        │  │                        │ │  │
│  │  └────────────────┘  └────────────────┘  └────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 모듈별 개발 현황 및 Main Task

### 3.1 RAG 파이프라인 [완성]

**파일**: `rag/pipeline.py`

**현재 상태**: 동작 가능

**기능**:
- 자연어 쿼리로 부품 검색
- Gemini API로 추천 응답 생성
- ChromaDB 벡터 검색

---

### 3.2 멀티 에이전트 시스템 [구현 중]

**파일**: `modules/multi_agent/`

**현재 상태**: CREWai 연동 완료, 에이전트 분리 구조 설계됨

#### 에이전트 분리 구조

| 에이전트 그룹 | 포함 에이전트 | 역할 |
|--------------|---------------|------|
| **채팅 에이전트** | RequirementAnalyzer, RecommendationWriter | 사용자 대화 처리, 결과 작성 |
| **추천 에이전트** | BudgetPlanner, ComponentSelector, CompatibilityChecker | 부품 선택, 검증, 외부 모듈 연동 |

#### 외부 모듈 연동

추천 에이전트는 다음 외부 모듈과 연동됨:
- `backend/data/price_prediction/` - 가격 예측치 제공
- `backend/data/compatibility/` - 호환성 검사 데이터
- `backend/data/recommendation/` - 시너지 기반 맞춤 추천

#### Main Task

| # | 작업 | 설명 | 예상 시간 |
|---|------|------|----------|
| 1 | CREWai 연동 | `crewai` 라이브러리 실제 연결 | **완료** |
| 2 | 에이전트 구현 | 4개 에이전트 클래스 정의 | **완료** |
| 3 | 도구(Tools) 정의 | SearchPartsTool, CompatibilityCheckTool 등 | **완료** |
| 4 | 가격예측 모듈 연동 | ComponentSelector에 가격 예측 통합 | 진행 중 |
| 5 | 추천엔진 연동 | 시너지 기반 맞춤 추천 통합 | 대기 |
| 6 | 테스트 | 전체 플로우 통합 테스트 | 대기 |

---

### 3.3 PC 사양 진단 모듈 [뼈대]

**파일**: `modules/pc_diagnosis/`

**현재 상태**: 데이터 모델, 점수 계산 로직 placeholder

#### Main Task

| # | 작업 | 설명 | 예상 시간 |
|---|------|------|----------|
| 1 | 벤치마크 DB | CPU/GPU 벤치마크 점수 데이터 수집 | 2일 |
| 2 | 점수 산출 | 실제 벤치마크 기반 점수 계산 로직 | 2일 |
| 3 | 병목 분석 | CPU-GPU 밸런스 분석 알고리즘 | 1일 |
| 4 | 업그레이드 추천 | ROI 기반 업그레이드 제안 로직 | 1일 |
| 5 | 테스트 | 다양한 사양 케이스 테스트 | 1일 |

**핵심 구현 포인트**:
```python
# engine.py - 실제 구현 필요한 부분
def _calculate_cpu_score(self, cpu: CPUSpecs) -> int:
    # TODO: 실제 벤치마크 DB 조회
    # Cinebench R23, PassMark 등 기준
    benchmark = self.benchmark_collector.get_cpu_score(cpu.name)
    return self._normalize_score(benchmark)
```

---

### 3.4 가격 예측 모듈 [뼈대]

**파일**: `modules/price_prediction/`

**현재 상태**: 모델 구조만 정의됨 (실제 학습/추론 필요)

#### Main Task

| # | 작업 | 설명 | 예상 시간 |
|---|------|------|----------|
| 1 | 가격 데이터 수집 | 다나와/네이버 크롤러 또는 API | 3일 |
| 2 | 데이터 전처리 | 시계열 피처 생성 | 1일 |
| 3 | 모델 학습 | Prophet 또는 TFT 학습 | 2일 |
| 4 | 추론 파이프라인 | 실시간 예측 API | 1일 |
| 5 | 구매 추천 로직 | 가격 추세 기반 추천 | 1일 |

**핵심 구현 포인트**:
```python
# predictor.py - 실제 구현 필요한 부분
def predict(self, request: PredictionRequest) -> PredictionResult:
    # TODO: 실제 모델 로드 및 추론
    from prophet import Prophet
    model = Prophet()
    model.fit(self._prepare_dataframe(request.price_history))
    future = model.make_future_dataframe(periods=request.prediction_days)
    forecast = model.predict(future)
    return self._parse_forecast(forecast)
```

---

### 3.5 GNN 추천 시스템 [뼈대]

**파일**: `modules/recommendation/`

**현재 상태**: 그래프 구조만 정의됨 (실제 GNN 학습 필요)

#### Main Task

| # | 작업 | 설명 | 예상 시간 |
|---|------|------|----------|
| 1 | 그래프 구축 | 부품 데이터 → 그래프 변환 | 2일 |
| 2 | 호환성 엣지 | 호환성 규칙 기반 엣지 생성 | 2일 |
| 3 | GNN 모델 | GraphSAGE/GAT 구현 | 3일 |
| 4 | 학습 파이프라인 | 추천 태스크 학습 | 2일 |
| 5 | 추론 API | 선택 기반 동적 추천 | 1일 |

**핵심 구현 포인트**:
```python
# models.py - 실제 구현 필요한 부분
class RecommendationGNN(nn.Module):
    def __init__(self, config: GNNConfig):
        # TODO: torch_geometric 레이어 구성
        self.conv1 = SAGEConv(config.input_dim, config.hidden_dim)
        self.conv2 = SAGEConv(config.hidden_dim, config.output_dim)
    
    def forward(self, x, edge_index):
        # TODO: 메시지 패싱 구현
        pass
```

---

### 3.6 호환성 검사 모듈 [뼈대]

**파일**: `modules/compatibility/`

**현재 상태**: 규칙 구조만 정의됨 (실제 검증 로직 필요)

#### Main Task

| # | 작업 | 설명 | 예상 시간 |
|---|------|------|----------|
| 1 | 소켓 DB | CPU-메인보드 소켓 매핑 데이터 | 1일 |
| 2 | 규칙 구현 | 8가지 호환성 규칙 실제 로직 | 3일 |
| 3 | 스펙 파싱 | 부품 스펙 문자열 파싱 | 2일 |
| 4 | 전력 계산 | TDP 기반 PSU 요구량 계산 | 1일 |
| 5 | 테스트 | 다양한 조합 케이스 테스트 | 1일 |

**핵심 구현 포인트**:
```python
# rules.py - 실제 구현 필요한 부분
def check_cpu_mb_socket(cpu_specs: dict, mb_specs: dict) -> RuleResult:
    # TODO: 실제 소켓 호환성 검사
    cpu_socket = cpu_specs.get("socket", "")
    mb_socket = mb_specs.get("socket", "")
    
    is_compatible = cpu_socket == mb_socket
    return RuleResult(
        passed=is_compatible,
        message=f"CPU 소켓 {cpu_socket} {'==' if is_compatible else '!='} 메인보드 소켓 {mb_socket}"
    )
```

---

### 3.7 Step-by-Step RAG [뼈대]

**파일**: `rag/step_by_step.py`

**현재 상태**: 흐름만 정의됨 (세션 관리, 호환성 필터 필요)

#### Main Task

| # | 작업 | 설명 | 예상 시간 |
|---|------|------|----------|
| 1 | 세션 관리 | Redis/메모리 기반 세션 저장 | 1일 |
| 2 | 컨텍스트 빌드 | 이전 선택 기반 쿼리 생성 | 1일 |
| 3 | 호환성 필터 | 후보 필터링 로직 연동 | 1일 |
| 4 | 예산 분배 | 단계별 예산 동적 조정 | 1일 |
| 5 | 테스트 | 전체 8단계 플로우 테스트 | 1일 |

---

## 4. 프론트엔드 연결 계획

### 현재 연결 상태

```javascript
// frontend/js/api.js - 현재 구현
export async function getPCRecommendation(userMessage, options = {}) {
    // POST /query 호출
}
```

### 추가 필요한 API 호출

```javascript
// frontend/js/api.js - 추가 구현 필요

// 내 사양 진단
export async function diagnosePCSpecs(specs) {
    // POST /diagnose
    return fetch(`${API_BASE_URL}/diagnose`, {
        method: 'POST',
        body: JSON.stringify(specs)
    });
}

// 가격 예측
export async function predictPrice(componentId) {
    // POST /predict-price
}

// 호환성 검사
export async function checkCompatibility(components) {
    // POST /compatibility
}

// 단계별 선택
export async function getStepCandidates(sessionId, step, selections) {
    // POST /step/next
}
```

### UI 추가 필요 사항

| 기능 | 현재 | 추가 필요 |
|------|------|----------|
| 기본 추천 | builder.html | - |
| 내 사양 진단 | - | 사양 입력 폼, 결과 표시 |
| 가격 예측 | - | 차트 컴포넌트, 추천 표시 |
| 호환성 검사 | - | 부품 선택 UI, 결과 표시 |
| 단계별 선택 | - | 스텝 위저드 UI |

---

## 5. 사용자 시나리오별 서비스 흐름

### 시나리오 1: 기본 추천 (현재 동작)

```
사용자: "150만원으로 배그 풀옵 PC 추천해줘"
    │
    ▼
[프론트엔드] builder.js
    │ getPCRecommendation()
    ▼
[백엔드] POST /query
    │
    ▼
[RAG] pipeline.query()
    │ 1. 쿼리 임베딩
    │ 2. 벡터 검색
    │ 3. Gemini 응답 생성
    ▼
[응답] 추천 부품 목록 + 설명
    │
    ▼
[프론트엔드] 부품 카드 렌더링
```

### 시나리오 2: 내 사양 진단 (구현 필요)

```
사용자: 현재 PC 사양 입력
    │
    ▼
[프론트엔드] 사양 입력 폼
    │ diagnosePCSpecs()
    ▼
[백엔드] POST /diagnose
    │
    ▼
[PC 진단] PCDiagnosisEngine.diagnose()
    │ 1. 벤치마크 점수 산출
    │ 2. 병목 분석
    │ 3. 업그레이드 추천
    ▼
[응답] 진단 결과 + 업그레이드 제안
    │
    ▼
[프론트엔드] 진단 결과 시각화
```

### 시나리오 3: 단계별 선택 (구현 필요)

```
사용자: "200만원 게이밍 PC" 입력
    │
    ▼
[Step 1: CPU 선택]
    │ POST /step/start
    │ → CPU 후보 3개 제시
    │ → 사용자 선택
    ▼
[Step 2: 메인보드 선택]
    │ POST /step/next (선택한 CPU 정보 포함)
    │ → 호환되는 메인보드만 필터링
    │ → 사용자 선택
    ▼
[Step 3~8: 나머지 부품]
    │ 이전 선택 컨텍스트 누적
    │ 호환성 자동 필터링
    ▼
[완료] 전체 구성 확인 + 호환성 검증
```

### 시나리오 4: 가격 예측 (구현 필요)

```
사용자: RTX 4070 가격 예측 요청
    │
    ▼
[백엔드] POST /predict-price
    │
    ▼
[가격 예측] PricePredictionModel.predict()
    │ 1. 가격 이력 조회
    │ 2. 시계열 예측
    │ 3. 구매 시점 추천
    ▼
[응답]
    - 30일 예측 가격 차트
    - "2주 후 5% 하락 예상"
    - "지금 구매 권장/대기 권장"
```

---

## 6. API 엔드포인트 설계

### 현재 구현된 엔드포인트

| Method | Path | 설명 | 상태 |
|--------|------|------|------|
| GET | `/` | 서비스 정보 | 완성 |
| GET | `/health` | 헬스 체크 | 완성 |
| GET | `/stats` | DB 통계 | 완성 |
| POST | `/query` | 기본 추천 | 완성 |
| POST | `/query-by-specs` | 사양 기반 추천 | 완성 |
| POST | `/compare` | 부품 비교 | 완성 |

### 추가 구현 필요한 엔드포인트

| Method | Path | 설명 | 담당 모듈 |
|--------|------|------|----------|
| POST | `/diagnose` | PC 사양 진단 | pc_diagnosis |
| POST | `/predict-price` | 가격 예측 | price_prediction |
| POST | `/recommend/personalized` | 개인화 추천 | recommendation |
| POST | `/compatibility/check` | 호환성 검사 | compatibility |
| POST | `/step/start` | 단계별 선택 시작 | step_by_step |
| POST | `/step/next` | 다음 단계 후보 | step_by_step |
| POST | `/step/complete` | 선택 완료 | step_by_step |
| POST | `/agent/recommend` | 멀티에이전트 추천 | multi_agent |

---

## 7. 개발 우선순위 및 일정

### 권장 개발 순서

```
Phase 1: 핵심 기능 (2주)
├── 호환성 검사 모듈 완성 ← 다른 모듈의 기반
└── Step-by-Step RAG 완성 ← UX 개선 핵심

Phase 2: 분석 기능 (2주)
├── PC 사양 진단 모듈 완성
└── 가격 예측 모듈 완성

Phase 3: 고급 기능 (3주)
├── GNN 추천 시스템 완성
└── 멀티 에이전트 시스템 완성

Phase 4: 통합 및 최적화 (1주)
├── 프론트엔드 UI 추가
└── 전체 통합 테스트
```

### 모듈별 담당자 배정 (예시)

| 모듈 | 예상 난이도 | 예상 기간 | 권장 인원 |
|------|------------|----------|----------|
| 호환성 검사 | 중 | 1주 | 1명 |
| PC 사양 진단 | 중 | 1주 | 1명 |
| Step-by-Step RAG | 중 | 1주 | 1명 |
| 가격 예측 | 상 | 2주 | 1명 |
| GNN 추천 | 상 | 3주 | 1-2명 |
| 멀티 에이전트 | 상 | 2주 | 1명 |

---

## 핵심 요약

1. **현재 상태**: RAG 기반 기본 추천만 동작, 나머지 모듈은 뼈대(구조+가이드)만 존재
2. **개발 필요**: 각 모듈의 실제 로직 구현 + API 엔드포인트 추가 + 프론트엔드 UI 추가
3. **서빙 방식**: 프론트엔드 → FastAPI → 모듈 레이어 → 데이터 레이어
4. **우선순위**: 호환성 → Step-by-Step → 진단/예측 → GNN/멀티에이전트
