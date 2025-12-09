"""
벡터 데이터베이스 초기화 스크립트

SQL 덤프 파일을 파싱하고 ChromaDB에 임베딩하여 저장합니다.
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.rag.pipeline import RAGPipeline
from backend.rag.config import SQL_DUMP_PATH
from loguru import logger
import argparse


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description="PC 부품 벡터 데이터베이스 초기화"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="기존 데이터를 삭제하고 재구축",
    )
    parser.add_argument(
        "--sql-file",
        type=str,
        default=str(SQL_DUMP_PATH),
        help="SQL 덤프 파일 경로",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="로그 레벨",
    )

    args = parser.parse_args()

    # 로깅 설정
    logger.remove()
    logger.add(
        sys.stdout,
        level=args.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    )

    try:
        logger.info("=" * 80)
        logger.info("PC 부품 벡터 데이터베이스 초기화 시작")
        logger.info("=" * 80)
        logger.info(f"SQL 파일: {args.sql_file}")
        logger.info(f"강제 재구축: {args.force}")
        logger.info("")

        # RAG 파이프라인 초기화
        pipeline = RAGPipeline()

        # 데이터베이스 초기화
        result = pipeline.initialize_database(
            sql_file_path=Path(args.sql_file),
            force_rebuild=args.force,
        )

        # 결과 출력
        logger.info("")
        logger.info("=" * 80)
        logger.info("초기화 결과")
        logger.info("=" * 80)
        logger.info(f"상태: {result['status']}")
        logger.info(f"메시지: {result['message']}")
        if "total_documents" in result:
            logger.info(f"총 문서 수: {result['total_documents']}")
        if "categories_sample" in result:
            logger.info("\n카테고리별 문서 수 (샘플):")
            for category, count in result["categories_sample"].items():
                logger.info(f"  - {category}: {count}개")

        logger.info("")
        logger.success("초기화 완료!")

    except FileNotFoundError as e:
        logger.error(f"파일을 찾을 수 없습니다: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"초기화 실패: {str(e)}")
        logger.exception(e)
        sys.exit(1)


if __name__ == "__main__":
    main()

