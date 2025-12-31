"""
온톨로지 기반 호환성 검사 엔진
===============================

PC 부품 간 호환성을 온톨로지와 규칙 기반으로 검증하는 모듈.
지식 그래프와 추론 엔진을 활용하여 정확한 호환성 판단.

담당자: [팀원 이름]
상태: 개발 예정
"""

from .engine import CompatibilityEngine
from .ontology import PCOntology
from .rules import CompatibilityRules

__all__ = [
    "CompatibilityEngine",
    "PCOntology",
    "CompatibilityRules",
]
