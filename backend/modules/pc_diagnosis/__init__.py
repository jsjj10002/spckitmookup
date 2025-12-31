"""
PC 사양 진단 모듈
=================

현재 사용자의 PC 사양을 분석하고 업그레이드 추천을 제공하는 모듈.
하드웨어 정보 수집, 병목 분석, 성능 벤치마크 기반 진단.

담당자: [팀원 이름]
상태: 개발 예정
"""

from .engine import PCDiagnosisEngine
from .collectors import (
    HardwareCollector,
    BenchmarkCollector,
)
from .analyzers import (
    BottleneckAnalyzer,
    UpgradeAdvisor,
)

__all__ = [
    "PCDiagnosisEngine",
    "HardwareCollector",
    "BenchmarkCollector",
    "BottleneckAnalyzer",
    "UpgradeAdvisor",
]
