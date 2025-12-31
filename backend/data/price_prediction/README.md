# 가격 예측 모듈 데이터

> 부품별 가격 이력, 환율, 이벤트 캘린더 데이터

---

## 목차

1. [필요 데이터 목록](#1-필요-데이터-목록)
2. [데이터 수집 방법](#2-데이터-수집-방법)
3. [데이터 형식](#3-데이터-형식)
4. [자동 수집 파이프라인](#4-자동-수집-파이프라인)

---

## 1. 필요 데이터 목록

| 파일명 | 설명 | 우선순위 | 상태 |
|--------|------|----------|------|
| `price_history/` | 부품별 일별 가격 이력 | 필수 | 미수집 |
| `exchange_rates.json` | USD/KRW 환율 이력 | 필수 | 미수집 |
| `product_releases.json` | 신제품 출시/단종 일정 | 권장 | 미수집 |
| `sale_events.json` | 대형 세일 이벤트 캘린더 | 권장 | 미수집 |
| `market_news.json` | 시장 뉴스/이슈 (선택) | 선택 | 미수집 |

---

## 2. 데이터 수집 방법

### 2.1 가격 이력 (price_history/)

**데이터 출처:**
- [다나와](https://www.danawa.com/) - 국내 최대 가격비교
- [네이버 쇼핑](https://shopping.naver.com/)
- [쿠팡](https://www.coupang.com/)
- [컴퓨존](https://www.compuzone.co.kr/)

**수집 방법:**

#### 방법 1: 다나와 가격 변동 크롤링 (권장)

```python
"""
다나와 가격 이력 수집 스크립트
주의: robots.txt 및 이용약관 확인 필요
과도한 요청 시 IP 차단 가능 - 딜레이 필수
"""
import requests
from bs4 import BeautifulSoup
import time
import json
from datetime import datetime

class DanawaCollector:
    BASE_URL = "https://prod.danawa.com/info/"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    def __init__(self, delay: float = 2.0):
        self.delay = delay  # 요청 간 딜레이 (초)
    
    def get_product_price(self, product_code: str) -> dict:
        """
        다나와 제품 코드로 현재 가격 조회
        
        Args:
            product_code: 다나와 제품 코드 (예: "18397651")
        
        Returns:
            {"date": "2024-12-31", "price": 720000, "lowest": 715000}
        """
        url = f"{self.BASE_URL}?pcode={product_code}"
        
        try:
            response = requests.get(url, headers=self.HEADERS, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 가격 추출 (다나와 페이지 구조에 따라 수정 필요)
            price_elem = soup.select_one('.lowestPrice .prc_c')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price = int(price_text.replace(',', '').replace('원', ''))
                
                return {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "price": price,
                    "source": "danawa"
                }
        except Exception as e:
            print(f"Error fetching {product_code}: {e}")
        
        return None
    
    def collect_daily(self, product_codes: list) -> list:
        """여러 제품의 일별 가격 수집"""
        results = []
        
        for code in product_codes:
            price_data = self.get_product_price(code)
            if price_data:
                price_data['product_code'] = code
                results.append(price_data)
            
            time.sleep(self.delay)  # Rate limiting
        
        return results


# 사용 예시
if __name__ == "__main__":
    collector = DanawaCollector(delay=2.0)
    
    # GPU 제품 코드 목록 (다나와에서 확인)
    GPU_PRODUCTS = {
        "RTX 4090": "18397651",
        "RTX 4080": "18484521",
        "RTX 4070 Ti": "18657891",
        # ...
    }
    
    prices = collector.collect_daily(list(GPU_PRODUCTS.values()))
    
    # JSON 저장
    with open('gpu_prices_daily.json', 'w', encoding='utf-8') as f:
        json.dump(prices, f, ensure_ascii=False, indent=2)
```

#### 방법 2: 네이버 쇼핑 API

```python
"""
네이버 쇼핑 API를 통한 가격 수집
API 키 발급: https://developers.naver.com/
"""
import requests

class NaverShoppingAPI:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://openapi.naver.com/v1/search/shop.json"
    
    def search_product(self, query: str, display: int = 10) -> list:
        """
        제품 검색 및 가격 조회
        
        Args:
            query: 검색어 (예: "RTX 4070")
            display: 결과 개수
        """
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }
        params = {
            "query": query,
            "display": display,
            "sort": "sim"  # 정확도순
        }
        
        response = requests.get(self.base_url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            return [
                {
                    "title": item['title'],
                    "lprice": int(item['lprice']),  # 최저가
                    "hprice": int(item['hprice']) if item['hprice'] else None,
                    "mall": item['mallName'],
                    "link": item['link']
                }
                for item in data.get('items', [])
            ]
        
        return []


# 환경 변수 설정 필요
# NAVER_CLIENT_ID=your_client_id
# NAVER_CLIENT_SECRET=your_client_secret
```

### 2.2 환율 데이터 (exchange_rates.json)

**데이터 출처:**
- [한국은행 경제통계시스템](https://ecos.bok.or.kr/)
- [ExchangeRate-API](https://www.exchangerate-api.com/) (무료 플랜 제공)
- [Fixer.io](https://fixer.io/)

**수집 방법:**

```python
"""
환율 데이터 수집
무료 API: ExchangeRate-API (월 1,500회)
"""
import requests
from datetime import datetime, timedelta

class ExchangeRateCollector:
    def __init__(self, api_key: str = None):
        # 무료 API (api_key 불필요)
        self.base_url = "https://open.er-api.com/v6/latest/USD"
    
    def get_current_rate(self) -> dict:
        """현재 USD/KRW 환율"""
        response = requests.get(self.base_url)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "usd_krw": data['rates'].get('KRW'),
                "source": "exchangerate-api"
            }
        
        return None
    
    def get_historical_rates(self, days: int = 365) -> list:
        """
        과거 환율 데이터 (유료 플랜 필요)
        대안: 한국은행 ECOS API 활용
        """
        # 유료 API 필요
        pass


# 한국은행 ECOS API 예시
class BOKExchangeRate:
    """
    한국은행 경제통계시스템 API
    API 키 발급: https://ecos.bok.or.kr/api/
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://ecos.bok.or.kr/api/StatisticSearch"
    
    def get_exchange_rate(self, start_date: str, end_date: str) -> list:
        """
        기간별 환율 조회
        
        Args:
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD)
        """
        # 통계표코드: 731Y001 (원/달러 환율)
        url = f"{self.base_url}/{self.api_key}/json/kr/1/100/731Y001/D/{start_date}/{end_date}/0000001"
        
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return [
                {
                    "date": item['TIME'],
                    "usd_krw": float(item['DATA_VALUE'])
                }
                for item in data.get('StatisticSearch', {}).get('row', [])
            ]
        
        return []
```

### 2.3 제품 출시/단종 일정 (product_releases.json)

**데이터 출처:**
- 제조사 공식 발표
- [VideoCardz](https://videocardz.com/) - GPU 루머/출시 정보
- [AnandTech](https://www.anandtech.com/)
- [Tom's Hardware](https://www.tomshardware.com/)

**수동 수집 (정확도 높음):**

```json
{
  "version": "1.0.0",
  "updated_at": "2024-12-31",
  "events": [
    {
      "type": "release",
      "category": "gpu",
      "brand": "NVIDIA",
      "product": "RTX 5090",
      "date": "2025-01-15",
      "confirmed": false,
      "source": "VideoCardz rumor",
      "impact": {
        "affected_products": ["RTX 4090", "RTX 4080"],
        "expected_price_change": -10
      }
    },
    {
      "type": "discontinue",
      "category": "gpu",
      "brand": "NVIDIA", 
      "product": "RTX 3060",
      "date": "2024-06-30",
      "confirmed": true
    }
  ]
}
```

### 2.4 세일 이벤트 캘린더 (sale_events.json)

```json
{
  "version": "1.0.0",
  "recurring_events": [
    {
      "name": "Black Friday",
      "date_pattern": "11월 넷째주 금요일",
      "typical_discount": 15,
      "categories": ["all"]
    },
    {
      "name": "Cyber Monday",
      "date_pattern": "Black Friday 다음 월요일",
      "typical_discount": 12,
      "categories": ["all"]
    },
    {
      "name": "Prime Day",
      "date_pattern": "7월 중순 (Amazon 발표)",
      "typical_discount": 10,
      "categories": ["all"]
    },
    {
      "name": "쿠팡 로켓와우 위크",
      "date_pattern": "분기별",
      "typical_discount": 8,
      "categories": ["all"]
    },
    {
      "name": "설/추석 연휴",
      "date_pattern": "명절 2주 전",
      "typical_discount": 5,
      "categories": ["all"]
    }
  ],
  "2025_events": [
    {
      "name": "CES 2025",
      "start_date": "2025-01-07",
      "end_date": "2025-01-10",
      "impact": "신제품 발표로 인한 구형 가격 하락"
    }
  ]
}
```

---

## 3. 데이터 형식

### price_history/{category}/{product_id}.json

```json
{
  "product_id": "nvidia_rtx4070",
  "product_name": "NVIDIA GeForce RTX 4070",
  "category": "gpu",
  "danawa_code": "18657891",
  "history": [
    {
      "date": "2024-01-01",
      "price": 750000,
      "lowest_price": 745000,
      "source": "danawa",
      "note": null
    },
    {
      "date": "2024-01-02", 
      "price": 748000,
      "lowest_price": 743000,
      "source": "danawa",
      "note": null
    }
  ],
  "metadata": {
    "first_record": "2024-01-01",
    "last_record": "2024-12-31",
    "total_records": 365,
    "msrp": 720000
  }
}
```

### exchange_rates.json

```json
{
  "version": "1.0.0",
  "currency_pair": "USD/KRW",
  "source": "한국은행 ECOS",
  "history": [
    {"date": "2024-01-01", "rate": 1305.50},
    {"date": "2024-01-02", "rate": 1308.20}
  ]
}
```

---

## 4. 자동 수집 파이프라인

### 일일 수집 스크립트

```python
"""
backend/scripts/collect_prices.py
일일 가격 수집 자동화 스크립트

사용법:
    python backend/scripts/collect_prices.py --category gpu
    python backend/scripts/collect_prices.py --all

크론 설정 (매일 오전 9시):
    0 9 * * * cd /path/to/project && python backend/scripts/collect_prices.py --all
"""
import argparse
import json
from datetime import datetime
from pathlib import Path

# 수집 대상 제품 목록
PRODUCTS = {
    "gpu": {
        "nvidia_rtx4090": "18397651",
        "nvidia_rtx4080": "18484521",
        "nvidia_rtx4070_ti": "18657891",
        "nvidia_rtx4070": "18765432",
        "nvidia_rtx4060_ti": "19123456",
        "amd_rx7900_xtx": "18512345",
        "amd_rx7900_xt": "18523456",
        "amd_rx7800_xt": "18734567"
    },
    "cpu": {
        "intel_i9_14900k": "19234567",
        "intel_i7_14700k": "19345678",
        "intel_i5_14600k": "19456789",
        "amd_r9_7950x3d": "18456789",
        "amd_r7_7800x3d": "18567890",
        "amd_r5_7600x": "18678901"
    }
}

def collect_and_save(category: str):
    """카테고리별 가격 수집 및 저장"""
    collector = DanawaCollector(delay=2.0)
    
    data_dir = Path(f"backend/data/price_prediction/price_history/{category}")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    for product_name, danawa_code in PRODUCTS.get(category, {}).items():
        filepath = data_dir / f"{product_name}.json"
        
        # 기존 데이터 로드
        if filepath.exists():
            with open(filepath) as f:
                product_data = json.load(f)
        else:
            product_data = {
                "product_id": product_name,
                "category": category,
                "danawa_code": danawa_code,
                "history": []
            }
        
        # 새 가격 수집
        price_info = collector.get_product_price(danawa_code)
        if price_info:
            product_data['history'].append(price_info)
            
            # 저장
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(product_data, f, ensure_ascii=False, indent=2)
            
            print(f"[OK] {product_name}: {price_info['price']:,}원")
        else:
            print(f"[FAIL] {product_name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", choices=["gpu", "cpu", "memory", "storage"])
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    
    if args.all:
        for cat in PRODUCTS.keys():
            collect_and_save(cat)
    elif args.category:
        collect_and_save(args.category)
```

---

## 5. 데이터 요구량

### 모델 학습을 위한 최소 데이터

| 항목 | 최소량 | 권장량 |
|------|--------|--------|
| 가격 이력 기간 | 6개월 | 2년 |
| 제품 수 | 20개 | 100개+ |
| 환율 데이터 | 동일 기간 | 동일 기간 |

### 초기 시드 데이터

학습 데이터가 없는 경우, 규칙 기반 예측으로 시작:

```python
# 간단한 규칙 기반 예측 (데이터 수집 전)
def simple_price_prediction(current_price: int, days: int, event: str = None) -> int:
    """
    규칙 기반 간단 예측
    - 신제품 출시: -10~15%
    - 블랙프라이데이: -15%
    - 일반: ±3%
    """
    if event == "new_release":
        return int(current_price * 0.88)
    elif event == "black_friday":
        return int(current_price * 0.85)
    else:
        # 일반적으로 신제품 주기(1년) 동안 약 15% 하락
        daily_decline = 0.15 / 365
        return int(current_price * (1 - daily_decline * days))
```

---

## 담당자 체크리스트

- [ ] 다나와 제품 코드 매핑 완료 (GPU 10개, CPU 10개)
- [ ] 가격 수집 스크립트 작성 및 테스트
- [ ] 환율 API 연동 (무료 플랜)
- [ ] 1개월 이상 가격 이력 수집
- [ ] 세일 이벤트 캘린더 작성
- [ ] 자동 수집 크론 설정
- [ ] 데이터 검증 및 이상치 제거
