# 데이터 디렉토리

> PC 부품 데이터베이스 및 모듈별 학습/참조 데이터

---

## 폴더 구조

```
data/
├── pc_data_dump.sql              # 기본 PC 부품 데이터 (RAG용)
├── PC 부품 DB 스키마 가이드.pdf    # 스키마 문서
│
├── pc_diagnosis/                 # PC 사양 진단 모듈
│   ├── cpu_benchmarks.json       # CPU 벤치마크 점수
│   ├── gpu_benchmarks.json       # GPU 벤치마크 점수
│   ├── game_requirements.json    # 게임별 권장사양
│   ├── purpose_specs.json        # 용도별 권장 스펙
│   └── README.md                 # 데이터 가이드
│
├── price_prediction/             # 가격 예측 모듈
│   ├── price_history/            # 부품별 가격 이력
│   │   ├── gpu/                  # GPU 가격
│   │   ├── cpu/                  # CPU 가격
│   │   └── ...
│   ├── exchange_rates.json       # 환율 데이터
│   ├── product_releases.json     # 출시/단종 일정
│   ├── sale_events.json          # 세일 이벤트 캘린더
│   └── README.md                 # 데이터 가이드
│
├── recommendation/               # GNN 추천 모듈
│   ├── component_nodes.json      # 부품 노드 데이터
│   ├── compatibility_edges.json  # 호환성 엣지
│   ├── synergy_edges.json        # 시너지 엣지
│   ├── attribute_mappings.json   # 속성 매핑
│   ├── popular_builds.json       # 인기 조합
│   └── README.md                 # 데이터 가이드
│
├── compatibility/                # 호환성 검사 모듈
│   ├── cpu_socket_map.json       # CPU 소켓 매핑
│   ├── memory_compatibility.json # 메모리 호환성
│   ├── form_factor_map.json      # 폼팩터 매핑
│   ├── psu_requirements.json     # 전력 요구량
│   ├── physical_dimensions.json  # 물리적 치수
│   └── README.md                 # 데이터 가이드
│
└── README.md                     # 이 파일
```

---

## 기본 데이터 (RAG용)

### pc_data_dump.sql

- **용량**: 약 11MB
- **레코드 수**: 135,660개
- **카테고리**: CPU, GPU, 메모리, 메인보드, SSD, PSU, 케이스, 쿨러 등

이 데이터는 RAG 시스템의 벡터 DB 구축에 사용된다.

```bash
# 벡터 DB 초기화
python backend/scripts/init_database.py
```

---

## 모듈별 데이터 요약

| 모듈 | 주요 데이터 | 수집 방법 | 상세 |
|------|------------|----------|------|
| PC 진단 | 벤치마크 점수 | PassMark, Cinebench 크롤링 | [README](./pc_diagnosis/README.md) |
| 가격 예측 | 가격 이력 | 다나와/네이버 크롤링 | [README](./price_prediction/README.md) |
| GNN 추천 | 그래프 데이터 | 기존 SQL + 규칙 생성 | [README](./recommendation/README.md) |
| 호환성 | 스펙 매핑 | 수동 정리 + 제조사 데이터 | [README](./compatibility/README.md) |

---

## 데이터 수집 우선순위

### Phase 1: 필수 (서비스 동작용)

1. **호환성 데이터** - 소켓, 폼팩터, 전력
2. **벤치마크 데이터** - CPU/GPU 상위 50개

### Phase 2: 권장 (기능 완성용)

3. **가격 이력** - 최소 3개월 데이터
4. **그래프 데이터** - 노드/엣지 생성

### Phase 3: 선택 (고도화용)

5. **게임 권장사양** - 인기 게임 30개
6. **인기 조합** - 커뮤니티 견적 50개

---

## 데이터 관리 규칙

### 파일 명명 규칙

```
{category}_{type}.json
{category}_{type}_{date}.json  # 버전 관리 시
```

예시:
- `cpu_benchmarks.json`
- `gpu_benchmarks_20241231.json`

### JSON 공통 헤더

```json
{
  "version": "1.0.0",
  "updated_at": "2024-12-31",
  "source": ["데이터 출처"],
  "data": [...]
}
```

### Git 관리

- 작은 JSON 파일: Git에 커밋
- 큰 파일 (>1MB): `.gitignore`에 추가, 별도 공유

```gitignore
# 대용량 데이터
data/price_prediction/price_history/
data/pc_diagnosis/*_full.json
```

---

## 데이터 검증

각 모듈의 README에 검증 스크립트 포함.

```bash
# 전체 데이터 검증
python backend/scripts/validate_data.py

# 특정 모듈 검증
python backend/scripts/validate_data.py --module compatibility
```

---

## 담당자

| 데이터 | 담당자 | 상태 |
|--------|--------|------|
| 호환성 | [이름] | 진행중 |
| 벤치마크 | [이름] | 대기 |
| 가격 이력 | [이름] | 대기 |
| 그래프 | [이름] | 대기 |
