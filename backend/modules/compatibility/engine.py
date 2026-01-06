"""
온톨로지 기반 호환성 검사 엔진
==============================

[목표]
------
PC 부품 간의 물리적/논리적 호환성을 온톨로지와 규칙 기반으로 검증.
사용자가 선택한 부품들이 실제로 조립 가능한지 확인.

[배경 지식]
----------
온톨로지(Ontology):
- 개념과 관계를 형식적으로 정의한 지식 표현 체계
- PC 부품의 속성, 관계, 제약조건을 명시적으로 표현
- 추론 엔진을 통해 암묵적 지식 도출 가능

호환성 검사 항목:
1. CPU-메인보드: 소켓, 칩셋, 세대 호환
2. 메모리-메인보드: DDR 세대, 속도, 슬롯 수
3. GPU-메인보드: PCIe 버전, 슬롯
4. GPU-케이스: 길이, 두께
5. GPU-PSU: 전력, 커넥터
6. CPU 쿨러-케이스: 높이 제한
7. 메인보드-케이스: 폼팩터
8. 저장장치-메인보드: M.2/SATA 슬롯

[아키텍처]
---------
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

[입력/출력 인터페이스]
-------------------
입력 (ComponentList):
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
                "m2_slots": 4,
                "pcie_slots": [{"version": "5.0", "lanes": 16}]
            }
        },
        ...
    ]
}
```

출력 (CompatibilityResult):
```python
{
    "is_compatible": True,
    "overall_score": 95,  # 100점 만점
    "checks": [
        {
            "check_id": "cpu_mb_socket",
            "name": "CPU-메인보드 소켓 호환성",
            "components": ["cpu", "motherboard"],
            "status": "pass",  # pass, fail, warning
            "message": "LGA1700 소켓으로 완벽 호환",
            "details": {"cpu_socket": "LGA1700", "mb_socket": "LGA1700"}
        },
        {
            "check_id": "gpu_psu_power",
            "name": "GPU-PSU 전력 호환성",
            "components": ["gpu", "psu"],
            "status": "warning",
            "message": "권장 전력 650W, 현재 550W (여유 부족)",
            "details": {"required": 650, "available": 550}
        }
    ],
    "power_summary": {
        "total_tdp": 310,
        "recommended_psu": 650,
        "current_psu": 550,
        "headroom_pct": -10
    },
    "recommendations": [
        "PSU를 650W 이상으로 업그레이드 권장",
        "고성능 쿨러 사용 시 CPU 성능 향상 가능"
    ]
}
```

[호환성 규칙 상세]
----------------
1. CPU-메인보드 규칙:
   - 소켓 일치 (LGA1700, AM5 등)
   - 칩셋 세대 호환
   - BIOS 버전 (최신 CPU 지원)

2. 메모리 규칙:
   - DDR 세대 일치
   - 최대 속도 지원
   - 용량 제한 확인

3. GPU 규칙:
   - PCIe 버전 호환 (하위 호환 가능)
   - 케이스 내부 길이
   - 전원 커넥터 수

4. 전원 규칙:
   - 총 TDP 계산
   - 20-30% 여유 권장
   - 커넥터 종류/수량

5. 케이스 규칙:
   - 메인보드 폼팩터
   - CPU 쿨러 높이
   - GPU 길이

[참고 기술/라이브러리]
------------------
- RDFLib: 온톨로지 처리 (Python)
- OWLReady2: 온톨로지 추론
- NetworkX: 그래프 기반 규칙 처리

[테스트]
-------
backend/tests/test_compatibility.py 참조
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
from pydantic import BaseModel, Field


# ============================================================================
# 열거형 및 상수
# ============================================================================

class CheckStatus(str, Enum):
    """검사 상태"""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    UNKNOWN = "unknown"


class FormFactor(str, Enum):
    """폼팩터"""
    ATX = "ATX"
    MICRO_ATX = "Micro-ATX"
    MINI_ITX = "Mini-ITX"
    E_ATX = "E-ATX"


# ============================================================================
# 데이터 모델
# ============================================================================

class ComponentSpecs(BaseModel):
    """부품 스펙"""
    category: str
    name: str
    specs: Dict[str, Any] = Field(default_factory=dict)


class CompatibilityCheck(BaseModel):
    """개별 호환성 검사 결과"""
    check_id: str
    name: str
    components: List[str]
    status: CheckStatus
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class PowerSummary(BaseModel):
    """전력 요약"""
    total_tdp: int = Field(..., description="총 TDP (W)")
    recommended_psu: int = Field(..., description="권장 PSU 용량 (W)")
    current_psu: Optional[int] = Field(None, description="현재 PSU 용량 (W)")
    headroom_pct: Optional[float] = Field(None, description="전력 여유율 (%)")


class CompatibilityResult(BaseModel):
    """호환성 검사 결과"""
    is_compatible: bool
    overall_score: int = Field(..., ge=0, le=100)
    checks: List[CompatibilityCheck]
    power_summary: Optional[PowerSummary] = None
    recommendations: List[str] = Field(default_factory=list)


# ============================================================================
# 소켓/칩셋 호환성 데이터베이스
# ============================================================================

# Intel 소켓-칩셋 호환성
INTEL_COMPATIBILITY = {
    "LGA1700": {
        "generations": [12, 13, 14],
        "chipsets": ["Z790", "Z690", "B760", "B660", "H770", "H670", "H610"],
        "memory": ["DDR5", "DDR4"],
    },
    "LGA1200": {
        "generations": [10, 11],
        "chipsets": ["Z590", "Z490", "B560", "B460", "H570", "H470", "H510", "H410"],
        "memory": ["DDR4"],
    },
}

# AMD 소켓-칩셋 호환성
AMD_COMPATIBILITY = {
    "AM5": {
        "generations": [7000],  # Ryzen 7000 시리즈
        "chipsets": ["X670E", "X670", "B650E", "B650", "A620"],
        "memory": ["DDR5"],
    },
    "AM4": {
        "generations": [3000, 5000],  # Ryzen 3000/5000 시리즈
        "chipsets": ["X570", "X470", "X370", "B550", "B450", "B350", "A520", "A320"],
        "memory": ["DDR4"],
    },
}

# 폼팩터 호환성
FORM_FACTOR_COMPATIBILITY = {
    "ATX": ["ATX", "Micro-ATX", "Mini-ITX"],
    "Micro-ATX": ["Micro-ATX", "Mini-ITX"],
    "Mini-ITX": ["Mini-ITX"],
    "E-ATX": ["E-ATX", "ATX", "Micro-ATX", "Mini-ITX"],
}

# GPU 전력 요구사항 (대략적 값)
GPU_POWER_REQUIREMENTS = {
    "RTX 4090": {"tdp": 450, "recommended_psu": 850, "connectors": "16-pin"},
    "RTX 4080": {"tdp": 320, "recommended_psu": 750, "connectors": "16-pin"},
    "RTX 4070 Ti": {"tdp": 285, "recommended_psu": 700, "connectors": "8-pin x2"},
    "RTX 4070": {"tdp": 200, "recommended_psu": 650, "connectors": "8-pin"},
    "RTX 4060 Ti": {"tdp": 160, "recommended_psu": 550, "connectors": "8-pin"},
    "RTX 4060": {"tdp": 115, "recommended_psu": 500, "connectors": "8-pin"},
    "RTX 3080": {"tdp": 320, "recommended_psu": 750, "connectors": "8-pin x2"},
    "RTX 3070": {"tdp": 220, "recommended_psu": 650, "connectors": "8-pin"},
    "RTX 3060": {"tdp": 170, "recommended_psu": 550, "connectors": "8-pin"},
}


# ============================================================================
# 호환성 엔진
# ============================================================================

class CompatibilityEngine:
    """
    PC 부품 호환성 검사 엔진
    
    온톨로지와 규칙 기반으로 부품 간 호환성을 검증.
    
    사용법:
    ```python
    engine = CompatibilityEngine()
    
    components = [
        {"category": "cpu", "name": "Intel Core i5-14600K", "specs": {...}},
        {"category": "motherboard", "name": "ASUS ROG Z790-A", "specs": {...}},
        ...
    ]
    
    result = engine.check_all(components)
    
    if result.is_compatible:
        print("모든 부품이 호환됩니다!")
    else:
        for check in result.checks:
            if check.status == CheckStatus.FAIL:
                print(f"호환 불가: {check.message}")
    ```
    """
    
    def __init__(
        self,
        strict_mode: bool = False,
    ):
        """
        Args:
            strict_mode: 엄격 모드 (경고도 실패로 처리)
        """
        self.strict_mode = strict_mode
        
        # 규칙 엔진 초기화
        from .rules import CompatibilityRules
        self.rules = CompatibilityRules()
        
        logger.info(f"CompatibilityEngine 초기화: strict_mode={strict_mode}")
    
    def check_all(
        self,
        components: List[Dict[str, Any]],
    ) -> CompatibilityResult:
        """
        모든 호환성 검사 수행
        
        Args:
            components: 부품 목록
            
        Returns:
            CompatibilityResult: 검사 결과
        """
        logger.info(f"호환성 검사 시작: {len(components)}개 부품")
        
        checks = []
        
        # 부품을 카테고리별로 분류
        by_category = self._categorize_components(components)
        
        # 1. CPU-메인보드 호환성
        if "cpu" in by_category and "motherboard" in by_category:
            check = self._check_cpu_motherboard(
                by_category["cpu"],
                by_category["motherboard"],
            )
            checks.append(check)
        
        # 2. 메모리-메인보드 호환성
        if "memory" in by_category and "motherboard" in by_category:
            check = self._check_memory_motherboard(
                by_category["memory"],
                by_category["motherboard"],
            )
            checks.append(check)
        
        # 3. GPU-케이스 호환성
        if "gpu" in by_category and "case" in by_category:
            check = self._check_gpu_case(
                by_category["gpu"],
                by_category["case"],
            )
            checks.append(check)
        
        # 4. 메인보드-케이스 폼팩터
        if "motherboard" in by_category and "case" in by_category:
            check = self._check_motherboard_case(
                by_category["motherboard"],
                by_category["case"],
            )
            checks.append(check)

        # 5. CPU 쿨러-케이스 호환성
        if "cpu_cooler" in by_category and "case" in by_category:
            check = self._check_cpu_cooler_case(
                by_category["cpu_cooler"],
                by_category["case"],
            )
            checks.append(check)

        # 6. 저장장치-메인보드 호환성
        storage_list = [c for c in components if c.get("category") == "storage"]
        if storage_list and "motherboard" in by_category:
            check = self._check_storage_motherboard(
                storage_list,
                by_category["motherboard"],
            )
            checks.append(check)
        
        # 7. 전력 계산
        power_summary = self._calculate_power(components, by_category)
        
        if "psu" in by_category:
            check = self._check_power(power_summary, by_category["psu"])
            checks.append(check)
        
        # 전체 결과 계산
        is_compatible, overall_score = self._calculate_overall(checks)
        
        # 권장 사항 생성
        recommendations = self._generate_recommendations(checks, power_summary)
        
        return CompatibilityResult(
            is_compatible=is_compatible,
            overall_score=overall_score,
            checks=checks,
            power_summary=power_summary,
            recommendations=recommendations,
        )
    
    def _categorize_components(
        self,
        components: List[Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        """부품을 카테고리별로 분류"""
        by_category = {}
        for comp in components:
            category = comp.get("category", "unknown")
            by_category[category] = comp
        return by_category
    
    def _check_cpu_motherboard(
        self,
        cpu: Dict[str, Any],
        motherboard: Dict[str, Any],
    ) -> CompatibilityCheck:
        """CPU-메인보드 호환성 검사"""
        cpu_specs = cpu.get("specs", {})
        mb_specs = motherboard.get("specs", {})
        
        cpu_socket = cpu_specs.get("socket", "")
        mb_socket = mb_specs.get("socket", "")
        
        # 소켓 확인
        if cpu_socket and mb_socket:
            if cpu_socket == mb_socket:
                return CompatibilityCheck(
                    check_id="cpu_mb_socket",
                    name="CPU-메인보드 소켓 호환성",
                    components=["cpu", "motherboard"],
                    status=CheckStatus.PASS,
                    message=f"{cpu_socket} 소켓으로 완벽 호환",
                    details={"cpu_socket": cpu_socket, "mb_socket": mb_socket},
                )
            else:
                return CompatibilityCheck(
                    check_id="cpu_mb_socket",
                    name="CPU-메인보드 소켓 호환성",
                    components=["cpu", "motherboard"],
                    status=CheckStatus.FAIL,
                    message=f"소켓 불일치: CPU({cpu_socket}) vs 메인보드({mb_socket})",
                    details={"cpu_socket": cpu_socket, "mb_socket": mb_socket},
                )
        
        # 소켓 정보 없으면 이름으로 추론
        return self._infer_cpu_mb_compatibility(cpu, motherboard)
    
    def _infer_cpu_mb_compatibility(
        self,
        cpu: Dict[str, Any],
        motherboard: Dict[str, Any],
    ) -> CompatibilityCheck:
        """CPU-메인보드 호환성 추론 (이름 기반)"""
        cpu_name = cpu.get("name", "").lower()
        mb_name = motherboard.get("name", "").lower()
        
        # Intel 14세대 + Z790/B760
        if ("14600" in cpu_name or "14700" in cpu_name or "14900" in cpu_name):
            if "z790" in mb_name or "b760" in mb_name or "h770" in mb_name:
                return CompatibilityCheck(
                    check_id="cpu_mb_socket",
                    name="CPU-메인보드 소켓 호환성",
                    components=["cpu", "motherboard"],
                    status=CheckStatus.PASS,
                    message="Intel 14세대 CPU와 700시리즈 메인보드 호환",
                    details={"inferred": True},
                )
        
        # AMD Ryzen 7000 + X670/B650
        if ("7800" in cpu_name or "7900" in cpu_name or "7600" in cpu_name):
            if "x670" in mb_name or "b650" in mb_name:
                return CompatibilityCheck(
                    check_id="cpu_mb_socket",
                    name="CPU-메인보드 소켓 호환성",
                    components=["cpu", "motherboard"],
                    status=CheckStatus.PASS,
                    message="AMD Ryzen 7000 시리즈와 600시리즈 메인보드 호환",
                    details={"inferred": True},
                )
        
        # 확인 불가
        return CompatibilityCheck(
            check_id="cpu_mb_socket",
            name="CPU-메인보드 소켓 호환성",
            components=["cpu", "motherboard"],
            status=CheckStatus.UNKNOWN,
            message="소켓 정보가 부족하여 호환성을 확인할 수 없습니다",
            details={"inferred": True},
        )
    
    def _check_memory_motherboard(
        self,
        memory: Dict[str, Any],
        motherboard: Dict[str, Any],
    ) -> CompatibilityCheck:
        """메모리-메인보드 호환성 검사"""
        mem_specs = memory.get("specs", {})
        mb_specs = motherboard.get("specs", {})
        
        mem_type = mem_specs.get("generation", mem_specs.get("type", ""))
        mb_mem_type = mb_specs.get("memory_type", "")
        
        # DDR 세대 확인
        if mem_type and mb_mem_type:
            if mem_type.upper() == mb_mem_type.upper():
                return CompatibilityCheck(
                    check_id="mem_mb_type",
                    name="메모리-메인보드 호환성",
                    components=["memory", "motherboard"],
                    status=CheckStatus.PASS,
                    message=f"{mem_type} 메모리 호환",
                    details={"memory_type": mem_type},
                )
            else:
                return CompatibilityCheck(
                    check_id="mem_mb_type",
                    name="메모리-메인보드 호환성",
                    components=["memory", "motherboard"],
                    status=CheckStatus.FAIL,
                    message=f"메모리 타입 불일치: {mem_type} vs {mb_mem_type}",
                    details={"memory_type": mem_type, "mb_type": mb_mem_type},
                )
        
        # 정보 부족 시 경고
        return CompatibilityCheck(
            check_id="mem_mb_type",
            name="메모리-메인보드 호환성",
            components=["memory", "motherboard"],
            status=CheckStatus.WARNING,
            message="메모리 타입 정보를 확인해주세요",
            details={},
        )
    
    def _check_gpu_case(
        self,
        gpu: Dict[str, Any],
        case: Dict[str, Any],
    ) -> CompatibilityCheck:
        """GPU-케이스 호환성 검사 (길이)"""
        gpu_specs = gpu.get("specs", {})
        case_specs = case.get("specs", {})
        
        gpu_length = gpu_specs.get("length", 0)  # mm
        case_max_gpu = case_specs.get("max_gpu_length", 0)  # mm
        
        if gpu_length and case_max_gpu:
            if gpu_length <= case_max_gpu:
                return CompatibilityCheck(
                    check_id="gpu_case_length",
                    name="GPU-케이스 길이 호환성",
                    components=["gpu", "case"],
                    status=CheckStatus.PASS,
                    message=f"GPU 길이 {gpu_length}mm, 케이스 허용 {case_max_gpu}mm",
                    details={"gpu_length": gpu_length, "case_max": case_max_gpu},
                )
            else:
                return CompatibilityCheck(
                    check_id="gpu_case_length",
                    name="GPU-케이스 길이 호환성",
                    components=["gpu", "case"],
                    status=CheckStatus.FAIL,
                    message=f"GPU가 너무 깁니다: {gpu_length}mm > {case_max_gpu}mm",
                    details={"gpu_length": gpu_length, "case_max": case_max_gpu},
                )
        
        return CompatibilityCheck(
            check_id="gpu_case_length",
            name="GPU-케이스 길이 호환성",
            components=["gpu", "case"],
            status=CheckStatus.WARNING,
            message="GPU/케이스 치수 정보를 확인해주세요",
            details={},
        )
    
    def _check_motherboard_case(
        self,
        motherboard: Dict[str, Any],
        case: Dict[str, Any],
    ) -> CompatibilityCheck:
        """메인보드-케이스 폼팩터 호환성"""
        mb_specs = motherboard.get("specs", {})
        case_specs = case.get("specs", {})
        
        mb_form = mb_specs.get("form_factor", "")
        case_supports = case_specs.get("supported_form_factors", [])
        
        # 케이스 폼팩터가 지정되어 있으면 해당 폼팩터 확인
        case_form = case_specs.get("form_factor", "")
        if case_form:
            compatible_forms = FORM_FACTOR_COMPATIBILITY.get(case_form, [])
            if mb_form in compatible_forms:
                return CompatibilityCheck(
                    check_id="mb_case_form",
                    name="메인보드-케이스 폼팩터",
                    components=["motherboard", "case"],
                    status=CheckStatus.PASS,
                    message=f"{mb_form} 메인보드가 {case_form} 케이스에 장착 가능",
                    details={"mb_form": mb_form, "case_form": case_form},
                )
            elif mb_form:
                return CompatibilityCheck(
                    check_id="mb_case_form",
                    name="메인보드-케이스 폼팩터",
                    components=["motherboard", "case"],
                    status=CheckStatus.FAIL,
                    message=f"{mb_form} 메인보드는 {case_form} 케이스에 맞지 않습니다",
                    details={"mb_form": mb_form, "case_form": case_form},
                )
        
        return CompatibilityCheck(
            check_id="mb_case_form",
            name="메인보드-케이스 폼팩터",
            components=["motherboard", "case"],
            status=CheckStatus.WARNING,
            message="폼팩터 정보를 확인해주세요",
            details={},
        )

    def _check_cpu_cooler_case(
        self,
        cpu_cooler: Dict[str, Any],
        case: Dict[str, Any],
    ) -> CompatibilityCheck:
        """CPU 쿨러-케이스 호환성 검사 (높이)"""
        cooler_specs = cpu_cooler.get("specs", {})
        case_specs = case.get("specs", {})
        
        cooler_height = cooler_specs.get("height", 0)  # mm
        case_max_height = case_specs.get("max_cooler_height", 0)  # mm
        
        if cooler_height and case_max_height:
            if cooler_height <= case_max_height:
                return CompatibilityCheck(
                    check_id="cooler_case_height",
                    name="CPU 쿨러-케이스 높이 호환성",
                    components=["cpu_cooler", "case"],
                    status=CheckStatus.PASS,
                    message=f"쿨러 높이 {cooler_height}mm, 케이스 허용 {case_max_height}mm",
                    details={"cooler_height": cooler_height, "case_max": case_max_height},
                )
            else:
                return CompatibilityCheck(
                    check_id="cooler_case_height",
                    name="CPU 쿨러-케이스 높이 호환성",
                    components=["cpu_cooler", "case"],
                    status=CheckStatus.FAIL,
                    message=f"CPU 쿨러가 너무 높습니다: {cooler_height}mm > {case_max_height}mm",
                    details={"cooler_height": cooler_height, "case_max": case_max_height},
                )
        
        return CompatibilityCheck(
            check_id="cooler_case_height",
            name="CPU 쿨러-케이스 높이 호환성",
            components=["cpu_cooler", "case"],
            status=CheckStatus.WARNING,
            message="CPU 쿨러/케이스 높이 정보를 확인해주세요",
            details={},
        )

    def _check_storage_motherboard(
        self,
        storage_list: List[Dict[str, Any]],
        motherboard: Dict[str, Any],
    ) -> CompatibilityCheck:
        """저장장치-메인보드 호환성 검사 (슬롯 수)"""
        mb_specs = motherboard.get("specs", {})
        m2_slots_available = mb_specs.get("m2_slots", 0)
        sata_slots_available = mb_specs.get("sata_slots", 0)
        
        m2_needed = 0
        sata_needed = 0
        
        for storage in storage_list:
            storage_specs = storage.get("specs", {})
            interface = storage_specs.get("interface", "").upper()
            if "M.2" in interface:
                m2_needed += 1
            elif "SATA" in interface:
                sata_needed += 1
        
        m2_ok = m2_needed <= m2_slots_available
        sata_ok = sata_needed <= sata_slots_available
        
        details = {
            "m2_needed": m2_needed,
            "m2_available": m2_slots_available,
            "sata_needed": sata_needed,
            "sata_available": sata_slots_available,
        }
        
        if m2_ok and sata_ok:
            return CompatibilityCheck(
                check_id="storage_mb_slots",
                name="저장장치-메인보드 슬롯 호환성",
                components=["storage", "motherboard"],
                status=CheckStatus.PASS,
                message="모든 저장장치가 메인보드에 연결 가능합니다.",
                details=details,
            )
        else:
            messages = []
            if not m2_ok:
                messages.append(f"M.2 슬롯 부족 (필요: {m2_needed}, 사용 가능: {m2_slots_available})")
            if not sata_ok:
                messages.append(f"SATA 슬롯 부족 (필요: {sata_needed}, 사용 가능: {sata_slots_available})")
                
            return CompatibilityCheck(
                check_id="storage_mb_slots",
                name="저장장치-메인보드 슬롯 호환성",
                components=["storage", "motherboard"],
                status=CheckStatus.FAIL,
                message="; ".join(messages),
                details=details,
            )
    
    def _calculate_power(
        self,
        components: List[Dict[str, Any]],
        by_category: Dict[str, Dict[str, Any]],
    ) -> PowerSummary:
        """전력 계산"""
        total_tdp = 0
        
        # CPU TDP
        if "cpu" in by_category:
            cpu_tdp = by_category["cpu"].get("specs", {}).get("tdp", 0)
            if not cpu_tdp:
                # 이름으로 추정
                cpu_name = by_category["cpu"].get("name", "")
                if "14900" in cpu_name or "14700" in cpu_name:
                    cpu_tdp = 125
                elif "14600" in cpu_name:
                    cpu_tdp = 125
                elif "13600" in cpu_name or "12600" in cpu_name:
                    cpu_tdp = 125
                else:
                    cpu_tdp = 65  # 기본값
            total_tdp += cpu_tdp
        
        # GPU TDP
        if "gpu" in by_category:
            gpu_tdp = by_category["gpu"].get("specs", {}).get("tdp", 0)
            if not gpu_tdp:
                gpu_name = by_category["gpu"].get("name", "")
                for model, specs in GPU_POWER_REQUIREMENTS.items():
                    if model.lower() in gpu_name.lower():
                        gpu_tdp = specs["tdp"]
                        break
                if not gpu_tdp:
                    gpu_tdp = 200  # 기본값
            total_tdp += gpu_tdp
        
        # 기타 부품 (대략적 추정)
        other_tdp = 100  # 메모리, 스토리지, 팬 등
        total_tdp += other_tdp
        
        # 권장 PSU: TDP의 1.3~1.5배
        recommended_psu = int(total_tdp * 1.4)
        # 50W 단위로 올림
        recommended_psu = ((recommended_psu + 49) // 50) * 50
        
        # 현재 PSU
        current_psu = None
        headroom_pct = None
        if "psu" in by_category:
            current_psu = by_category["psu"].get("specs", {}).get("wattage", 0)
            if not current_psu:
                # 이름에서 추출 시도
                psu_name = by_category["psu"].get("name", "")
                import re
                match = re.search(r"(\d{3,4})W", psu_name)
                if match:
                    current_psu = int(match.group(1))
            
            if current_psu:
                headroom_pct = ((current_psu - total_tdp) / current_psu) * 100
        
        return PowerSummary(
            total_tdp=total_tdp,
            recommended_psu=recommended_psu,
            current_psu=current_psu,
            headroom_pct=round(headroom_pct, 1) if headroom_pct else None,
        )
    
    def _check_power(
        self,
        power_summary: PowerSummary,
        psu: Dict[str, Any],
    ) -> CompatibilityCheck:
        """전력 호환성 검사"""
        if power_summary.current_psu is None:
            return CompatibilityCheck(
                check_id="power_check",
                name="전력 호환성",
                components=["psu"],
                status=CheckStatus.WARNING,
                message="PSU 용량을 확인할 수 없습니다",
                details={},
            )
        
        if power_summary.current_psu >= power_summary.recommended_psu:
            return CompatibilityCheck(
                check_id="power_check",
                name="전력 호환성",
                components=["psu"],
                status=CheckStatus.PASS,
                message=f"전력 여유 충분: {power_summary.current_psu}W (권장 {power_summary.recommended_psu}W)",
                details={
                    "current": power_summary.current_psu,
                    "recommended": power_summary.recommended_psu,
                    "tdp": power_summary.total_tdp,
                },
            )
        elif power_summary.current_psu >= power_summary.total_tdp:
            return CompatibilityCheck(
                check_id="power_check",
                name="전력 호환성",
                components=["psu"],
                status=CheckStatus.WARNING,
                message=f"전력 여유 부족: {power_summary.current_psu}W (권장 {power_summary.recommended_psu}W)",
                details={
                    "current": power_summary.current_psu,
                    "recommended": power_summary.recommended_psu,
                    "tdp": power_summary.total_tdp,
                },
            )
        else:
            return CompatibilityCheck(
                check_id="power_check",
                name="전력 호환성",
                components=["psu"],
                status=CheckStatus.FAIL,
                message=f"전력 부족: {power_summary.current_psu}W < TDP {power_summary.total_tdp}W",
                details={
                    "current": power_summary.current_psu,
                    "recommended": power_summary.recommended_psu,
                    "tdp": power_summary.total_tdp,
                },
            )
    
    def _calculate_overall(
        self,
        checks: List[CompatibilityCheck],
    ) -> Tuple[bool, int]:
        """전체 결과 계산"""
        if not checks:
            return True, 100
        
        fail_count = sum(1 for c in checks if c.status == CheckStatus.FAIL)
        warning_count = sum(1 for c in checks if c.status == CheckStatus.WARNING)
        
        # 실패가 있으면 호환 불가
        is_compatible = fail_count == 0
        
        if self.strict_mode:
            is_compatible = is_compatible and warning_count == 0
        
        # 점수 계산
        total = len(checks)
        pass_count = sum(1 for c in checks if c.status == CheckStatus.PASS)
        unknown_count = sum(1 for c in checks if c.status == CheckStatus.UNKNOWN)
        
        # PASS: 100점, WARNING: 70점, UNKNOWN: 50점, FAIL: 0점
        score = (pass_count * 100 + warning_count * 70 + unknown_count * 50) / total
        
        return is_compatible, int(score)
    
    def _generate_recommendations(
        self,
        checks: List[CompatibilityCheck],
        power_summary: Optional[PowerSummary],
    ) -> List[str]:
        """권장 사항 생성"""
        recommendations = []
        
        for check in checks:
            if check.status == CheckStatus.FAIL:
                if "socket" in check.check_id:
                    recommendations.append(
                        "CPU와 메인보드의 소켓이 일치하는지 확인하세요"
                    )
                elif "memory" in check.check_id:
                    recommendations.append(
                        "메모리 타입(DDR4/DDR5)이 메인보드와 호환되는지 확인하세요"
                    )
                elif "form" in check.check_id:
                    recommendations.append(
                        "메인보드 폼팩터가 케이스에 맞는지 확인하세요"
                    )
            
            elif check.status == CheckStatus.WARNING:
                if "power" in check.check_id:
                    if power_summary and power_summary.recommended_psu:
                        recommendations.append(
                            f"안정적인 운용을 위해 {power_summary.recommended_psu}W 이상 PSU 권장"
                        )
        
        return recommendations[:5]  # 최대 5개


# ============================================================================
# 간편 함수
# ============================================================================

def check_compatibility(
    components: List[Dict[str, Any]],
) -> CompatibilityResult:
    """
    간편 호환성 검사 함수
    
    Args:
        components: 부품 목록
        
    Returns:
        CompatibilityResult: 검사 결과
    """
    engine = CompatibilityEngine()
    return engine.check_all(components)


# ============================================================================
# 테스트용 메인
# ============================================================================

if __name__ == "__main__":
    import json
    
    engine = CompatibilityEngine()
    
    # 테스트 부품
    test_components = [
        {
            "category": "cpu",
            "name": "Intel Core i5-14600K",
            "specs": {"socket": "LGA1700", "tdp": 125}
        },
        {
            "category": "motherboard",
            "name": "ASUS ROG Strix Z790-A Gaming WiFi",
            "specs": {
                "socket": "LGA1700",
                "form_factor": "ATX",
                "memory_type": "DDR5"
            }
        },
        {
            "category": "memory",
            "name": "Samsung DDR5-5600 32GB",
            "specs": {"generation": "DDR5", "capacity": 32, "speed": 5600}
        },
        {
            "category": "gpu",
            "name": "RTX 4070",
            "specs": {"tdp": 200, "length": 300}
        },
        {
            "category": "psu",
            "name": "Corsair RM750",
            "specs": {"wattage": 750}
        },
        {
            "category": "case",
            "name": "NZXT H7 Flow",
            "specs": {"form_factor": "ATX", "max_gpu_length": 400}
        },
    ]
    
    result = engine.check_all(test_components)
    
    print("호환성 검사 결과:")
    print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))
