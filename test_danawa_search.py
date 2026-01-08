
import requests
from bs4 import BeautifulSoup
import re
import time

def search_danawa_price(product_name):
    print(f"Searching for: {product_name}")
    url = f"https://search.danawa.com/dsearch.php?k1={product_name}&module=goods&act=dispMain"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://www.danawa.com/"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            print(f"Failed to fetch page: {response.status_code}")
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 상품 리스트 가져오기 (첫 번째 결과)
        # product_list = soup.select('.product_list > .prod_item')
        # 다나와 검색 결과 구조는 자주 바뀔 수 있으므로 여러 선택자 시도
        
        # 일반적인 리스트 아이템
        items = soup.select('.prod_item')
        
        for item in items:
            # 광고 상품 제외 (ad_link 클래스 등 확인)
            if 'prod_ad_item' in item.get('class', []):
                continue
                
            # 제품명
            name_elem = item.select_one('.prod_name > a')
            if not name_elem:
                continue
                
            name = name_elem.get_text().strip()
            
            # 가격
            price_elem = item.select_one('.price_sect > a > strong')
            if not price_elem:
                continue
                
            price_str = price_elem.get_text().strip().replace(",", "")
            
            print(f"Found: {name} - {price_str} won")
            
            if price_str.isdigit():
                return int(price_str)
                
        print("No valid price found in search results.")
        return None
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    # 테스트 케이스
    products = [
        "AMD Ryzen 7 7800X3D",
        "GeForce RTX 4070 Ti",
        "Shure SM7B" # PC 부품 아닌 것도 테스트
    ]
    
    for p in products:
        price = search_danawa_price(p)
        print(f"Result: {price}")
        print("-" * 30)
        time.sleep(1)
