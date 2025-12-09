"""
RAG 파이프라인 - 전체 시스템 통합
"""
from typing import Dict, Any, List, Optional
from pathlib import Path
from loguru import logger

from .embedder import GeminiEmbedder
from .vector_store import PCComponentVectorStore
from .retriever import PCComponentRetriever
from .generator import PCRecommendationGenerator
from .data_parser import PCDataParser
from .config import SQL_DUMP_PATH, CHROMA_PERSIST_DIRECTORY, CHROMA_COLLECTION_NAME


class RAGPipeline:
    """RAG 시스템 전체 파이프라인"""

    def __init__(
        self,
        embedder: Optional[GeminiEmbedder] = None,
        vector_store: Optional[PCComponentVectorStore] = None,
        retriever: Optional[PCComponentRetriever] = None,
        generator: Optional[PCRecommendationGenerator] = None,
    ):
        """
        Args:
            embedder: 임베딩 생성기
            vector_store: 벡터 데이터베이스
            retriever: 검색기
            generator: 응답 생성기
        """
        # 각 컴포넌트 초기화
        self.embedder = embedder or GeminiEmbedder()
        self.vector_store = vector_store or PCComponentVectorStore(embedder=self.embedder)
        self.retriever = retriever or PCComponentRetriever(vector_store=self.vector_store)
        self.generator = generator or PCRecommendationGenerator()

        logger.info("RAGPipeline 초기화 완료")

    def initialize_database(
        self,
        sql_file_path: Path = SQL_DUMP_PATH,
        force_rebuild: bool = False,
    ) -> Dict[str, Any]:
        """
        SQL 데이터를 파싱하고 벡터 데이터베이스 구축

        Args:
            sql_file_path: SQL 덤프 파일 경로
            force_rebuild: 기존 데이터를 삭제하고 재구축할지 여부

        Returns:
            초기화 결과 정보
        """
        logger.info("=" * 60)
        logger.info("벡터 데이터베이스 초기화 시작")
        logger.info("=" * 60)

        # 기존 데이터 확인
        current_count = self.vector_store.collection.count()
        if current_count > 0 and not force_rebuild:
            logger.info(f"기존 데이터 존재: {current_count}개 문서. 초기화 건너뜀.")
            return {
                "status": "skipped",
                "message": "기존 데이터가 존재합니다.",
                "document_count": current_count,
            }

        if force_rebuild:
            logger.warning("기존 데이터 삭제 중...")
            self.vector_store.delete_collection()

        # 1. SQL 파일 파싱
        logger.info("Step 1: SQL 데이터 파싱")
        parser = PCDataParser(sql_file_path=sql_file_path)
        tables_data = parser.parse_sql_dump()

        # 2. 문서 생성
        logger.info("Step 2: 문서 생성")
        documents = parser.create_component_documents(tables_data)

        if not documents:
            raise ValueError("생성된 문서가 없습니다.")

        # 3. 벡터 데이터베이스에 추가
        logger.info("Step 3: 벡터 데이터베이스에 추가")
        self.vector_store.add_documents(documents)

        # 4. 통계 정보
        stats = self.vector_store.get_stats()

        logger.info("=" * 60)
        logger.info("벡터 데이터베이스 초기화 완료")
        logger.info(f"총 문서 수: {stats['total_documents']}")
        logger.info("=" * 60)

        return {
            "status": "success",
            "message": "벡터 데이터베이스 초기화 완료",
            **stats,
        }

    def query(
        self,
        user_query: str,
        top_k: int = 5,
        category: Optional[str] = None,
        include_context: bool = False,
    ) -> Dict[str, Any]:
        """
        사용자 쿼리에 대한 PC 부품 추천 생성

        Args:
            user_query: 사용자 쿼리
            top_k: 검색할 부품 수
            category: 특정 카테고리로 제한
            include_context: 검색된 원본 데이터 포함 여부

        Returns:
            추천 결과 딕셔너리
        """
        logger.info(f"쿼리 처리 시작: '{user_query}'")

        # 1. 관련 부품 검색
        retrieved_components = self.retriever.retrieve(
            query=user_query,
            top_k=top_k,
            category=category,
        )

        if not retrieved_components:
            logger.warning("검색된 부품이 없습니다. AI 생성 단계로 진행합니다.")
            # early return 제거 -> generator가 처리하도록 함

        # 2. 추천 생성
        recommendation = self.generator.generate_recommendation(
            user_query=user_query,
            retrieved_components=retrieved_components,
        )

        # 3. 결과 구성
        result = {
            "query": user_query,
            "recommendation": recommendation,
            "retrieved_count": len(retrieved_components),
        }

        if include_context:
            result["retrieved_components"] = retrieved_components

        logger.info(f"쿼리 처리 완료: {len(retrieved_components)}개 부품 검색, 추천 생성 완료")

        return result

    def query_by_specs(
        self,
        requirements: Dict[str, Any],
        top_k: int = 3,
    ) -> Dict[str, Any]:
        """
        사양 요구사항 기반 부품 세트 추천

        Args:
            requirements: 요구사항 딕셔너리
            top_k: 각 카테고리별 검색 결과 수

        Returns:
            카테고리별 추천 결과
        """
        logger.info(f"사양 기반 쿼리 처리: {requirements}")

        # 1. 카테고리별 부품 검색
        components_by_category = self.retriever.retrieve_by_specs(
            requirements=requirements,
            top_k=top_k,
        )

        # 2. 전체 부품 리스트 생성
        all_components = []
        for category, components in components_by_category.items():
            all_components.extend(components)

        # 3. 전체 쿼리 생성
        query_parts = []
        if "purpose" in requirements:
            query_parts.append(f"{requirements['purpose']}용")
        if "budget" in requirements:
            query_parts.append(f"예산 {requirements['budget']}만원")
        query_parts.append("PC 조립")

        user_query = " ".join(query_parts)

        # 4. 추천 생성
        recommendation = self.generator.generate_recommendation(
            user_query=user_query,
            retrieved_components=all_components,
        )

        return {
            "requirements": requirements,
            "recommendation": recommendation,
            "components_by_category": {
                cat: [c["metadata"]["name"] for c in comps]
                for cat, comps in components_by_category.items()
            },
            "total_retrieved": len(all_components),
        }

    def compare_components(
        self,
        component_ids: List[str],
    ) -> Dict[str, Any]:
        """
        여러 부품을 비교 분석

        Args:
            component_ids: 비교할 부품 ID 리스트

        Returns:
            비교 분석 결과
        """
        logger.info(f"부품 비교: {len(component_ids)}개")

        # ChromaDB에서 부품 조회
        components = []
        for comp_id in component_ids:
            result = self.vector_store.collection.get(ids=[comp_id])
            if result["ids"]:
                components.append({
                    "id": result["ids"][0],
                    "document": result["documents"][0],
                    "metadata": result["metadatas"][0],
                })

        if len(components) < 2:
            raise ValueError("비교하려면 최소 2개의 부품이 필요합니다.")

        # 비교 분석 생성
        comparison = self.generator.generate_comparison(components)

        return {
            "compared_components": [c["metadata"]["name"] for c in components],
            "comparison": comparison,
        }

    def get_stats(self) -> Dict[str, Any]:
        """시스템 통계 조회"""
        return self.vector_store.get_stats()

