# Price Prediction 모듈

> 시계열 트랜스포머 기반 PC 부품 가격 예측 시스템

## 목차

- [개요](#개요)
- [아키텍처](#아키텍처)
- [파일 구조](#파일-구조)
- [핵심 기능](#핵심-기능)
- [데이터 모델](#데이터-모델)
- [사용법](#사용법)
- [구현 가이드](#구현-가이드)
- [테스트](#테스트)
- [참고 자료](#참고-자료)

---

## 개요

### 목표

PC 부품의 미래 가격을 예측하여 사용자에게 **최적의 구매 시점**을 추천한다.

### 배경 지식

PC 부품 가격은 다양한 요인에 의해 변동된다:

| 요인 | 영향 | 예시 |
|------|------|------|
| **신제품 출시** | 구제품 가격 하락 | RTX 50시리즈 출시 → RTX 40시리즈 가격 하락 |
| **환율 변동** | 전체 가격 변동 | 달러-원 환율 상승 → 수입 부품 가격 상승 |
| **수요 변동** | 급격한 가격 변동 | 마이닝 붐 → GPU 가격 폭등 |
| **공급망 이슈** | 품귀 현상 | 반도체 부족 → 전체 부품 가격 상승 |
| **계절성** | 주기적 변동 | 연말 쇼핑 시즌 → 할인 |

### 시계열 예측 모델 후보

| 모델 | 장점 | 단점 |
|------|------|------|
| **ARIMA/SARIMA** | 간단, 해석 가능 | 비선형 패턴 처리 어려움 |
| **Prophet** | 계절성 처리 강점 | 외부 요인 반영 제한적 |
| **LSTM/GRU** | 복잡한 패턴 학습 | 학습 데이터 많이 필요 |
| **Temporal Fusion Transformer** | 최신, 정확도 높음 | 구현 복잡 |
| **Informer** | 장기 예측에 최적화 | 계산 비용 높음 |

---

## 아키텍처

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

---

## 파일 구조

```
price_prediction/
├── __init__.py          # 모듈 초기화 및 exports
├── predictor.py         # 메인 예측 모델 (PricePredictionModel)
├── data_collector.py    # 가격 데이터 수집기
├── features.py          # 특성 추출기 (PriceFeatureExtractor)
└── README.md            # 이 문서
```

### 파일별 역할

| 파일 | 역할 | 주요 클래스 |
|------|------|-------------|
| `predictor.py` | 가격 예측 모델 및 구매 추천 | `PricePredictionModel`, `BuyRecommendation` |
| `data_collector.py` | 가격 데이터 수집 및 저장 | `PriceDataCollector`, `PriceCollectionScheduler` |
| `features.py` | 시계열 특성 추출 | `PriceFeatureExtractor`, `PriceFeatures` |

---

## 핵심 기능

### 1. 가격 데이터 수집 (PriceDataCollector)

다양한 소스에서 PC 부품 가격 이력을 수집한다.

**데이터 소스 후보:**

| 소스 | 장점 | 단점 |
|------|------|------|
| 다나와 | 국내 최대 가격비교 | 크롤링 정책 확인 필요 |
| 네이버 쇼핑 | 다양한 판매처 | API 제한 |
| 에누리 | 가격 추이 제공 | 크롤링 정책 |
| PCPartPicker | 해외 데이터 | 국내 가격과 다름 |

**수집 데이터 형식:**

```python
{
    "component_id": "gpu_rtx4070",
    "component_name": "RTX 4070",
    "category": "gpu",
    "date": "2026-01-02",
    "min_price": 650000,
    "avg_price": 680000,
    "max_price": 720000,
    "source": "danawa"
}
```

### 2. 특성 추출 (PriceFeatureExtractor)

시계열 예측에 필요한 다양한 특성을 추출한다.

**시계열 기본 특성:**

| 특성 | 설명 | 윈도우 |
|------|------|--------|
| MA (이동평균) | 단기/장기 추세 | 7일, 30일 |
| EMA (지수이동평균) | 최근 데이터에 가중치 | 7일 |
| Volatility | 변동성 (표준편차/평균) | - |
| Momentum | 가격 변화 속도 | 7일 |

**계절성 특성:**

| 특성 | 설명 |
|------|------|
| day_of_week | 요일 (0-6) |
| month | 월 (1-12) |
| quarter | 분기 (1-4) |
| is_holiday_season | 휴일 시즌 여부 (11, 12, 1월) |

**외부 요인 특성:**

| 특성 | 설명 | 소스 |
|------|------|------|
| exchange_rate | USD/KRW 환율 | 환율 API |
| new_product_flag | 신제품 출시 플래그 | 뉴스/캘린더 |
| sale_event_flag | 대형 세일 이벤트 | 캘린더 |

### 3. 가격 예측 (PricePredictionModel)

시계열 모델을 사용하여 미래 가격을 예측한다.

**예측 출력:**
- **포인트 예측**: 각 날짜의 예상 가격
- **신뢰 구간**: 95% 신뢰구간 (상한/하한)
- **추세 분석**: 상승/하락/안정 방향 및 강도

### 4. 구매 추천 (BuyRecommendation)

예측 결과를 바탕으로 구매 시점을 추천한다.

**추천 액션:**

| 액션 | 조건 | 메시지 |
|------|------|--------|
| `BUY_NOW` | 상승 추세 | "지금 구매가 유리합니다" |
| `WAIT` | 강한 하락 추세 | "X일까지 대기 권장" |
| `WATCH` | 불확실 | "가격 변동 모니터링 권장" |

---

## 데이터 모델

### 입력: PricePredictionRequest

```python
{
    "component_id": "gpu_rtx4070",
    "component_name": "RTX 4070",
    "category": "gpu",
    "current_price": 720000,
    "price_history": [
        {"date": "2026-01-01", "price": 750000},
        {"date": "2026-01-02", "price": 745000},
        # ... 최소 30일 이상 권장
    ],
    "prediction_days": 30,  # 예측 기간 (일)
    "include_factors": ["exchange_rate", "seasonality"]
}
```

### 출력: PricePredictionResult

```python
{
    "component_id": "gpu_rtx4070",
    "component_name": "RTX 4070",
    "predictions": [
        {
            "date": "2026-02-01",
            "price": 710000,
            "lower": 690000,  # 95% 신뢰구간 하한
            "upper": 730000   # 95% 신뢰구간 상한
        },
        # ... 30일 예측
    ],
    "trend": {
        "direction": "down",      # up, down, stable
        "strength": 0.65,         # 추세 강도 (0-1)
        "expected_change_pct": -3.2  # 예측 기간 내 예상 변화율
    },
    "buy_recommendation": {
        "action": "wait",         # buy_now, wait, watch
        "confidence": 0.72,
        "best_buy_date": "2026-02-15",
        "expected_price_at_best": 680000,
        "reasoning": "향후 2주 내 약 5% 가격 하락 예상"
    },
    "factors_impact": {
        "seasonality": -2.1,      # % 영향
        "exchange_rate": +0.5,
        "new_product": -3.0
    },
    "model_confidence": 0.72,
    "generated_at": "2026-01-02T10:30:00"
}
```

---

## 사용법

### 기본 예측

```python
from backend.modules.price_prediction import PricePredictionModel

model = PricePredictionModel()

# 가격 이력 (최소 7일, 권장 30일 이상)
history = [
    {"date": "2026-01-01", "price": 750000},
    {"date": "2026-01-02", "price": 745000},
    # ...
]

result = model.predict(
    component_id="gpu_rtx4070",
    component_name="RTX 4070",
    category="gpu",
    current_price=720000,
    price_history=history,
    prediction_days=30,
    include_factors=["seasonality", "exchange_rate"]
)

print(f"추세: {result.trend.direction.value}")
print(f"예상 변화율: {result.trend.expected_change_pct}%")
print(f"구매 추천: {result.buy_recommendation.action.value}")
print(f"추천 사유: {result.buy_recommendation.reasoning}")
```

### 간편 함수 사용

```python
from backend.modules.price_prediction import predict_price

result = predict_price(
    component_name="RTX 4070",
    category="gpu",
    current_price=720000,
    prediction_days=30
)
```

### 가격 데이터 수집

```python
from backend.modules.price_prediction.data_collector import PriceDataCollector

collector = PriceDataCollector()

# 가격 수집
record = collector.collect_price(
    component_name="RTX 4070",
    category="gpu",
    source="manual"  # 또는 "danawa", "naver"
)

# 수집된 데이터 저장
collector.add_price_record(record)
collector.save_to_file("prices.json")

# 가격 이력 조회
history = collector.get_price_history("gpu_rtx4070", days=30)
```

### 특성 추출

```python
from backend.modules.price_prediction.features import PriceFeatureExtractor

extractor = PriceFeatureExtractor()

features = extractor.extract(price_history)

print(f"7일 이동평균: {features.ma_7}")
print(f"변동성: {features.volatility}")
print(f"모멘텀: {features.momentum}")
print(f"휴일 시즌: {features.is_holiday_season}")
```

---

## 구현 가이드

### 1단계: 가격 데이터 수집기 구현

크롤링 또는 API를 통해 실제 가격 데이터를 수집한다.

```python
# data_collector.py - 다나와 크롤링 예시 (구현 필요)
import requests
from bs4 import BeautifulSoup

def collect_from_danawa(component_name: str):
    url = f"https://search.danawa.com/dsearch.php?query={component_name}"
    headers = {"User-Agent": "Mozilla/5.0 ..."}
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 가격 추출 로직
    price_element = soup.select_one('.price_sect')
    # ...
```

**크롤링 주의사항:**
- `robots.txt` 확인
- 적절한 딜레이 설정 (1-2초)
- User-Agent 설정
- 과도한 요청으로 IP 차단 주의

### 2단계: 시계열 모델 구현

Prophet 또는 PyTorch Forecasting을 사용하여 예측 모델을 구현한다.

**Prophet 예시:**

```python
from prophet import Prophet
import pandas as pd

def train_prophet_model(price_history):
    # 데이터 준비
    df = pd.DataFrame(price_history)
    df = df.rename(columns={"date": "ds", "price": "y"})
    
    # 모델 학습
    model = Prophet(
        changepoint_prior_scale=0.05,
        seasonality_mode='multiplicative'
    )
    model.fit(df)
    
    # 예측
    future = model.make_future_dataframe(periods=30)
    forecast = model.predict(future)
    
    return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
```

**Temporal Fusion Transformer 예시:**

```python
from pytorch_forecasting import TemporalFusionTransformer
from pytorch_forecasting.data import TimeSeriesDataSet

# 데이터셋 준비
training = TimeSeriesDataSet(
    data,
    time_idx="time_idx",
    target="price",
    group_ids=["component_id"],
    # ...
)

# 모델 학습
trainer.fit(tft, training)
```

### 3단계: 외부 요인 연동

환율, 신제품 출시 일정 등 외부 데이터를 연동한다.

```python
# 환율 API 예시 (구현 필요)
def get_exchange_rate():
    # 한국수출입은행 API 또는 다른 환율 API
    response = requests.get("https://api.exchangerate.host/latest?base=USD&symbols=KRW")
    return response.json()["rates"]["KRW"]
```

### 4단계: 모델 성능 평가

예측 정확도를 측정하고 개선한다.

**평가 지표:**

| 지표 | 목표 | 설명 |
|------|------|------|
| MAPE | < 5% | 평균 절대 백분율 오차 |
| 방향성 정확도 | > 70% | 상승/하락 방향 예측 정확도 |
| 최적 구매 시점 정확도 | > 65% | 추천 날짜의 실제 최저가 여부 |

---

## 테스트

### 테스트 파일 위치

```
backend/tests/test_price_prediction.py
```

### 테스트 실행

```bash
# 전체 테스트
pytest backend/tests/test_price_prediction.py -v

# 특정 테스트
pytest backend/tests/test_price_prediction.py::test_price_prediction -v
```

### 테스트 항목

1. **예측 모델 테스트**
   - 기본 예측 기능
   - 추세 분석 정확도
   
2. **특성 추출 테스트**
   - 이동평균 계산
   - 변동성 계산
   - 계절성 특성

3. **구매 추천 테스트**
   - 상승 추세 → BUY_NOW
   - 하락 추세 → WAIT

---

## TODO

### 필수 구현

- [ ] 가격 데이터 크롤링 구현 (다나와, 네이버)
- [ ] Prophet 또는 TFT 모델 실제 학습
- [ ] 환율 API 연동
- [ ] 신제품 출시 일정 데이터 구축

### 선택적 구현

- [ ] 실시간 가격 알림 기능
- [ ] 가격 예측 시각화 (차트)
- [ ] 여러 부품 동시 예측
- [ ] 모델 앙상블 (여러 모델 조합)

---

## 주의사항

1. **법적 이슈**: 웹 크롤링 시 해당 사이트의 이용약관 확인 필수
2. **데이터 양**: 모델 학습에 최소 수백 일의 데이터 필요
3. **예측 한계**: 급격한 시장 변동 시 예측 신뢰도 하락 가능
4. **면책 고지**: 사용자에게 "예측"임을 명확히 고지 필요

---

## 참고 자료

### 시계열 예측 라이브러리

- [Prophet](https://facebook.github.io/prophet/) - Facebook 시계열 예측
- [PyTorch Forecasting](https://pytorch-forecasting.readthedocs.io/) - TFT 구현
- [Darts](https://unit8co.github.io/darts/) - 통합 시계열 라이브러리
- [Informer](https://github.com/zhouhaoyi/Informer2020) - 장기 시계열 예측

### 데이터 소스

- [다나와](https://www.danawa.com/)
- [네이버 쇼핑](https://shopping.naver.com/)
- [에누리](https://www.enuri.com/)
- [PCPartPicker](https://pcpartpicker.com/)

### 논문

- [Attention Is All You Need (Transformer)](https://arxiv.org/abs/1706.03762)
- [Temporal Fusion Transformers](https://arxiv.org/abs/1912.09363)
- [Informer](https://arxiv.org/abs/2012.07436)

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2026-01-02 | 0.1.0 | 초기 스켈레톤 구현 |
