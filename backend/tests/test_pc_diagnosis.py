"""
PC 사양 진단 모듈 테스트
========================

테스트 실행:
```bash
pytest backend/tests/test_pc_diagnosis.py -v
```
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestPCDiagnosisEngine:
    """PCDiagnosisEngine 테스트"""
    
    @pytest.fixture
    def engine(self):
        """테스트용 엔진 인스턴스"""
        from backend.modules.pc_diagnosis.engine import PCDiagnosisEngine
        return PCDiagnosisEngine()
    
    @pytest.fixture
    def sample_specs(self):
        """테스트용 샘플 스펙"""
        return {
            "cpu": {
                "name": "Intel Core i5-12400F",
                "cores": 6,
                "threads": 12,
            },
            "gpu": {
                "name": "RTX 3060",
                "vram": 12,
            },
            "memory": {
                "capacity": 16,
                "speed": 3200,
                "generation": "DDR4"
            },
            "storage": {
                "type": "NVMe SSD",
                "capacity": 512,
            },
            "usage_purpose": "gaming"
        }
    
    def test_engine_initialization(self, engine):
        """엔진 초기화 테스트"""
        assert engine is not None
        assert len(engine.cpu_benchmarks) > 0
        assert len(engine.gpu_benchmarks) > 0
    
    def test_diagnosis_result(self, engine, sample_specs):
        """진단 결과 테스트"""
        result = engine.diagnose(sample_specs)
        
        assert result is not None
        assert 0 <= result.overall_score <= 100
        assert result.tier is not None
        assert result.bottleneck is not None
        assert "cpu" in result.component_scores
        assert "gpu" in result.component_scores
    
    def test_component_scores(self, engine, sample_specs):
        """부품별 점수 테스트"""
        result = engine.diagnose(sample_specs)
        
        for comp, score_data in result.component_scores.items():
            assert 0 <= score_data.score <= 100
            assert score_data.tier is not None
    
    def test_bottleneck_detection(self, engine):
        """병목 감지 테스트"""
        # CPU 병목 상황 (약한 CPU + 강한 GPU)
        weak_cpu_specs = {
            "cpu": {"name": "Intel Core i5-12400F"},  # 55점
            "gpu": {"name": "RTX 4070 Ti"},  # 72점
            "memory": {"capacity": 16, "speed": 3200, "generation": "DDR4"},
            "storage": {"type": "SSD", "capacity": 512},
        }
        
        result = engine.diagnose(weak_cpu_specs)
        
        # 병목 결과 확인
        assert result.bottleneck is not None
    
    def test_purpose_fitness(self, engine, sample_specs):
        """목적별 적합성 테스트"""
        result = engine.diagnose(sample_specs)
        
        assert "gaming" in result.purpose_fitness
        assert "work" in result.purpose_fitness
        
        # 적합도는 0-1 사이
        for purpose, fitness in result.purpose_fitness.items():
            assert 0 <= fitness <= 1
    
    def test_upgrade_recommendations(self, engine, sample_specs):
        """업그레이드 추천 테스트"""
        result = engine.diagnose(sample_specs)
        
        # 추천 목록은 리스트
        assert isinstance(result.upgrade_recommendations, list)
        
        # 각 추천 항목 검증
        for rec in result.upgrade_recommendations:
            assert rec.component is not None
            assert rec.priority >= 1


class TestHardwareCollector:
    """HardwareCollector 테스트"""
    
    @pytest.fixture
    def collector(self):
        from backend.modules.pc_diagnosis.collectors import HardwareCollector
        return HardwareCollector()
    
    def test_normalize_cpu_name(self, collector):
        """CPU 이름 정규화 테스트"""
        # 다양한 표기법 테스트
        variations = [
            "i5-12400f",
            "Intel Core i5-12400F",
            "i5 12400",
        ]
        
        for name in variations:
            normalized = collector.normalize_cpu_name(name)
            assert "i5" in normalized.lower() or "12400" in normalized
    
    def test_parse_natural_language(self, collector):
        """자연어 파싱 테스트"""
        result = collector.parse_natural_language(
            "i5 12400f, RTX 3060, 램 16기가, SSD 512GB"
        )
        
        assert "cpu" in result
        assert "gpu" in result
        assert "memory" in result
        assert "storage" in result


class TestBottleneckAnalyzer:
    """BottleneckAnalyzer 테스트"""
    
    @pytest.fixture
    def analyzer(self):
        from backend.modules.pc_diagnosis.analyzers import BottleneckAnalyzer
        return BottleneckAnalyzer()
    
    def test_balanced_system(self, analyzer):
        """밸런스 시스템 테스트"""
        result = analyzer.analyze(
            cpu_score=70,
            gpu_score=72,
            memory_score=70,
            resolution="1080p"
        )
        
        # 점수 차이가 적으면 밸런스 양호
        assert result.component == "none" or result.percentage < 20
    
    def test_cpu_bottleneck(self, analyzer):
        """CPU 병목 테스트"""
        result = analyzer.analyze(
            cpu_score=50,
            gpu_score=85,
            memory_score=70,
            resolution="1080p"
        )
        
        # 큰 점수 차이는 병목 발생
        assert result.percentage > 0
    
    def test_resolution_impact(self, analyzer):
        """해상도별 영향 테스트"""
        # 같은 스펙으로 해상도만 다르게
        result_1080p = analyzer.analyze(70, 70, 70, "1080p")
        result_4k = analyzer.analyze(70, 70, 70, "4k")
        
        # 두 결과 모두 생성됨
        assert result_1080p is not None
        assert result_4k is not None


# pytest 실행
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
