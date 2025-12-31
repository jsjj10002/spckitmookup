"""
시계열 트랜스포머 기반 가격 예측 모델
=====================================

[목표]
------
PC 부품의 미래 가격을 예측하여 사용자에게 최적의 구매 시점 추천.

[배경 지식]
----------
PC 부품 가격은 다양한 요인에 의해 변동됨:
1. 신제품 출시 사이클 (신제품 출시 → 구제품 가격 하락)
2. 환율 변동 (달러-원 환율)
3. 수요 변동 (게임 출시, 마이닝 붐 등)
4. 공급망 이슈 (반도체 부족 등)
5. 계절성 (연말 쇼핑 시즌, 학기 시작 등)

시계열 예측 모델:
- ARIMA/SARIMA: 전통적 통계 모델
- Prophet: Facebook의 시계열 모델 (계절성 처리에 강함)
- LSTM/GRU: 순환 신경망 기반
- Temporal Fusion Transformer (TFT): 최신 시계열 트랜스포머
- Informer: 장기 예측에 최적화된 트랜스포머

[아키텍처]
---------
```
                    ┌─────────────────────────────────────────┐
                    │         PricePredictionModel             │
                    │                                          │
┌──────────────┐    │  ┌──────────────────────────────────┐  │
│ Price Data   │───▶│  │     PriceFeatureExtractor        │  │
│ (Historical) │    │  │  - 시계열 특성 추출              │  │
└──────────────┘    │  │  - 외부 요인 인코딩              │  │
                    │  └─────────────┬────────────────────┘  │
┌──────────────┐    │                │                        │
│ External     │───▶│                ▼                        │
│ Features     │    │  ┌──────────────────────────────────┐  │
│ (환율, 뉴스) │    │  │    Temporal Fusion Transformer    │  │
└──────────────┘    │  │    또는 다른 시계열 모델           │  │
                    │  └─────────────┬────────────────────┘  │
                    │                │                        │
                    │                ▼                        │
                    │  ┌──────────────────────────────────┐  │
                    │  │     Prediction Output            │  │
                    │  │  - 예측 가격 (포인트)             │  │
                    │  │  - 신뢰 구간                      │  │
                    │  │  - 추세 분석                      │  │
                    │  └──────────────────────────────────┘  │
                    └─────────────────────────────────────────┘
                                     │
                                     ▼
                    ┌─────────────────────────────────────────┐
                    │     BuyingRecommendation                 │
                    │  - 구매 적기 추천                        │
                    │  - 대기 권장 기간                        │
                    │  - 가격 하락 확률                        │
                    └─────────────────────────────────────────┘
```

[데이터 요구사항]
---------------
학습 데이터:
- 일별 가격 데이터 (최소 6개월, 권장 2년 이상)
- 부품별 가격 이력
- 환율 데이터 (USD/KRW)
- 제품 출시일/단종일 정보

외부 특성:
- 환율 변동
- 신제품 출시 일정
- 대규모 세일 이벤트 (블랙프라이데이 등)

[입력/출력 인터페이스]
-------------------
입력 (PricePredictionRequest):
```python
{
    "component_id": "gpu_rtx4070",
    "component_name": "RTX 4070",
    "category": "gpu",
    "current_price": 720000,
    "price_history": [
        {"date": "2024-01-01", "price": 750000},
        {"date": "2024-01-02", "price": 745000},
        ...
    ],
    "prediction_days": 30,  # 예측 기간 (일)
    "include_factors": ["exchange_rate", "seasonality"]
}
```

출력 (PricePredictionResult):
```python
{
    "component_id": "gpu_rtx4070",
    "predictions": [
        {"date": "2024-02-01", "price": 710000, "lower": 690000, "upper": 730000},
        {"date": "2024-02-02", "price": 705000, "lower": 680000, "upper": 730000},
        ...
    ],
    "trend": {
        "direction": "down",  # up, down, stable
        "strength": 0.65,  # 추세 강도 (0-1)
        "expected_change_pct": -3.2  # 예측 기간 내 예상 변화율
    },
    "buy_recommendation": {
        "action": "wait",  # buy_now, wait, watch
        "confidence": 0.72,
        "best_buy_date": "2024-02-15",
        "expected_price_at_best": 680000,
        "reasoning": "향후 2주 내 약 5% 가격 하락 예상"
    },
    "factors_impact": {
        "seasonality": -2.1,  # % 영향
        "exchange_rate": +0.5,
        "new_product": -3.0
    }
}
```

[구현 단계]
----------
1단계: 가격 데이터 수집기 구현 (크롤링/API)
2단계: 특성 추출기 구현 (시계열 특성, 외부 요인)
3단계: 기본 예측 모델 구현 (Prophet 또는 ARIMA)
4단계: 트랜스포머 모델 구현 (TFT)
5단계: 앙상블 및 모델 선택 로직
6단계: 구매 추천 로직 구현

[참고 기술/라이브러리]
------------------
- PyTorch Forecasting: TFT 구현
  https://pytorch-forecasting.readthedocs.io/
- Darts: 시계열 예측 라이브러리
  https://unit8co.github.io/darts/
- Prophet: Facebook의 시계열 예측
  https://facebook.github.io/prophet/
- Informer: 장기 시계열 예측
  https://github.com/zhouhaoyi/Informer2020

[모델 성능 목표]
--------------
- MAPE (Mean Absolute Percentage Error): 5% 이하
- 방향성 정확도: 70% 이상
- 최적 구매 시점 예측 정확도: 65% 이상

[주의사항]
---------
- 가격 데이터 수집 시 법적 이슈 확인 (크롤링 정책)
- 모델 학습에 최소 수백 일의 데이터 필요
- 급격한 시장 변동 시 예측 신뢰도 하락 가능
- 사용자에게 "예측"임을 명확히 고지 필요

[데이터 소스 후보]
----------------
- 다나와 가격비교
- 네이버 쇼핑
- 에누리 가격비교
- PCPartPicker (해외)

[테스트]
-------
backend/tests/test_price_prediction.py 참조
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from loguru import logger
from pydantic import BaseModel, Field


# ============================================================================
# 열거형 및 상수 정의
# ============================================================================

class TrendDirection(str, Enum):
    """가격 추세 방향"""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"


class BuyAction(str, Enum):
    """구매 권장 행동"""
    BUY_NOW = "buy_now"      # 지금 구매 권장
    WAIT = "wait"           # 대기 권장
    WATCH = "watch"         # 관망 (불확실)


# ============================================================================
# 데이터 모델
# ============================================================================

class PricePoint(BaseModel):
    """가격 데이터 포인트"""
    date: str = Field(..., description="날짜 (YYYY-MM-DD)")
    price: int = Field(..., description="가격 (원)")


class PredictionPoint(BaseModel):
    """예측 데이터 포인트"""
    date: str
    price: int = Field(..., description="예측 가격")
    lower: int = Field(..., description="하한 (95% 신뢰구간)")
    upper: int = Field(..., description="상한 (95% 신뢰구간)")


class TrendAnalysis(BaseModel):
    """추세 분석 결과"""
    direction: TrendDirection
    strength: float = Field(..., ge=0, le=1, description="추세 강도")
    expected_change_pct: float = Field(..., description="예상 변화율 (%)")


class BuyRecommendation(BaseModel):
    """구매 추천"""
    action: BuyAction
    confidence: float = Field(..., ge=0, le=1)
    best_buy_date: Optional[str] = None
    expected_price_at_best: Optional[int] = None
    reasoning: str


class FactorsImpact(BaseModel):
    """요인별 가격 영향"""
    seasonality: Optional[float] = Field(None, description="계절성 영향 (%)")
    exchange_rate: Optional[float] = Field(None, description="환율 영향 (%)")
    new_product: Optional[float] = Field(None, description="신제품 영향 (%)")
    supply_chain: Optional[float] = Field(None, description="공급망 영향 (%)")


class PricePredictionRequest(BaseModel):
    """가격 예측 요청"""
    component_id: str
    component_name: str
    category: str
    current_price: int
    price_history: List[PricePoint] = Field(default_factory=list)
    prediction_days: int = Field(30, description="예측 기간 (일)")
    include_factors: List[str] = Field(default_factory=list)


class PricePredictionResult(BaseModel):
    """가격 예측 결과"""
    component_id: str
    component_name: str
    predictions: List[PredictionPoint]
    trend: TrendAnalysis
    buy_recommendation: BuyRecommendation
    factors_impact: Optional[FactorsImpact] = None
    model_confidence: float = Field(..., ge=0, le=1, description="모델 신뢰도")
    generated_at: str


# ============================================================================
# 가격 예측 모델
# ============================================================================

class PricePredictionModel:
    """
    시계열 기반 가격 예측 모델
    
    다양한 시계열 예측 알고리즘을 지원하며,
    가격 추세 분석 및 최적 구매 시점 추천을 제공.
    
    사용법:
    ```python
    model = PricePredictionModel()
    
    # 가격 이력 데이터
    history = [
        {"date": "2024-01-01", "price": 750000},
        {"date": "2024-01-02", "price": 745000},
        ...
    ]
    
    result = model.predict(
        component_id="gpu_rtx4070",
        component_name="RTX 4070",
        category="gpu",
        current_price=720000,
        price_history=history,
        prediction_days=30
    )
    
    print(f"추세: {result.trend.direction}")
    print(f"구매 권장: {result.buy_recommendation.action}")
    ```
    """
    
    # 카테고리별 가격 변동성 (표준편차 비율)
    CATEGORY_VOLATILITY = {
        "gpu": 0.08,      # GPU는 변동성이 큼
        "cpu": 0.05,      # CPU는 상대적으로 안정
        "memory": 0.10,   # 메모리는 변동성이 매우 큼
        "storage": 0.06,  # SSD는 지속적 하락 추세
        "motherboard": 0.04,
        "psu": 0.03,
        "case": 0.02,
    }
    
    # 계절성 패턴 (월별 가격 조정 계수)
    SEASONALITY = {
        1: 1.02,   # 1월: 연초 수요 증가
        2: 1.00,
        3: 0.99,   # 3월: 신학기
        4: 0.98,
        5: 0.98,
        6: 0.97,   # 6월: 여름 비수기
        7: 0.97,
        8: 0.98,
        9: 0.99,   # 9월: 신학기
        10: 1.00,
        11: 0.95,  # 11월: 블랙프라이데이
        12: 0.96,  # 12월: 연말 세일
    }
    
    def __init__(
        self,
        model_type: str = "simple",  # simple, prophet, tft
        use_external_factors: bool = True,
    ):
        """
        Args:
            model_type: 사용할 모델 타입
                - "simple": 단순 이동평균 기반 (기본)
                - "prophet": Facebook Prophet
                - "tft": Temporal Fusion Transformer
            use_external_factors: 외부 요인 사용 여부
        """
        self.model_type = model_type
        self.use_external_factors = use_external_factors
        
        # TODO: 실제 ML 모델 로드
        # if model_type == "prophet":
        #     from prophet import Prophet
        #     self.model = Prophet()
        # elif model_type == "tft":
        #     from pytorch_forecasting import TemporalFusionTransformer
        #     self.model = TemporalFusionTransformer.load_from_checkpoint(...)
        
        logger.info(f"PricePredictionModel 초기화: model_type={model_type}")
    
    def predict(
        self,
        component_id: str,
        component_name: str,
        category: str,
        current_price: int,
        price_history: List[Dict[str, Any]],
        prediction_days: int = 30,
        include_factors: Optional[List[str]] = None,
    ) -> PricePredictionResult:
        """
        가격 예측 수행
        
        Args:
            component_id: 부품 ID
            component_name: 부품 이름
            category: 카테고리
            current_price: 현재 가격
            price_history: 가격 이력
            prediction_days: 예측 기간
            include_factors: 포함할 외부 요인
            
        Returns:
            PricePredictionResult: 예측 결과
        """
        logger.info(f"가격 예측 시작: {component_name}, {prediction_days}일")
        
        # 가격 이력이 없으면 현재 가격 기반 예측
        if not price_history:
            price_history = [{"date": datetime.now().strftime("%Y-%m-%d"), "price": current_price}]
        
        # 1. 추세 분석
        trend = self._analyze_trend(price_history, category)
        
        # 2. 예측 생성
        predictions = self._generate_predictions(
            price_history=price_history,
            current_price=current_price,
            prediction_days=prediction_days,
            trend=trend,
            category=category,
        )
        
        # 3. 외부 요인 영향 계산
        factors_impact = None
        if include_factors:
            factors_impact = self._calculate_factors_impact(
                category=category,
                factors=include_factors,
            )
        
        # 4. 구매 추천 생성
        buy_recommendation = self._generate_buy_recommendation(
            predictions=predictions,
            trend=trend,
            current_price=current_price,
        )
        
        # 5. 모델 신뢰도 계산
        model_confidence = self._calculate_model_confidence(
            price_history=price_history,
            category=category,
        )
        
        return PricePredictionResult(
            component_id=component_id,
            component_name=component_name,
            predictions=predictions,
            trend=trend,
            buy_recommendation=buy_recommendation,
            factors_impact=factors_impact,
            model_confidence=model_confidence,
            generated_at=datetime.now().isoformat(),
        )
    
    def _analyze_trend(
        self,
        price_history: List[Dict[str, Any]],
        category: str,
    ) -> TrendAnalysis:
        """가격 추세 분석"""
        if len(price_history) < 2:
            return TrendAnalysis(
                direction=TrendDirection.STABLE,
                strength=0.0,
                expected_change_pct=0.0,
            )
        
        # 가격 리스트 추출
        prices = [p["price"] for p in price_history]
        
        # 선형 회귀로 추세 계산
        n = len(prices)
        x = np.arange(n)
        slope = np.polyfit(x, prices, 1)[0]
        
        # 추세 방향 결정
        avg_price = np.mean(prices)
        change_pct = (slope * n) / avg_price * 100
        
        if abs(change_pct) < 1:
            direction = TrendDirection.STABLE
        elif change_pct > 0:
            direction = TrendDirection.UP
        else:
            direction = TrendDirection.DOWN
        
        # 추세 강도 계산 (R-squared 간소화)
        strength = min(1.0, abs(change_pct) / 10)
        
        return TrendAnalysis(
            direction=direction,
            strength=round(strength, 2),
            expected_change_pct=round(change_pct, 2),
        )
    
    def _generate_predictions(
        self,
        price_history: List[Dict[str, Any]],
        current_price: int,
        prediction_days: int,
        trend: TrendAnalysis,
        category: str,
    ) -> List[PredictionPoint]:
        """예측 가격 생성"""
        predictions = []
        
        # 변동성 계수
        volatility = self.CATEGORY_VOLATILITY.get(category, 0.05)
        
        # 일별 추세 변화율
        daily_change_pct = trend.expected_change_pct / 30  # 월간 → 일간
        
        base_date = datetime.now()
        predicted_price = current_price
        
        for day in range(1, prediction_days + 1):
            pred_date = base_date + timedelta(days=day)
            month = pred_date.month
            
            # 추세 적용
            predicted_price *= (1 + daily_change_pct / 100)
            
            # 계절성 적용
            if self.use_external_factors:
                seasonality = self.SEASONALITY.get(month, 1.0)
                predicted_price *= seasonality
            
            # 신뢰구간 계산
            uncertainty = volatility * np.sqrt(day) * predicted_price
            
            predictions.append(PredictionPoint(
                date=pred_date.strftime("%Y-%m-%d"),
                price=int(predicted_price),
                lower=int(predicted_price - 1.96 * uncertainty),
                upper=int(predicted_price + 1.96 * uncertainty),
            ))
        
        return predictions
    
    def _calculate_factors_impact(
        self,
        category: str,
        factors: List[str],
    ) -> FactorsImpact:
        """외부 요인 영향 계산"""
        impact = FactorsImpact()
        
        # TODO: 실제 외부 데이터 기반 계산
        # 현재는 카테고리별 기본값 사용
        
        if "seasonality" in factors:
            current_month = datetime.now().month
            seasonality_coef = self.SEASONALITY.get(current_month, 1.0)
            impact.seasonality = round((seasonality_coef - 1) * 100, 2)
        
        if "exchange_rate" in factors:
            # TODO: 실제 환율 데이터 연동
            impact.exchange_rate = 0.5  # Placeholder
        
        if "new_product" in factors:
            # TODO: 신제품 출시 일정 데이터 연동
            if category == "gpu":
                impact.new_product = -2.0  # GPU는 신제품 출시 시 하락
        
        return impact
    
    def _generate_buy_recommendation(
        self,
        predictions: List[PredictionPoint],
        trend: TrendAnalysis,
        current_price: int,
    ) -> BuyRecommendation:
        """구매 추천 생성"""
        if not predictions:
            return BuyRecommendation(
                action=BuyAction.WATCH,
                confidence=0.5,
                reasoning="예측 데이터 부족",
            )
        
        # 최저 예측가 찾기
        min_prediction = min(predictions, key=lambda p: p.price)
        min_price = min_prediction.price
        
        # 가격 하락 예상인 경우
        if trend.direction == TrendDirection.DOWN:
            if trend.strength > 0.5:
                # 강한 하락 추세
                return BuyRecommendation(
                    action=BuyAction.WAIT,
                    confidence=0.7 + trend.strength * 0.2,
                    best_buy_date=min_prediction.date,
                    expected_price_at_best=min_price,
                    reasoning=f"강한 하락 추세로 {min_prediction.date}까지 대기 권장. "
                             f"예상 가격: {min_price:,}원 "
                             f"(현재 대비 {((min_price - current_price) / current_price * 100):.1f}%)",
                )
            else:
                # 약한 하락 추세
                return BuyRecommendation(
                    action=BuyAction.WATCH,
                    confidence=0.5 + trend.strength * 0.2,
                    best_buy_date=min_prediction.date,
                    expected_price_at_best=min_price,
                    reasoning=f"약한 하락 추세. 급하지 않다면 가격 변동 모니터링 권장.",
                )
        
        # 가격 상승 예상인 경우
        elif trend.direction == TrendDirection.UP:
            return BuyRecommendation(
                action=BuyAction.BUY_NOW,
                confidence=0.6 + trend.strength * 0.3,
                reasoning=f"상승 추세로 지금 구매가 유리. "
                         f"예상 상승률: {trend.expected_change_pct:.1f}%",
            )
        
        # 안정적인 경우
        else:
            return BuyRecommendation(
                action=BuyAction.WATCH,
                confidence=0.5,
                reasoning="가격이 안정적입니다. 필요 시 구매해도 무방합니다.",
            )
    
    def _calculate_model_confidence(
        self,
        price_history: List[Dict[str, Any]],
        category: str,
    ) -> float:
        """모델 신뢰도 계산"""
        # 데이터 양에 따른 신뢰도
        data_confidence = min(1.0, len(price_history) / 90)  # 90일 기준
        
        # 카테고리별 예측 난이도
        category_difficulty = {
            "cpu": 0.8,
            "gpu": 0.6,  # GPU는 변동성이 커서 예측 어려움
            "memory": 0.5,
            "storage": 0.7,
            "motherboard": 0.8,
            "psu": 0.9,
            "case": 0.9,
        }
        category_conf = category_difficulty.get(category, 0.7)
        
        # 종합 신뢰도
        return round(data_confidence * category_conf, 2)
    
    def train(
        self,
        training_data: List[Dict[str, Any]],
        validation_split: float = 0.2,
    ):
        """
        모델 학습 (ML 모델용)
        
        TODO: 실제 ML 모델 학습 구현
        
        Args:
            training_data: 학습 데이터
            validation_split: 검증 데이터 비율
        """
        logger.info(f"모델 학습 시작: {len(training_data)}개 데이터")
        
        # TODO: Prophet 또는 TFT 모델 학습
        # if self.model_type == "prophet":
        #     df = self._prepare_prophet_data(training_data)
        #     self.model.fit(df)
        # elif self.model_type == "tft":
        #     training_dataset = self._prepare_tft_data(training_data)
        #     trainer.fit(self.model, training_dataset)
        
        logger.info("모델 학습 완료 (placeholder)")
    
    def save_model(self, path: str):
        """모델 저장"""
        logger.info(f"모델 저장: {path}")
        # TODO: 모델 직렬화 및 저장
    
    def load_model(self, path: str):
        """모델 로드"""
        logger.info(f"모델 로드: {path}")
        # TODO: 모델 역직렬화 및 로드


# ============================================================================
# 간편 함수
# ============================================================================

def predict_price(
    component_name: str,
    category: str,
    current_price: int,
    prediction_days: int = 30,
) -> PricePredictionResult:
    """
    간편 가격 예측 함수
    
    Args:
        component_name: 부품 이름
        category: 카테고리
        current_price: 현재 가격
        prediction_days: 예측 기간
        
    Returns:
        PricePredictionResult: 예측 결과
    """
    model = PricePredictionModel()
    return model.predict(
        component_id=f"{category}_{component_name.lower().replace(' ', '_')}",
        component_name=component_name,
        category=category,
        current_price=current_price,
        price_history=[],
        prediction_days=prediction_days,
    )


# ============================================================================
# 테스트용 메인
# ============================================================================

if __name__ == "__main__":
    import json
    
    # 테스트 데이터 생성
    base_price = 720000
    history = []
    base_date = datetime.now() - timedelta(days=30)
    
    for i in range(30):
        date = base_date + timedelta(days=i)
        # 약간의 변동과 하락 추세 시뮬레이션
        price = base_price - (i * 500) + np.random.randint(-5000, 5000)
        history.append({
            "date": date.strftime("%Y-%m-%d"),
            "price": max(650000, int(price))
        })
    
    # 예측 실행
    model = PricePredictionModel()
    result = model.predict(
        component_id="gpu_rtx4070",
        component_name="RTX 4070",
        category="gpu",
        current_price=700000,
        price_history=history,
        prediction_days=30,
        include_factors=["seasonality", "exchange_rate"],
    )
    
    print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False, default=str))
