"""
병목 분석기 및 업그레이드 조언 모듈
===================================

[목표]
------
1. BottleneckAnalyzer: CPU-GPU-메모리 간 병목 현상 분석
2. UpgradeAdvisor: 최적 업그레이드 경로 추천

[분석 항목]
----------
- CPU-GPU 밸런스 분석
- 메모리 대역폭 병목
- 스토리지 I/O 병목
- 전력 공급 여유도

[업그레이드 추천 기준]
-------------------
- 성능 향상 대비 비용 효율성 (ROI)
- 현재 시스템과의 호환성
- 향후 확장성

[참고 자료]
----------
- Tom's Hardware Bottleneck Calculator
- PC-Builds.com Bottleneck Calculator
- UserBenchmark 비교 데이터

[TODO]
-----
- [ ] 게임별 병목 분석 (특정 게임 최적화)
- [ ] 해상도별 병목 패턴 분석
- [ ] 작업 유형별 상세 분석
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from loguru import logger


# ============================================================================
# 열거형 및 데이터 클래스
# ============================================================================

class BottleneckSeverity(str, Enum):
    """병목 심각도"""
    NONE = "none"           # 0-10%: 병목 없음
    MINOR = "minor"         # 10-20%: 경미한 병목
    MODERATE = "moderate"   # 20-35%: 중간 병목
    SEVERE = "severe"       # 35-50%: 심각한 병목
    CRITICAL = "critical"   # 50%+: 치명적 병목


@dataclass
class BottleneckAnalysisResult:
    """병목 분석 결과"""
    component: str          # 병목 발생 부품
    severity: BottleneckSeverity
    percentage: float       # 병목 퍼센티지 (0-100)
    description: str        # 설명
    impact_areas: List[str] # 영향 받는 영역


@dataclass
class UpgradeOption:
    """업그레이드 옵션"""
    component: str          # 업그레이드 대상 부품
    current: str            # 현재 제품
    recommended: str        # 추천 제품
    price_range: Tuple[int, int]  # 예상 가격 범위 (최소, 최대)
    expected_improvement: int     # 예상 성능 향상 (%)
    roi_score: float        # 투자 대비 효율 점수 (0-10)
    notes: str              # 추가 설명


# ============================================================================
# 병목 분석기
# ============================================================================

class BottleneckAnalyzer:
    """
    PC 부품 간 병목 현상 분석
    
    CPU, GPU, 메모리 간의 성능 밸런스를 분석하여
    시스템 전체 성능을 저하시키는 병목 지점을 찾아냄.
    
    사용법:
    ```python
    analyzer = BottleneckAnalyzer()
    
    result = analyzer.analyze(
        cpu_score=55,
        gpu_score=72,
        memory_score=65,
        resolution="1080p"
    )
    
    print(f"병목: {result.component}, 심각도: {result.severity}")
    ```
    
    [분석 로직]
    ----------
    1080p 게임 기준:
    - CPU 의존도: 40%, GPU 의존도: 50%, 기타: 10%
    
    1440p 게임 기준:
    - CPU 의존도: 25%, GPU 의존도: 65%, 기타: 10%
    
    4K 게임 기준:
    - CPU 의존도: 15%, GPU 의존도: 80%, 기타: 5%
    
    병목 계산:
    bottleneck_pct = |cpu_effective - gpu_effective| / max(cpu_effective, gpu_effective) * 100
    """
    
    # 해상도별 CPU/GPU 의존도
    RESOLUTION_WEIGHTS = {
        "1080p": {"cpu": 0.40, "gpu": 0.50, "other": 0.10},
        "1440p": {"cpu": 0.25, "gpu": 0.65, "other": 0.10},
        "4k": {"cpu": 0.15, "gpu": 0.80, "other": 0.05},
    }
    
    # 작업 유형별 CPU/GPU 의존도
    WORKLOAD_WEIGHTS = {
        "gaming": {"cpu": 0.35, "gpu": 0.55, "memory": 0.10},
        "streaming": {"cpu": 0.50, "gpu": 0.30, "memory": 0.20},
        "video_editing": {"cpu": 0.35, "gpu": 0.40, "memory": 0.25},
        "3d_rendering": {"cpu": 0.30, "gpu": 0.55, "memory": 0.15},
        "development": {"cpu": 0.45, "gpu": 0.10, "memory": 0.45},
        "general": {"cpu": 0.40, "gpu": 0.30, "memory": 0.30},
    }
    
    def __init__(self):
        logger.info("BottleneckAnalyzer 초기화")
    
    def analyze(
        self,
        cpu_score: int,
        gpu_score: int,
        memory_score: int,
        resolution: str = "1080p",
        workload: str = "gaming",
    ) -> BottleneckAnalysisResult:
        """
        병목 분석 수행
        
        Args:
            cpu_score: CPU 점수 (0-100)
            gpu_score: GPU 점수 (0-100)
            memory_score: 메모리 점수 (0-100)
            resolution: 대상 해상도 (1080p, 1440p, 4k)
            workload: 작업 유형
            
        Returns:
            BottleneckAnalysisResult: 분석 결과
        """
        logger.info(f"병목 분석: CPU={cpu_score}, GPU={gpu_score}, MEM={memory_score}")
        
        # 가중치 적용
        res_weights = self.RESOLUTION_WEIGHTS.get(resolution, self.RESOLUTION_WEIGHTS["1080p"])
        work_weights = self.WORKLOAD_WEIGHTS.get(workload, self.WORKLOAD_WEIGHTS["general"])
        
        # 유효 점수 계산 (해상도와 작업 유형 가중치 적용)
        cpu_effective = cpu_score * (res_weights["cpu"] + work_weights["cpu"]) / 2
        gpu_effective = gpu_score * (res_weights["gpu"] + work_weights["gpu"]) / 2
        
        # 병목 퍼센티지 계산
        max_effective = max(cpu_effective, gpu_effective)
        if max_effective == 0:
            bottleneck_pct = 0
        else:
            bottleneck_pct = abs(cpu_effective - gpu_effective) / max_effective * 100
        
        # 병목 부품 결정
        if abs(cpu_effective - gpu_effective) < 5:
            # 밸런스 양호
            return BottleneckAnalysisResult(
                component="none",
                severity=BottleneckSeverity.NONE,
                percentage=bottleneck_pct,
                description="CPU와 GPU가 잘 균형을 이루고 있습니다.",
                impact_areas=[]
            )
        
        if cpu_effective < gpu_effective:
            # CPU 병목
            bottleneck_component = "cpu"
            impact_areas = self._get_cpu_bottleneck_impacts(workload)
            description = self._get_cpu_bottleneck_description(bottleneck_pct, resolution)
        else:
            # GPU 병목
            bottleneck_component = "gpu"
            impact_areas = self._get_gpu_bottleneck_impacts(workload)
            description = self._get_gpu_bottleneck_description(bottleneck_pct, resolution)
        
        # 심각도 결정
        severity = self._determine_severity(bottleneck_pct)
        
        return BottleneckAnalysisResult(
            component=bottleneck_component,
            severity=severity,
            percentage=round(bottleneck_pct, 1),
            description=description,
            impact_areas=impact_areas
        )
    
    def _determine_severity(self, percentage: float) -> BottleneckSeverity:
        """병목 퍼센티지로 심각도 결정"""
        if percentage < 10:
            return BottleneckSeverity.NONE
        elif percentage < 20:
            return BottleneckSeverity.MINOR
        elif percentage < 35:
            return BottleneckSeverity.MODERATE
        elif percentage < 50:
            return BottleneckSeverity.SEVERE
        else:
            return BottleneckSeverity.CRITICAL
    
    def _get_cpu_bottleneck_impacts(self, workload: str) -> List[str]:
        """CPU 병목 시 영향 받는 영역"""
        impacts = {
            "gaming": ["최소 프레임 저하", "1% Low FPS 감소", "오픈 월드 게임 성능"],
            "streaming": ["인코딩 성능", "방송 품질", "멀티태스킹"],
            "video_editing": ["프리뷰 재생", "타임라인 반응성", "렌더링 속도"],
            "development": ["컴파일 시간", "IDE 반응성", "가상화 성능"],
            "general": ["멀티태스킹", "응용프로그램 실행 속도"],
        }
        return impacts.get(workload, impacts["general"])
    
    def _get_gpu_bottleneck_impacts(self, workload: str) -> List[str]:
        """GPU 병목 시 영향 받는 영역"""
        impacts = {
            "gaming": ["평균 FPS", "그래픽 품질 설정", "레이 트레이싱"],
            "streaming": ["하드웨어 인코딩", "게임 성능"],
            "video_editing": ["GPU 가속 효과", "컬러 그레이딩", "프리뷰"],
            "3d_rendering": ["렌더링 시간", "뷰포트 성능"],
            "general": ["하드웨어 가속", "디스플레이 출력"],
        }
        return impacts.get(workload, impacts["general"])
    
    def _get_cpu_bottleneck_description(self, pct: float, resolution: str) -> str:
        """CPU 병목 설명 생성"""
        if pct < 20:
            return f"경미한 CPU 병목 ({pct:.0f}%). 대부분의 상황에서 큰 영향 없음."
        elif pct < 35:
            return (f"중간 수준의 CPU 병목 ({pct:.0f}%). "
                   f"{resolution}에서 일부 게임에서 프레임 드랍 발생 가능.")
        else:
            return (f"심각한 CPU 병목 ({pct:.0f}%). "
                   f"GPU 성능의 상당 부분이 활용되지 못하고 있습니다. "
                   f"CPU 업그레이드를 강력히 권장합니다.")
    
    def _get_gpu_bottleneck_description(self, pct: float, resolution: str) -> str:
        """GPU 병목 설명 생성"""
        if pct < 20:
            return f"경미한 GPU 병목 ({pct:.0f}%). 이상적인 게이밍 상황입니다."
        elif pct < 35:
            return (f"중간 수준의 GPU 병목 ({pct:.0f}%). "
                   f"{resolution}에서 그래픽 설정을 조절하면 개선됩니다.")
        else:
            return (f"심각한 GPU 병목 ({pct:.0f}%). "
                   f"더 높은 해상도나 그래픽 설정을 원하시면 GPU 업그레이드를 권장합니다.")
    
    def analyze_memory_bottleneck(
        self,
        memory_capacity: int,
        memory_speed: int,
        workload: str = "gaming",
    ) -> Optional[BottleneckAnalysisResult]:
        """
        메모리 병목 분석
        
        Args:
            memory_capacity: 메모리 용량 (GB)
            memory_speed: 메모리 속도 (MHz)
            workload: 작업 유형
            
        Returns:
            병목 분석 결과 (병목 없으면 None)
        """
        # 작업별 권장 메모리
        recommended_memory = {
            "gaming": 16,
            "streaming": 32,
            "video_editing": 32,
            "3d_rendering": 64,
            "development": 32,
            "general": 16,
        }
        
        min_required = recommended_memory.get(workload, 16)
        
        if memory_capacity < min_required:
            shortage_pct = (min_required - memory_capacity) / min_required * 100
            
            return BottleneckAnalysisResult(
                component="memory",
                severity=self._determine_severity(shortage_pct),
                percentage=shortage_pct,
                description=(f"{workload}용으로 최소 {min_required}GB 메모리 권장. "
                           f"현재 {memory_capacity}GB로 부족할 수 있습니다."),
                impact_areas=["멀티태스킹", "대용량 파일 처리", "응용프로그램 성능"]
            )
        
        return None


# ============================================================================
# 업그레이드 조언자
# ============================================================================

class UpgradeAdvisor:
    """
    업그레이드 우선순위 및 옵션 추천
    
    현재 시스템의 약점을 분석하여 최적의 업그레이드 경로를 제안.
    비용 대비 성능 향상(ROI)을 고려하여 우선순위 결정.
    
    사용법:
    ```python
    advisor = UpgradeAdvisor()
    
    options = advisor.recommend(
        current_specs={...},
        component_scores={...},
        bottleneck_result={...},
        budget=500000
    )
    
    for opt in options:
        print(f"{opt.component}: {opt.current} → {opt.recommended}")
        print(f"  예상 향상: {opt.expected_improvement}%, ROI: {opt.roi_score}")
    ```
    """
    
    # 업그레이드 경로 데이터베이스
    # 형식: {현재 부품 키워드: [(추천 부품, 예상 향상%, 가격 범위)]}
    UPGRADE_PATHS = {
        # CPU 업그레이드 경로
        "cpu": {
            "i5-12400": [
                ("i5-13600K", 25, (280000, 350000)),
                ("i5-14600K", 35, (350000, 420000)),
                ("i7-13700K", 45, (400000, 480000)),
            ],
            "i5-13400": [
                ("i5-14600K", 20, (350000, 420000)),
                ("i7-14700K", 40, (450000, 550000)),
            ],
            "ryzen 5 5600": [
                ("Ryzen 7 5800X3D", 30, (350000, 420000)),
                ("Ryzen 5 7600X", 25, (280000, 350000)),
                ("Ryzen 7 7800X3D", 45, (450000, 520000)),
            ],
        },
        # GPU 업그레이드 경로
        "gpu": {
            "rtx 3060": [
                ("RTX 4060 Ti", 30, (450000, 550000)),
                ("RTX 4070", 55, (650000, 750000)),
                ("RTX 4070 Super", 70, (750000, 850000)),
            ],
            "rtx 3070": [
                ("RTX 4070", 25, (650000, 750000)),
                ("RTX 4070 Ti Super", 45, (900000, 1050000)),
            ],
            "rtx 4060": [
                ("RTX 4060 Ti", 15, (450000, 550000)),
                ("RTX 4070", 40, (650000, 750000)),
            ],
        },
        # 메모리 업그레이드
        "memory": {
            "16gb ddr4": [
                ("32GB DDR4-3600", 15, (70000, 100000)),
            ],
            "16gb ddr5": [
                ("32GB DDR5-6000", 20, (150000, 200000)),
            ],
        },
    }
    
    def __init__(self):
        logger.info("UpgradeAdvisor 초기화")
    
    def recommend(
        self,
        current_specs: Dict[str, Any],
        component_scores: Dict[str, Any],
        bottleneck_result: Optional[BottleneckAnalysisResult] = None,
        budget: Optional[int] = None,
        max_options: int = 5,
    ) -> List[UpgradeOption]:
        """
        업그레이드 옵션 추천
        
        Args:
            current_specs: 현재 시스템 스펙
            component_scores: 부품별 점수
            bottleneck_result: 병목 분석 결과 (선택)
            budget: 예산 제한 (선택)
            max_options: 최대 추천 개수
            
        Returns:
            List[UpgradeOption]: 추천 옵션 리스트 (ROI 순 정렬)
        """
        options = []
        
        # 병목 부품 우선 추천
        if bottleneck_result and bottleneck_result.component != "none":
            bottleneck_options = self._get_upgrade_options(
                component=bottleneck_result.component,
                current_specs=current_specs,
                score=component_scores.get(bottleneck_result.component, {}).get("score", 50),
            )
            options.extend(bottleneck_options)
        
        # 낮은 점수 부품 추천 (60점 미만)
        for comp, score_data in component_scores.items():
            if score_data.get("score", 100) < 60:
                if comp not in [o.component for o in options]:
                    comp_options = self._get_upgrade_options(
                        component=comp,
                        current_specs=current_specs,
                        score=score_data.get("score", 50),
                    )
                    options.extend(comp_options)
        
        # 예산 필터링
        if budget:
            options = [o for o in options if o.price_range[0] <= budget]
        
        # ROI 점수 계산 및 정렬
        for opt in options:
            opt.roi_score = self._calculate_roi(opt)
        
        options.sort(key=lambda x: x.roi_score, reverse=True)
        
        return options[:max_options]
    
    def _get_upgrade_options(
        self,
        component: str,
        current_specs: Dict[str, Any],
        score: int,
    ) -> List[UpgradeOption]:
        """특정 부품의 업그레이드 옵션 조회"""
        options = []
        
        # 현재 부품 이름 추출
        if component == "cpu":
            current_name = current_specs.get("cpu", {}).get("name", "").lower()
        elif component == "gpu":
            current_name = current_specs.get("gpu", {}).get("name", "").lower()
        elif component == "memory":
            capacity = current_specs.get("memory", {}).get("capacity", 16)
            gen = current_specs.get("memory", {}).get("generation", "DDR4")
            current_name = f"{capacity}gb {gen}".lower()
        else:
            return []
        
        # 업그레이드 경로 검색
        paths = self.UPGRADE_PATHS.get(component, {})
        for key, upgrades in paths.items():
            if key in current_name:
                for recommended, improvement, price_range in upgrades:
                    options.append(UpgradeOption(
                        component=component,
                        current=current_specs.get(component, {}).get("name", current_name),
                        recommended=recommended,
                        price_range=price_range,
                        expected_improvement=improvement,
                        roi_score=0,  # 나중에 계산
                        notes=f"{improvement}% 성능 향상 예상",
                    ))
                break
        
        return options
    
    def _calculate_roi(self, option: UpgradeOption) -> float:
        """
        ROI (투자 대비 효율) 점수 계산
        
        점수 = (성능 향상%) / (가격(만원)) * 10
        """
        avg_price = (option.price_range[0] + option.price_range[1]) / 2
        price_in_10k = avg_price / 10000  # 만원 단위
        
        if price_in_10k == 0:
            return 10.0
        
        roi = (option.expected_improvement / price_in_10k) * 10
        return round(min(10.0, roi), 2)
    
    def get_budget_builds(
        self,
        budget: int,
        purpose: str = "gaming",
    ) -> List[Dict[str, Any]]:
        """
        예산별 권장 빌드 조회
        
        Args:
            budget: 총 예산
            purpose: 사용 목적
            
        Returns:
            권장 빌드 리스트
        """
        # TODO: 예산별 최적 빌드 데이터베이스 구현
        # 현재는 placeholder
        return [
            {
                "name": f"{purpose}용 {budget//10000}만원 빌드",
                "components": {},
                "expected_performance": "구현 예정",
            }
        ]


# ============================================================================
# 테스트용 메인
# ============================================================================

if __name__ == "__main__":
    # BottleneckAnalyzer 테스트
    analyzer = BottleneckAnalyzer()
    
    # CPU 병목 상황
    result = analyzer.analyze(
        cpu_score=55,
        gpu_score=78,
        memory_score=70,
        resolution="1080p",
        workload="gaming"
    )
    print(f"병목 분석 결과:")
    print(f"  부품: {result.component}")
    print(f"  심각도: {result.severity.value}")
    print(f"  퍼센티지: {result.percentage}%")
    print(f"  설명: {result.description}")
    print(f"  영향: {result.impact_areas}")
    print()
    
    # UpgradeAdvisor 테스트
    advisor = UpgradeAdvisor()
    
    options = advisor.recommend(
        current_specs={
            "cpu": {"name": "Intel Core i5-12400F"},
            "gpu": {"name": "RTX 3060"},
            "memory": {"capacity": 16, "generation": "DDR4"},
        },
        component_scores={
            "cpu": {"score": 55},
            "gpu": {"score": 45},
            "memory": {"score": 70},
        },
        budget=700000
    )
    
    print("\n업그레이드 추천:")
    for opt in options:
        print(f"  {opt.component}: {opt.current} → {opt.recommended}")
        print(f"    가격: {opt.price_range[0]:,}원 ~ {opt.price_range[1]:,}원")
        print(f"    예상 향상: {opt.expected_improvement}%, ROI: {opt.roi_score}")
