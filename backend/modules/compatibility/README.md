# Compatibility 모듈

> 온톨로지 기반 PC 부품 호환성 검사 시스템

## 목차

- [개요](#개요)
- [아키텍처](#아키텍처)
- [파일 구조](#파일-구조)
- [호환성 규칙](#호환성-규칙)
- [데이터 모델](#데이터-모델)
- [사용법](#사용법)
- [구현 가이드](#구현-가이드)
- [테스트](#테스트)
- [참고 자료](#참고-자료)

---

## 개요

### 목표

PC 부품 간의 물리적/논리적 호환성을 **온톨로지와 규칙 기반**으로 검증하여, 사용자가 선택한 부품들이 실제로 조립 가능한지 확인한다.

### 호환성 검사 항목

| 검사 항목 | 관련 부품 | 검사 내용 |
|-----------|----------|----------|
| **소켓 호환성** | CPU, 메인보드, 쿨러 | 소켓 타입 일치 |
| **메모리 호환성** | 메모리, 메인보드 | DDR 세대, 속도, 용량 |
| **PCIe 호환성** | GPU, 메인보드 | PCIe 버전, 레인 수 |
| **폼팩터 호환성** | 메인보드, 케이스 | ATX, Micro-ATX 등 |
| **물리적 호환성** | GPU, 케이스 | GPU 길이, 쿨러 높이 |
| **전력 호환성** | GPU, PSU | TDP, 전원 커넥터 |
| **스토리지 호환성** | 저장장치, 메인보드 | M.2, SATA 슬롯 |

### 핵심 기술

- **온톨로지(Ontology)**: 부품 개념/속성/관계의 형식적 정의
- **규칙 엔진(Rule Engine)**: 조건-검사-결과 기반 규칙 처리
- **지식 그래프**: 부품 간 관계를 그래프로 표현

---

## 아키텍처

```
                    ┌────────────────────────────────────────┐
                    │         CompatibilityEngine            │
                    │                                        │
부품 목록 입력 ────▶│  ┌────────────────────────────────┐  │
                    │  │         PCOntology              │  │
                    │  │  (지식 그래프 / 온톨로지)       │  │
                    │  │  - 부품 클래스 정의             │  │
                    │  │  - 속성 관계 정의               │  │
                    │  │  - 호환성 규칙 정의             │  │
                    │  └──────────────┬─────────────────┘  │
                    │                 │                     │
                    │                 ▼                     │
                    │  ┌────────────────────────────────┐  │
                    │  │      CompatibilityRules        │  │
                    │  │  (규칙 기반 추론 엔진)          │  │
                    │  │  - 소켓 호환성 규칙            │  │
                    │  │  - 폼팩터 규칙                 │  │
                    │  │  - 전력 계산 규칙              │  │
                    │  │  - 물리적 치수 규칙            │  │
                    │  └──────────────┬─────────────────┘  │
                    │                 │                     │
                    │                 ▼                     │
                    │  ┌────────────────────────────────┐  │
                    │  │      Validation Result         │  │
                    │  │  - 호환성 결과                 │  │
                    │  │  - 경고 사항                   │  │
                    │  │  - 권장 사항                   │  │
                    │  └────────────────────────────────┘  │
                    └────────────────────────────────────────┘
```

---

## 파일 구조

```
compatibility/
├── __init__.py          # 모듈 초기화 및 exports
├── engine.py            # 메인 호환성 검사 엔진
├── rules.py             # 호환성 규칙 정의
├── ontology.py          # PC 부품 온톨로지 정의
└── README.md            # 이 문서
```

### 파일별 역할

| 파일 | 역할 | 주요 클래스 |
|------|------|-------------|
| `engine.py` | 호환성 검사 파이프라인 | `CompatibilityEngine`, `CompatibilityResult` |
| `rules.py` | 개별 호환성 규칙 | `CompatibilityRules`, `RuleResult` |
| `ontology.py` | 부품 개념/속성 정의 | `PCOntology`, `ComponentClass` |

---

## 호환성 규칙

### 1. CPU-메인보드 소켓 규칙

| 소켓 | 지원 CPU | 지원 칩셋 |
|------|----------|----------|
| **LGA1700** | Intel 12/13/14세대 | Z790, Z690, B760, B660, H770, H610 |
| **LGA1200** | Intel 10/11세대 | Z590, Z490, B560, B460 |
| **AM5** | AMD Ryzen 7000 | X670E, X670, B650E, B650, A620 |
| **AM4** | AMD Ryzen 3000/5000 | X570, X470, B550, B450, A520 |

**규칙 예시:**
```python
if cpu.socket == motherboard.socket:
    status = PASS
else:
    status = FAIL
    message = f"소켓 불일치: CPU({cpu.socket}) ≠ 메인보드({mb.socket})"
```

### 2. 메모리-메인보드 규칙

| 메모리 타입 | 지원 소켓 | 속도 범위 |
|-------------|----------|----------|
| **DDR5** | LGA1700, AM5 | 4800-8000 MHz |
| **DDR4** | LGA1700, LGA1200, AM4 | 2133-5333 MHz |

**검사 항목:**
- DDR 세대 일치
- 최대 지원 속도
- 최대 지원 용량
- 슬롯 수

### 3. 메인보드-케이스 폼팩터 규칙

| 케이스 폼팩터 | 지원 메인보드 |
|---------------|---------------|
| **E-ATX** | E-ATX, ATX, Micro-ATX, Mini-ITX |
| **ATX** | ATX, Micro-ATX, Mini-ITX |
| **Micro-ATX** | Micro-ATX, Mini-ITX |
| **Mini-ITX** | Mini-ITX |

### 4. GPU-케이스 물리적 규칙

| GPU 티어 | 일반적 길이 | 권장 케이스 허용 |
|----------|------------|-----------------|
| 하이엔드 (4090) | 336mm+ | 380mm+ |
| 상위 (4080, 4070 Ti) | 300-330mm | 340mm+ |
| 중급 (4070, 4060) | 240-280mm | 300mm+ |

### 5. 전력 규칙

**TDP 계산:**
```
총 TDP = CPU TDP + GPU TDP + 기타(~100W)
권장 PSU = 총 TDP × 1.3 ~ 1.5
```

**GPU별 권장 PSU:**

| GPU | TDP | 권장 PSU | 전원 커넥터 |
|-----|-----|----------|-------------|
| RTX 4090 | 450W | 850W | 16-pin |
| RTX 4080 | 320W | 750W | 16-pin |
| RTX 4070 Ti | 285W | 700W | 8-pin x2 |
| RTX 4070 | 200W | 650W | 8-pin |
| RTX 4060 | 115W | 500W | 8-pin |

---

## 데이터 모델

### 입력: ComponentList

```python
{
    "components": [
        {
            "category": "cpu",
            "name": "Intel Core i5-14600K",
            "specs": {
                "socket": "LGA1700",
                "tdp": 125,
                "generation": 14
            }
        },
        {
            "category": "motherboard",
            "name": "ASUS ROG Strix Z790-A",
            "specs": {
                "socket": "LGA1700",
                "chipset": "Z790",
                "form_factor": "ATX",
                "memory_type": "DDR5",
                "memory_slots": 4,
                "m2_slots": 4
            }
        },
        {
            "category": "memory",
            "name": "Samsung DDR5-5600 32GB",
            "specs": {
                "generation": "DDR5",
                "capacity": 32,
                "speed": 5600
            }
        },
        {
            "category": "gpu",
            "name": "RTX 4070",
            "specs": {
                "tdp": 200,
                "length": 300
            }
        },
        {
            "category": "psu",
            "name": "Corsair RM750",
            "specs": {
                "wattage": 750
            }
        },
        {
            "category": "case",
            "name": "NZXT H7 Flow",
            "specs": {
                "form_factor": "ATX",
                "max_gpu_length": 400,
                "max_cooler_height": 185
            }
        }
    ]
}
```

### 출력: CompatibilityResult

```python
{
    "is_compatible": True,
    "overall_score": 95,  # 100점 만점
    "checks": [
        {
            "check_id": "cpu_mb_socket",
            "name": "CPU-메인보드 소켓 호환성",
            "components": ["cpu", "motherboard"],
            "status": "pass",  # pass, fail, warning, unknown
            "message": "LGA1700 소켓으로 완벽 호환",
            "details": {
                "cpu_socket": "LGA1700",
                "mb_socket": "LGA1700"
            }
        },
        {
            "check_id": "mem_mb_type",
            "name": "메모리-메인보드 호환성",
            "components": ["memory", "motherboard"],
            "status": "pass",
            "message": "DDR5 메모리 호환",
            "details": {
                "memory_type": "DDR5"
            }
        },
        {
            "check_id": "power_check",
            "name": "전력 호환성",
            "components": ["psu"],
            "status": "pass",
            "message": "전력 여유 충분: 750W (권장 600W)",
            "details": {
                "current": 750,
                "recommended": 600,
                "tdp": 425
            }
        }
    ],
    "power_summary": {
        "total_tdp": 425,
        "recommended_psu": 600,
        "current_psu": 750,
        "headroom_pct": 43.3
    },
    "recommendations": [
        "현재 구성은 호환성이 우수합니다.",
        "고성능 쿨러 사용 시 CPU 성능 향상 가능"
    ]
}
```

---

## 사용법

### 기본 호환성 검사

```python
from backend.modules.compatibility import CompatibilityEngine

engine = CompatibilityEngine()

# 부품 목록 정의
components = [
    {
        "category": "cpu",
        "name": "Intel Core i5-14600K",
        "specs": {"socket": "LGA1700", "tdp": 125}
    },
    {
        "category": "motherboard",
        "name": "ASUS ROG Strix Z790-A",
        "specs": {"socket": "LGA1700", "memory_type": "DDR5", "form_factor": "ATX"}
    },
    {
        "category": "memory",
        "name": "Samsung DDR5-5600 32GB",
        "specs": {"generation": "DDR5"}
    }
]

# 호환성 검사
result = engine.check_all(components)

print(f"호환 여부: {result.is_compatible}")
print(f"점수: {result.overall_score}/100")

for check in result.checks:
    status = "PASS" if check.status.value == "pass" else "FAIL"
    print(f"[{status}] {check.name}: {check.message}")
```

### 간편 함수 사용

```python
from backend.modules.compatibility import check_compatibility

result = check_compatibility(components)

if not result.is_compatible:
    for check in result.checks:
        if check.status.value == "fail":
            print(f"호환 불가: {check.message}")
```

### 규칙 엔진 직접 사용

```python
from backend.modules.compatibility.rules import CompatibilityRules

rules = CompatibilityRules()

# 두 부품 간 호환성 검사
cpu = {"category": "cpu", "name": "i5-14600K", "specs": {"socket": "LGA1700"}}
mb = {"category": "motherboard", "name": "Z790-A", "specs": {"socket": "LGA1700"}}

results = rules.check_pair(cpu, mb)

for result in results:
    print(f"{result.rule_id}: {result.message}")
    print(f"  통과: {result.passed}")
```

### 온톨로지 사용

```python
from backend.modules.compatibility.ontology import PCOntology, ComponentClass

ontology = PCOntology()

# 부품(개체) 추가
ontology.add_individual(
    id="cpu_i5_14600k",
    class_type=ComponentClass.CPU,
    properties={
        "name": "Intel Core i5-14600K",
        "hasSocket": "LGA1700",
        "hasTDP": 125
    }
)

ontology.add_individual(
    id="mb_asus_z790",
    class_type=ComponentClass.MOTHERBOARD,
    properties={
        "name": "ASUS ROG Strix Z790-A",
        "hasSocket": "LGA1700",
        "hasMemoryType": "DDR5"
    }
)

# 호환 가능한 메인보드 질의
compatible_mbs = ontology.query_compatible(
    "cpu_i5_14600k",
    ComponentClass.MOTHERBOARD
)

for mb in compatible_mbs:
    print(f"호환 메인보드: {mb.properties.get('name')}")

# 온톨로지 저장
ontology.export_to_json("pc_ontology.json")
```

---

## 구현 가이드

### 1단계: 호환성 데이터베이스 구축

소켓, 칩셋, 폼팩터 등 호환성 정보를 데이터베이스로 구축한다.

```python
# engine.py에 호환성 데이터 추가

INTEL_COMPATIBILITY = {
    "LGA1700": {
        "generations": [12, 13, 14],
        "chipsets": ["Z790", "Z690", "B760", "B660", "H770", "H610"],
        "memory": ["DDR5", "DDR4"],
    },
    # ...
}

AMD_COMPATIBILITY = {
    "AM5": {
        "generations": [7000],
        "chipsets": ["X670E", "X670", "B650E", "B650", "A620"],
        "memory": ["DDR5"],
    },
    # ...
}
```

### 2단계: 규칙 함수 구현

각 호환성 검사를 위한 규칙 함수를 구현한다.

```python
# rules.py

def check_cpu_mb_socket(cpu: Dict, mb: Dict) -> RuleResult:
    """CPU-메인보드 소켓 호환성 검사"""
    cpu_socket = cpu.get("specs", {}).get("socket", "")
    mb_socket = mb.get("specs", {}).get("socket", "")
    
    # 이름에서 소켓 추론 (스펙 정보 없는 경우)
    if not cpu_socket:
        cpu_socket = infer_cpu_socket(cpu.get("name", ""))
    
    if not mb_socket:
        mb_socket = infer_mb_socket(mb.get("name", ""))
    
    if cpu_socket == mb_socket:
        return RuleResult(
            rule_id="cpu_mb_socket",
            passed=True,
            severity=RuleSeverity.INFO,
            message=f"{cpu_socket} 소켓으로 호환됩니다."
        )
    else:
        return RuleResult(
            rule_id="cpu_mb_socket",
            passed=False,
            severity=RuleSeverity.ERROR,
            message=f"소켓 불일치: CPU({cpu_socket}) ≠ 메인보드({mb_socket})"
        )
```

### 3단계: 온톨로지 확장

OWL(Web Ontology Language) 형식으로 온톨로지를 확장한다 (선택적).

```python
# OWLReady2 예시
from owlready2 import *

onto = get_ontology("http://example.org/pc_components.owl")

with onto:
    class Component(Thing):
        pass
    
    class CPU(Component):
        pass
    
    class hasSocket(DataProperty):
        domain = [CPU, Motherboard]
        range = [str]
    
    class compatibleWith(ObjectProperty):
        domain = [Component]
        range = [Component]
```

### 4단계: 추론 엔진 연동

온톨로지 추론 엔진을 연동하여 암묵적 지식을 도출한다.

```python
# OWLReady2 추론 예시
with onto:
    # 규칙 정의
    rule = Imp()
    rule.set_as_rule("""
        CPU(?c), Motherboard(?m), hasSocket(?c, ?s), hasSocket(?m, ?s)
        -> compatibleWith(?c, ?m)
    """)

# 추론 실행
sync_reasoner_pellet(infer_property_values=True)
```

---

## 테스트

### 테스트 파일 위치

```
backend/tests/test_compatibility.py
```

### 테스트 실행

```bash
# 전체 테스트
pytest backend/tests/test_compatibility.py -v

# 특정 테스트
pytest backend/tests/test_compatibility.py::test_compatibility_check -v
```

### 테스트 항목

1. **호환 조합 테스트**
   - Intel CPU + Intel 칩셋 메인보드
   - AMD CPU + AMD 칩셋 메인보드
   - 올바른 폼팩터 조합

2. **비호환 조합 테스트**
   - Intel CPU + AMD 메인보드
   - DDR4 메모리 + DDR5 전용 메인보드
   - 큰 GPU + 작은 케이스

3. **전력 계산 테스트**
   - TDP 합산
   - PSU 권장 용량 계산
   - 여유율 계산

4. **엣지 케이스 테스트**
   - 스펙 정보 누락 시 처리
   - 알 수 없는 부품 처리

---

## TODO

### 필수 구현

- [ ] 더 많은 소켓/칩셋 호환성 데이터 추가
- [ ] BIOS 버전 호환성 체크 (최신 CPU + 구형 메인보드)
- [ ] 전원 커넥터 호환성 (GPU 전원 핀 수)
- [ ] M.2 슬롯 및 SATA 포트 수 검사

### 선택적 구현

- [ ] OWL 온톨로지 파일 생성 및 추론 엔진 연동
- [ ] 규칙 파일 외부화 (YAML/JSON)
- [ ] 실시간 호환성 체크 API
- [ ] 호환성 시각화 (그래프)

---

## 참고 자료

### 온톨로지 도구

- [OWLReady2](https://owlready2.readthedocs.io/) - Python 온톨로지 라이브러리
- [RDFLib](https://rdflib.readthedocs.io/) - RDF 처리
- [Protégé](https://protege.stanford.edu/) - 온톨로지 편집기

### 호환성 데이터 소스

- [PCPartPicker](https://pcpartpicker.com/) - 호환성 체크 참고
- [Intel ARK](https://ark.intel.com/) - Intel CPU 스펙
- [AMD Product Specifications](https://www.amd.com/en/products/specifications) - AMD CPU 스펙

### 관련 논문

- [Knowledge Graphs for PC Component Compatibility](https://example.com) (예시)
- [Ontology-based Product Configuration](https://example.com) (예시)

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2026-01-02 | 0.1.0 | 초기 스켈레톤 구현 |
