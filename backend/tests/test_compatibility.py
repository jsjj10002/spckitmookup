"""
호환성 엔진 모듈 테스트
======================

테스트 실행:
```bash
pytest backend/tests/test_compatibility.py -v
```
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestCompatibilityEngine:
    """CompatibilityEngine 테스트"""
    
    @pytest.fixture
    def engine(self):
        from backend.modules.compatibility.engine import CompatibilityEngine
        return CompatibilityEngine()
    
    @pytest.fixture
    def compatible_build(self):
        """호환되는 빌드 샘플"""
        return [
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
                "name": "DDR5-5600 32GB",
                "specs": {"generation": "DDR5", "capacity": 32}
            },
            {
                "category": "case",
                "name": "NZXT H7 Flow",
                "specs": {"form_factor": "ATX", "max_gpu_length": 400}
            },
            {
                "category": "psu",
                "name": "Corsair RM750",
                "specs": {"wattage": 750}
            },
        ]
    
    @pytest.fixture
    def incompatible_build(self):
        """비호환 빌드 샘플 (소켓 불일치)"""
        return [
            {
                "category": "cpu",
                "name": "Intel Core i5-14600K",
                "specs": {"socket": "LGA1700", "tdp": 125}
            },
            {
                "category": "motherboard",
                "name": "MSI MAG B650 TOMAHAWK",
                "specs": {"socket": "AM5", "memory_type": "DDR5"}  # AMD 소켓
            },
        ]
    
    def test_engine_initialization(self, engine):
        """엔진 초기화 테스트"""
        assert engine is not None
        assert engine.rules is not None
    
    def test_compatible_build(self, engine, compatible_build):
        """호환 빌드 테스트"""
        result = engine.check_all(compatible_build)
        
        assert result.is_compatible == True
        assert result.overall_score > 80
    
    def test_incompatible_build(self, engine, incompatible_build):
        """비호환 빌드 테스트"""
        result = engine.check_all(incompatible_build)
        
        # 소켓 불일치로 호환 불가
        assert result.is_compatible == False
        
        # 실패한 검사 찾기
        failed_checks = [c for c in result.checks if c.status.value == "fail"]
        assert len(failed_checks) > 0
    
    def test_power_calculation(self, engine, compatible_build):
        """전력 계산 테스트"""
        result = engine.check_all(compatible_build)
        
        assert result.power_summary is not None
        assert result.power_summary.total_tdp > 0
        assert result.power_summary.recommended_psu > 0
    
    def test_recommendations_generation(self, engine, compatible_build):
        """권장사항 생성 테스트"""
        result = engine.check_all(compatible_build)
        
        # 권장사항은 리스트
        assert isinstance(result.recommendations, list)


class TestCompatibilityRules:
    """CompatibilityRules 테스트"""
    
    @pytest.fixture
    def rules(self):
        from backend.modules.compatibility.rules import CompatibilityRules
        return CompatibilityRules()
    
    def test_rules_initialization(self, rules):
        """규칙 초기화 테스트"""
        assert len(rules.rules) > 0
    
    def test_cpu_mb_socket_compatible(self, rules):
        """CPU-메인보드 소켓 호환 테스트"""
        cpu = {
            "category": "cpu",
            "name": "Intel Core i5-14600K",
            "specs": {"socket": "LGA1700"}
        }
        mb = {
            "category": "motherboard",
            "name": "ASUS ROG Z790-A",
            "specs": {"socket": "LGA1700"}
        }
        
        results = rules.check_pair(cpu, mb)
        
        # 소켓 호환성 검사 결과 찾기
        socket_check = next((r for r in results if "socket" in r.rule_id), None)
        assert socket_check is not None
        assert socket_check.passed == True
    
    def test_cpu_mb_socket_incompatible(self, rules):
        """CPU-메인보드 소켓 비호환 테스트"""
        cpu = {
            "category": "cpu",
            "name": "Intel Core i5-14600K",
            "specs": {"socket": "LGA1700"}
        }
        mb = {
            "category": "motherboard",
            "name": "MSI B650",
            "specs": {"socket": "AM5"}
        }
        
        results = rules.check_pair(cpu, mb)
        
        socket_check = next((r for r in results if "socket" in r.rule_id), None)
        assert socket_check is not None
        assert socket_check.passed == False
    
    def test_memory_mb_type(self, rules):
        """메모리-메인보드 타입 테스트"""
        memory = {
            "category": "memory",
            "name": "DDR5-5600",
            "specs": {"generation": "DDR5"}
        }
        mb = {
            "category": "motherboard",
            "name": "ASUS Z790",
            "specs": {"memory_type": "DDR5"}
        }
        
        results = rules.check_pair(memory, mb)
        
        mem_check = next((r for r in results if "memory" in r.rule_id), None)
        assert mem_check is not None
        assert mem_check.passed == True


class TestPCOntology:
    """PCOntology 테스트"""
    
    @pytest.fixture
    def ontology(self):
        from backend.modules.compatibility.ontology import PCOntology, ComponentClass
        onto = PCOntology()
        
        # 테스트 개체 추가
        onto.add_individual(
            id="cpu_i5_14600k",
            class_type=ComponentClass.CPU,
            properties={
                "name": "Intel Core i5-14600K",
                "hasSocket": "LGA1700",
            }
        )
        onto.add_individual(
            id="mb_asus_z790",
            class_type=ComponentClass.MOTHERBOARD,
            properties={
                "name": "ASUS ROG Strix Z790-A",
                "hasSocket": "LGA1700",
            }
        )
        onto.add_individual(
            id="mb_msi_b650",
            class_type=ComponentClass.MOTHERBOARD,
            properties={
                "name": "MSI MAG B650",
                "hasSocket": "AM5",
            }
        )
        
        return onto
    
    def test_ontology_initialization(self, ontology):
        """온톨로지 초기화 테스트"""
        from backend.modules.compatibility.ontology import ComponentClass
        
        assert len(ontology.classes) > 0
        assert ComponentClass.CPU in ontology.classes
    
    def test_add_and_get_individual(self, ontology):
        """개체 추가 및 조회 테스트"""
        ind = ontology.get_individual("cpu_i5_14600k")
        
        assert ind is not None
        assert ind.properties["name"] == "Intel Core i5-14600K"
    
    def test_query_compatible(self, ontology):
        """호환 부품 질의 테스트"""
        from backend.modules.compatibility.ontology import ComponentClass
        
        compatible = ontology.query_compatible("cpu_i5_14600k", ComponentClass.MOTHERBOARD)
        
        # LGA1700 소켓인 메인보드만 반환
        assert len(compatible) == 1
        assert compatible[0].id == "mb_asus_z790"


# pytest 실행
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
