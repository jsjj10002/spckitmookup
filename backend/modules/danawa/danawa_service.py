"""
다나와 데이터 서비스 모듈
========================

[목표]
------
다나와 크롤링 데이터(CSV)에서 가격 정보를 조회하고,
다나와 제품 페이지 URL을 생성하는 서비스.

[주요 기능]
----------
1. CSV 파일에서 최신 가격 조회
2. 제품명 또는 ID로 제품 검색
3. 다나와 제품 페이지 URL 생성

[사용법]
-------
```python
from modules.danawa import DanawaService

service = DanawaService()
price = service.get_latest_price("18170813", "cpu")
url = service.get_danawa_url("18170813")
```
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import csv
import re
from loguru import logger
from functools import lru_cache
import requests
from bs4 import BeautifulSoup


# ============================================================================
# 상수 정의
# ============================================================================

# 다나와 제품 페이지 URL 템플릿
DANAWA_PRODUCT_URL_TEMPLATE = "https://prod.danawa.com/info/?pcode={product_id}"

# CSV 파일명과 시스템 카테고리 매핑
CATEGORY_CSV_MAP = {
    "cpu": "CPU.csv",
    "gpu": "VGA.csv",
    "memory": "RAM.csv",
    "motherboard": "MBoard.csv",
    "storage": "SSD.csv",
    "psu": "Power.csv",
    "case": "Case.csv",
    "cooler": "Cooler.csv",
}

# 가격 파싱 우선순위 (정품 우선)
PRICE_TYPE_PRIORITY = ["정품", "멀티팩 정품", "멀티팩(정품)", "벌크", "unknown", "중고", "해외구매"]


# ============================================================================
# 다나와 데이터 서비스
# ============================================================================

class DanawaService:
    """
    다나와 가격 데이터 조회 서비스
    
    CSV 파일에서 제품 가격 정보를 조회하고,
    다나와 제품 페이지 URL을 생성합니다.
    
    Args:
        data_dir (Path | str | None): CSV 데이터 디렉토리 경로.
            None이면 기본 경로(backend/data) 사용.
    
    사용 예:
        service = DanawaService()
        
        # 가격 조회
        price = service.get_latest_price("18170813", "cpu")
        print(f"가격: {price:,}원")
        
        # 다나와 URL 생성
        url = service.get_danawa_url("18170813")
        print(f"URL: {url}")
        
        # 제품명으로 검색
        product = service.find_product_by_name("AMD 라이젠", "cpu")
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Args:
            data_dir: CSV 데이터 디렉토리 경로 (기본값: backend/data)
        """
        if data_dir is None:
            # 기본 경로: backend/data
            self.data_dir = Path(__file__).parent.parent.parent / "data"
        else:
            self.data_dir = Path(data_dir)
        
        # 카테고리별 데이터 캐시
        self._cache: Dict[str, List[Dict[str, Any]]] = {}
        
        logger.info(f"DanawaService 초기화 완료. 데이터 디렉토리: {self.data_dir}")
    
    def get_danawa_url(self, product_id: str) -> str:
        """
        다나와 제품 페이지 URL 생성
        
        Args:
            product_id: 다나와 제품 ID
            
        Returns:
            str: 다나와 제품 페이지 URL
        """
        return DANAWA_PRODUCT_URL_TEMPLATE.format(product_id=product_id)

    def fetch_product_image_url(self, product_id: str) -> Optional[str]:
        """
        제품 상세 페이지에서 이미지 URL 크롤링
        """
        if not product_id:
            return None
            
        try:
            url = self.get_danawa_url(product_id)
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Referer": "https://www.danawa.com/"
            }
            response = requests.get(url, headers=headers, timeout=2)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            # ID가 baseImage인 이미지 태그 찾기
            img = soup.select_one('#baseImage')
            if img:
                return img.get('src')
                
            # 없을 경우 meta tag 시도
            meta_img = soup.select_one('meta[property="og:image"]')
            if meta_img:
                return meta_img.get('content')
                
            return None
        except Exception as e:
            logger.warning(f"이미지 크롤링 실패 ({product_id}): {e}")
            return None
    
    def get_latest_price(self, product_id: str, category: str) -> Optional[int]:
        """
        제품의 최신 가격 조회
        
        Args:
            product_id: 다나와 제품 ID
            category: 제품 카테고리 (cpu, gpu, memory 등)
            
        Returns:
            int | None: 가격 (원) 또는 None (찾을 수 없는 경우)
        """
        data = self._load_category_data(category)
        if not data:
            return None
        
        for product in data:
            if str(product.get("id")) == str(product_id):
                return product.get("latest_price")
        
        return None
    
    def find_product_by_name(
        self, 
        name: str, 
        category: str,
        exact_match: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        제품명으로 제품 검색
        
        Args:
            name: 검색할 제품명 (부분 일치)
            category: 제품 카테고리
            exact_match: True이면 정확히 일치하는 제품만 검색
            
        Returns:
            dict | None: 제품 정보 또는 None
        """
        data = self._load_category_data(category)
        if not data:
            return None
        
        for product in data:
            product_name = product.get("name", "")
            if exact_match:
                if product_name == name:
                    return product
            else:
                if name.lower() in product_name.lower():
                    return product
        
        return None
    
    def find_product_by_fuzzy_name(
        self, 
        name: str, 
        category: str
    ) -> Optional[Dict[str, Any]]:
        """
        제품명으로 유사도 기반 제품 검색 (fuzzy matching)
        
        모델명에서 핵심 키워드(숫자, 모델코드)를 추출하여 매칭
        
        Args:
            name: 검색할 제품명
            category: 제품 카테고리
            
        Returns:
            dict | None: 가장 유사한 제품 정보 또는 None
        """
        data = self._load_category_data(category)
        if not data:
            return None
        
        # 핵심 키워드 추출 (모델 번호 등)
        keywords = self._extract_model_keywords(name)
        if not keywords:
            return None
        
        best_match = None
        best_score = 0
        
        for product in data:
            product_name = product.get("name", "")
            score = self._calculate_match_score(keywords, product_name)
            
            if score > best_score:
                best_score = score
                best_match = product
        
        # 최소 매칭 점수 기준 (숫자 키워드 1개 이상 매칭)
        if best_score >= 2 and best_match:
            logger.debug(f"Fuzzy match: '{name}' -> '{best_match.get('name')}' (score={best_score})")
            return best_match
        
        return None
    
    def get_price_by_name(self, name: str, category: str) -> Optional[int]:
        """
        제품명으로 가격 조회 (유사도 기반 매칭)
        
        Args:
            name: 검색할 제품명
            category: 제품 카테고리
            
        Returns:
            int | None: 가격 또는 None
        """
        product = self.find_product_by_fuzzy_name(name, category)
        if product:
            return product.get("latest_price")
        return None
    
    def get_product_by_name_with_url(self, name: str, category: str) -> Optional[Dict[str, Any]]:
        """
        제품명으로 제품 정보 조회 (URL 포함)
        
        Args:
            name: 검색할 제품명
            category: 제품 카테고리
            
        Returns:
            dict | None: {id, name, price, danawa_url}
        """
        # 1. Fuzzy match from CSV (Fast)
        product = self.find_product_by_fuzzy_name(name, category)
        if product:
            p_id = str(product.get("id"))
            # 이미지 URL 크롤링 (약간의 지연 발생 가능)
            image_url = self.fetch_product_image_url(p_id)
            
            return {
                "id": product.get("id"),
                "name": product.get("name"),
                "price": product.get("latest_price"),
                "danawa_url": self.get_danawa_url(p_id),
                "image_url": image_url
            }
            
        # 2. Web Search (Slow, Fallback)
        # CSV에 없는 경우에만 실행
        try:
            web_info = self.fetch_price_from_web(name)
            if web_info:
                return {
                    "id": None, # ID 없음
                    "name": name,
                    "price": web_info.get("price"),
                    "image_url": web_info.get("image_url"),
                    "danawa_url": f"https://search.danawa.com/dsearch.php?k1={name}",
                }
        except Exception as e:
            logger.warning(f"Web search fallback failed for '{name}': {e}")
            
        return None
    
    def fetch_price_from_web(self, product_name: str) -> Optional[Dict[str, Any]]:
        """
        다나와 웹 검색을 통한 가격 및 이미지 조회 (Fallback)
        Returns: {price: int, image_url: str}
        """
        try:
            url = f"https://search.danawa.com/dsearch.php?k1={product_name}&module=goods&act=dispMain"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Referer": "https://www.danawa.com/"
            }
            # 타임아웃 2초로 설정하여 응답 지연 방지
            response = requests.get(url, headers=headers, timeout=2)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.select('.prod_item')
            
            for item in items:
                # 광고 상품 제외
                if 'prod_ad_item' in item.get('class', []):
                    continue
                    
                # 가격 정보 추출
                price_elem = item.select_one('.price_sect > a > strong')
                if not price_elem:
                    continue
                
                price_str = price_elem.get_text().strip().replace(",", "")
                if price_str.isdigit():
                    price = int(price_str)
                    # 비정상적으로 낮은 가격(액세서리 등) 필터링
                    if price > 5000:
                        # 이미지 추출
                        image_url = None
                        img_elem = item.select_one('.thumb_image img')
                        if img_elem:
                            image_url = img_elem.get('src') or img_elem.get('data-original')
                            if image_url and image_url.startswith('//'):
                                image_url = 'https:' + image_url
                        
                        return {
                            "price": price,
                            "image_url": image_url
                        }
                    
            return None
        except Exception as e:
            logger.warning(f"Web search failed for {product_name}: {e}")
            return None
    
    def _extract_model_keywords(self, name: str) -> List[str]:
        """
        제품명에서 모델 식별 키워드 추출
        
        예: "AMD Ryzen 7 9700X 3.8 GHz" -> ["amd", "ryzen", "7", "9700x"]
        """
        # 소문자로 변환하고 특수문자 제거
        cleaned = re.sub(r'[^\w\s]', ' ', name)
        words = cleaned.split()
        
        keywords = []
        for word in words:
            word = word.lower().strip()
            if not word:
                continue
            # 단위 등 제외 (GHz, MHz, GB, Core 등)
            if word in ['ghz', 'mhz', 'gb', 'mb', 'tb', 'core', 'w', 'nm']:
                continue
            # 순수 숫자이고 작은 값이면 제외 (코어 수, 클럭 수 등) 
            if word.isdigit() and int(word) < 100:
                continue
            keywords.append(word)
        
        return keywords
    
    def _calculate_match_score(self, keywords: List[str], product_name: str) -> float:
        """
        키워드와 제품명 간의 매칭 점수 계산
        """
        product_name_lower = product_name.lower()
        score = 0
        
        for keyword in keywords:
            if keyword in product_name_lower:
                # 모델 번호(숫자 포함)에 더 높은 가중치
                if any(c.isdigit() for c in keyword):
                    score += 2
                else:
                    score += 1
        
        return score

    def get_product_info(self, product_id: str, category: str) -> Optional[Dict[str, Any]]:
        """
        제품 ID로 전체 정보 조회
        
        Args:
            product_id: 다나와 제품 ID
            category: 제품 카테고리
            
        Returns:
            dict | None: 제품 정보 (id, name, latest_price, danawa_url)
        """
        data = self._load_category_data(category)
        if not data:
            return None
        
        for product in data:
            if str(product.get("id")) == str(product_id):
                # 이미지 URL 크롤링
                image_url = self.fetch_product_image_url(str(product.get("id")))

                return {
                    "id": product.get("id"),
                    "name": product.get("name"),
                    "latest_price": product.get("latest_price"),
                    "danawa_url": self.get_danawa_url(str(product.get("id"))),
                    "image_url": image_url
                }
        
        return None
    
    def search_products(
        self, 
        query: str, 
        category: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        제품 검색 (여러 결과 반환)
        
        Args:
            query: 검색 쿼리 (제품명 부분 일치)
            category: 제품 카테고리
            limit: 최대 결과 수
            
        Returns:
            list: 제품 정보 리스트
        """
        data = self._load_category_data(category)
        if not data:
            return []
        
        results = []
        query_lower = query.lower()
        
        for product in data:
            product_name = product.get("name", "")
            if query_lower in product_name.lower():
                results.append({
                    "id": product.get("id"),
                    "name": product_name,
                    "latest_price": product.get("latest_price"),
                    "danawa_url": self.get_danawa_url(str(product.get("id"))),
                })
                
                if len(results) >= limit:
                    break
        
        return results
    
    def _load_category_data(self, category: str) -> List[Dict[str, Any]]:
        """
        카테고리별 CSV 데이터 로드 (캐싱 적용)
        
        Args:
            category: 제품 카테고리
            
        Returns:
            list: 제품 데이터 리스트
        """
        # 캐시 확인
        if category in self._cache:
            return self._cache[category]
        
        # CSV 파일 경로 확인
        csv_filename = CATEGORY_CSV_MAP.get(category.lower())
        if not csv_filename:
            logger.warning(f"알 수 없는 카테고리: {category}")
            return []
        
        csv_path = self.data_dir / csv_filename
        if not csv_path.exists():
            logger.warning(f"CSV 파일을 찾을 수 없음: {csv_path}")
            return []
        
        # CSV 파일 로드
        try:
            products = self._parse_csv(csv_path)
            self._cache[category] = products
            logger.info(f"카테고리 '{category}' 데이터 로드 완료: {len(products)}개 제품")
            return products
        except Exception as e:
            logger.error(f"CSV 파일 로드 실패: {csv_path}, 오류: {e}")
            return []
    
    def _parse_csv(self, csv_path: Path) -> List[Dict[str, Any]]:
        """
        CSV 파일 파싱
        
        Args:
            csv_path: CSV 파일 경로
            
        Returns:
            list: 파싱된 제품 데이터 리스트
        """
        products = []
        
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header = next(reader)
            
            # 헤더에서 날짜 컬럼 추출 (최신 날짜가 마지막)
            date_columns = header[2:]  # Id, Name 이후의 컬럼들
            
            for row in reader:
                if not row or len(row) < 2:
                    continue
                
                product_id = row[0].strip()
                product_name = row[1].strip()
                
                # 최신 가격 추출 (마지막 날짜 컬럼부터 역순으로 검색)
                latest_price = None
                for i in range(len(row) - 1, 1, -1):
                    if i < len(row):
                        price = self._parse_price(row[i])
                        if price is not None and price > 0:
                            latest_price = price
                            break
                
                products.append({
                    "id": product_id,
                    "name": product_name,
                    "latest_price": latest_price,
                })
        
        return products
    
    def _parse_price(self, price_str: str) -> Optional[int]:
        """
        복잡한 가격 문자열에서 대표 가격 파싱
        
        가격 형식 예시:
        - "멀티팩 정품_860,180"
        - "_정품_2,900,000|_멀티팩 정품_2,006,050"
        - "0"
        - "중고_14,250"
        - "123,456" (단순 숫자)
        
        Args:
            price_str: 가격 문자열
            
        Returns:
            int | None: 파싱된 가격 또는 None
        """
        if not price_str or price_str.strip() == "0":
            return None
        
        price_str = price_str.strip()
        
        # 가격비교예정 등 비가격 문자열 처리
        if "가격비교" in price_str or not any(c.isdigit() for c in price_str):
            return None
        
        prices = {}
        
        # 여러 가격이 | 로 구분된 경우 분리
        parts = price_str.split("|")
        
        for part in parts:
            part = part.strip()
            
            # 패턴 1: "유형_가격" 또는 "_유형_가격" 형식
            # 예: "멀티팩 정품_860,180", "_정품_2,900,000"
            # 마지막 언더스코어 전까지가 유형, 이후가 가격
            if "_" in part:
                # 마지막 언더스코어를 기준으로 분리
                last_underscore_idx = part.rfind("_")
                price_type = part[:last_underscore_idx].strip().lstrip("_")
                price_val_str = part[last_underscore_idx + 1:].replace(",", "")
                
                if price_val_str.isdigit() and int(price_val_str) > 0:
                    if not price_type:
                        price_type = "unknown"
                    prices[price_type] = int(price_val_str)
            else:
                # 패턴 2: 단순 숫자만 있는 경우 (예: "123,456")
                cleaned = re.sub(r"[^\d]", "", part)
                if cleaned and int(cleaned) > 0:
                    prices["unknown"] = int(cleaned)
        
        # 우선순위에 따라 가격 선택
        for p_type in PRICE_TYPE_PRIORITY:
            if p_type in prices:
                return prices[p_type]
        
        # 우선순위에 없으면 첫 번째 가격 반환
        return list(prices.values())[0] if prices else None
    
    def clear_cache(self):
        """캐시 초기화"""
        self._cache.clear()
        logger.info("DanawaService 캐시 초기화 완료")


# ============================================================================
# 모듈 테스트
# ============================================================================

if __name__ == "__main__":
    # 서비스 초기화 및 테스트
    service = DanawaService()
    
    # CPU 가격 조회 테스트
    print("=== CPU 가격 조회 테스트 ===")
    test_id = "18170813"  # AMD A4 7300
    price = service.get_latest_price(test_id, "cpu")
    url = service.get_danawa_url(test_id)
    print(f"제품 ID: {test_id}")
    print(f"가격: {price:,}원" if price else "가격 정보 없음")
    print(f"다나와 URL: {url}")
    
    # 제품 검색 테스트
    print("\n=== 제품 검색 테스트 ===")
    results = service.search_products("라이젠", "cpu", limit=5)
    for product in results:
        print(f"- {product['name']}: {product['latest_price']:,}원" if product['latest_price'] else f"- {product['name']}: 가격 없음")
