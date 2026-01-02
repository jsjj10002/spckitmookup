# PC Diagnosis 모듈

> PC 사양 진단 및 병목 분석 시스템

## 목차

- [개요](#개요)
- [아키텍처](#아키텍처)
- [파일 구조](#파일-구조)
- [핵심 기능](#핵심-기능)
- [데이터 모델](#데이터-모델)
- [사용법](#사용법)
- [구현 가이드](#구현-가이드)
- [테스트](#테스트)
- [참고 자료](#참고-자료)

---

## 개요

### 목표

사용자의 현재 PC 사양을 종합적으로 분석하여 다음을 제공:
1. 현재 사양의 **성능 등급 판정**
2. **병목 현상(Bottleneck) 탐지**
3. **목적별 적합성 평가** (게임, 업무, 개발 등)
4. **업그레이드 우선순위 추천**

### 배경 지식

PC 성능은 개별 부품 성능뿐만 아니라 **부품 간 밸런스**에 크게 영향을 받는다.

**병목 현상(Bottleneck) 유형:**

| 유형 | 설명 | 증상 |
|------|------|------|
| **CPU 병목** | CPU가 GPU보다 느림 | GPU 사용률 낮음, 1% Low FPS 저하 |
| **GPU 병목** | GPU가 CPU보다 느림 | GPU 사용률 99%, 이상적인 상태 |
| **메모리 병목** | RAM 용량/속도 부족 | 스왑 발생, 전체 성능 저하 |
| **스토리지 병목** | 느린 저장장치 | 로딩 지연, 게임 끊김 |

---

## 아키텍처

```
사용자 입력 (PC 사양)
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                    PCDiagnosisEngine                         │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────────────────────┐ │
│  │ HardwareCollector │→│         스펙 정규화              │ │
│  │ (하드웨어 정보)   │  │  (다양한 입력 포맷 통일)        │ │
│  └──────────────────┘  └───────────────┬──────────────────┘ │
│                                         │                    │
│                                         ▼                    │
│  ┌──────────────────┐  ┌──────────────────────────────────┐ │
│  │ BenchmarkCollector│→│      성능 점수 산출              │ │
│  │ (벤치마크 DB)     │  │  (Cinebench, 3DMark 기준)       │ │
│  └──────────────────┘  └───────────────┬──────────────────┘ │
│                                         │                    │
│                                         ▼                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │               BottleneckAnalyzer                      │   │
│  │  - CPU vs GPU 밸런스 분석                            │   │
│  │  - 메모리 대역폭 분석                                │   │
│  │  - 스토리지 병목 분석                                │   │
│  └──────────────────────────┬───────────────────────────┘   │
│                              │                               │
│                              ▼                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │               UpgradeAdvisor                          │   │
│  │  - 업그레이드 우선순위 결정                          │   │
│  │  - 예산별 업그레이드 옵션 제안                       │   │
│  │  - ROI(투자 대비 성능 향상) 계산                     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
진단 결과 (DiagnosisResult)
```

---

## 파일 구조

```
pc_diagnosis/
├── __init__.py          # 모듈 초기화 및 exports
├── engine.py            # 메인 진단 엔진 (PCDiagnosisEngine)
├── collectors.py        # 하드웨어/벤치마크 정보 수집기
├── analyzers.py         # 병목 분석기 및 업그레이드 조언
└── README.md            # 이 문서
```

### 파일별 역할

| 파일 | 역할 | 주요 클래스 |
|------|------|-------------|
| `engine.py` | 진단 파이프라인 전체 흐름 관리 | `PCDiagnosisEngine`, `DiagnosisResult`, 벤치마크 DB |
| `collectors.py` | 하드웨어 정보 수집 및 정규화 | `HardwareCollector`, `BenchmarkCollector` |
| `analyzers.py` | 병목 분석 및 업그레이드 추천 | `BottleneckAnalyzer`, `UpgradeAdvisor` |

---

## 핵심 기능

### 1. 하드웨어 정보 수집 (HardwareCollector)

다양한 형식의 입력을 표준화된 형태로 변환한다.

**지원 입력 형식:**
- 자연어: "i5 12400f, RTX 3060, 램 16기가"
- JSON: `{"cpu": "Intel Core i5-12400F", "gpu": "RTX 3060"}`
- 구조화된 딕셔너리

**정규화 예시:**

| 입력 | 정규화 결과 |
|------|-------------|
| "i5 12400f" | "i5-12400" |
| "Intel Core i5-12400F" | "i5-12400" |
| "GeForce RTX 3060" | "rtx 3060" |
| "라이젠 5 5600x" | "ryzen 5 5600x" |

### 2. 벤치마크 점수 조회 (BenchmarkCollector)

CPU/GPU의 성능 점수를 벤치마크 데이터베이스에서 조회한다.

**점수 기준:**
- **CPU**: Cinebench R23 Multi-Thread 기준 (100점 = i9-14900K)
- **GPU**: 3DMark Time Spy 기준 (100점 = RTX 4090)

**벤치마크 점수 예시:**

| CPU | 점수 | GPU | 점수 |
|-----|------|-----|------|
| i9-14900K | 100 | RTX 4090 | 100 |
| i7-14700K | 88 | RTX 4080 | 85 |
| i5-14600K | 75 | RTX 4070 Ti | 72 |
| i5-12400F | 55 | RTX 4060 | 45 |
| Ryzen 7 7800X3D | 72 | RTX 3060 | 45 |

### 3. 병목 분석 (BottleneckAnalyzer)

CPU-GPU 점수 차이를 기반으로 병목 현상을 분석한다.

**병목 심각도:**

| 심각도 | 점수 차이 | 설명 |
|--------|----------|------|
| NONE | < 10% | 밸런스 양호 |
| MINOR | 10-20% | 경미한 병목 |
| MODERATE | 20-35% | 중간 병목 |
| SEVERE | 35-50% | 심각한 병목 |
| CRITICAL | > 50% | 치명적 병목 |

**해상도별 분석 가중치:**

| 해상도 | CPU 의존도 | GPU 의존도 |
|--------|-----------|-----------|
| 1080p | 40% | 50% |
| 1440p | 25% | 65% |
| 4K | 15% | 80% |

### 4. 업그레이드 추천 (UpgradeAdvisor)

병목 현상과 현재 스펙을 기반으로 최적의 업그레이드 경로를 제안한다.

**추천 기준:**
- ROI (투자 대비 성능 향상)
- 현재 시스템과의 호환성
- 향후 확장성

---

## 데이터 모델

### 입력: UserPCSpecs

```python
{
    "cpu": {
        "name": "Intel Core i5-12400F",
        "cores": 6,
        "threads": 12,
        "base_clock": 2.5,  # GHz
        "boost_clock": 4.4
    },
    "gpu": {
        "name": "RTX 3060",
        "vram": 12,  # GB
        "memory_type": "GDDR6"
    },
    "memory": {
        "capacity": 16,  # GB
        "speed": 3200,  # MHz
        "channels": 2,
        "generation": "DDR4"
    },
    "storage": {
        "type": "NVMe SSD",
        "capacity": 512,  # GB
        "read_speed": 3500  # MB/s
    },
    "usage_purpose": "gaming"  # gaming, work, development, streaming
}
```

### 출력: DiagnosisResult

```python
{
    "overall_score": 65,  # 100점 만점
    "tier": "mid-high",   # entry, mid, mid-high, high, enthusiast
    "bottleneck": {
        "type": "cpu",    # cpu, gpu, memory, storage, none
        "severity": 25,   # 0-100
        "description": "CPU가 GPU 대비 성능이 낮아 병목이 발생할 수 있습니다."
    },
    "component_scores": {
        "cpu": {"score": 55, "tier": "mid", "notes": "Intel Core i5-12400F"},
        "gpu": {"score": 45, "tier": "mid", "notes": "RTX 3060, VRAM 12GB"},
        "memory": {"score": 65, "tier": "mid-high", "notes": "16GB DDR4-3200"},
        "storage": {"score": 85, "tier": "high", "notes": "NVMe SSD 512GB"}
    },
    "purpose_fitness": {
        "gaming": 0.65,
        "work": 0.70,
        "development": 0.68,
        "streaming": 0.55
    },
    "upgrade_recommendations": [
        {
            "component": "cpu",
            "current": "Intel Core i5-12400F",
            "recommended": "i5-13600K 또는 i5-14600K",
            "expected_improvement": 25,  # %
            "estimated_cost": 350000,
            "priority": 1
        },
        {
            "component": "memory",
            "current": "16GB DDR4-3200",
            "recommended": "32GB DDR4-3600",
            "expected_improvement": 15,
            "estimated_cost": 80000,
            "priority": 2
        }
    ]
}
```

---

## 사용법

### 기본 진단

```python
from backend.modules.pc_diagnosis import PCDiagnosisEngine

engine = PCDiagnosisEngine()

# PC 스펙 정의
specs = {
    "cpu": {
        "name": "Intel Core i5-12400F",
        "cores": 6,
        "threads": 12
    },
    "gpu": {
        "name": "RTX 3060",
        "vram": 12
    },
    "memory": {
        "capacity": 16,
        "speed": 3200,
        "generation": "DDR4"
    },
    "storage": {
        "type": "NVMe SSD",
        "capacity": 512
    },
    "usage_purpose": "gaming"
}

# 진단 실행
result = engine.diagnose(specs)

print(f"전체 점수: {result.overall_score}/100")
print(f"등급: {result.tier.value}")
print(f"병목: {result.bottleneck.description}")
```

### 자연어 입력 파싱

```python
from backend.modules.pc_diagnosis.collectors import HardwareCollector

collector = HardwareCollector()

# 자연어에서 스펙 추출
specs = collector.parse_natural_language(
    "i5 12400f, RTX 3060, 램 16기가, SSD 512GB"
)

print(specs)
# {'cpu': {'name': 'i5-12400'}, 'gpu': {'name': 'rtx 3060'}, ...}
```

### 병목 분석

```python
from backend.modules.pc_diagnosis.analyzers import BottleneckAnalyzer

analyzer = BottleneckAnalyzer()

result = analyzer.analyze(
    cpu_score=55,
    gpu_score=72,
    memory_score=65,
    resolution="1080p",
    workload="gaming"
)

print(f"병목 유형: {result.component}")
print(f"심각도: {result.severity.value}")
print(f"영향: {result.impact_areas}")
```

### 업그레이드 추천

```python
from backend.modules.pc_diagnosis.analyzers import UpgradeAdvisor

advisor = UpgradeAdvisor()

options = advisor.recommend(
    current_specs=specs,
    component_scores=component_scores,
    bottleneck_result=bottleneck,
    budget=500000  # 50만원
)

for opt in options:
    print(f"{opt.component}: {opt.current} → {opt.recommended}")
    print(f"  예상 향상: {opt.expected_improvement}%")
    print(f"  예상 비용: {opt.price_range[0]:,}원 ~ {opt.price_range[1]:,}원")
    print(f"  ROI 점수: {opt.roi_score}")
```

---

## 구현 가이드

### 1단계: 벤치마크 데이터베이스 구축

`engine.py`의 `CPU_BENCHMARK_SCORES`, `GPU_BENCHMARK_SCORES` 딕셔너리를 확장한다.

```python
CPU_BENCHMARK_SCORES = {
    # Intel 14세대
    "i9-14900k": 100,
    "i7-14700k": 88,
    "i5-14600k": 75,
    # ... 더 많은 CPU 추가
}

GPU_BENCHMARK_SCORES = {
    # NVIDIA RTX 40시리즈
    "rtx 4090": 100,
    "rtx 4080": 85,
    # ... 더 많은 GPU 추가
}
```

### 2단계: 점수 산출 로직 구현

각 부품 카테고리별 점수 계산 로직을 구현한다.

**메모리 점수 계산:**
- 용량 기준 (최대 50점): 64GB=50, 32GB=40, 16GB=30, 8GB=15
- 속도 기준 (최대 30점): 6000MHz+=30, 4800MHz+=25, 3600MHz+=20
- 채널 기준 (최대 20점): 4채널=20, 2채널=15, 1채널=5

**스토리지 점수 계산:**
- 타입 기준 (최대 60점): NVMe=60, SATA SSD=40, HDD=15
- 속도 기준 (최대 40점): 7000MB/s+=40, 5000MB/s+=35, 3000MB/s+=25

### 3단계: 외부 데이터 연동 (선택)

실시간 벤치마크 데이터를 위해 외부 API 연동을 구현한다.

```python
# 예시: UserBenchmark API (비공식)
# PassMark API
# Cinebench 결과 데이터베이스
```

### 4단계: 프론트엔드 연동

브라우저에서 시스템 정보 자동 수집 기능을 구현한다 (선택적).

```javascript
// navigator.userAgentData 등 활용
const systemInfo = await navigator.userAgentData.getHighEntropyValues([
    "platform", "platformVersion", "architecture"
]);
```

---

## 테스트

### 테스트 파일 위치

```
backend/tests/test_pc_diagnosis.py
```

### 테스트 실행

```bash
# 전체 테스트
pytest backend/tests/test_pc_diagnosis.py -v

# 특정 테스트
pytest backend/tests/test_pc_diagnosis.py::test_diagnosis_engine -v
```

### 테스트 항목

1. **진단 엔진 테스트**
   - 정상 스펙 진단
   - 부족한 정보 처리
   
2. **벤치마크 점수 조회 테스트**
   - 정확한 매칭
   - 부분 매칭
   - 매칭 실패 시 기본값

3. **병목 분석 테스트**
   - CPU 병목 감지
   - GPU 병목 감지
   - 밸런스 양호 판정

4. **업그레이드 추천 테스트**
   - 예산 내 옵션 필터링
   - ROI 점수 계산

---

## TODO

### 필수 구현

- [ ] 벤치마크 데이터베이스 확장 (더 많은 CPU/GPU)
- [ ] 벤치마크 데이터 JSON 파일 외부화
- [ ] 메모리 병목 분석 상세화
- [ ] 스토리지 병목 분석 추가

### 선택적 구현

- [ ] 외부 벤치마크 API 연동 (UserBenchmark, PassMark)
- [ ] 게임별 성능 예측 (특정 게임 FPS 추정)
- [ ] 실시간 가격 연동으로 업그레이드 비용 정확도 향상
- [ ] 그래픽 시각화 (점수 차트, 병목 다이어그램)

---

## 참고 자료

### 벤치마크 소스

- [Cinebench R23](https://www.maxon.net/en/cinebench) - CPU 벤치마크
- [3DMark](https://www.3dmark.com/) - GPU 벤치마크
- [UserBenchmark](https://www.userbenchmark.com/) - 상대적 성능 비교

### 병목 분석 참고

- [Tom's Hardware Bottleneck Calculator](https://www.tomshardware.com/)
- [PC-Builds.com Bottleneck Calculator](https://pc-builds.com/bottleneck-calculator/)

### 기술 문서

- [Pydantic 문서](https://docs.pydantic.dev/)
- [NumPy 문서](https://numpy.org/doc/)

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2026-01-02 | 0.1.0 | 초기 스켈레톤 구현 |
