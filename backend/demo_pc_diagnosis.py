import sys
import os

# 백엔드 모듈 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.pc_diagnosis.engine import PCDiagnosisEngine
from modules.pc_diagnosis.analyzers import UpgradeAdvisor

def print_section(title):
    print(f"\n{'='*50}")
    print(f" {title}")
    print(f"{'='*50}")

def run_demo():
    print_section("PC 진단 모듈 데모 시작")

    # 1. 진단 엔진 초기화
    engine = PCDiagnosisEngine()
    
    # 2. 테스트 케이스: CPU 병목이 예상되는 PC
    # i3-10100F (구형 보급형) + RTX 4070 (최신 고성능)
    user_specs = {
        "cpu": {
            "name": "i3-10100F",  # 벤치마크 점수 낮음
            "cores": 4,
            "threads": 8
        },
        "gpu": {
            "name": "RTX 4070",   # 벤치마크 점수 높음 (62점)
            "vram": 12,
            "memory_type": "GDDR6X"
        },
        "memory": {
            "capacity": 16,
            "speed": 2666,
            "generation": "DDR4"
        },
        "storage": {
            "type": "SSD",
            "capacity": 500,
            "read_speed": 500
        },
        "usage_purpose": "gaming"
    }

    print(">> 분석 대상 PC 스펙:")
    print(f"   CPU: {user_specs['cpu']['name']}")
    print(f"   GPU: {user_specs['gpu']['name']}")
    print(f"   RAM: {user_specs['memory']['capacity']}GB")
    
    # 3. 진단 수행
    result = engine.diagnose(user_specs)

    print_section("진단 결과 리포트")
    print(f"종합 점수: {result.overall_score}점")
    print(f"성능 등급: {result.tier.value}")
    
    print(f"\n[병목 분석]")
    if result.bottleneck.type != "none":
        print(f"[!] 발견됨: {result.bottleneck.type.upper()} 병목")
        print(f"   심각도: {result.bottleneck.severity}/100")
        print(f"   설명: {result.bottleneck.description}")
    else:
        print("[OK] 병목 없음 (밸런스 양호)")

    print(f"\n[부품별 성능 점수]")
    for comp, data in result.component_scores.items():
        print(f"   - {comp.upper()}: {data.score}점 ({data.tier.value})")

    print_section("업그레이드 추천")
    for idx, rec in enumerate(result.upgrade_recommendations, 1):
        print(f"{idx}. {rec.component.upper()} 업그레이드 (우선순위: {rec.priority})")
        print(f"   현재: {rec.current} -> 추천: {rec.recommended}")
        print(f"   예상 비용: {rec.estimated_cost:,}원")
        print("-" * 30)

    # 4. 예산별 견적 추천 테스트
    print_section("예산별 추천 견적 (Budget Builds)")
    advisor = UpgradeAdvisor()
    
    budgets = [900000, 1400000, 3000000] # 90만원, 140만원, 300만원
    
    for budget in budgets:
        print(f"\n>>> 예산 {budget:,}원일 때 추천 견적:")
        builds = advisor.get_budget_builds(budget)
        
        if not builds:
            print("   해당 예산에 맞는 추천 견적이 없습니다.")
            continue
            
        for build in builds:
            print(f"   [{build['name']}]")
            print(f"   가격대: {build['price_range'][0]:,} ~ {build['price_range'][1]:,}원")
            print(f"   CPU: {build['components']['cpu']}")
            print(f"   GPU: {build['components']['gpu']}")
            print("")

if __name__ == "__main__":
    run_demo()
