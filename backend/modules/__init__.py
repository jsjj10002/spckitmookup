"""
Spckit AI Backend Modules
=========================

PC 부품 추천 시스템의 핵심 모듈 패키지.
각 모듈은 독립적으로 개발 및 테스트 가능하도록 설계됨.

모듈 구성:
---------
- multi_agent: CREWai 기반 멀티 에이전트 오케스트레이션
- pc_diagnosis: PC 사양 진단 및 분석
- price_prediction: 시계열 트랜스포머 기반 가격 예측
- recommendation: GNN 기반 초개인화 추천 시스템
- compatibility: 온톨로지 기반 호환성 검사 엔진

사용법:
------
```python
from backend.modules.multi_agent import AgentOrchestrator
from backend.modules.pc_diagnosis import PCDiagnosisEngine
from backend.modules.price_prediction import PricePredictionModel
from backend.modules.recommendation import GNNRecommendationEngine
from backend.modules.compatibility import CompatibilityEngine
```
"""

__version__ = "0.1.0"
__author__ = "Spckit AI Team"

# 모듈 목록 (활성화된 것만 import)
__all__ = [
    "multi_agent",
    "pc_diagnosis", 
    "price_prediction",
    "recommendation",
    "compatibility",
]
