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
    
    def collect_price(
        self,
        component_name: str,
        category: str,
        source: Optional[str] = None,
    ) -> Optional[PriceRecord]:
        """
        현재 가격 수집
        
        Args:
            component_name: 부품 이름
            category: 카테고리
            source: 데이터 소스
            
        Returns:
            PriceRecord 또는 None
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
        
        실제 구현 시 가격 API 또는 크롤링으로 대체
        """
        # 카테고리별 기본 가격 범위 (테스트용)
        default_prices = {
            "gpu": {"min": 500000, "max": 2000000},
            "cpu": {"min": 200000, "max": 800000},
            "memory": {"min": 50000, "max": 300000},
            "storage": {"min": 80000, "max": 400000},
            "motherboard": {"min": 150000, "max": 600000},
            "psu": {"min": 80000, "max": 300000},
            "case": {"min": 50000, "max": 200000},
        }
        
        price_range = default_prices.get(category, {"min": 100000, "max": 500000})
        avg_price = (price_range["min"] + price_range["max"]) // 2
        
        return PriceRecord(
            component_id=f"{category}_{component_name.lower().replace(' ', '_')}",
            component_name=component_name,
            category=category,
            date=datetime.now().strftime("%Y-%m-%d"),
            min_price=price_range["min"],
            avg_price=avg_price,
            max_price=price_range["max"],
            source="manual",
        )
    
    def _collect_from_danawa(
        self,
        component_name: str,
        category: str,
    ) -> Optional[PriceRecord]:
        """
        다나와에서 가격 수집
        
        TODO: 실제 크롤링 구현
        """
        logger.warning("다나와 크롤링은 아직 구현되지 않았습니다.")
        
        # Placeholder 구현
        # 실제 구현 시 다음과 같은 로직:
        #
        # url = f"https://search.danawa.com/dsearch.php?query={component_name}"
        # headers = {"User-Agent": "Mozilla/5.0 ..."}
        # response = requests.get(url, headers=headers)
        # soup = BeautifulSoup(response.text, 'html.parser')
        # price_element = soup.select_one('.price_sect')
        # ...
        
        return self._collect_manual(component_name, category)
    
    def _collect_from_naver(
        self,
        component_name: str,
        category: str,
    ) -> Optional[PriceRecord]:
        """
        네이버 쇼핑에서 가격 수집
        
        TODO: 네이버 쇼핑 API 또는 크롤링 구현
        """
        logger.warning("네이버 쇼핑 크롤링은 아직 구현되지 않았습니다.")
        return self._collect_manual(component_name, category)
    
    def add_price_record(self, record: PriceRecord):
        """
        가격 레코드 추가
        
        Args:
            record: 추가할 가격 레코드
        """
        if record.component_id not in self._cache:
            self._cache[record.component_id] = []
        
        self._cache[record.component_id].append(record)
        logger.debug(f"가격 레코드 추가: {record.component_id}, {record.date}")
    
    def get_price_history(
        self,
        component_id: str,
        days: int = 30,
    ) -> List[PriceRecord]:
        """
        가격 이력 조회
        
        Args:
            component_id: 부품 ID
            days: 조회 기간 (일)
            
        Returns:
            PriceRecord 리스트
        """
        # 캐시에서 조회
        records = self._cache.get(component_id, [])
        
        # 파일에서 추가 로드
        file_path = self.data_dir / f"{component_id}.json"
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                file_data = json.load(f)
                for item in file_data:
                    records.append(PriceRecord(**item))
        
        # 날짜 필터링
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        filtered = [r for r in records if r.date >= cutoff_date]
        
        # 날짜순 정렬
        filtered.sort(key=lambda r: r.date)
        
        return filtered
    
    def save_to_file(self, filename: Optional[str] = None):
        """
        캐시된 데이터를 파일로 저장
        
        Args:
            filename: 저장 파일명 (선택)
        """
        if filename:
            file_path = self.data_dir / filename
            all_records = []
            for records in self._cache.values():
                all_records.extend([r.__dict__ for r in records])
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(all_records, f, indent=2, ensure_ascii=False)
            
            logger.info(f"데이터 저장: {file_path}")
        else:
            # 부품별로 개별 파일 저장
            for component_id, records in self._cache.items():
                file_path = self.data_dir / f"{component_id}.json"
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump([r.__dict__ for r in records], f, indent=2, ensure_ascii=False)
            
            logger.info(f"데이터 저장: {len(self._cache)}개 파일")
    
    def load_from_file(self, filename: str):
        """
        파일에서 데이터 로드
        
        Args:
            filename: 로드할 파일명
        """
        file_path = self.data_dir / filename
        if not file_path.exists():
            logger.warning(f"파일 없음: {file_path}")
            return
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for item in data:
            record = PriceRecord(**item)
            self.add_price_record(record)
        
        logger.info(f"데이터 로드: {file_path}, {len(data)}개 레코드")
    
    def get_latest_price(self, component_id: str) -> Optional[int]:
        """
        최신 가격 조회
        
        Args:
            component_id: 부품 ID
            
        Returns:
            최신 평균 가격 또는 None
        """
        history = self.get_price_history(component_id, days=7)
        if history:
            return history[-1].avg_price
        return None


# ============================================================================
# 스케줄러 (선택적 구현)
# ============================================================================

class PriceCollectionScheduler:
    """
    가격 수집 스케줄러
    
    정기적으로 가격 데이터를 수집하는 스케줄러.
    
    TODO: APScheduler 또는 Celery와 연동하여 구현
    """
    
    def __init__(
        self,
        collector: PriceDataCollector,
        interval_hours: int = 24,
    ):
        """
        Args:
            collector: 가격 수집기 인스턴스
            interval_hours: 수집 간격 (시간)
        """
        self.collector = collector
        self.interval_hours = interval_hours
        self.components_to_track: List[Dict[str, str]] = []
        
        logger.info(f"PriceCollectionScheduler 초기화: interval={interval_hours}h")
    
    def add_component(self, component_name: str, category: str):
        """추적할 부품 추가"""
        self.components_to_track.append({
            "name": component_name,
            "category": category,
        })
    
    def run_collection(self):
        """
        수집 실행
        
        스케줄러에 의해 주기적으로 호출
        """
        logger.info("가격 수집 시작")
        
        for comp in self.components_to_track:
            try:
                record = self.collector.collect_price(
                    component_name=comp["name"],
                    category=comp["category"],
                )
                if record:
                    self.collector.add_price_record(record)
            except Exception as e:
                logger.error(f"수집 실패: {comp['name']}, {e}")
        
        # 저장
        self.collector.save_to_file()
        
        logger.info(f"가격 수집 완료: {len(self.components_to_track)}개 부품")
    
    def start(self):
        """
        스케줄러 시작
        
        TODO: APScheduler 연동
        """
        logger.info("스케줄러 시작 (placeholder)")
        # from apscheduler.schedulers.background import BackgroundScheduler
        # scheduler = BackgroundScheduler()
        # scheduler.add_job(self.run_collection, 'interval', hours=self.interval_hours)
        # scheduler.start()


# ============================================================================
# 테스트용 메인
# ============================================================================

if __name__ == "__main__":
    # 수집기 테스트
    collector = PriceDataCollector()
    
    # 가격 수집 테스트
    components = [
        ("RTX 4070", "gpu"),
        ("Intel Core i5-14600K", "cpu"),
        ("Samsung 990 Pro 1TB", "storage"),
    ]
    
    for name, category in components:
        record = collector.collect_price(name, category)
        if record:
            print(f"{record.component_name}: {record.avg_price:,}원")
            collector.add_price_record(record)
    
    # 저장
    collector.save_to_file("test_prices.json")
    print("\n데이터 저장 완료")
