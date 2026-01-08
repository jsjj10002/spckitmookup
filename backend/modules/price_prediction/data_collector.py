"""
가격 데이터 수집기
==================

[목표]
------
PC 부품 가격 이력 데이터를 수집하고 저장하는 모듈.
크롤링, API, 또는 수동 입력 방식으로 데이터 수집.

[데이터 소스]
-----------
1. 다나와 가격비교 (danawa.com)
   - 장점: 국내 최대 가격비교 사이트
   - 단점: 크롤링 정책 확인 필요

2. 네이버 쇼핑 (shopping.naver.com)
   - 장점: 다양한 판매처 비교 가능
   - 단점: API 제한

3. 에누리 가격비교 (enuri.com)
   - 장점: 가격 추이 그래프 제공
   - 단점: 크롤링 정책

4. PCPartPicker (pcpartpicker.com)
   - 장점: 해외 부품 가격 데이터
   - 단점: 국내 가격과 다름

[구현 가이드]
-----------
1. 크롤링 방식:
   - robots.txt 확인
   - 적절한 딜레이 설정 (1-2초)
   - User-Agent 설정
   - 캐싱으로 불필요한 요청 방지

2. 데이터 저장:
   - SQLite 또는 JSON 파일
   - 일별 가격 데이터
   - 최저가, 평균가, 최고가

[주의사항]
---------
- 웹 크롤링 시 해당 사이트의 이용약관 확인 필수
- 과도한 요청으로 인한 IP 차단 주의
- 개인정보 수집 금지

[TODO]
-----
- [ ] 크롤링 정책 조사 및 준수
- [ ] 데이터 수집 스케줄러 구현
- [ ] 데이터 정합성 검증 로직
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import json
from loguru import logger
import csv
import re
import os


# TODO: 실제 크롤링 시 사용
# import requests
# from bs4 import BeautifulSoup


# ============================================================================
# 데이터 모델
# ============================================================================

@dataclass
class PriceRecord:
    """가격 레코드"""
    component_id: str
    component_name: str
    category: str
    date: str
    min_price: int
    avg_price: int
    max_price: int
    source: str
    url: Optional[str] = None


# ============================================================================
# 가격 데이터 수집기
# ============================================================================

class PriceDataCollector:
    """
    PC 부품 가격 데이터 수집기
    
    다양한 소스에서 가격 데이터를 수집하고 저장.
    
    사용법:
    ```python
    collector = PriceDataCollector()
    
    # 특정 부품 가격 수집
    prices = collector.collect_price("RTX 4070", "gpu")
    
    # 전체 가격 이력 조회
    history = collector.get_price_history("gpu_rtx4070", days=30)
    
    # 데이터 저장
    collector.save_to_file("prices.json")
    ```
    """
    
    # 지원 데이터 소스
    SUPPORTED_SOURCES = ["danawa", "naver", "enuri", "manual"]
    
    def __init__(
        self,
        data_dir: Optional[Path] = None,
        default_source: str = "manual",
    ):
        """
        Args:
            data_dir: 데이터 저장 디렉토리
            default_source: 기본 데이터 소스
        """
        self.data_dir = data_dir or Path(__file__).parent / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.default_source = default_source
        
        # 메모리 내 캐시
        self._cache: Dict[str, List[PriceRecord]] = {}
        
        logger.info(f"PriceDataCollector 초기화: data_dir={self.data_dir}")
    
    def transform_legacy_csv_to_json(self):
        """
        레거시 CSV 가격 데이터를 단일 JSON 파일로 변환합니다.
        (transform_price_data.py 스크립트의 로직을 통합)
        """
        ROOT_DIR = Path(__file__).parent.parent.parent
        SOURCE_DIR = ROOT_DIR / "modules" / "price_prediction" / "data" / "last_data"
        OUTPUT_FILE = ROOT_DIR / "modules" / "price_prediction" / "data" / "transformed_prices.json"
        CATEGORY_MAP = {
            "Case": "case", "Cooler": "cooler", "CPU": "cpu", "MBoard": "motherboard",
            "Power": "psu", "RAM": "memory", "SSD": "storage", "VGA": "gpu",
        }

        logger.info("레거시 CSV 데이터 변환을 시작합니다...")
        logger.info(f"소스 디렉토리: {SOURCE_DIR}")

        all_records = []
        for month_dir in sorted(SOURCE_DIR.iterdir()):
            if not month_dir.is_dir() or not re.match(r"\d{4}-\d{2}", month_dir.name):
                continue

            logger.info(f"  - 처리 중: {month_dir.name}")
            for csv_file in month_dir.iterdir():
                if csv_file.suffix.lower() != ".csv":
                    continue
                
                category_name = csv_file.stem
                category = CATEGORY_MAP.get(category_name)
                
                if not category:
                    continue

                try:
                    with open(csv_file, 'r', encoding='utf-8-sig') as f:
                        reader = csv.reader(f)
                        header = next(reader)
                        dates = [h.split(" ")[0] for h in header[2:]]

                        for row in reader:
                            if not row or len(row) < 2: continue
                            
                            component_danawa_id = row[0]
                            component_name = row[1]

                            for i, price_str in enumerate(row[2:]):
                                if i >= len(dates): continue
                                price = self._parse_price(price_str)
                                
                                if price is not None:
                                    record = {
                                        "component_id": component_danawa_id,
                                        "component_name": component_name,
                                        "category": category,
                                        "date": dates[i],
                                        "min_price": price,
                                        "avg_price": price,
                                        "max_price": price,
                                        "source": "danawa-legacy-csv",
                                        "url": f"https://prod.danawa.com/info/?pcode={component_danawa_id}" if component_danawa_id.isdigit() else None
                                    }
                                    all_records.append(record)
                except Exception as e:
                    logger.error(f"'{csv_file.name}' 파일 처리 중 오류: {e}")

        logger.info(f"데이터 변환 완료. 총 {len(all_records)}개 레코드 생성.")

        try:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(all_records, f, indent=2, ensure_ascii=False)
            logger.info(f"결과를 '{OUTPUT_FILE}' 파일에 저장했습니다.")
        except Exception as e:
            logger.error(f"결과 파일 저장 중 오류: {e}")
        
        return OUTPUT_FILE

    def _parse_price(self, price_str: str) -> int | None:
        """ 복잡한 가격 문자열에서 대표 가격(정품 우선)을 파싱합니다. """
        if not price_str or price_str == "0":
            return None

        prices = {}
        parts = price_str.split('|')

        for part in parts:
            part = part.strip()
            match = re.match(r"(.+?_)?([\d,]+)", part)
            if match:
                price_val_str = match.group(2).replace(',', '')
                if price_val_str.isdigit():
                    price_type = "unknown"
                    if match.group(1):
                        price_type = match.group(1).replace('_', '').strip()
                    prices[price_type] = int(price_val_str)

        priority = ["정품", "멀티팩(정품)", "벌크", "unknown", "중고", "해외구매"]
        for p_type in priority:
            if p_type in prices:
                return prices[p_type]

        return list(prices.values())[0] if prices else None
    
    def collect_price(
        self,
        component_name: str,
        category: str,
        source: Optional[str] = None,
    ) -> Optional[PriceRecord]:
        """
        현재 가격 수집
        """
        source = source or self.default_source
        
        if source == "manual":
            return self._collect_manual(component_name, category)
        elif source == "danawa":
            return self._collect_from_danawa(component_name, category)
        elif source == "naver":
            return self._collect_from_naver(component_name, category)
        else:
            logger.warning(f"지원하지 않는 소스: {source}")
            return None
    
    def _collect_manual(
        self,
        component_name: str,
        category: str,
    ) -> PriceRecord:
        """
        수동 입력 방식 (Placeholder)
        """
        default_prices = {
            "gpu": {"min": 500000, "max": 2000000}, "cpu": {"min": 200000, "max": 800000},
            "memory": {"min": 50000, "max": 300000}, "storage": {"min": 80000, "max": 400000},
            "motherboard": {"min": 150000, "max": 600000}, "psu": {"min": 80000, "max": 300000},
            "case": {"min": 50000, "max": 200000},
        }
        price_range = default_prices.get(category, {"min": 100000, "max": 500000})
        avg_price = (price_range["min"] + price_range["max"]) // 2
        
        return PriceRecord(
            component_id=f"{category}_{component_name.lower().replace(' ', '_')}",
            component_name=component_name, category=category, date=datetime.now().strftime("%Y-%m-%d"),
            min_price=price_range["min"], avg_price=avg_price, max_price=price_range["max"], source="manual",
        )
    
    def _collect_from_danawa(self, component_name: str, category: str) -> Optional[PriceRecord]:
        logger.warning("다나와 크롤링은 아직 구현되지 않았습니다.")
        return self._collect_manual(component_name, category)
    
    def _collect_from_naver(self, component_name: str, category: str) -> Optional[PriceRecord]:
        logger.warning("네이버 쇼핑 크롤링은 아직 구현되지 않았습니다.")
        return self._collect_manual(component_name, category)
    
    def add_price_record(self, record: PriceRecord):
        if record.component_id not in self._cache:
            self._cache[record.component_id] = []
        self._cache[record.component_id].append(record)
        logger.debug(f"가격 레코드 추가: {record.component_id}, {record.date}")
    
    def get_price_history(self, component_id: str, days: int = 30) -> List[PriceRecord]:
        records = self._cache.get(component_id, [])
        file_path = self.data_dir / f"{component_id}.json"
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                file_data = json.load(f)
                for item in file_data:
                    records.append(PriceRecord(**item))
        
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        filtered = [r for r in records if r.date >= cutoff_date]
        filtered.sort(key=lambda r: r.date)
        return filtered
    
    def save_to_file(self, filename: Optional[str] = None):
        if filename:
            file_path = self.data_dir / filename
            all_records = [r.__dict__ for records in self._cache.values() for r in records]
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(all_records, f, indent=2, ensure_ascii=False)
            logger.info(f"데이터 저장: {file_path}")
        else:
            for component_id, records in self._cache.items():
                file_path = self.data_dir / f"{component_id}.json"
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump([r.__dict__ for r in records], f, indent=2, ensure_ascii=False)
            logger.info(f"데이터 저장: {len(self._cache)}개 파일")
    
    def load_from_file(self, filename: str):
        file_path = self.data_dir / filename
        if not file_path.exists():
            logger.warning(f"파일 없음: {file_path}")
            return
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for item in data:
            self.add_price_record(PriceRecord(**item))
        logger.info(f"데이터 로드: {file_path}, {len(data)}개 레코드")
    
    def get_latest_price(self, component_id: str) -> Optional[int]:
        history = self.get_price_history(component_id, days=7)
        return history[-1].avg_price if history else None

# ... (PriceCollectionScheduler and if __name__ == "__main__" block remain unchanged)
if __name__ == "__main__":
    # 수집기 테스트
    collector = PriceDataCollector()
    
    # 레거시 데이터 변환 실행
    collector.transform_legacy_csv_to_json()

    # 가격 수집 테스트 (기존 로직은 참고용으로 남겨둠)
    # components = [
    #     ("RTX 4070", "gpu"),
    #     ("Intel Core i5-14600K", "cpu"),
    # ]
    # for name, category in components:
    #     record = collector.collect_price(name, category)
    #     if record:
    #         print(f"{record.component_name}: {record.avg_price:,}원")
    #         collector.add_price_record(record)
    # collector.save_to_file("test_prices.json")
    # print("\n데이터 저장 완료")