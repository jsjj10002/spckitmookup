"""
GNN 기반 초개인화 추천 시스템
==============================

그래프 신경망(Graph Neural Network)을 활용한 PC 부품 추천.
사용자-부품-속성 간 관계를 그래프로 모델링하여 개인화 추천 제공.

담당자: [팀원 이름]
상태: 개발 예정
"""

from .engine import GNNRecommendationEngine
from .graph_builder import PCComponentGraph
from .models import RecommendationGNN

__all__ = [
    "GNNRecommendationEngine",
    "PCComponentGraph",
    "RecommendationGNN",
]
