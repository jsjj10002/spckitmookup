"""
가격 예측 특성 추출기
=====================

[목표]
------
시계열 예측 모델에 필요한 특성(Feature)을 추출하는 모듈.

[추출 특성 목록]
--------------
1. 시계열 기본 특성
   - 이동평균 (MA)
   - 지수이동평균 (EMA)
   - 변동성 (Volatility)
   - 모멘텀 (Momentum)

2. 계절성 특성
   - 요일 효과
   - 월별 패턴
   - 분기별 패턴

3. 외부 요인 특성
   - 환율 (USD/KRW)
   - 신제품 출시 플래그
   - 대형 세일 이벤트 플래그
   - 반도체 지수

4. 카테고리 특성
   - 부품 카테고리 인코딩
   - 제조사 인코딩
   - 출시 후 경과 시간

[특성 엔지니어링 가이드]
--------------------
- Lag Features: 과거 가격 (1일, 7일, 30일 전)
- Rolling Statistics: 이동평균, 이동표준편차
- Date Features: 요일, 월, 분기
- External Features: 환율, 시장 지수

[참고]
-----
- tsfresh: 자동 시계열 특성 추출
- featuretools: 자동 특성 엔지니어링
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from loguru import logger


# ============================================================================
# 데이터 클래스
# ============================================================================

@dataclass
class PriceFeatures:
    """추출된 가격 특성"""
    # 시계열 특성
    ma_7: Optional[float] = None   # 7일 이동평균
    ma_30: Optional[float] = None  # 30일 이동평균
    ema_7: Optional[float] = None  # 7일 지수이동평균
    volatility: Optional[float] = None  # 변동성
    momentum: Optional[float] = None    # 모멘텀
    
    # 가격 변화
    price_change_1d: Optional[float] = None  # 1일 변화율
    price_change_7d: Optional[float] = None  # 7일 변화율
    price_change_30d: Optional[float] = None # 30일 변화율
    
    # 계절성
    day_of_week: Optional[int] = None
    month: Optional[int] = None
    quarter: Optional[int] = None
    is_holiday_season: Optional[bool] = None
    
    # 외부 요인
    exchange_rate: Optional[float] = None
    new_product_flag: Optional[bool] = None
    sale_event_flag: Optional[bool] = None


# ============================================================================
# 특성 추출기
# ============================================================================

class PriceFeatureExtractor:
    """
    가격 예측용 특성 추출기
    
    시계열 데이터에서 예측에 필요한 다양한 특성을 추출.
    
    사용법:
    ```python
    extractor = PriceFeatureExtractor()
    
    price_history = [
        {"date": "2024-01-01", "price": 750000},
        {"date": "2024-01-02", "price": 745000},
        ...
    ]
    
    features = extractor.extract(price_history)
    print(f"7일 이동평균: {features.ma_7}")
    print(f"변동성: {features.volatility}")
    ```
    """
    
    # 휴일/세일 시즌 (월 기준)
    HOLIDAY_MONTHS = [11, 12, 1]  # 블프, 연말, 새해
    
    def __init__(
        self,
        include_external: bool = True,
    ):
        """
        Args:
            include_external: 외부 요인 특성 포함 여부
        """
        self.include_external = include_external
        logger.info("PriceFeatureExtractor 초기화")
    
    def extract(
        self,
        price_history: List[Dict[str, Any]],
        current_date: Optional[datetime] = None,
    ) -> PriceFeatures:
        """
        특성 추출
        
        Args:
            price_history: 가격 이력 리스트
            current_date: 기준 날짜 (기본: 오늘)
            
        Returns:
            PriceFeatures: 추출된 특성
        """
        if not price_history:
            return PriceFeatures()
        
        current_date = current_date or datetime.now()
        prices = [p["price"] for p in price_history]
        
        features = PriceFeatures()
        
        # 시계열 특성
        features.ma_7 = self._calculate_ma(prices, 7)
        features.ma_30 = self._calculate_ma(prices, 30)
        features.ema_7 = self._calculate_ema(prices, 7)
        features.volatility = self._calculate_volatility(prices)
        features.momentum = self._calculate_momentum(prices)
        
        # 가격 변화율
        features.price_change_1d = self._calculate_change(prices, 1)
        features.price_change_7d = self._calculate_change(prices, 7)
        features.price_change_30d = self._calculate_change(prices, 30)
        
        # 계절성 특성
        features.day_of_week = current_date.weekday()
        features.month = current_date.month
        features.quarter = (current_date.month - 1) // 3 + 1
        features.is_holiday_season = current_date.month in self.HOLIDAY_MONTHS
        
        # 외부 요인 (구현 예정)
        if self.include_external:
            features.exchange_rate = self._get_exchange_rate()
            features.new_product_flag = False  # TODO: 신제품 데이터 연동
            features.sale_event_flag = self._check_sale_event(current_date)
        
        return features
    
    def extract_batch(
        self,
        price_history: List[Dict[str, Any]],
        window_size: int = 7,
    ) -> List[PriceFeatures]:
        """
        시계열 윈도우별 특성 추출 (배치)
        
        모델 학습용 데이터셋 생성에 사용.
        
        Args:
            price_history: 가격 이력
            window_size: 윈도우 크기
            
        Returns:
            특성 리스트
        """
        if len(price_history) < window_size:
            return []
        
        features_list = []
        
        for i in range(window_size, len(price_history)):
            window = price_history[i - window_size:i]
            date_str = price_history[i]["date"]
            date = datetime.strptime(date_str, "%Y-%m-%d")
            
            features = self.extract(window, date)
            features_list.append(features)
        
        return features_list
    
    def _calculate_ma(self, prices: List[int], window: int) -> Optional[float]:
        """이동평균 계산"""
        if len(prices) < window:
            return None
        return float(np.mean(prices[-window:]))
    
    def _calculate_ema(self, prices: List[int], window: int) -> Optional[float]:
        """지수이동평균 계산"""
        if len(prices) < window:
            return None
        
        alpha = 2 / (window + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = alpha * price + (1 - alpha) * ema
        
        return float(ema)
    
    def _calculate_volatility(self, prices: List[int]) -> Optional[float]:
        """변동성 계산 (표준편차 / 평균)"""
        if len(prices) < 2:
            return None
        
        std = np.std(prices)
        mean = np.mean(prices)
        
        if mean == 0:
            return 0.0
        
        return float(std / mean)
    
    def _calculate_momentum(self, prices: List[int], period: int = 7) -> Optional[float]:
        """
        모멘텀 계산
        
        최근 가격 - N일 전 가격
        """
        if len(prices) < period:
            return None
        
        return float(prices[-1] - prices[-period])
    
    def _calculate_change(self, prices: List[int], days: int) -> Optional[float]:
        """가격 변화율 계산 (%)"""
        if len(prices) < days + 1:
            return None
        
        old_price = prices[-(days + 1)]
        new_price = prices[-1]
        
        if old_price == 0:
            return 0.0
        
        return float((new_price - old_price) / old_price * 100)
    
    def _get_exchange_rate(self) -> Optional[float]:
        """
        현재 환율 조회
        
        TODO: 실제 환율 API 연동
        """
        # Placeholder: 고정 환율 반환
        return 1350.0
    
    def _check_sale_event(self, date: datetime) -> bool:
        """
        대형 세일 이벤트 여부 확인
        
        TODO: 세일 캘린더 데이터 연동
        """
        # 블랙프라이데이 (11월 넷째 주 금요일)
        if date.month == 11 and date.day >= 22 and date.day <= 28:
            if date.weekday() == 4:  # 금요일
                return True
        
        # 사이버먼데이 (블프 다음 월요일)
        if date.month in [11, 12] and date.day <= 3:
            if date.weekday() == 0:  # 월요일
                return True
        
        return False
    
    def to_dict(self, features: PriceFeatures) -> Dict[str, Any]:
        """특성을 딕셔너리로 변환"""
        return {
            "ma_7": features.ma_7,
            "ma_30": features.ma_30,
            "ema_7": features.ema_7,
            "volatility": features.volatility,
            "momentum": features.momentum,
            "price_change_1d": features.price_change_1d,
            "price_change_7d": features.price_change_7d,
            "price_change_30d": features.price_change_30d,
            "day_of_week": features.day_of_week,
            "month": features.month,
            "quarter": features.quarter,
            "is_holiday_season": features.is_holiday_season,
            "exchange_rate": features.exchange_rate,
            "new_product_flag": features.new_product_flag,
            "sale_event_flag": features.sale_event_flag,
        }
    
    def to_array(self, features: PriceFeatures) -> np.ndarray:
        """
        특성을 numpy 배열로 변환
        
        ML 모델 입력용
        """
        feature_dict = self.to_dict(features)
        
        # None을 0으로, bool을 int로 변환
        values = []
        for v in feature_dict.values():
            if v is None:
                values.append(0.0)
            elif isinstance(v, bool):
                values.append(1.0 if v else 0.0)
            else:
                values.append(float(v))
        
        return np.array(values)


# ============================================================================
# 테스트용 메인
# ============================================================================

if __name__ == "__main__":
    from datetime import timedelta
    
    # 테스트 데이터 생성
    base_price = 750000
    history = []
    base_date = datetime.now() - timedelta(days=30)
    
    for i in range(30):
        date = base_date + timedelta(days=i)
        # 약간의 변동과 하락 추세
        price = base_price - (i * 500) + np.random.randint(-5000, 5000)
        history.append({
            "date": date.strftime("%Y-%m-%d"),
            "price": max(650000, int(price))
        })
    
    # 특성 추출
    extractor = PriceFeatureExtractor()
    features = extractor.extract(history)
    
    print("추출된 특성:")
    for key, value in extractor.to_dict(features).items():
        print(f"  {key}: {value}")
    
    print(f"\n특성 배열 형태: {extractor.to_array(features).shape}")
