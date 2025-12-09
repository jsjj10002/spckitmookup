"""
SQL 파싱 디버그 스크립트
"""
import sys
from pathlib import Path
import re

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.rag.config import SQL_DUMP_PATH
from loguru import logger
import sqlparse


def debug_sql_parsing():
    """SQL 파싱 상세 디버그"""
    logger.info(f"SQL 파일: {SQL_DUMP_PATH}")
    
    if not SQL_DUMP_PATH.exists():
        logger.error("SQL 파일 없음!")
        return
    
    # 파일 읽기
    with open(SQL_DUMP_PATH, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    logger.info(f"파일 크기: {len(content)} 바이트")
    
    # MySQL 주석 제거 전
    insert_before = content.upper().count("INSERT INTO")
    logger.info(f"INSERT INTO 발견 (원본): {insert_before}개")
    
    # MySQL 특수 주석 제거
    content = re.sub(r'/\*!.*?\*/', '', content, flags=re.DOTALL)
    content = re.sub(r'LOCK TABLES.*?;', '', content, flags=re.IGNORECASE)
    content = re.sub(r'UNLOCK TABLES;', '', content, flags=re.IGNORECASE)
    
    insert_after = content.upper().count("INSERT INTO")
    logger.info(f"INSERT INTO 발견 (정제 후): {insert_after}개")
    
    # sqlparse로 분할
    statements = sqlparse.split(content)
    logger.info(f"총 statement 수: {len(statements)}")
    
    # INSERT 문 찾기
    insert_statements = []
    for i, stmt in enumerate(statements):
        if stmt.strip().upper().startswith("INSERT INTO"):
            insert_statements.append((i, stmt))
    
    logger.info(f"INSERT 문 발견: {len(insert_statements)}개")
    
    # 첫 번째 INSERT 문 상세 분석
    if insert_statements:
        idx, first_insert = insert_statements[0]
        logger.info(f"\n첫 번째 INSERT 문 (statement {idx}):")
        logger.info("=" * 80)
        logger.info(first_insert[:500] + "...")
        logger.info("=" * 80)
        
        # 테이블명 추출
        table_match = re.search(
            r"INSERT INTO\s+`?(\w+)`?\s*\(([^)]+)\)", 
            first_insert, 
            re.IGNORECASE
        )
        
        if table_match:
            table_name = table_match.group(1)
            columns_str = table_match.group(2)
            columns = [c.strip().strip("`") for c in columns_str.split(",")]
            
            logger.info(f"\n테이블명: {table_name}")
            logger.info(f"컬럼 수: {len(columns)}")
            logger.info(f"컬럼: {columns[:5]}...")
            
            # VALUES 절 추출
            values_match = re.search(
                r"VALUES\s*(.+);?\s*$", 
                first_insert, 
                re.IGNORECASE | re.DOTALL
            )
            
            if values_match:
                values_str = values_match.group(1)
                logger.info(f"\nVALUES 절 길이: {len(values_str)} 문자")
                logger.info(f"VALUES 미리보기:\n{values_str[:200]}...")
                
                # 레코드 개수 추정
                record_count = values_str.count("),(")  + 1
                logger.info(f"\n예상 레코드 수: 약 {record_count}개")
            else:
                logger.error("VALUES 절을 찾을 수 없음!")
        else:
            logger.error("테이블명/컬럼을 파싱할 수 없음!")
            logger.info(f"INSERT 문 시작: {first_insert[:200]}")
    else:
        logger.error("INSERT 문을 하나도 찾을 수 없습니다!")
        
        # 원본 파일에서 직접 검색
        logger.info("\n원본 파일에서 직접 검색:")
        with open(SQL_DUMP_PATH, "r", encoding="utf-8", errors="ignore") as f:
            line_num = 0
            for line in f:
                line_num += 1
                if "INSERT INTO" in line.upper():
                    logger.info(f"라인 {line_num}: {line[:100]}")
                    if line_num > 10:
                        break


if __name__ == "__main__":
    debug_sql_parsing()

