"""
RAG 시스템 테스트 스크립트
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.rag.pipeline import RAGPipeline
from loguru import logger
import json


def test_query(pipeline: RAGPipeline, query: str):
    """쿼리 테스트"""
    logger.info(f"\n{'=' * 60}")
    logger.info(f"쿼리: {query}")
    logger.info(f"{'=' * 60}")

    result = pipeline.query(user_query=query, top_k=5, include_context=True)

    logger.info(f"\n검색된 부품 수: {result['retrieved_count']}")
    logger.info(f"\n추천 결과:")
    logger.info(json.dumps(result["recommendation"], indent=2, ensure_ascii=False))

    if result.get("retrieved_components"):
        logger.info(f"\n검색된 부품 목록:")
        for i, comp in enumerate(result["retrieved_components"][:3], 1):
            logger.info(f"  {i}. {comp['metadata']['name']} (유사도: {comp['similarity']:.2%})")


def test_specs_query(pipeline: RAGPipeline):
    """사양 기반 쿼리 테스트"""
    logger.info(f"\n{'=' * 60}")
    logger.info("사양 기반 쿼리 테스트")
    logger.info(f"{'=' * 60}")

    requirements = {
        "budget": 150,
        "purpose": "게임",
        "categories": ["cpu", "gpu", "memory"],
    }

    logger.info(f"요구사항: {requirements}")

    result = pipeline.query_by_specs(requirements=requirements, top_k=3)

    logger.info(f"\n추천 결과:")
    logger.info(json.dumps(result["recommendation"], indent=2, ensure_ascii=False))


def main():
    """메인 테스트 함수"""
    logger.info("=" * 60)
    logger.info("RAG 시스템 테스트 시작")
    logger.info("=" * 60)

    # RAG 파이프라인 초기화
    pipeline = RAGPipeline()

    # 통계 확인
    stats = pipeline.get_stats()
    logger.info(f"\n벡터 DB 통계:")
    logger.info(f"  - 총 문서 수: {stats['total_documents']}")
    logger.info(f"  - 컬렉션 이름: {stats['collection_name']}")

    if stats['total_documents'] == 0:
        logger.error("\n벡터 데이터베이스가 비어있습니다!")
        logger.error("먼저 init_database.py 스크립트를 실행하세요:")
        logger.error("  python backend/scripts/init_database.py")
        sys.exit(1)

    # 테스트 쿼리 실행
    test_queries = [
        "게임용 고성능 그래픽카드 추천해줘",
        "150만원 예산으로 게이밍 PC 만들고 싶어",
        "인텔 i7 프로세서 추천",
    ]

    for query in test_queries:
        try:
            test_query(pipeline, query)
        except Exception as e:
            logger.error(f"쿼리 테스트 실패: {str(e)}")
            logger.exception(e)

    # 사양 기반 쿼리 테스트
    try:
        test_specs_query(pipeline)
    except Exception as e:
        logger.error(f"사양 기반 쿼리 테스트 실패: {str(e)}")
        logger.exception(e)

    logger.success("\n테스트 완료!")


if __name__ == "__main__":
    main()

