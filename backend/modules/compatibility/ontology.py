"""
PC 부품 온톨로지
================

[목표]
------
PC 부품의 개념, 속성, 관계를 형식적으로 정의하는 온톨로지.
지식 그래프 형태로 부품 간 관계를 표현.

[온톨로지 구조]
--------------
클래스 계층:
```
Component (부품)
├── Processor (프로세서)
│   ├── CPU
│   └── GPU
├── Memory (메모리)
│   ├── RAM
│   └── Storage
├── Board (보드)
│   └── Motherboard
├── Power (전원)
│   └── PSU
├── Cooling (쿨링)
│   ├── CPUCooler
│   └── CaseFan
└── Enclosure (인클로저)
    └── Case
```

속성:
- hasSocket: 소켓 타입 (CPU, 메인보드)
- hasFormFactor: 폼팩터 (메인보드, 케이스)
- hasTDP: 전력 소모량
- hasMemoryType: 메모리 타입 (DDR4, DDR5)
- hasCapacity: 용량 (메모리, 스토리지)
- hasLength: 길이 (GPU, 케이스)

관계:
- compatibleWith: 호환됨
- requiresSocket: 특정 소켓 필요
- supportsMemory: 특정 메모리 지원
- fitsIn: 케이스에 장착 가능

[참고]
-----
- OWL (Web Ontology Language)
- RDFLib: Python RDF 라이브러리
- OWLReady2: 온톨로지 추론 라이브러리

[TODO]
-----
- [ ] OWL 온톨로지 파일 생성
- [ ] RDFLib 기반 질의 구현
- [ ] 추론 엔진 연동
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
from loguru import logger


# ============================================================================
# 온톨로지 클래스 정의
# ============================================================================

class ComponentClass(str, Enum):
    """부품 클래스"""
    COMPONENT = "Component"
    PROCESSOR = "Processor"
    CPU = "CPU"
    GPU = "GPU"
    MEMORY = "Memory"
    RAM = "RAM"
    STORAGE = "Storage"
    BOARD = "Board"
    MOTHERBOARD = "Motherboard"
    POWER = "Power"
    PSU = "PSU"
    COOLING = "Cooling"
    CPU_COOLER = "CPUCooler"
    CASE_FAN = "CaseFan"
    ENCLOSURE = "Enclosure"
    CASE = "Case"


class PropertyType(str, Enum):
    """속성 타입"""
    DATA_PROPERTY = "data"       # 데이터 속성 (리터럴 값)
    OBJECT_PROPERTY = "object"  # 객체 속성 (다른 개체 참조)


# ============================================================================
# 데이터 클래스
# ============================================================================

@dataclass
class OntologyProperty:
    """온톨로지 속성"""
    name: str
    property_type: PropertyType
    domain: List[ComponentClass]  # 이 속성을 가질 수 있는 클래스들
    range_type: str  # 값의 타입 (int, str, ComponentClass 등)
    description: str = ""


@dataclass
class OntologyClass:
    """온톨로지 클래스"""
    name: ComponentClass
    parent: Optional[ComponentClass] = None
    properties: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class OntologyIndividual:
    """온톨로지 개체 (실제 부품)"""
    id: str
    class_type: ComponentClass
    properties: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# PC 온톨로지 정의
# ============================================================================

class PCOntology:
    """
    PC 부품 온톨로지
    
    부품의 클래스, 속성, 관계를 정의하고 관리.
    
    사용법:
    ```python
    ontology = PCOntology()
    
    # 개체 추가
    ontology.add_individual(
        id="cpu_i5_14600k",
        class_type=ComponentClass.CPU,
        properties={
            "hasSocket": "LGA1700",
            "hasTDP": 125,
            "name": "Intel Core i5-14600K"
        }
    )
    
    # 호환성 질의
    compatible = ontology.query_compatible("cpu_i5_14600k", ComponentClass.MOTHERBOARD)
    ```
    """
    
    # 클래스 계층 정의
    CLASS_HIERARCHY = {
        ComponentClass.COMPONENT: None,
        ComponentClass.PROCESSOR: ComponentClass.COMPONENT,
        ComponentClass.CPU: ComponentClass.PROCESSOR,
        ComponentClass.GPU: ComponentClass.PROCESSOR,
        ComponentClass.MEMORY: ComponentClass.COMPONENT,
        ComponentClass.RAM: ComponentClass.MEMORY,
        ComponentClass.STORAGE: ComponentClass.MEMORY,
        ComponentClass.BOARD: ComponentClass.COMPONENT,
        ComponentClass.MOTHERBOARD: ComponentClass.BOARD,
        ComponentClass.POWER: ComponentClass.COMPONENT,
        ComponentClass.PSU: ComponentClass.POWER,
        ComponentClass.COOLING: ComponentClass.COMPONENT,
        ComponentClass.CPU_COOLER: ComponentClass.COOLING,
        ComponentClass.CASE_FAN: ComponentClass.COOLING,
        ComponentClass.ENCLOSURE: ComponentClass.COMPONENT,
        ComponentClass.CASE: ComponentClass.ENCLOSURE,
    }
    
    # 속성 정의
    PROPERTIES = {
        # 데이터 속성
        "name": OntologyProperty(
            name="name",
            property_type=PropertyType.DATA_PROPERTY,
            domain=[ComponentClass.COMPONENT],
            range_type="str",
            description="부품 이름"
        ),
        "hasSocket": OntologyProperty(
            name="hasSocket",
            property_type=PropertyType.DATA_PROPERTY,
            domain=[ComponentClass.CPU, ComponentClass.MOTHERBOARD, ComponentClass.CPU_COOLER],
            range_type="str",
            description="소켓 타입 (LGA1700, AM5 등)"
        ),
        "hasFormFactor": OntologyProperty(
            name="hasFormFactor",
            property_type=PropertyType.DATA_PROPERTY,
            domain=[ComponentClass.MOTHERBOARD, ComponentClass.CASE],
            range_type="str",
            description="폼팩터 (ATX, Micro-ATX 등)"
        ),
        "hasTDP": OntologyProperty(
            name="hasTDP",
            property_type=PropertyType.DATA_PROPERTY,
            domain=[ComponentClass.CPU, ComponentClass.GPU],
            range_type="int",
            description="TDP (W)"
        ),
        "hasWattage": OntologyProperty(
            name="hasWattage",
            property_type=PropertyType.DATA_PROPERTY,
            domain=[ComponentClass.PSU],
            range_type="int",
            description="정격 출력 (W)"
        ),
        "hasMemoryType": OntologyProperty(
            name="hasMemoryType",
            property_type=PropertyType.DATA_PROPERTY,
            domain=[ComponentClass.RAM, ComponentClass.MOTHERBOARD],
            range_type="str",
            description="메모리 타입 (DDR4, DDR5)"
        ),
        "hasCapacity": OntologyProperty(
            name="hasCapacity",
            property_type=PropertyType.DATA_PROPERTY,
            domain=[ComponentClass.RAM, ComponentClass.STORAGE],
            range_type="int",
            description="용량 (GB)"
        ),
        "hasLength": OntologyProperty(
            name="hasLength",
            property_type=PropertyType.DATA_PROPERTY,
            domain=[ComponentClass.GPU],
            range_type="int",
            description="길이 (mm)"
        ),
        "maxGPULength": OntologyProperty(
            name="maxGPULength",
            property_type=PropertyType.DATA_PROPERTY,
            domain=[ComponentClass.CASE],
            range_type="int",
            description="최대 GPU 길이 (mm)"
        ),
        "maxCoolerHeight": OntologyProperty(
            name="maxCoolerHeight",
            property_type=PropertyType.DATA_PROPERTY,
            domain=[ComponentClass.CASE],
            range_type="int",
            description="최대 쿨러 높이 (mm)"
        ),
        
        # 객체 속성
        "compatibleWith": OntologyProperty(
            name="compatibleWith",
            property_type=PropertyType.OBJECT_PROPERTY,
            domain=[ComponentClass.COMPONENT],
            range_type="Component",
            description="호환됨"
        ),
    }
    
    def __init__(self):
        """온톨로지 초기화"""
        self.classes: Dict[ComponentClass, OntologyClass] = {}
        self.individuals: Dict[str, OntologyIndividual] = {}
        self.compatibility_rules: List[Dict[str, Any]] = []
        
        # 클래스 초기화
        self._init_classes()
        
        logger.info("PCOntology 초기화 완료")
    
    def _init_classes(self):
        """클래스 초기화"""
        for class_type, parent in self.CLASS_HIERARCHY.items():
            self.classes[class_type] = OntologyClass(
                name=class_type,
                parent=parent,
            )
    
    def add_individual(
        self,
        id: str,
        class_type: ComponentClass,
        properties: Dict[str, Any],
    ):
        """
        개체(부품) 추가
        
        Args:
            id: 개체 ID
            class_type: 클래스 타입
            properties: 속성 딕셔너리
        """
        individual = OntologyIndividual(
            id=id,
            class_type=class_type,
            properties=properties,
        )
        self.individuals[id] = individual
        logger.debug(f"개체 추가: {id} ({class_type.value})")
    
    def get_individual(self, id: str) -> Optional[OntologyIndividual]:
        """개체 조회"""
        return self.individuals.get(id)
    
    def get_individuals_by_class(
        self,
        class_type: ComponentClass,
        include_subclasses: bool = True,
    ) -> List[OntologyIndividual]:
        """
        클래스별 개체 조회
        
        Args:
            class_type: 클래스 타입
            include_subclasses: 하위 클래스 포함 여부
            
        Returns:
            개체 리스트
        """
        result = []
        target_classes = {class_type}
        
        if include_subclasses:
            target_classes = self._get_subclasses(class_type)
            target_classes.add(class_type)
        
        for individual in self.individuals.values():
            if individual.class_type in target_classes:
                result.append(individual)
        
        return result
    
    def _get_subclasses(self, class_type: ComponentClass) -> Set[ComponentClass]:
        """하위 클래스 조회"""
        subclasses = set()
        for cls, parent in self.CLASS_HIERARCHY.items():
            if parent == class_type:
                subclasses.add(cls)
                subclasses.update(self._get_subclasses(cls))
        return subclasses
    
    def query_compatible(
        self,
        individual_id: str,
        target_class: ComponentClass,
    ) -> List[OntologyIndividual]:
        """
        호환 가능한 부품 질의
        
        Args:
            individual_id: 기준 부품 ID
            target_class: 찾을 부품 클래스
            
        Returns:
            호환 가능한 부품 리스트
        """
        individual = self.get_individual(individual_id)
        if not individual:
            return []
        
        compatible = []
        candidates = self.get_individuals_by_class(target_class)
        
        for candidate in candidates:
            if self._check_compatibility(individual, candidate):
                compatible.append(candidate)
        
        return compatible
    
    def _check_compatibility(
        self,
        component1: OntologyIndividual,
        component2: OntologyIndividual,
    ) -> bool:
        """
        두 부품 간 호환성 확인
        
        규칙 기반 검사
        """
        # 소켓 호환성 검사
        socket1 = component1.properties.get("hasSocket")
        socket2 = component2.properties.get("hasSocket")
        
        if socket1 and socket2:
            if socket1 != socket2:
                return False
        
        # 메모리 타입 호환성
        mem_type1 = component1.properties.get("hasMemoryType")
        mem_type2 = component2.properties.get("hasMemoryType")
        
        if mem_type1 and mem_type2:
            if mem_type1 != mem_type2:
                return False
        
        return True
    
    def add_compatibility_rule(
        self,
        rule_id: str,
        condition: Dict[str, Any],
        action: str,
    ):
        """
        호환성 규칙 추가
        
        Args:
            rule_id: 규칙 ID
            condition: 조건 (속성 비교)
            action: 결과 (compatible, incompatible)
        """
        self.compatibility_rules.append({
            "id": rule_id,
            "condition": condition,
            "action": action,
        })
    
    def export_to_json(self, path: str):
        """온톨로지를 JSON으로 내보내기"""
        data = {
            "classes": {
                cls.value: {
                    "parent": parent.value if parent else None,
                }
                for cls, parent in self.CLASS_HIERARCHY.items()
            },
            "properties": {
                name: {
                    "type": prop.property_type.value,
                    "domain": [d.value for d in prop.domain],
                    "range": prop.range_type,
                    "description": prop.description,
                }
                for name, prop in self.PROPERTIES.items()
            },
            "individuals": {
                id: {
                    "class": ind.class_type.value,
                    "properties": ind.properties,
                }
                for id, ind in self.individuals.items()
            },
            "rules": self.compatibility_rules,
        }
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"온톨로지 내보내기: {path}")
    
    def import_from_json(self, path: str):
        """JSON에서 온톨로지 가져오기"""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 개체 로드
        for id, ind_data in data.get("individuals", {}).items():
            self.add_individual(
                id=id,
                class_type=ComponentClass(ind_data["class"]),
                properties=ind_data["properties"],
            )
        
        # 규칙 로드
        self.compatibility_rules = data.get("rules", [])
        
        logger.info(f"온톨로지 가져오기: {path}, {len(self.individuals)}개 개체")


# ============================================================================
# 테스트용 메인
# ============================================================================

if __name__ == "__main__":
    ontology = PCOntology()
    
    # 테스트 개체 추가
    ontology.add_individual(
        id="cpu_i5_14600k",
        class_type=ComponentClass.CPU,
        properties={
            "name": "Intel Core i5-14600K",
            "hasSocket": "LGA1700",
            "hasTDP": 125,
        }
    )
    
    ontology.add_individual(
        id="mb_asus_z790",
        class_type=ComponentClass.MOTHERBOARD,
        properties={
            "name": "ASUS ROG Strix Z790-A",
            "hasSocket": "LGA1700",
            "hasFormFactor": "ATX",
            "hasMemoryType": "DDR5",
        }
    )
    
    ontology.add_individual(
        id="mb_msi_b650",
        class_type=ComponentClass.MOTHERBOARD,
        properties={
            "name": "MSI MAG B650 TOMAHAWK",
            "hasSocket": "AM5",  # 다른 소켓
            "hasFormFactor": "ATX",
            "hasMemoryType": "DDR5",
        }
    )
    
    # 호환 가능한 메인보드 질의
    compatible_mbs = ontology.query_compatible("cpu_i5_14600k", ComponentClass.MOTHERBOARD)
    
    print("i5-14600K와 호환되는 메인보드:")
    for mb in compatible_mbs:
        print(f"  - {mb.properties.get('name')}")
    
    # JSON 내보내기
    ontology.export_to_json("/tmp/pc_ontology_test.json")
    print("\n온톨로지 내보내기 완료")
