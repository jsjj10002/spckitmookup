"""
멀티 에이전트 파이프라인 단계별 실행 데모
==========================================

가상의 쿼리를 입력하여 각 에이전트 단계별 처리 과정을 시각적으로 확인.

실행 방법:
```bash
cd backend
uv run python tests/demo_multi_agent_pipeline.py
```
"""

import json
import time
from typing import Dict, Any
from unittest.mock import MagicMock, patch
from colorama import init, Fore, Style, Back

# colorama 초기화 (Windows 터미널 색상 지원)
init()


# ============================================================================
# 시뮬레이션 데이터: 각 에이전트의 예상 출력
# ============================================================================

DEMO_QUERY = "150만원으로 배그 풀옵 가능한 게임용 PC 만들어줘"

SIMULATED_OUTPUTS = {
    "requirement_analyzer": {
        "description": "사용자 요청에서 핵심 요구사항 추출",
        "output": {
            "budget": 1500000,
            "purpose": "gaming",
            "target_games": ["PUBG (배틀그라운드)"],
            "performance_target": "최고 옵션 (Ultra)",
            "preferences": {
                "priority": "GPU 성능 우선",
                "brand_preference": None
            }
        }
    },
    "budget_planner": {
        "description": "예산 분배 계획 수립",
        "output": {
            "total_budget": 1500000,
            "allocation": {
                "GPU": {"amount": 555000, "ratio": "37%", "reason": "게임용 최우선"},
                "CPU": {"amount": 345000, "ratio": "23%", "reason": "게임 성능 보조"},
                "Motherboard": {"amount": 150000, "ratio": "10%", "reason": "안정적인 플랫폼"},
                "Memory": {"amount": 135000, "ratio": "9%", "reason": "16GB 이상 권장"},
                "Storage": {"amount": 165000, "ratio": "11%", "reason": "NVMe SSD 필수"},
                "PSU": {"amount": 75000, "ratio": "5%", "reason": "안정적인 전원"},
                "Case": {"amount": 75000, "ratio": "5%", "reason": "쿨링 고려"}
            }
        }
    },
    "component_selector": {
        "description": "RAG 검색을 통한 최적 부품 선정",
        "output": {
            "selected_components": [
                {
                    "category": "GPU",
                    "name": "NVIDIA GeForce RTX 4060 Ti 8GB",
                    "price": 549000,
                    "specs": {"VRAM": "8GB GDDR6", "TDP": "160W"},
                    "search_query": "RTX 4060 Ti 50만원대"
                },
                {
                    "category": "CPU",
                    "name": "Intel Core i5-13400F",
                    "price": 239000,
                    "specs": {"Cores": "10C/16T", "Socket": "LGA1700"},
                    "search_query": "인텔 i5 게이밍 CPU"
                },
                {
                    "category": "Motherboard",
                    "name": "ASUS PRIME B760M-A",
                    "price": 159000,
                    "specs": {"Socket": "LGA1700", "Form": "M-ATX"},
                    "search_query": "B760 메인보드"
                },
                {
                    "category": "Memory",
                    "name": "Samsung DDR5-5600 16GB x2",
                    "price": 139000,
                    "specs": {"Capacity": "32GB", "Speed": "5600MHz"},
                    "search_query": "DDR5 32GB 램"
                },
                {
                    "category": "Storage",
                    "name": "Samsung 990 EVO 1TB",
                    "price": 129000,
                    "specs": {"Interface": "NVMe PCIe 5.0", "Read": "5000MB/s"},
                    "search_query": "NVMe SSD 1TB"
                },
                {
                    "category": "PSU",
                    "name": "Seasonic Focus GX-650",
                    "price": 99000,
                    "specs": {"Wattage": "650W", "Efficiency": "80+ Gold"},
                    "search_query": "650W 80+ 파워"
                },
                {
                    "category": "Case",
                    "name": "NZXT H5 Flow",
                    "price": 89000,
                    "specs": {"Form": "Mid Tower", "Airflow": "Mesh Front"},
                    "search_query": "미들타워 케이스"
                }
            ]
        }
    },
    "compatibility_checker": {
        "description": "선정된 부품 간 호환성 검증",
        "output": {
            "overall_status": "PASS",
            "checks": [
                {"check": "CPU-Motherboard Socket", "status": "✓ PASS", "detail": "LGA1700 호환"},
                {"check": "Memory-Motherboard", "status": "✓ PASS", "detail": "DDR5 지원 확인"},
                {"check": "GPU-Case Clearance", "status": "✓ PASS", "detail": "최대 365mm, GPU 240mm"},
                {"check": "PSU Wattage", "status": "✓ PASS", "detail": "예상 소비전력 450W, 여유 200W"},
                {"check": "Storage Interface", "status": "✓ PASS", "detail": "M.2 NVMe 슬롯 지원"}
            ],
            "warnings": [],
            "recommendations": ["추후 GPU 업그레이드 시 750W 파워 권장"]
        }
    },
    "recommendation_writer": {
        "description": "최종 견적서 작성",
        "output": {
            "title": "🎮 게임용 PC 견적서 - 배그 풀옵 사양",
            "summary": "PUBG 최고 옵션 60FPS 이상 구동 가능한 가성비 게이밍 PC",
            "components": [
                {"category": "GPU", "name": "RTX 4060 Ti 8GB", "price": 549000},
                {"category": "CPU", "name": "i5-13400F", "price": 239000},
                {"category": "Motherboard", "name": "ASUS B760M-A", "price": 159000},
                {"category": "Memory", "name": "DDR5 32GB", "price": 139000},
                {"category": "Storage", "name": "990 EVO 1TB", "price": 129000},
                {"category": "PSU", "name": "650W Gold", "price": 99000},
                {"category": "Case", "name": "NZXT H5", "price": 89000}
            ],
            "total_price": 1403000,
            "remaining_budget": 97000,
            "performance_estimate": {
                "PUBG_Ultra_FHD": "80-100 FPS",
                "PUBG_Ultra_QHD": "50-70 FPS"
            }
        }
    }
}


# ============================================================================
# 출력 헬퍼 함수
# ============================================================================

def print_header(text: str):
    """섹션 헤더 출력"""
    print(f"\n{Back.BLUE}{Fore.WHITE} {text} {Style.RESET_ALL}")
    print("=" * 70)

def print_agent_start(agent_name: str, description: str):
    """에이전트 시작 로그"""
    print(f"\n{Fore.CYAN}▶ [{agent_name}]{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}목표:{Style.RESET_ALL} {description}")
    print(f"  {Fore.GREEN}처리 중...{Style.RESET_ALL}", end="", flush=True)

def print_agent_complete(duration: float):
    """에이전트 완료 로그"""
    print(f" {Fore.GREEN}완료! ({duration:.2f}초){Style.RESET_ALL}")

def print_output(data: Dict[str, Any], indent: int = 2):
    """출력 데이터를 보기 좋게 출력"""
    formatted = json.dumps(data, indent=2, ensure_ascii=False)
    for line in formatted.split('\n'):
        print(" " * indent + Fore.WHITE + line + Style.RESET_ALL)


def simulate_agent_execution(agent_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """에이전트 실행 시뮬레이션"""
    print_agent_start(agent_name, data["description"])
    
    # 처리 시간 시뮬레이션 (0.5~1.5초)
    duration = 0.5 + (hash(agent_name) % 10) / 10
    time.sleep(duration)
    
    print_agent_complete(duration)
    
    print(f"  {Fore.MAGENTA}출력:{Style.RESET_ALL}")
    print_output(data["output"], indent=4)
    
    return data["output"]


# ============================================================================
# 메인 데모 실행
# ============================================================================

def run_demo():
    """멀티 에이전트 파이프라인 데모 실행"""
    
    print_header("멀티 에이전트 PC 추천 파이프라인 데모")
    
    print(f"\n{Fore.YELLOW}═══ 사용자 쿼리 ═══{Style.RESET_ALL}")
    print(f'  "{DEMO_QUERY}"')
    
    print(f"\n{Fore.CYAN}파이프라인 시작...{Style.RESET_ALL}")
    print("-" * 70)
    
    start_time = time.time()
    
    # 1단계: 요구사항 분석
    step1 = simulate_agent_execution("RequirementAnalyzerAgent", SIMULATED_OUTPUTS["requirement_analyzer"])
    
    # 2단계: 예산 분배
    step2 = simulate_agent_execution("BudgetPlannerAgent", SIMULATED_OUTPUTS["budget_planner"])
    
    # 3단계: 부품 선택
    step3 = simulate_agent_execution("ComponentSelectorAgent", SIMULATED_OUTPUTS["component_selector"])
    
    # 4단계: 호환성 검증
    step4 = simulate_agent_execution("CompatibilityCheckerAgent", SIMULATED_OUTPUTS["compatibility_checker"])
    
    # 5단계: 최종 견적서 작성
    step5 = simulate_agent_execution("RecommendationWriterAgent", SIMULATED_OUTPUTS["recommendation_writer"])
    
    total_time = time.time() - start_time
    
    # 최종 결과 요약
    print_header("파이프라인 완료")
    
    print(f"\n{Fore.GREEN}✓ 총 처리 시간: {total_time:.2f}초{Style.RESET_ALL}")
    print(f"{Fore.GREEN}✓ 처리된 에이전트: 5개{Style.RESET_ALL}")
    
    final = step5
    print(f"\n{Fore.YELLOW}═══ 최종 견적 요약 ═══{Style.RESET_ALL}")
    print(f"  제목: {final['title']}")
    print(f"  총 가격: {final['total_price']:,}원")
    print(f"  예산 잔액: {final['remaining_budget']:,}원")
    print(f"\n  {Fore.CYAN}부품 목록:{Style.RESET_ALL}")
    for comp in final['components']:
        print(f"    - {comp['category']}: {comp['name']} ({comp['price']:,}원)")
    
    print(f"\n  {Fore.CYAN}예상 성능:{Style.RESET_ALL}")
    for game, fps in final['performance_estimate'].items():
        print(f"    - {game}: {fps}")
    
    print("\n" + "=" * 70)
    print(f"{Fore.GREEN}데모 완료!{Style.RESET_ALL}\n")


if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}데모가 중단되었습니다.{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}오류 발생: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
