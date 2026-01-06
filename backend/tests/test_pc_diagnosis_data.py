import pytest
from backend.modules.pc_diagnosis.collectors import BenchmarkCollector
from backend.modules.pc_diagnosis.analyzers import UpgradeAdvisor
import os

class TestPCDiagnosisData:
    def test_benchmark_data_loading(self):
        """벤치마크 데이터 로드 테스트"""
        collector = BenchmarkCollector()
        
        # 데이터가 로드되었는지 확인
        assert len(collector.cpu_benchmarks) > 0
        assert len(collector.gpu_benchmarks) > 0
        
        # 특정 샘플 데이터 확인
        assert "i5-12400f" in collector.cpu_benchmarks
        assert collector.cpu_benchmarks["i5-12400f"] == 55
        
    def test_budget_builds_loading(self):
        """예산별 견적 로드 테스트"""
        advisor = UpgradeAdvisor()
        
        # 1. 500만원 예산 (모든 견적 나와야 함 or 적어도 고사양)
        builds_high = advisor.get_budget_builds(5000000)
        assert len(builds_high) > 0
        
        # 2. 아주 적은 예산 (견적 없어야 함)
        builds_low = advisor.get_budget_builds(100000)
        assert len(builds_low) == 0
        
        # 3. 데이터 구조 확인
        build = builds_high[0]
        assert "name" in build
        assert "components" in build
        assert "price_range" in build
