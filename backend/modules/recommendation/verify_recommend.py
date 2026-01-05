import sys
import os
from backend.modules.recommendation.engine import GNNRecommendationEngine

def run_test(engine, title, selected, target):
    print(f"\n[시나리오] {title}")
    result = engine.recommend(selected_components=selected, target_category=target, top_k=3)
    
    if hasattr(result, 'recommendations'):
        recs = result.recommendations
    else: # 리스트 형식으로 반환될 경우 대응
        recs = result

    for r in recs:
        # 클래스 속성 또는 딕셔너리 대응
        name = getattr(r, 'name', r.get('name') if isinstance(r, dict) else "Unknown")
        score = getattr(r, 'scores', None)
        score_val = getattr(score, 'relevance', r.get('score') if isinstance(r, dict) else 0.0)
        print(f"  {getattr(r, 'rank', 0)}위: {name} (점수: {score_val:.4f})")

def verify():
    engine = GNNRecommendationEngine()
    print("=== GNN 추천 엔진 10대 시나리오 집중 검증 ===")

    # 1. 고사양 게임 (GPU 중심)
    run_test(engine, "RTX 4090 + i9-13900K 조합 시 파워(PSU) 추천", 
             [{"category": "gpu", "name": "GeForce RTX 4090"}, {"category": "cpu", "name": "Intel Core i9 13900K"}], "psu")

    # 2. 인텔 최신 메인스트림
    run_test(engine, "i5-14400F 선택 시 메인보드 추천", 
             [{"category": "cpu", "name": "Intel Core i5 14400F"}], "motherboard")

    # 3. AMD 가성비 작업용
    run_test(engine, "Ryzen 5 5600 선택 시 메인보드 추천", 
             [{"category": "cpu", "name": "AMD Ryzen 5 5600"}], "motherboard")

    # 4. 워크스테이션급 (Threadripper)
    run_test(engine, "Threadripper 2920X 선택 시 메인보드 추천", 
             [{"category": "cpu", "name": "AMD Threadripper 2920X"}], "motherboard")

    # 5. 초저가 사무용
    run_test(engine, "i3-9100 선택 시 메인보드 추천", 
             [{"category": "cpu", "name": "Intel Core i3 9100"}], "motherboard")

    # 6. 하이엔드 쿨링 (CPU 기반)
    run_test(engine, "i9-13900K 선택 시 CPU 쿨러 추천", 
             [{"category": "cpu", "name": "Intel Core i9 13900K"}], "cpucooler")

    # 7. 그래픽 중심 가성비
    run_test(engine, "RTX 3060 선택 시 파워(PSU) 추천", 
             [{"category": "gpu", "name": "GeForce RTX 3060"}], "psu")

    # 8. DDR4 메모리 기반 빌드
    run_test(engine, "i5-12600KF 선택 시 RAM 추천", 
             [{"category": "cpu", "name": "Intel Core i5 12600KF"}], "memory")

    # 9. 구형 시스템 업그레이드 (LGA1150)
    run_test(engine, "Xeon E3-1270 V3 선택 시 메인보드 추천", 
             [{"category": "cpu", "name": "Intel Xeon E3 1270 V3"}], "motherboard")

    # 10. 고성능 NVMe 저장장치
    run_test(engine, "Z790 메인보드 선택 시 SSD 추천", 
             [{"category": "motherboard", "name": "Z790"}], "internal-hard-drive")

if __name__ == "__main__":
    verify()