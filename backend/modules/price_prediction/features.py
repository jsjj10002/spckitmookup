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

3. 외부 요인 특성 (현재 비활성화)
   - 환율 (USD/KRW)
   - 신제품 출시 플래그
   - 대형 세일 이벤트 플래그
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
    
    # 계절성
    day_of_week: Optional[int] = None
    month: Optional[int] = None
    quarter: Optional[int] = None
    is_holiday_season: Optional[bool] = None


# ============================================================================
# 특성 추출기
# ============================================================================

class PriceFeatureExtractor:
    """
    가격 예측용 특성 추출기
    
    사용법:
    ```python
    extractor = PriceFeatureExtractor()
    price_history = [{"date": "2024-01-01", "price": 750000}, ...]
    features = extractor.extract(price_history)
    print(f"7일 이동평균: {features.ma_7}")
    ```
    """
    
    HOLIDAY_MONTHS = [11, 12, 1]
    
    def __init__(self):
        logger.info("PriceFeatureExtractor 초기화")
    
    def extract(
        self,
        price_history: List[Dict[str, Any]],
        current_date: Optional[datetime] = None,
    ) -> PriceFeatures:
        """
        특성 추출
        """
        if not price_history:
            return PriceFeatures()
        
        # current_date가 없으면 price_history의 마지막 날짜를 사용
        if current_date is None:
            last_date_str = price_history[-1]["date"]
            current_date = datetime.strptime(last_date_str, "%Y-%m-%d")

        prices = [p["price"] for p in price_history]
        
        features = PriceFeatures()
        
        # 시계열 특성
        features.ma_7 = self._calculate_ma(prices, 7)
        features.ma_30 = self._calculate_ma(prices, 30)
        features.ema_7 = self._calculate_ema(prices, 7)
        features.volatility = self._calculate_volatility(prices)
        features.momentum = self._calculate_momentum(prices)
        
        # 계절성 특성
        features.day_of_week = current_date.weekday()
        features.month = current_date.month
        features.quarter = (current_date.month - 1) // 3 + 1
        features.is_holiday_season = current_date.month in self.HOLIDAY_MONTHS
        
        return features
    
    def _calculate_ma(self, prices: List[int], window: int) -> Optional[float]:
        if len(prices) < window:
            return None
        return float(np.mean(prices[-window:]))
    
    def _calculate_ema(self, prices: List[int], window: int) -> Optional[float]:
        if len(prices) < window:
            return None
        
        alpha = 2 / (window + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = alpha * price + (1 - alpha) * ema
        
        return float(ema)
    
    def _calculate_volatility(self, prices: List[int]) -> Optional[float]:
        if len(prices) < 2:
            return None
        
        std = np.std(prices)
        mean = np.mean(prices)
        
        if mean == 0:
            return 0.0
        
        return float(std / mean)
    
    def _calculate_momentum(self, prices: List[int], period: int = 7) -> Optional[float]:
        if len(prices) < period:
            return None
        
        return float(prices[-1] - prices[-period])
    
    def to_dict(self, features: PriceFeatures) -> Dict[str, Any]:
        """특성을 딕셔너리로 변환"""
        return {
            "ma_7": features.ma_7,
            "ma_30": features.ma_30,
            "ema_7": features.ema_7,
            "volatility": features.volatility,
            "momentum": features.momentum,
            "day_of_week": features.day_of_week,
            "month": features.month,
            "quarter": features.quarter,
            "is_holiday_season": features.is_holiday_season,
        }
    
    def to_array(self, features: PriceFeatures) -> np.ndarray:
        """특성을 numpy 배열로 변환"""
        feature_dict = self.to_dict(features)
        
        values = []
        for v in feature_dict.values():
            if v is None:
                values.append(0.0)
            elif isinstance(v, bool):
                values.append(1.0 if v else 0.0)
            else:
                values.append(float(v))
        
        return np.array(values)

