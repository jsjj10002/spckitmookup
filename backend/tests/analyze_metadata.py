"""
Vector DB 메타데이터 구조 분석 스크립트
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.pipeline import RAGPipeline

def analyze_metadata():
    print("=" * 60)
    print(" Vector DB 메타데이터 분석")
    print("=" * 60)
    
    pipeline = RAGPipeline()
    collection = pipeline.vector_store.collection
    
    # 카테고리별 샘플 데이터 조회
    categories = ["cpu", "motherboard", "memory", "gpu"]
    
    for category in categories:
        print(f"\n[{category.upper()}] 샘플 데이터:")
        print("-" * 40)
        
        try:
            results = collection.get(
                where={"category": category},
                limit=3,
                include=["metadatas", "documents"]
            )
            
            if results and results["metadatas"]:
                for i, meta in enumerate(results["metadatas"]):
                    print(f"\n  샘플 {i+1}:")
                    print(f"    - name: {meta.get('name', 'N/A')}")
                    print(f"    - price: {meta.get('price', 'N/A')}")
                    print(f"    - socket: {meta.get('socket', 'N/A')}")
                    print(f"    - memory_type: {meta.get('memory_type', 'N/A')}")
                    print(f"    - form_factor: {meta.get('form_factor', 'N/A')}")
                    print(f"    - tdp: {meta.get('tdp', 'N/A')}")
                    
                    # 모든 키 출력
                    all_keys = list(meta.keys())
                    print(f"    - 전체 필드: {all_keys}")
            else:
                print(f"  (데이터 없음)")
                
        except Exception as e:
            print(f"  오류: {e}")
    
    print("\n" + "=" * 60)
    print(" 분석 완료")
    print("=" * 60)

if __name__ == "__main__":
    analyze_metadata()
