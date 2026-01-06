"""
호환성 규칙 엔진
================

[목표]
------
PC 부품 간 호환성을 규칙 기반으로 검사하는 엔진.

[규칙 구조]
----------
각 규칙은 다음 요소로 구성:
- condition: 검사 조건 (어떤 부품 조합에 적용)
- check: 검사 로직 (속성 비교, 계산 등)
- message: 결과 메시지 템플릿
- severity: 심각도 (error, warning, info)

[규칙 카테고리]
--------------
1. 소켓 규칙: CPU/메인보드/쿨러 소켓 호환
2. 메모리 규칙: DDR 세대, 속도, 용량
3. 폼팩터 규칙: 메인보드/케이스 크기
4. 전력 규칙: TDP/PSU 용량
5. 물리적 규칙: GPU 길이, 쿨러 높이

[확장 가능성]
-----------
- 규칙 파일(YAML/JSON) 외부화
- 규칙 우선순위 지정
- 사용자 정의 규칙 추가

[TODO]
-----
- [ ] 규칙 파일 외부화
- [ ] 더 상세한 호환성 데이터베이스
- [ ] BIOS 버전 호환성 체크
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from loguru import logger


# ============================================================================
# 열거형 및 상수
# ============================================================================

class RuleSeverity(str, Enum):
    """규칙 심각도"""
    ERROR = "error"      # 반드시 해결 필요
    WARNING = "warning"  # 권장 사항
    INFO = "info"        # 참고 정보


class RuleCategory(str, Enum):
    """규칙 카테고리"""
    SOCKET = "socket"
    MEMORY = "memory"
    FORM_FACTOR = "form_factor"
    POWER = "power"
    PHYSICAL = "physical"
    INTERFACE = "interface"


# ============================================================================
# 데이터 클래스
# ============================================================================

@dataclass
class RuleResult:
    """규칙 검사 결과"""
    rule_id: str
    passed: bool
    severity: RuleSeverity
    message: str
    details: Dict[str, Any] = None


@dataclass
class CompatibilityRule:
    """호환성 규칙"""
    id: str
    name: str
    category: RuleCategory
    severity: RuleSeverity
    applies_to: List[str]  # 적용 대상 카테고리 조합 (예: ["cpu", "motherboard"])
    check_function: Callable[[Dict[str, Any], Dict[str, Any]], RuleResult]
    description: str = ""


# ============================================================================
# 규칙 정의 함수들
# ============================================================================

def check_cpu_mb_socket(cpu: Dict[str, Any], mb: Dict[str, Any]) -> RuleResult:
    """CPU-메인보드 소켓 호환성 검사"""
    cpu_socket = cpu.get("specs", {}).get("socket", "")
    mb_socket = mb.get("specs", {}).get("socket", "")
    
    # 소켓 정보가 없으면 이름에서 추론
    if not cpu_socket:
        cpu_name = cpu.get("name", "").lower()
        if "14" in cpu_name and ("600" in cpu_name or "700" in cpu_name or "900" in cpu_name):
            cpu_socket = "LGA1700"
        elif "13" in cpu_name and ("600" in cpu_name or "700" in cpu_name or "900" in cpu_name):
            cpu_socket = "LGA1700"
        elif "7800" in cpu_name or "7900" in cpu_name or "7600" in cpu_name:
            cpu_socket = "AM5"
        elif "5800" in cpu_name or "5900" in cpu_name or "5600" in cpu_name:
            cpu_socket = "AM4"
    
    if not mb_socket:
        mb_name = mb.get("name", "").lower()
        if "z790" in mb_name or "b760" in mb_name or "z690" in mb_name:
            mb_socket = "LGA1700"
        elif "x670" in mb_name or "b650" in mb_name:
            mb_socket = "AM5"
        elif "x570" in mb_name or "b550" in mb_name:
            mb_socket = "AM4"
    
    if not cpu_socket or not mb_socket:
        return RuleResult(
            rule_id="cpu_mb_socket",
            passed=True,  # 정보 부족 시 통과 (경고만)
            severity=RuleSeverity.WARNING,
            message="소켓 정보를 확인할 수 없습니다. 수동으로 확인해주세요.",
            details={"cpu_socket": cpu_socket, "mb_socket": mb_socket},
        )
    
    if cpu_socket == mb_socket:
        return RuleResult(
            rule_id="cpu_mb_socket",
            passed=True,
            severity=RuleSeverity.INFO,
            message=f"{cpu_socket} 소켓으로 호환됩니다.",
            details={"cpu_socket": cpu_socket, "mb_socket": mb_socket},
        )
    else:
        return RuleResult(
            rule_id="cpu_mb_socket",
            passed=False,
            severity=RuleSeverity.ERROR,
            message=f"소켓 불일치: CPU({cpu_socket}) ≠ 메인보드({mb_socket})",
            details={"cpu_socket": cpu_socket, "mb_socket": mb_socket},
        )


def check_memory_mb_type(memory: Dict[str, Any], mb: Dict[str, Any]) -> RuleResult:
    """메모리-메인보드 타입 호환성"""
    mem_type = memory.get("specs", {}).get("generation", "")
    if not mem_type:
        mem_type = memory.get("specs", {}).get("type", "")
    
    mb_mem_type = mb.get("specs", {}).get("memory_type", "")
    
    # 이름에서 추론
    if not mem_type:
        mem_name = memory.get("name", "").lower()
        if "ddr5" in mem_name:
            mem_type = "DDR5"
        elif "ddr4" in mem_name:
            mem_type = "DDR4"
    
    if not mb_mem_type:
        mb_name = mb.get("name", "").lower()
        if "ddr5" in mb_name or "z790" in mb_name or "x670" in mb_name or "b650" in mb_name:
            mb_mem_type = "DDR5"
        elif "ddr4" in mb_name:
            mb_mem_type = "DDR4"
    
    if not mem_type or not mb_mem_type:
        return RuleResult(
            rule_id="memory_mb_type",
            passed=True,
            severity=RuleSeverity.WARNING,
            message="메모리 타입을 확인해주세요.",
            details={},
        )
    
    mem_type_upper = mem_type.upper()
    mb_mem_type_upper = mb_mem_type.upper()
    
    if mem_type_upper == mb_mem_type_upper:
        return RuleResult(
            rule_id="memory_mb_type",
            passed=True,
            severity=RuleSeverity.INFO,
            message=f"{mem_type} 메모리 호환됩니다.",
            details={"memory_type": mem_type},
        )
    else:
        return RuleResult(
            rule_id="memory_mb_type",
            passed=False,
            severity=RuleSeverity.ERROR,
            message=f"메모리 타입 불일치: {mem_type} ≠ {mb_mem_type}",
            details={"memory_type": mem_type, "mb_type": mb_mem_type},
        )


def check_mb_case_form(mb: Dict[str, Any], case: Dict[str, Any]) -> RuleResult:
    """메인보드-케이스 폼팩터 호환성"""
    mb_form = mb.get("specs", {}).get("form_factor", "")
    case_form = case.get("specs", {}).get("form_factor", "")
    
    # 폼팩터 호환 매트릭스
    compatibility = {
        "E-ATX": ["E-ATX"],
        "ATX": ["ATX", "E-ATX"],
        "Micro-ATX": ["Micro-ATX", "ATX", "E-ATX"],
        "Mini-ITX": ["Mini-ITX", "Micro-ATX", "ATX", "E-ATX"],
    }
    
    if not mb_form or not case_form:
        return RuleResult(
            rule_id="mb_case_form",
            passed=True,
            severity=RuleSeverity.WARNING,
            message="폼팩터 정보를 확인해주세요.",
            details={},
        )
    
    compatible_cases = compatibility.get(mb_form, [])
    
    if case_form in compatible_cases:
        return RuleResult(
            rule_id="mb_case_form",
            passed=True,
            severity=RuleSeverity.INFO,
            message=f"{mb_form} 메인보드가 {case_form} 케이스에 장착 가능합니다.",
            details={"mb_form": mb_form, "case_form": case_form},
        )
    else:
        return RuleResult(
            rule_id="mb_case_form",
            passed=False,
            severity=RuleSeverity.ERROR,
            message=f"{mb_form} 메인보드는 {case_form} 케이스에 맞지 않습니다.",
            details={"mb_form": mb_form, "case_form": case_form},
        )


def check_gpu_case_length(gpu: Dict[str, Any], case: Dict[str, Any]) -> RuleResult:
    """GPU-케이스 길이 호환성"""
    gpu_length = gpu.get("specs", {}).get("length", 0)
    case_max = case.get("specs", {}).get("max_gpu_length", 0)
    
    if not gpu_length or not case_max:
        return RuleResult(
            rule_id="gpu_case_length",
            passed=True,
            severity=RuleSeverity.WARNING,
            message="GPU/케이스 치수를 확인해주세요.",
            details={},
        )
    
    if gpu_length <= case_max:
        headroom = case_max - gpu_length
        return RuleResult(
            rule_id="gpu_case_length",
            passed=True,
            severity=RuleSeverity.INFO,
            message=f"GPU 길이 {gpu_length}mm, 여유 공간 {headroom}mm",
            details={"gpu_length": gpu_length, "case_max": case_max},
        )
    else:
        return RuleResult(
            rule_id="gpu_case_length",
            passed=False,
            severity=RuleSeverity.ERROR,
            message=f"GPU가 너무 깁니다: {gpu_length}mm > {case_max}mm",
            details={"gpu_length": gpu_length, "case_max": case_max},
        )


def check_cooler_case_height(cooler: Dict[str, Any], case: Dict[str, Any]) -> RuleResult:
    """CPU 쿨러-케이스 높이 호환성"""
    cooler_height = cooler.get("specs", {}).get("height", 0)
    case_max = case.get("specs", {}).get("max_cooler_height", 0)
    
    if not cooler_height or not case_max:
        return RuleResult(
            rule_id="cooler_case_height",
            passed=True,
            severity=RuleSeverity.WARNING,
            message="쿨러/케이스 높이를 확인해주세요.",
            details={},
        )
    
    if cooler_height <= case_max:
        return RuleResult(
            rule_id="cooler_case_height",
            passed=True,
            severity=RuleSeverity.INFO,
            message=f"쿨러 높이 {cooler_height}mm, 케이스 허용 {case_max}mm",
            details={"cooler_height": cooler_height, "case_max": case_max},
        )
    else:
        return RuleResult(
            rule_id="cooler_case_height",
            passed=False,
            severity=RuleSeverity.ERROR,
            message=f"쿨러가 너무 높습니다: {cooler_height}mm > {case_max}mm",
            details={"cooler_height": cooler_height, "case_max": case_max},
        )


def get_pcie_version_from_string(s: str) -> Optional[float]:
    """문자열에서 PCIe 버전(예: 4.0)을 추출합니다."""
    if not isinstance(s, str):
        return None
    match = re.search(r'(\d+\.\d+)', s)
    if match:
        return float(match.group(1))
    match = re.search(r'(\d+)', s) # "5" 같은 정수형 버전도 고려
    if match:
        return float(match.group(1))
    return None


def check_gpu_mb_pcie(gpu: Dict[str, Any], mb: Dict[str, Any]) -> RuleResult:
    """GPU-메인보드 PCIe 버전 호환성"""
    gpu_interface = gpu.get("specs", {}).get("interface", "")
    mb_slots = mb.get("specs", {}).get("pcie_slots", [])
    
    gpu_version = get_pcie_version_from_string(gpu_interface)
    
    mb_version = None
    if isinstance(mb_slots, list) and mb_slots:
        # lanes가 16인 주 슬롯을 우선으로 찾음
        primary_slots = [s for s in mb_slots if isinstance(s, dict) and s.get("lanes") == 16]
        if primary_slots:
             version_str = str(primary_slots[0].get("version", ""))
             mb_version = get_pcie_version_from_string(version_str)
        else: # x16 슬롯 정보가 없으면 가장 높은 버전으로 가정
             versions = [get_pcie_version_from_string(str(s.get("version",""))) for s in mb_slots if isinstance(s, dict)]
             valid_versions = [v for v in versions if v is not None]
             if valid_versions:
                 mb_version = max(valid_versions)

    if not gpu_version or not mb_version:
        return RuleResult(
            rule_id="gpu_mb_pcie",
            passed=True,
            severity=RuleSeverity.INFO,
            message="PCIe 버전 정보 부족으로 호환성 자동 검사를 건너뜁니다.",
            details={"gpu_interface": gpu_interface, "mb_slots": mb_slots},
        )

    if mb_version >= gpu_version:
        return RuleResult(
            rule_id="gpu_mb_pcie",
            passed=True,
            severity=RuleSeverity.INFO,
            message=f"PCIe 호환: GPU(v{gpu_version})는 메인보드(v{mb_version})와 호환됩니다.",
            details={"gpu_version": gpu_version, "mb_version": mb_version},
        )
    else:
        return RuleResult(
            rule_id="gpu_mb_pcie",
            passed=True,
            severity=RuleSeverity.WARNING,
            message=f"성능 저하 가능성: GPU(PCIe {gpu_version})의 모든 성능을 사용하려면 메인보드(PCIe {mb_version})의 PCIe 버전이 {gpu_version} 이상이어야 합니다.",
            details={"gpu_version": gpu_version, "mb_version": mb_version},
        )


def check_storage_mb_interface(storage: Dict[str, Any], mb: Dict[str, Any]) -> RuleResult:
    """저장장치-메인보드 인터페이스 호환성"""
    storage_interface = storage.get("specs", {}).get("interface", "").upper()
    m2_slots = mb.get("specs", {}).get("m2_slots", 0)
    sata_slots = mb.get("specs", {}).get("sata_slots", 0)

    if not storage_interface:
        return RuleResult(
            rule_id="storage_mb_interface",
            passed=True,
            severity=RuleSeverity.WARNING,
            message="저장장치의 인터페이스 정보를 확인할 수 없습니다.",
            details={},
        )
    
    if "M.2" in storage_interface:
        if m2_slots > 0:
            return RuleResult(
                rule_id="storage_mb_interface",
                passed=True,
                severity=RuleSeverity.INFO,
                message="M.2 저장장치를 메인보드의 M.2 슬롯에 연결할 수 있습니다.",
                details={"interface": "M.2", "m2_slots_available": m2_slots},
            )
        else:
            return RuleResult(
                rule_id="storage_mb_interface",
                passed=False,
                severity=RuleSeverity.ERROR,
                message="M.2 저장장치를 연결할 슬롯이 메인보드에 없습니다.",
                details={"interface": "M.2", "m2_slots_available": m2_slots},
            )

    elif "SATA" in storage_interface:
        if sata_slots > 0:
            return RuleResult(
                rule_id="storage_mb_interface",
                passed=True,
                severity=RuleSeverity.INFO,
                message="SATA 저장장치를 메인보드의 SATA 슬롯에 연결할 수 있습니다.",
                details={"interface": "SATA", "sata_slots_available": sata_slots},
            )
        else: # SATA 슬롯이 없는 경우
            return RuleResult(
                rule_id="storage_mb_interface",
                passed=False,
                severity=RuleSeverity.ERROR,
                message="SATA 저장장치를 연결할 슬롯이 메인보드에 없습니다.",
                details={"interface": "SATA", "sata_slots_available": sata_slots},
            )
            
    # 검사 대상이 아닌 인터페이스
    return RuleResult(
        rule_id="storage_mb_interface",
        passed=True,
        severity=RuleSeverity.INFO,
        message=f"'{storage_interface}' 인터페이스는 현재 자동 검사 대상이 아닙니다.",
        details={"interface": storage_interface},
    )


# ============================================================================
# 규칙 엔진
# ============================================================================

class CompatibilityRules:
    """
    호환성 규칙 엔진
    
    등록된 규칙들을 기반으로 부품 호환성 검사 수행.
    
    사용법:
    ```python
    rules = CompatibilityRules()
    
    # 두 부품 검사
    results = rules.check_pair(cpu, motherboard)
    
    for result in results:
        print(f"{result.rule_id}: {result.message}")
    ```
    """
    
    def __init__(self):
        """규칙 엔진 초기화"""
        self.rules: List[CompatibilityRule] = []
        self._register_default_rules()
        
        logger.info(f"CompatibilityRules 초기화: {len(self.rules)}개 규칙")
    
    def _register_default_rules(self):
        """기본 규칙 등록"""
        # CPU-메인보드 소켓
        self.register_rule(CompatibilityRule(
            id="cpu_mb_socket",
            name="CPU-메인보드 소켓 호환성",
            category=RuleCategory.SOCKET,
            severity=RuleSeverity.ERROR,
            applies_to=["cpu", "motherboard"],
            check_function=check_cpu_mb_socket,
            description="CPU와 메인보드의 소켓이 일치하는지 확인"
        ))
        
        # 메모리-메인보드 타입
        self.register_rule(CompatibilityRule(
            id="memory_mb_type",
            name="메모리-메인보드 타입 호환성",
            category=RuleCategory.MEMORY,
            severity=RuleSeverity.ERROR,
            applies_to=["memory", "motherboard"],
            check_function=check_memory_mb_type,
            description="메모리 타입(DDR4/DDR5)이 메인보드와 호환되는지 확인"
        ))
        
        # 메인보드-케이스 폼팩터
        self.register_rule(CompatibilityRule(
            id="mb_case_form",
            name="메인보드-케이스 폼팩터",
            category=RuleCategory.FORM_FACTOR,
            severity=RuleSeverity.ERROR,
            applies_to=["motherboard", "case"],
            check_function=check_mb_case_form,
            description="메인보드 폼팩터가 케이스에 맞는지 확인"
        ))
        
        # GPU-케이스 길이
        self.register_rule(CompatibilityRule(
            id="gpu_case_length",
            name="GPU-케이스 길이 호환성",
            category=RuleCategory.PHYSICAL,
            severity=RuleSeverity.ERROR,
            applies_to=["gpu", "case"],
            check_function=check_gpu_case_length,
            description="GPU 길이가 케이스에 맞는지 확인"
        ))
        
        # 쿨러-케이스 높이
        self.register_rule(CompatibilityRule(
            id="cooler_case_height",
            name="CPU 쿨러-케이스 높이 호환성",
            category=RuleCategory.PHYSICAL,
            severity=RuleSeverity.ERROR,
            applies_to=["cpu_cooler", "case"],
            check_function=check_cooler_case_height,
            description="CPU 쿨러 높이가 케이스에 맞는지 확인"
        ))
        
        # GPU-메인보드 PCIe
        self.register_rule(CompatibilityRule(
            id="gpu_mb_pcie",
            name="GPU-메인보드 PCIe 호환성",
            category=RuleCategory.INTERFACE,
            severity=RuleSeverity.WARNING,
            applies_to=["gpu", "motherboard"],
            check_function=check_gpu_mb_pcie,
            description="GPU와 메인보드의 PCIe 버전 호환성 확인"
        ))

        # 저장장치-메인보드 인터페이스
        self.register_rule(CompatibilityRule(
            id="storage_mb_interface",
            name="저장장치-메인보드 인터페이스 호환성",
            category=RuleCategory.INTERFACE,
            severity=RuleSeverity.ERROR,
            applies_to=["storage", "motherboard"],
            check_function=check_storage_mb_interface,
            description="저장장치 인터페이스가 메인보드에서 지원되는지 확인"
        ))
    
    def register_rule(self, rule: CompatibilityRule):
        """규칙 등록"""
        self.rules.append(rule)
        logger.debug(f"규칙 등록: {rule.id}")
    
    def get_applicable_rules(
        self,
        category1: str,
        category2: str,
    ) -> List[CompatibilityRule]:
        """
        두 카테고리에 적용 가능한 규칙 조회
        
        Args:
            category1: 첫 번째 부품 카테고리
            category2: 두 번째 부품 카테고리
            
        Returns:
            적용 가능한 규칙 리스트
        """
        applicable = []
        
        for rule in self.rules:
            # 순서에 관계없이 매칭
            if (set(rule.applies_to) == {category1, category2} or
                set(rule.applies_to) == {category2, category1}):
                applicable.append(rule)
        
        return applicable
    
    def check_pair(
        self,
        component1: Dict[str, Any],
        component2: Dict[str, Any],
    ) -> List[RuleResult]:
        """
        두 부품 간 호환성 검사
        
        Args:
            component1: 첫 번째 부품
            component2: 두 번째 부품
            
        Returns:
            검사 결과 리스트
        """
        cat1 = component1.get("category", "unknown")
        cat2 = component2.get("category", "unknown")
        
        applicable_rules = self.get_applicable_rules(cat1, cat2)
        results = []
        
        for rule in applicable_rules:
            # 규칙의 applies_to 순서에 맞게 인자 전달
            if rule.applies_to[0] == cat1:
                result = rule.check_function(component1, component2)
            else:
                result = rule.check_function(component2, component1)
            
            results.append(result)
        
        return results
    
    def check_all(
        self,
        components: List[Dict[str, Any]],
    ) -> List[RuleResult]:
        """
        모든 부품 조합에 대해 호환성 검사
        
        Args:
            components: 부품 리스트
            
        Returns:
            모든 검사 결과 리스트
        """
        all_results = []
        
        # 모든 쌍에 대해 검사
        for i, comp1 in enumerate(components):
            for comp2 in components[i+1:]:
                results = self.check_pair(comp1, comp2)
                all_results.extend(results)
        
        return all_results


# ============================================================================
# 테스트용 메인
# ============================================================================

if __name__ == "__main__":
    rules = CompatibilityRules()
    
    # 테스트 부품
    cpu = {
        "category": "cpu",
        "name": "Intel Core i5-14600K",
        "specs": {"socket": "LGA1700", "tdp": 125}
    }
    
    mb_compatible = {
        "category": "motherboard",
        "name": "ASUS ROG Strix Z790-A",
        "specs": {"socket": "LGA1700", "memory_type": "DDR5", "form_factor": "ATX"}
    }
    
    mb_incompatible = {
        "category": "motherboard",
        "name": "MSI MAG B650 TOMAHAWK",
        "specs": {"socket": "AM5", "memory_type": "DDR5", "form_factor": "ATX"}
    }
    
    # 호환되는 조합 테스트
    print("호환되는 조합 테스트:")
    results = rules.check_pair(cpu, mb_compatible)
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"  [{status}] {result.rule_id}: {result.message}")
    
    # 비호환 조합 테스트
    print("\n비호환 조합 테스트:")
    results = rules.check_pair(cpu, mb_incompatible)
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"  [{status}] {result.rule_id}: {result.message}")
