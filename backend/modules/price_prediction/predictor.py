import json
from pathlib import Path
from datetime import datetime, timedelta
import argparse
import pandas as pd
from loguru import logger
import numpy as np
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

# ============================================================================
# 데이터 모델 (Pydantic)
# ============================================================================

class TrendDirection(str, Enum):
    """가격 추세 방향"""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"

class BuyAction(str, Enum):
    """구매 추천 행동"""
    BUY_NOW = "buy_now"
    WAIT = "wait"
    WATCH = "watch"

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
    """
    CATEGORY_VOLATILITY = {
        "gpu": 0.08, "cpu": 0.05, "memory": 0.10, "storage": 0.06,
        "motherboard": 0.04, "psu": 0.03, "case": 0.02,
    }
    SEASONALITY = {
        1: 1.02, 2: 1.00, 3: 0.99, 4: 0.98, 5: 0.98, 6: 0.97,
        7: 0.97, 8: 0.98, 9: 0.99, 10: 1.00, 11: 0.95, 12: 0.96,
    }
    
    def __init__(self, model_type: str = "simple", use_external_factors: bool = True):
        self.model_type = model_type
        self.use_external_factors = use_external_factors
        logger.info(f"PricePredictionModel 초기화: model_type={model_type}")
    
    def predict(
        self, component_id: str, component_name: str, category: str,
        current_price: int, price_history: List[Dict[str, Any]],
        prediction_days: int = 30, include_factors: Optional[List[str]] = None,
        start_date: Optional[str] = None
    ) -> PricePredictionResult:
        logger.info(f"가격 예측 시작: {component_name}, {prediction_days}일")
        
        if not price_history:
            price_history = [{"date": datetime.now().strftime("%Y-%m-%d"), "price": current_price}]
        
        trend = self._analyze_trend(price_history, category)
        predictions = self._generate_predictions(price_history, current_price, prediction_days, trend, category, start_date)
        
        factors_impact = self._calculate_factors_impact(category, include_factors) if include_factors else None
        
        buy_recommendation = self._generate_buy_recommendation(predictions, trend, current_price)
        model_confidence = self._calculate_model_confidence(price_history, category)
        
        return PricePredictionResult(
            component_id=component_id, component_name=component_name,
            predictions=predictions, trend=trend, buy_recommendation=buy_recommendation,
            factors_impact=factors_impact, model_confidence=model_confidence,
            generated_at=datetime.now().isoformat(),
        )
    
    def _analyze_trend(self, price_history: List[Dict[str, Any]], category: str) -> TrendAnalysis:
        if len(price_history) < 2:
            return TrendAnalysis(direction=TrendDirection.STABLE, strength=0.0, expected_change_pct=0.0)
        
        prices = [p["price"] for p in price_history]
        n = len(prices)
        x = np.arange(n)
        slope = np.polyfit(x, prices, 1)[0]
        
        avg_price = np.mean(prices)
        if avg_price == 0: return TrendAnalysis(direction=TrendDirection.STABLE, strength=0.0, expected_change_pct=0.0)
        
        change_pct = (slope * n) / avg_price * 100
        
        if abs(change_pct) < 1: direction = TrendDirection.STABLE
        elif change_pct > 0: direction = TrendDirection.UP
        else: direction = TrendDirection.DOWN
        
        strength = min(1.0, abs(change_pct) / 10)
        
        return TrendAnalysis(direction=direction, strength=round(strength, 2), expected_change_pct=round(change_pct, 2))

    def _generate_predictions(
        self, price_history: List[Dict[str, Any]], current_price: int,
        prediction_days: int, trend: TrendAnalysis, category: str,
        start_date_str: Optional[str] = None
    ) -> List[PredictionPoint]:
        predictions = []
        volatility = self.CATEGORY_VOLATILITY.get(category, 0.05)
        daily_change_pct = trend.expected_change_pct / 30
        
        if start_date_str:
            base_date = datetime.strptime(start_date_str, "%Y-%m-%d") - timedelta(days=1)
        else:
            base_date = datetime.strptime(price_history[-1]['date'], "%Y-%m-%d")

        predicted_price = float(current_price)
        
        for day in range(1, prediction_days + 1):
            pred_date = base_date + timedelta(days=day)
            month = pred_date.month
            
            predicted_price *= (1 + daily_change_pct / 100)
            
            if self.use_external_factors:
                seasonality = self.SEASONALITY.get(month, 1.0)
                predicted_price *= seasonality
            
            uncertainty = volatility * np.sqrt(day) * predicted_price
            
            predictions.append(PredictionPoint(
                date=pred_date.strftime("%Y-%m-%d"), price=int(predicted_price),
                lower=int(predicted_price - 1.96 * uncertainty),
                upper=int(predicted_price + 1.96 * uncertainty),
            ))
        return predictions

    def _calculate_factors_impact(self, category: str, factors: List[str]) -> FactorsImpact:
        impact = FactorsImpact()
        if "seasonality" in factors:
            current_month = datetime.now().month
            seasonality_coef = self.SEASONALITY.get(current_month, 1.0)
            impact.seasonality = round((seasonality_coef - 1) * 100, 2)
        if "exchange_rate" in factors: impact.exchange_rate = 0.5
        if "new_product" in factors and category == "gpu": impact.new_product = -2.0
        return impact

    def _generate_buy_recommendation(
        self, predictions: List[PredictionPoint], trend: TrendAnalysis, current_price: int
    ) -> BuyRecommendation:
        """구매 추천 생성"""
        if not predictions:
            return BuyRecommendation(action=BuyAction.WATCH, confidence=0.5, reasoning="예측 데이터가 부족하여 추천을 생성할 수 없습니다.")

        min_prediction = min(predictions, key=lambda p: p.price)
        min_price = min_prediction.price
        
        price_change_pct = ((min_price - current_price) / current_price) * 100

        # 예측된 최저가가 현재가보다 유의미하게 낮을 경우
        if price_change_pct < -2.0: # 2% 이상 하락 시
            return BuyRecommendation(
                action=BuyAction.WAIT,
                confidence=min(0.9, 0.5 + abs(price_change_pct) / 10),
                best_buy_date=min_prediction.date,
                expected_price_at_best=min_price,
                reasoning=(
                    f"향후 {len(predictions)}일 내에 가격이 약 {abs(price_change_pct):.1f}% 하락할 것으로 예측됩니다. "
                    f"{min_prediction.date} 경에 최저가({min_price:,}원)에 도달할 것으로 보이니, 그때까지 기다리는 것을 추천합니다."
                ),
            )

        # 예측된 가격이 현재 가격보다 계속 상승하거나 큰 변동이 없는 경우
        # 첫 예측가가 현재가보다 이미 높거나, 최저 예측가와의 차이가 미미한 경우
        if predictions[0].price > current_price or abs(price_change_pct) < 1.0:
            reasoning = "향후 가격이 상승하거나 현재 수준을 유지할 것으로 예상됩니다. 지금 구매하는 것이 유리할 수 있습니다."
            if trend.direction == TrendDirection.DOWN:
                 reasoning = f"과거 데이터는 하락 추세이나, 단기적으로는 계절성 등의 요인으로 가격이 상승하거나 유지될 것으로 보입니다. 따라서 지금 구매를 고려하는 것이 좋습니다."

            return BuyRecommendation(
                action=BuyAction.BUY_NOW,
                confidence=0.6,
                reasoning=reasoning,
            )

        # 그 외의 경우 (약한 하락 등)
        return BuyRecommendation(
            action=BuyAction.WATCH,
            confidence=0.5,
            best_buy_date=min_prediction.date,
            expected_price_at_best=min_price,
            reasoning=f"가격이 소폭 하락할 가능성이 있습니다. 예상 최저가는 {min_prediction.date} 경의 {min_price:,}원입니다. 급하지 않다면 가격 변동을 주시하는 것을 추천합니다.",
        )

    def _calculate_model_confidence(self, price_history: List[Dict[str, Any]], category: str) -> float:
        data_confidence = min(1.0, len(price_history) / 90)
        category_difficulty = {"gpu": 0.6, "memory": 0.5, "storage": 0.7, "motherboard": 0.8, "psu": 0.9, "case": 0.9}
        category_conf = category_difficulty.get(category, 0.7)
        return round(data_confidence * category_conf, 2)

# ============================================================================
# 데이터 로더 및 메인 실행
# ============================================================================
ROOT_DIR = Path(__file__).parent.parent.parent.parent
DATA_FILE = ROOT_DIR / "backend" / "modules" / "price_prediction" / "data" / "transformed_prices.json"
PREDICTION_OUTPUT_FILE = ROOT_DIR / "backend" / "modules" / "price_prediction" / "data" / "predicted_prices.json"

def get_component_data(component_id: str, days_history: int = 0) -> dict | None:
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            all_data = json.load(f)
    except Exception as e:
        print(f"데이터 파일을 읽는 중 오류 발생: {e}")
        return None

    component_records_list = [record for record in all_data if str(record.get("component_id")) == component_id]
    if not component_records_list:
        print(f"ID가 '{component_id}'인 부품을 찾을 수 없습니다.")
        return None

    component_records = pd.DataFrame(component_records_list)
    component_records['date'] = pd.to_datetime(component_records['date'])
    component_records = component_records.sort_values(by='date')
    
    price_history = component_records.apply(lambda row: {"date": row['date'].strftime('%Y-%m-%d'), "price": row['min_price']}, axis=1).tolist()
    
    if days_history > 0:
        price_history = price_history[-days_history:]

    if not price_history:
        return None

    latest = component_records.iloc[-1]
    return {
        "component_id": component_id, "component_name": latest['component_name'],
        "category": latest['category'], "current_price": latest['min_price'],
        "price_history": price_history,
    }

def main():
    parser = argparse.ArgumentParser(description="가격 예측 모델을 실행하고 결과를 파일로 저장합니다.")
    parser.add_argument("component_id", type=str, help="가격을 예측할 부품의 ID")
    parser.add_argument("--history", type=int, default=0, help="가격 기록 일수 (0=전체)")
    parser.add_argument("--predict", type=int, default=30, help="예측 기간 (일)")
    parser.add_argument("--start-date", type=str, default=None, help="예측 시작일 (YYYY-MM-DD)")
    args = parser.parse_args()

    component_data = get_component_data(args.component_id, args.history)
    if not component_data:
        return

    model = PricePredictionModel()
    result = model.predict(
        component_id=component_data["component_id"],
        component_name=component_data["component_name"],
        category=component_data["category"],
        current_price=component_data["current_price"],
        price_history=component_data["price_history"],
        prediction_days=args.predict,
        include_factors=["seasonality", "exchange_rate"],
        start_date=args.start_date
    )

    output_data = result.model_dump()
    
    try:
        with open(PREDICTION_OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)
        logger.info(f"예측 결과가 '{PREDICTION_OUTPUT_FILE}' 파일에 저장되었습니다.")
    except Exception as e:
        logger.error(f"예측 결과 저장 중 오류 발생: {e}")
    
    print(json.dumps(output_data, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    main()