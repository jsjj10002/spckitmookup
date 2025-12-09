"""
SQL 파일 구조 확인 스크립트
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.rag.config import SQL_DUMP_PATH
from loguru import logger


def check_sql_file():
    """SQL 파일 구조 확인"""
    logger.info(f"SQL 파일 경로: {SQL_DUMP_PATH}")
    
    if not SQL_DUMP_PATH.exists():
        logger.error(f"❌ SQL 파일을 찾을 수 없습니다: {SQL_DUMP_PATH}")
        return
    
    logger.info(f"✅ SQL 파일 존재: {SQL_DUMP_PATH}")
    logger.info(f"📊 파일 크기: {SQL_DUMP_PATH.stat().st_size / 1024 / 1024:.2f} MB")
    
    # 파일 내용 미리보기
    logger.info("\n첫 100줄 미리보기:")
    logger.info("=" * 80)
    
    with open(SQL_DUMP_PATH, "r", encoding="utf-8", errors="ignore") as f:
        for i, line in enumerate(f, 1):
            if i <= 100:
                print(f"{i:3d}: {line.rstrip()}")
            else:
                break
    
    logger.info("=" * 80)
    
    # INSERT 문 개수 확인
    logger.info("\n📈 SQL 문 분석:")
    with open(SQL_DUMP_PATH, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
        
        insert_count = content.upper().count("INSERT INTO")
        create_count = content.upper().count("CREATE TABLE")
        
        logger.info(f"  - CREATE TABLE 문: {create_count}개")
        logger.info(f"  - INSERT INTO 문: {insert_count}개")
        
        # 테이블 이름 추출
        import re
        tables = re.findall(r"CREATE TABLE\s+`?(\w+)`?", content, re.IGNORECASE)
        if tables:
            logger.info(f"\n📋 발견된 테이블 ({len(tables)}개):")
            for table in tables:
                logger.info(f"  - {table}")


if __name__ == "__main__":
    check_sql_file()

