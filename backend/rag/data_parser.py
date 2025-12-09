"""
SQL 데이터 파싱 및 처리 모듈
"""
import re
import sqlparse
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger

from .config import SQL_DUMP_PATH


class PCDataParser:
    """SQL 덤프 파일에서 PC 부품 정보를 추출하는 클래스"""

    def __init__(self, sql_file_path: Path = SQL_DUMP_PATH):
        """
        Args:
            sql_file_path: SQL 덤프 파일 경로
        """
        self.sql_file_path = sql_file_path
        logger.info(f"PCDataParser 초기화: {sql_file_path}")

    def parse_sql_dump(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        SQL 덤프 파일을 파싱하여 부품 정보 추출

        Returns:
            테이블별 부품 정보 딕셔너리
        """
        logger.info(f"SQL 파일 파싱 시작: {self.sql_file_path}")

        if not self.sql_file_path.exists():
            raise FileNotFoundError(f"SQL 파일을 찾을 수 없습니다: {self.sql_file_path}")

        with open(self.sql_file_path, "r", encoding="utf-8", errors="ignore") as f:
            sql_content = f.read()

        # MySQL 특수 주석 제거
        sql_content = re.sub(r'/\*!.*?\*/', '', sql_content, flags=re.DOTALL)
        
        # LOCK TABLES, UNLOCK TABLES 제거
        sql_content = re.sub(r'LOCK TABLES.*?;', '', sql_content, flags=re.IGNORECASE)
        sql_content = re.sub(r'UNLOCK TABLES;', '', sql_content, flags=re.IGNORECASE)

        # SQL 문 파싱
        statements = sqlparse.split(sql_content)
        tables_data = {}
        
        insert_count = 0
        failed_count = 0

        for i, statement in enumerate(statements):
            if not statement.strip():
                continue

            # INSERT 문 파싱
            statement_upper = statement.strip().upper()
            if statement_upper.startswith("INSERT INTO") or "INSERT INTO" in statement_upper[:100]:
                insert_count += 1
                table_name, records = self._parse_insert_statement(statement)
                if table_name and records:
                    if table_name not in tables_data:
                        tables_data[table_name] = []
                    tables_data[table_name].extend(records)
                    logger.debug(f"테이블 '{table_name}': {len(records)}개 레코드 파싱 성공")
                elif table_name:
                    failed_count += 1
                    logger.debug(f"테이블 '{table_name}': 레코드 파싱 실패 (statement {i})")
                else:
                    failed_count += 1
                    logger.debug(f"INSERT 문 파싱 실패 (statement {i}): {statement[:200]}...")

        logger.info(f"파싱 완료: {len(tables_data)}개 테이블, 총 {sum(len(v) for v in tables_data.values())}개 레코드")
        logger.info(f"INSERT 문 발견: {insert_count}개, 성공: {insert_count - failed_count}개, 실패: {failed_count}개")
        return tables_data

    def _parse_insert_statement(
        self, statement: str
    ) -> tuple[str, List[Dict[str, Any]]]:
        """
        INSERT 문에서 테이블명과 데이터 추출

        Args:
            statement: SQL INSERT 문

        Returns:
            (테이블명, 레코드 리스트)
        """
        try:
            # MySQL 특수 주석 제거
            statement = re.sub(r'/\*!.*?\*/', '', statement, flags=re.DOTALL)
            
            # 테이블명 추출 (두 가지 형식 지원)
            # 형식 1: INSERT INTO table (col1, col2) VALUES
            table_match_with_cols = re.search(
                r"INSERT INTO\s+`?(\w+)`?\s*\(([^)]+)\)\s*VALUES", 
                statement, 
                re.IGNORECASE
            )
            
            # 형식 2: INSERT INTO table VALUES (MySQL 덤프 스타일)
            table_match_no_cols = re.search(
                r"INSERT INTO\s+`?(\w+)`?\s+VALUES",
                statement,
                re.IGNORECASE
            )
            
            table_name = None
            columns = None
            
            if table_match_with_cols:
                # 컬럼명이 있는 경우
                table_name = table_match_with_cols.group(1)
                columns = [col.strip().strip("`") for col in table_match_with_cols.group(2).split(",")]
            elif table_match_no_cols:
                # 컬럼명이 없는 경우 (MySQL 덤프 스타일)
                table_name = table_match_no_cols.group(1)
                # 컬럼명 없이 인덱스 기반 저장
                columns = None
            else:
                return None, []

            # VALUES 절 추출
            values_match = re.search(r"VALUES\s*(.+);?\s*$", statement, re.IGNORECASE | re.DOTALL)
            if not values_match:
                return table_name, []

            values_str = values_match.group(1)

            # 각 레코드 파싱 - 중첩 괄호 처리 개선
            records = []
            
            # 괄호 기반 값 그룹 추출 (중첩 괄호 고려)
            pattern = r'\(([^()]*(?:\([^()]*\)[^()]*)*)\)'
            value_groups = re.findall(pattern, values_str)
            
            for idx, value_group in enumerate(value_groups):
                try:
                    # 값들을 파싱 (쉼표로 구분, 문자열 내부 쉼표는 무시)
                    values = self._split_values(value_group)
                    
                    if columns:
                        # 컬럼명이 있는 경우
                        if len(values) == len(columns):
                            record = {}
                            for col, val in zip(columns, values):
                                # 값 정제
                                val = val.strip().strip("'\"")
                                if val.upper() == "NULL" or val == "":
                                    val = None
                                record[col] = val
                            records.append(record)
                        else:
                            logger.debug(f"컬럼 수 불일치: {len(columns)} vs {len(values)} - {table_name}")
                    else:
                        # 컬럼명이 없는 경우 - 인덱스 기반 저장
                        record = {}
                        for i, val in enumerate(values):
                            val = val.strip().strip("'\"")
                            if val.upper() == "NULL" or val == "":
                                val = None
                            # field_0, field_1, ... 형식으로 저장
                            record[f"field_{i}"] = val
                        
                        # 첫 몇 개 필드를 주요 속성으로 간주
                        if len(values) > 1:
                            record["name"] = record.get("field_1", "Unknown")  # 보통 두 번째 필드가 이름
                        records.append(record)
                        
                except Exception as e:
                    logger.debug(f"레코드 파싱 오류: {str(e)}")
                    continue

            return table_name, records

        except Exception as e:
            logger.warning(f"INSERT 문 파싱 중 오류: {str(e)}")
            return None, []

    def _split_values(self, value_string: str) -> List[str]:
        """
        쉼표로 구분된 값들을 분리 (문자열 내부 쉼표는 무시)

        Args:
            value_string: 값 문자열

        Returns:
            값 리스트
        """
        values = []
        current_value = ""
        in_quotes = False
        quote_char = None

        for char in value_string:
            if char in ("'", '"') and (not in_quotes or char == quote_char):
                in_quotes = not in_quotes
                quote_char = char if in_quotes else None
                current_value += char
            elif char == "," and not in_quotes:
                values.append(current_value.strip())
                current_value = ""
            else:
                current_value += char

        if current_value:
            values.append(current_value.strip())

        return values

    def create_component_documents(
        self, tables_data: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        부품 데이터를 문서 형태로 변환 (RAG용)

        Args:
            tables_data: 테이블별 부품 정보

        Returns:
            문서 리스트 (각 문서는 부품 하나를 나타냄)
        """
        documents = []

        for table_name, records in tables_data.items():
            logger.info(f"{table_name} 테이블 처리 중: {len(records)}개 레코드")

            for record in records:
                doc = self._create_document_from_record(table_name, record)
                if doc:
                    documents.append(doc)

        logger.info(f"총 {len(documents)}개의 문서 생성 완료")
        return documents

    def _create_document_from_record(
        self, table_name: str, record: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        레코드를 문서로 변환

        Args:
            table_name: 테이블명 (부품 카테고리)
            record: 레코드 데이터

        Returns:
            문서 딕셔너리
        """
        try:
            # 부품 이름 추출 (다양한 필드명 시도)
            name = (
                record.get("name")
                or record.get("product_name")
                or record.get("model")
                or "Unknown"
            )

            # 텍스트 설명 생성 (검색용)
            text_parts = [f"카테고리: {table_name}", f"제품명: {name}"]

            # 주요 스펙 추가
            for key, value in record.items():
                if value and key not in ["id", "created_at", "updated_at"]:
                    text_parts.append(f"{key}: {value}")

            text = "\n".join(text_parts)

            # 메타데이터
            metadata = {
                "category": table_name,
                "name": name,
                "source": "sql_database",
                **record,
            }

            return {"text": text, "metadata": metadata}

        except Exception as e:
            logger.warning(f"문서 생성 실패: {table_name}, {str(e)}")
            return None

