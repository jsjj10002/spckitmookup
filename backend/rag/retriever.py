"""
PC 부품 검색 및 추천 모듈
"""
from typing import List, Dict, Any, Optional
from loguru import logger

from .vector_store import PCComponentVectorStore
from .config import TOP_K_RESULTS


class PCComponentRetriever:
    """PC 부품 검색 및 필터링을 담당하는 클래스"""

    def __init__(
        self,
        vector_store: PCComponentVectorStore,
        top_k: int = TOP_K_RESULTS,
    ):
        """
        Args:
            vector_store: 벡터 데이터베이스
            top_k: 기본 검색 결과 수
        """
        self.vector_store = vector_store
        self.top_k = top_k
        logger.info(f"PCComponentRetriever 초기화: top_k={top_k}")

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        category: Optional[str] = None,
        min_similarity: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        쿼리에 맞는 PC 부품 검색

        Args:
            query: 사용자 쿼리 (예: "게임용 고성능 그래픽카드")
            top_k: 검색 결과 수
            category: 특정 카테고리로 필터링 (예: "gpu")
            min_similarity: 최소 유사도 (0~1)

        Returns:
            검색 결과 리스트
        """
        top_k = top_k or self.top_k

        # 메타데이터 필터 구성
        filter_metadata = {"category": category} if category else None

        # 벡터 검색 수행
        results = self.vector_store.search(
            query=query,
            top_k=top_k * 2,  # 필터링을 고려하여 더 많이 검색
            filter_metadata=filter_metadata,
        )

        # 유사도 필터링
        filtered_results = [r for r in results if r["similarity"] >= min_similarity]

        # 상위 k개만 반환
        filtered_results = filtered_results[:top_k]

        logger.info(
            f"검색 완료: '{query}' -> {len(filtered_results)}개 부품 "
            f"(category={category}, min_similarity={min_similarity})"
        )

        return filtered_results

    def retrieve_by_specs(
        self,
        requirements: Dict[str, Any],
        top_k: Optional[int] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        사양 요구사항에 맞는 부품 세트 검색

        Args:
            requirements: 요구사항 딕셔너리
                예: {
                    "budget": 150,
                    "purpose": "게임",
                    "categories": ["cpu", "gpu", "memory"]
                }
            top_k: 각 카테고리별 검색 결과 수

        Returns:
            카테고리별 검색 결과 딕셔너리
        """
        top_k = top_k or self.top_k

        # 쿼리 문자열 생성
        query_parts = []
        if "purpose" in requirements:
            query_parts.append(f"목적: {requirements['purpose']}")
        if "budget" in requirements:
            query_parts.append(f"예산: {requirements['budget']}만원")
        if "preferences" in requirements:
            query_parts.append(f"선호사항: {requirements['preferences']}")

        base_query = " ".join(query_parts)

        # 카테고리별 검색
        results_by_category = {}
        categories = requirements.get("categories", ["cpu", "gpu", "memory", "motherboard"])

        for category in categories:
            category_query = f"{base_query} {category}"
            results = self.retrieve(
                query=category_query,
                top_k=top_k,
                category=category,
            )
            results_by_category[category] = results

        logger.info(
            f"사양 기반 검색 완료: {len(categories)}개 카테고리, "
            f"총 {sum(len(v) for v in results_by_category.values())}개 부품"
        )

        return results_by_category

    def retrieve_compatible_components(
        self,
        base_component: Dict[str, Any],
        target_category: str,
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        기존 부품과 호환되는 부품 검색

        Args:
            base_component: 기준 부품 정보
            target_category: 검색할 카테고리
            top_k: 검색 결과 수

        Returns:
            호환 가능한 부품 리스트
        """
        top_k = top_k or self.top_k

        # 호환성 쿼리 생성
        base_name = base_component.get("name", "")
        base_category = base_component.get("category", "")

        query = f"{base_category} {base_name}와 호환되는 {target_category}"

        results = self.retrieve(
            query=query,
            top_k=top_k,
            category=target_category,
        )

        logger.info(
            f"호환성 검색 완료: {base_category} -> {target_category}, {len(results)}개 부품"
        )

        return results

    def get_popular_components(
        self,
        category: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        인기 있는 부품 조회 (카테고리별)

        Args:
            category: 부품 카테고리
            limit: 최대 결과 수

        Returns:
            부품 리스트
        """
        # 벡터 DB에서 카테고리별 조회
        results = self.vector_store.get_by_category(category=category, limit=limit)

        logger.info(f"인기 부품 조회: {category}, {len(results)}개")
        return results

