"""
PC 사양 진단 엔진
==================

[목표]
------
사용자의 현재 PC 사양을 종합적으로 분석하여 다음을 제공:
1. 현재 사양의 성능 등급 판정
2. 병목 현상(Bottleneck) 탐지
3. 목적별 적합성 평가
4. 업그레이드 우선순위 추천

[배경 지식]
----------
PC 성능은 개별 부품 성능뿐만 아니라 부품 간 밸런스에 크게 영향을 받음.
예: 고성능 GPU + 저성능 CPU = CPU 병목으로 GPU 성능 미달

병목 현상(Bottleneck):
- CPU 병목: CPU가 GPU보다 느려서 GPU가 대기하는 현상
- GPU 병목: GPU가 CPU보다 느려서 CPU가 대기하는 현상 (이상적)
- 메모리 병목: RAM 용량/속도 부족으로 전체 성능 저하
- 스토리지 병목: 느린 저장장치로 인한 로딩 지연

[아키텍처]
---------
```
사용자 입력 (PC 사양)
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                    PCDiagnosisEngine                         │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────────────────────┐ │
│  │ HardwareCollector │→│         스펙 정규화              │ │
│  │ (하드웨어 정보)   │  │  (다양한 입력 포맷 통일)        │ │
│  └──────────────────┘  └───────────────┬──────────────────┘ │
│                                         │                    │
│                                         ▼                    │
│  ┌──────────────────┐  ┌──────────────────────────────────┐ │
│  │ BenchmarkCollector│→│      성능 점수 산출              │ │
│  │ (벤치마크 DB)     │  │  (Cinebench, 3DMark 기준)       │ │
│  └──────────────────┘  └───────────────┬──────────────────┘ │
│                                         │                    │
│                                         ▼                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │               BottleneckAnalyzer                      │   │
│  │  - CPU vs GPU 밸런스 분석                            │   │
│  │  - 메모리 대역폭 분석                                │   │
│  │  - 스토리지 병목 분석                                │   │
│  └──────────────────────────┬───────────────────────────┘   │
│                              │                               │
│                              ▼                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │               UpgradeAdvisor                          │   │
│  │  - 업그레이드 우선순위 결정                          │   │
│  │  - 예산별 업그레이드 옵션 제안                       │   │
│  │  - ROI(투자 대비 성능 향상) 계산                     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
진단 결과 (DiagnosisResult)
```

[입력/출력 인터페이스]
-------------------
입력 (UserPCSpecs):
```python
{
    "cpu": {
        "name": "Intel Core i5-12400F",
        "cores": 6,
        "threads": 12,
        "base_clock": 2.5,  # GHz
        "boost_clock": 4.4
    },
    "gpu": {
        "name": "RTX 3060",
        "vram": 12,  # GB
        "memory_type": "GDDR6"
    },
    "memory": {
        "capacity": 16,  # GB
        "speed": 3200,  # MHz
        "channels": 2
    },
    "storage": {
        "type": "NVMe SSD",
        "capacity": 512,  # GB
        "read_speed": 3500  # MB/s
    },
    "usage_purpose": "gaming"  # gaming, work, development, streaming
}
```

출력 (DiagnosisResult):
```python
{
    "overall_score": 75,  # 100점 만점
    "tier": "mid-high",  # entry, mid, mid-high, high, enthusiast
    "bottleneck": {
        "type": "none",  # cpu, gpu, memory, storage, none
        "severity": 0,  # 0-100
        "description": "밸런스가 좋습니다"
    },
    "component_scores": {
        "cpu": {"score": 72, "tier": "mid"},
        "gpu": {"score": 78, "tier": "mid-high"},
        "memory": {"score": 70, "tier": "mid"},
        "storage": {"score": 85, "tier": "high"}
    },
    "purpose_fitness": {
        "gaming": 0.80,
        "work": 0.75,
        "development": 0.70,
        "streaming": 0.65
    },
    "upgrade_recommendations": [
        {
            "component": "memory",
            "current": "16GB DDR4-3200",
            "recommended": "32GB DDR4-3600",
            "expected_improvement": 15,  # %
            "estimated_cost": 80000,
            "priority": 1
        }
    ]
}
```

[구현 단계]
----------
1단계: 하드웨어 스펙 파서 구현 (다양한 입력 형식 처리)
2단계: 벤치마크 데이터베이스 구축 (CPU/GPU 점수 매핑)
3단계: 병목 분석 알고리즘 구현
4단계: 업그레이드 추천 로직 구현
5단계: 프론트엔드 연동 (시스템 정보 자동 수집 옵션)

[참고 기술/데이터]
----------------
- Cinebench R23 점수 데이터: CPU 성능 기준
- 3DMark Time Spy 점수: GPU 성능 기준
- UserBenchmark: 상대적 성능 비교 (참고용)
- PCPartPicker: 호환성 및 가격 데이터

[벤치마크 점수 매핑 예시]
----------------------
CPU (Cinebench R23 Multi 기준):
- Intel i9-14900K: 100점 (40,000점 기준)
- Intel i5-14600K: 75점
- Intel i5-12400F: 55점
- AMD Ryzen 5 5600X: 52점

GPU (3DMark Time Spy 기준):
- RTX 4090: 100점 (36,000점 기준)
- RTX 4080: 85점
- RTX 4070 Ti: 72점
- RTX 3060: 45점

[테스트]
-------
backend/tests/test_pc_diagnosis.py 참조
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
from pydantic import BaseModel, Field


# ============================================================================
# 열거형 및 상수 정의
# ============================================================================

class PerformanceTier(str, Enum):
    """성능 등급"""
    ENTRY = "entry"         # 50점 미만
    MID = "mid"             # 50-65점
    MID_HIGH = "mid-high"   # 65-80점
    HIGH = "high"           # 80-90점
    ENTHUSIAST = "enthusiast"  # 90점 이상


class BottleneckType(str, Enum):
    """병목 유형"""
    NONE = "none"
    CPU = "cpu"
    GPU = "gpu"
    MEMORY = "memory"
    STORAGE = "storage"


class UsagePurpose(str, Enum):
    """사용 목적"""
    GAMING = "gaming"
    WORK = "work"
    DEVELOPMENT = "development"
    STREAMING = "streaming"
    VIDEO_EDITING = "video_editing"


# ============================================================================
# 데이터 모델
# ============================================================================

class CPUSpecs(BaseModel):
    """CPU 스펙"""
    name: str = Field(..., description="CPU 모델명")
    cores: Optional[int] = Field(None, description="코어 수")
    threads: Optional[int] = Field(None, description="스레드 수")
    base_clock: Optional[float] = Field(None, description="기본 클럭 (GHz)")
    boost_clock: Optional[float] = Field(None, description="부스트 클럭 (GHz)")


class GPUSpecs(BaseModel):
    """GPU 스펙"""
    name: str = Field(..., description="GPU 모델명")
    vram: Optional[int] = Field(None, description="VRAM 용량 (GB)")
    memory_type: Optional[str] = Field(None, description="메모리 타입")


class MemorySpecs(BaseModel):
    """메모리 스펙"""
    capacity: int = Field(..., description="용량 (GB)")
    speed: Optional[int] = Field(None, description="속도 (MHz)")
    channels: Optional[int] = Field(2, description="채널 수")
    generation: Optional[str] = Field("DDR4", description="세대")


class StorageSpecs(BaseModel):
    """저장장치 스펙"""
    type: str = Field(..., description="타입 (SSD, NVMe SSD, HDD)")
    capacity: int = Field(..., description="용량 (GB)")
    read_speed: Optional[int] = Field(None, description="읽기 속도 (MB/s)")


class UserPCSpecs(BaseModel):
    """사용자 PC 전체 스펙"""
    cpu: CPUSpecs
    gpu: GPUSpecs
    memory: MemorySpecs
    storage: StorageSpecs
    usage_purpose: Optional[UsagePurpose] = Field(UsagePurpose.GAMING)


class ComponentScore(BaseModel):
    """부품별 점수"""
    score: int = Field(..., ge=0, le=100)
    tier: PerformanceTier
    notes: Optional[str] = None


class BottleneckResult(BaseModel):
    """병목 분석 결과"""
    type: BottleneckType
    severity: int = Field(..., ge=0, le=100, description="심각도 (0=없음, 100=심각)")
    description: str


class UpgradeRecommendation(BaseModel):
    """업그레이드 추천"""
    component: str
    current: str
    recommended: str
    expected_improvement: int  # 예상 성능 향상 %
    estimated_cost: int  # 예상 비용 (원)
    priority: int = Field(..., ge=1, le=5)  # 1=최우선


class DiagnosisResult(BaseModel):
    """진단 결과"""
    overall_score: int = Field(..., ge=0, le=100)
    tier: PerformanceTier
    bottleneck: BottleneckResult
    component_scores: Dict[str, ComponentScore]
    purpose_fitness: Dict[str, float]
    upgrade_recommendations: List[UpgradeRecommendation]


# ============================================================================
# 벤치마크 데이터베이스 (임시 - 실제 구현 시 외부 데이터 로드)
# ============================================================================

# CPU 점수 (Cinebench R23 Multi 기준, 100점 = i9-14900K)
CPU_BENCHMARK_SCORES = {
    # Intel 14세대
    "i9-14900k": 100,
    "i7-14700k": 88,
    "i5-14600k": 75,
    "i5-14400f": 60,
    
    # Intel 13세대
    "i9-13900k": 95,
    "i7-13700k": 82,
    "i5-13600k": 72,
    "i5-13400f": 58,
    
    # Intel 12세대
    "i9-12900k": 80,
    "i7-12700k": 70,
    "i5-12600k": 62,
    "i5-12400f": 55,
    
    # AMD Ryzen 7000
    "ryzen 9 7950x": 100,
    "ryzen 7 7800x3d": 72,
    "ryzen 7 7700x": 68,
    "ryzen 5 7600x": 58,
    
    # AMD Ryzen 5000
    "ryzen 9 5900x": 70,
    "ryzen 7 5800x": 60,
    "ryzen 5 5600x": 52,
}

# GPU 점수 (3DMark Time Spy 기준, 100점 = RTX 4090)
GPU_BENCHMARK_SCORES = {
    # NVIDIA RTX 40시리즈
    "rtx 4090": 100,
    "rtx 4080 super": 88,
    "rtx 4080": 85,
    "rtx 4070 ti super": 78,
    "rtx 4070 ti": 72,
    "rtx 4070 super": 68,
    "rtx 4070": 62,
    "rtx 4060 ti": 52,
    "rtx 4060": 45,
    
    # NVIDIA RTX 30시리즈
    "rtx 3090": 72,
    "rtx 3080": 65,
    "rtx 3070": 55,
    "rtx 3060 ti": 50,
    "rtx 3060": 45,
    "rtx 3050": 32,
    
    # AMD RX 7000
    "rx 7900 xtx": 88,
    "rx 7900 xt": 80,
    "rx 7800 xt": 65,
    "rx 7700 xt": 58,
    "rx 7600": 45,
}


# ============================================================================
# 진단 엔진 구현
# ============================================================================

class PCDiagnosisEngine:
    """
    PC 사양 진단 엔진
    
    사용법:
    ```python
    engine = PCDiagnosisEngine()
    specs = {
        "cpu": {"name": "Intel Core i5-12400F", ...},
        "gpu": {"name": "RTX 3060", ...},
        ...
    }
    result = engine.diagnose(specs)
    ```
    """
    
    def __init__(
        self,
        cpu_benchmark_db: Optional[Dict[str, int]] = None,
        gpu_benchmark_db: Optional[Dict[str, int]] = None,
    ):
        """
        Args:
            cpu_benchmark_db: CPU 벤치마크 점수 딕셔너리
            gpu_benchmark_db: GPU 벤치마크 점수 딕셔너리
        """
        self.cpu_benchmarks = cpu_benchmark_db or CPU_BENCHMARK_SCORES
        self.gpu_benchmarks = gpu_benchmark_db or GPU_BENCHMARK_SCORES
        
        logger.info("PCDiagnosisEngine 초기화 완료")
    
    def diagnose(self, specs: Dict[str, Any]) -> DiagnosisResult:
        """
        PC 사양 종합 진단
        
        Args:
            specs: 사용자 PC 스펙 딕셔너리
            
        Returns:
            DiagnosisResult: 진단 결과
        """
        logger.info("PC 사양 진단 시작")
        
        # 스펙 파싱 및 검증
        user_specs = UserPCSpecs(**specs)
        
        # 1. 각 부품별 점수 산출
        component_scores = self._calculate_component_scores(user_specs)
        
        # 2. 병목 분석
        bottleneck = self._analyze_bottleneck(component_scores, user_specs)
        
        # 3. 전체 점수 계산
        overall_score = self._calculate_overall_score(component_scores, bottleneck)
        
        # 4. 성능 등급 결정
        tier = self._determine_tier(overall_score)
        
        # 5. 목적별 적합성 평가
        purpose_fitness = self._evaluate_purpose_fitness(
            component_scores, user_specs.usage_purpose
        )
        
        # 6. 업그레이드 추천 생성
        upgrade_recommendations = self._generate_upgrade_recommendations(
            user_specs, component_scores, bottleneck
        )
        
        result = DiagnosisResult(
            overall_score=overall_score,
            tier=tier,
            bottleneck=bottleneck,
            component_scores=component_scores,
            purpose_fitness=purpose_fitness,
            upgrade_recommendations=upgrade_recommendations,
        )
        
        logger.info(f"진단 완료: 전체 점수 {overall_score}, 등급 {tier.value}")
        return result
    
    def _calculate_component_scores(
        self, specs: UserPCSpecs
    ) -> Dict[str, ComponentScore]:
        """각 부품별 점수 산출"""
        scores = {}
        
        # CPU 점수
        cpu_score = self._get_cpu_score(specs.cpu.name)
        scores["cpu"] = ComponentScore(
            score=cpu_score,
            tier=self._determine_tier(cpu_score),
            notes=f"{specs.cpu.name}"
        )
        
        # GPU 점수
        gpu_score = self._get_gpu_score(specs.gpu.name)
        scores["gpu"] = ComponentScore(
            score=gpu_score,
            tier=self._determine_tier(gpu_score),
            notes=f"{specs.gpu.name}, VRAM {specs.gpu.vram}GB"
        )
        
        # 메모리 점수
        memory_score = self._calculate_memory_score(specs.memory)
        scores["memory"] = ComponentScore(
            score=memory_score,
            tier=self._determine_tier(memory_score),
            notes=f"{specs.memory.capacity}GB {specs.memory.generation}-{specs.memory.speed}"
        )
        
        # 스토리지 점수
        storage_score = self._calculate_storage_score(specs.storage)
        scores["storage"] = ComponentScore(
            score=storage_score,
            tier=self._determine_tier(storage_score),
            notes=f"{specs.storage.type} {specs.storage.capacity}GB"
        )
        
        return scores
    
    def _get_cpu_score(self, cpu_name: str) -> int:
        """CPU 이름으로 점수 조회"""
        normalized = cpu_name.lower()
        
        for key, score in self.cpu_benchmarks.items():
            if key in normalized:
                return score
        
        # 매칭 실패 시 기본값
        logger.warning(f"CPU 점수 미발견: {cpu_name}, 기본값 50 사용")
        return 50
    
    def _get_gpu_score(self, gpu_name: str) -> int:
        """GPU 이름으로 점수 조회"""
        normalized = gpu_name.lower()
        
        for key, score in self.gpu_benchmarks.items():
            if key in normalized:
                return score
        
        # 매칭 실패 시 기본값
        logger.warning(f"GPU 점수 미발견: {gpu_name}, 기본값 50 사용")
        return 50
    
    def _calculate_memory_score(self, memory: MemorySpecs) -> int:
        """메모리 점수 계산"""
        score = 0
        
        # 용량 기준 (최대 50점)
        if memory.capacity >= 64:
            score += 50
        elif memory.capacity >= 32:
            score += 40
        elif memory.capacity >= 16:
            score += 30
        elif memory.capacity >= 8:
            score += 15
        else:
            score += 5
        
        # 속도 기준 (최대 30점)
        if memory.speed:
            if memory.speed >= 6000:
                score += 30
            elif memory.speed >= 4800:
                score += 25
            elif memory.speed >= 3600:
                score += 20
            elif memory.speed >= 3200:
                score += 15
            else:
                score += 10
        else:
            score += 15  # 기본값
        
        # 채널 기준 (최대 20점)
        if memory.channels:
            if memory.channels >= 4:
                score += 20
            elif memory.channels >= 2:
                score += 15
            else:
                score += 5
        else:
            score += 10
        
        return min(100, score)
    
    def _calculate_storage_score(self, storage: StorageSpecs) -> int:
        """스토리지 점수 계산"""
        score = 0
        
        # 타입 기준 (최대 60점)
        storage_type = storage.type.lower()
        if "nvme" in storage_type:
            score += 60
        elif "ssd" in storage_type:
            score += 40
        elif "hdd" in storage_type:
            score += 15
        else:
            score += 30
        
        # 속도 기준 (최대 40점)
        if storage.read_speed:
            if storage.read_speed >= 7000:
                score += 40
            elif storage.read_speed >= 5000:
                score += 35
            elif storage.read_speed >= 3000:
                score += 25
            elif storage.read_speed >= 500:
                score += 15
            else:
                score += 5
        else:
            # 타입 기반 추정
            if "nvme" in storage_type:
                score += 25
            elif "ssd" in storage_type:
                score += 15
            else:
                score += 5
        
        return min(100, score)
    
    def _analyze_bottleneck(
        self,
        component_scores: Dict[str, ComponentScore],
        specs: UserPCSpecs,
    ) -> BottleneckResult:
        """
        병목 분석
        
        CPU와 GPU 점수 차이가 20점 이상이면 병목 발생으로 판단
        """
        cpu_score = component_scores["cpu"].score
        gpu_score = component_scores["gpu"].score
        memory_score = component_scores["memory"].score
        
        # CPU vs GPU 병목 분석
        score_diff = cpu_score - gpu_score
        
        if abs(score_diff) < 15:
            # 밸런스 양호
            return BottleneckResult(
                type=BottleneckType.NONE,
                severity=0,
                description="CPU와 GPU 밸런스가 좋습니다."
            )
        elif score_diff > 15:
            # GPU가 병목 (CPU > GPU)
            severity = min(100, (score_diff - 15) * 3)
            return BottleneckResult(
                type=BottleneckType.GPU,
                severity=severity,
                description=f"GPU가 CPU 대비 성능이 낮아 병목이 발생할 수 있습니다. "
                           f"GPU 업그레이드를 권장합니다."
            )
        else:
            # CPU가 병목 (GPU > CPU)
            severity = min(100, (abs(score_diff) - 15) * 3)
            return BottleneckResult(
                type=BottleneckType.CPU,
                severity=severity,
                description=f"CPU가 GPU 대비 성능이 낮아 병목이 발생할 수 있습니다. "
                           f"특히 고해상도 게임에서 CPU 병목이 두드러질 수 있습니다."
            )
    
    def _calculate_overall_score(
        self,
        component_scores: Dict[str, ComponentScore],
        bottleneck: BottleneckResult,
    ) -> int:
        """전체 점수 계산 (가중 평균)"""
        weights = {
            "cpu": 0.30,
            "gpu": 0.35,
            "memory": 0.20,
            "storage": 0.15,
        }
        
        weighted_sum = sum(
            component_scores[comp].score * weight
            for comp, weight in weights.items()
            if comp in component_scores
        )
        
        # 병목 페널티 적용
        bottleneck_penalty = bottleneck.severity * 0.05
        
        return max(0, min(100, int(weighted_sum - bottleneck_penalty)))
    
    def _determine_tier(self, score: int) -> PerformanceTier:
        """점수로 성능 등급 결정"""
        if score >= 90:
            return PerformanceTier.ENTHUSIAST
        elif score >= 80:
            return PerformanceTier.HIGH
        elif score >= 65:
            return PerformanceTier.MID_HIGH
        elif score >= 50:
            return PerformanceTier.MID
        else:
            return PerformanceTier.ENTRY
    
    def _evaluate_purpose_fitness(
        self,
        component_scores: Dict[str, ComponentScore],
        primary_purpose: UsagePurpose,
    ) -> Dict[str, float]:
        """목적별 적합성 평가"""
        cpu_score = component_scores["cpu"].score
        gpu_score = component_scores["gpu"].score
        memory_score = component_scores["memory"].score
        storage_score = component_scores["storage"].score
        
        # 각 목적별 부품 중요도
        purpose_weights = {
            "gaming": {"cpu": 0.25, "gpu": 0.45, "memory": 0.20, "storage": 0.10},
            "work": {"cpu": 0.35, "gpu": 0.15, "memory": 0.30, "storage": 0.20},
            "development": {"cpu": 0.35, "gpu": 0.10, "memory": 0.35, "storage": 0.20},
            "streaming": {"cpu": 0.40, "gpu": 0.30, "memory": 0.20, "storage": 0.10},
            "video_editing": {"cpu": 0.30, "gpu": 0.35, "memory": 0.25, "storage": 0.10},
        }
        
        fitness = {}
        for purpose, weights in purpose_weights.items():
            weighted_score = (
                cpu_score * weights["cpu"] +
                gpu_score * weights["gpu"] +
                memory_score * weights["memory"] +
                storage_score * weights["storage"]
            )
            fitness[purpose] = round(weighted_score / 100, 2)
        
        return fitness
    
    def _generate_upgrade_recommendations(
        self,
        specs: UserPCSpecs,
        component_scores: Dict[str, ComponentScore],
        bottleneck: BottleneckResult,
    ) -> List[UpgradeRecommendation]:
        """업그레이드 추천 생성"""
        recommendations = []
        
        # 병목 부품 우선 추천
        if bottleneck.type != BottleneckType.NONE:
            if bottleneck.type == BottleneckType.CPU:
                recommendations.append(UpgradeRecommendation(
                    component="cpu",
                    current=specs.cpu.name,
                    recommended="차세대 CPU로 업그레이드 권장",
                    expected_improvement=20,
                    estimated_cost=400000,
                    priority=1,
                ))
            elif bottleneck.type == BottleneckType.GPU:
                recommendations.append(UpgradeRecommendation(
                    component="gpu",
                    current=specs.gpu.name,
                    recommended="RTX 4070 이상 GPU로 업그레이드 권장",
                    expected_improvement=25,
                    estimated_cost=700000,
                    priority=1,
                ))
        
        # 낮은 점수 부품 추천 (60점 미만)
        for comp, score_data in component_scores.items():
            if score_data.score < 60 and comp not in [r.component for r in recommendations]:
                recommendations.append(UpgradeRecommendation(
                    component=comp,
                    current=score_data.notes or comp,
                    recommended=f"{comp} 업그레이드 권장",
                    expected_improvement=15,
                    estimated_cost=200000,
                    priority=2 if score_data.score < 40 else 3,
                ))
        
        # 메모리 16GB 미만이면 추천
        if specs.memory.capacity < 16:
            recommendations.append(UpgradeRecommendation(
                component="memory",
                current=f"{specs.memory.capacity}GB",
                recommended="최소 16GB 이상 권장",
                expected_improvement=20,
                estimated_cost=80000,
                priority=1,
            ))
        
        # 우선순위로 정렬
        recommendations.sort(key=lambda x: x.priority)
        
        return recommendations[:5]  # 최대 5개


# ============================================================================
# 유틸리티 함수
# ============================================================================

def create_diagnosis_engine(
    config: Optional[Dict[str, Any]] = None
) -> PCDiagnosisEngine:
    """
    진단 엔진 팩토리 함수
    
    Args:
        config: 설정 딕셔너리
        
    Returns:
        PCDiagnosisEngine 인스턴스
    """
    return PCDiagnosisEngine()


# ============================================================================
# 메인 (테스트용)
# ============================================================================

if __name__ == "__main__":
    import json
    
    engine = PCDiagnosisEngine()
    
    # 테스트 스펙
    test_specs = {
        "cpu": {
            "name": "Intel Core i5-12400F",
            "cores": 6,
            "threads": 12,
            "base_clock": 2.5,
            "boost_clock": 4.4
        },
        "gpu": {
            "name": "RTX 3060",
            "vram": 12,
            "memory_type": "GDDR6"
        },
        "memory": {
            "capacity": 16,
            "speed": 3200,
            "channels": 2,
            "generation": "DDR4"
        },
        "storage": {
            "type": "NVMe SSD",
            "capacity": 512,
            "read_speed": 3500
        },
        "usage_purpose": "gaming"
    }
    
    result = engine.diagnose(test_specs)
    print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))
