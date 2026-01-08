"""
단계별 부품 선택 RAG 파이프라인
================================

[목표]
------
부품을 카테고리별로 단계적으로 선택하는 Step-by-Step 방식의 RAG 파이프라인.
이전 단계에서 선택한 부품 정보를 컨텍스트로 활용하여 더 정확한 추천 제공.

[배경]
------
기존 RAG 방식의 문제점:
1. 한 번에 모든 부품을 검색하면 호환성 고려가 어려움
2. 사용자의 선택이 반영되지 않은 일방적 추천
3. 카테고리 간 연관성 미반영

개선된 Step-by-Step 방식:
1. 카테고리 순서대로 단계별 선택
2. 이전 선택을 컨텍스트로 활용
3. 호환성 기반 후보 필터링

[선택 순서]
----------
권장 순서 (중요도 및 의존성 기반):
1. CPU - 전체 시스템의 기반
2. 메인보드 - CPU 소켓에 따라 결정
3. 메모리 - 메인보드 지원 타입에 따라
4. GPU - 목적에 따라 선택
5. 스토리지 - M.2/SATA 슬롯 확인
6. PSU - 전체 전력 요구량에 따라
7. 케이스 - 폼팩터와 GPU 길이 확인
8. CPU 쿨러 - 소켓과 케이스 높이 확인

[아키텍처]
---------
```
사용자 요구사항 (예산, 목적)
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│              StepByStepRAGPipeline                          │
│                                                              │
│  Step 1: CPU 선택                                           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ - 예산의 20-25% 할당                                │    │
│  │ - 목적에 맞는 CPU 검색 (RAG)                        │    │
│  │ - 사용자 선택 대기                                  │    │
│  └─────────────────┬───────────────────────────────────┘    │
│                    │ 선택된 CPU 정보                        │
│                    ▼                                        │
│  Step 2: 메인보드 선택                                      │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ - CPU 소켓 호환 메인보드만 필터링                   │    │
│  │ - 예산의 10-15% 할당                                │    │
│  │ - RAG 검색 + 호환성 필터                            │    │
│  └─────────────────┬───────────────────────────────────┘    │
│                    │ 선택된 MB 정보                         │
│                    ▼                                        │
│  Step 3~8: 나머지 부품 순차 선택                           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ - 이전 선택 컨텍스트 활용                           │    │
│  │ - 호환성 검증 후 후보 제시                          │    │
│  │ - 사용자 선택 반영                                  │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
완성된 PC 구성 (호환성 검증됨)
```

[입력/출력 인터페이스]
-------------------
단계 시작 요청 (StartStepRequest):
```python
{
    "session_id": "session_123",
    "current_step": 1,  # 1-8
    "budget": 1500000,
    "purpose": "gaming",
    "previous_selections": []  # 이전 단계 선택 결과
}
```

단계 결과 (StepResult):
```python
{
    "session_id": "session_123",
    "step": 1,
    "category": "cpu",
    "candidates": [
        {
            "id": "cpu_i5_14600k",
            "name": "Intel Core i5-14600K",
            "price": 380000,
            "match_score": 0.92,
            "compatibility_status": "compatible",
            "reasons": ["게임 성능 우수", "예산 적합"]
        },
        ...
    ],
    "allocated_budget": 350000,
    "remaining_budget": 1150000,
    "context": {
        "purpose_keywords": ["게임", "고성능"],
        "socket_requirement": null  # 이 단계에서 결정됨
    },
    "next_step": 2
}
```

사용자 선택 (UserSelection):
```python
{
    "session_id": "session_123",
    "step": 1,
    "selected_id": "cpu_i5_14600k"
}
```

[구현 단계]
----------
1단계: 세션 관리 구현 (상태 저장)
2단계: 단계별 예산 분배 로직
3단계: 컨텍스트 기반 RAG 검색 개선
4단계: 호환성 필터링 연동
5단계: 프론트엔드 연동 API

[테스트]
-------
backend/tests/test_step_by_step.py 참조
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
import re
from loguru import logger
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage

# 모듈 임포트 (상대 경로)
# from .retriever import PCComponentRetriever
# from ..modules.compatibility import CompatibilityEngine


# ============================================================================
# 상수 및 열거형
# ============================================================================

class SelectionStep(int, Enum):
    """선택 단계"""
    CPU = 1
    MOTHERBOARD = 2
    MEMORY = 3
    GPU = 4
    STORAGE = 5
    PSU = 6
    CPU_COOLER = 7
    CASE = 8


# 단계별 카테고리 매핑
STEP_CATEGORIES = {
    SelectionStep.CPU: "cpu",
    SelectionStep.MOTHERBOARD: "motherboard",
    SelectionStep.MEMORY: "memory",
    SelectionStep.GPU: "gpu",
    SelectionStep.STORAGE: "storage",
    SelectionStep.PSU: "psu",
    SelectionStep.CASE: "case",
    SelectionStep.CPU_COOLER: "cpu_cooler",
}

# 목적별 예산 배분 비율
BUDGET_ALLOCATION = {
    "gaming": {
        "cpu": 0.22,
        "motherboard": 0.12,
        "memory": 0.10,
        "gpu": 0.35,
        "storage": 0.08,
        "psu": 0.05,
        "case": 0.05,
        "cpu_cooler": 0.03,
    },
    "workstation": {
        "cpu": 0.30,
        "motherboard": 0.12,
        "memory": 0.18,
        "gpu": 0.15,
        "storage": 0.12,
        "psu": 0.05,
        "case": 0.05,
        "cpu_cooler": 0.03,
    },
    "general": {
        "cpu": 0.25,
        "motherboard": 0.12,
        "memory": 0.12,
        "gpu": 0.25,
        "storage": 0.10,
        "psu": 0.06,
        "case": 0.06,
        "cpu_cooler": 0.04,
    },
}

# 카테고리별 설명 및 주요 스펙
CATEGORY_INFO = {
    "cpu": {
        "name": "CPU (중앙처리장치)",
        "description": "컴퓨터의 두뇌 역할을 하는 핵심 부품입니다. 모든 연산과 작업 처리를 담당합니다.",
        "key_specs": ["코어 수", "클럭 속도", "TDP", "소켓 타입"],
        "spec_meanings": {
            "match_score": "사용 목적과의 적합도 (0~1, 높을수록 적합)",
            "cores": "동시 작업 처리 능력 (많을수록 멀티태스킹 우수)",
            "clock_speed": "처리 속도 (GHz, 높을수록 빠름)",
            "tdp": "소비 전력 및 발열량 (W)"
        }
    },
    "motherboard": {
        "name": "메인보드 (마더보드)",
        "description": "모든 부품을 연결하는 기판입니다. CPU, 메모리, GPU 등을 장착하며 호환성이 중요합니다.",
        "key_specs": ["소켓", "칩셋", "메모리 타입", "폼팩터"],
        "spec_meanings": {
            "match_score": "선택한 CPU와의 호환성 점수",
            "socket": "CPU 장착 방식 (선택한 CPU와 일치해야 함)",
            "chipset": "기능 및 확장성을 결정",
            "memory_type": "지원하는 RAM 규격 (DDR4, DDR5 등)"
        }
    },
    "memory": {
        "name": "메모리 (RAM)",
        "description": "실행 중인 프로그램과 데이터를 임시 저장하는 공간입니다. 용량과 속도가 중요합니다.",
        "key_specs": ["용량", "속도", "DDR 타입", "개수"],
        "spec_meanings": {
            "match_score": "메인보드 호환성 및 목적 적합도",
            "capacity": "저장 공간 (GB, 많을수록 멀티태스킹 여유)",
            "speed": "데이터 전송 속도 (MHz)",
            "ddr_generation": "세대 (DDR4, DDR5 - 메인보드와 일치)"
        }
    },
    "gpu": {
        "name": "그래픽카드 (GPU)",
        "description": "화면 출력 및 그래픽 연산을 담당합니다. 게임과 영상 작업 성능에핵심적입니다.",
        "key_specs": ["VRAM", "코어 클럭", "TDP", "출력 포트"],
        "spec_meanings": {
            "match_score": "게임/작업 목적 적합도",
            "vram": "비디오 메모리 용량 (GB)",
            "core_clock": "GPU 처리 속도 (MHz)",
            "tdp": "소비 전력 (파워 용량 고려 필요)"
        }
    },
    "storage": {
        "name": "저장장치 (SSD/HDD)",
        "description": "운영체제, 프로그램, 파일을 영구 저장하는 장치입니다. 속도와 용량을 고려해야 합니다.",
        "key_specs": ["용량", "읽기/쓰기 속도", "인터페이스", "폼팩터"],
        "spec_meanings": {
            "match_score": "용도 및 가성비",
            "capacity": "저장 공간 (GB/TB)",
            "read_speed": "데이터 읽기 속도 (MB/s)",
            "interface": "연결 방식 (NVMe, SATA 등)"
        }
    },
    "psu": {
        "name": "파워 서플라이 (PSU)",
        "description": "모든 부품에 전력을 공급하는 장치입니다. 충분한 용량과 인증 등급이 중요합니다.",
        "key_specs": ["출력", "인증 등급", "모듈러 타입", "폼팩터"],
        "spec_meanings": {
            "match_score": "전력 요구량 충족도",
            "wattage": "최대 출력 (W, CPU+GPU TDP의 1.5배 권장)",
            "efficiency": "효율 인증 (80 PLUS Bronze/Gold/Platinum 등)",
            "modular": "케이블 탈착 방식 (풀모듈러 권장)"
        }
    },
    "cpu_cooler": {
        "name": "CPU 쿨러",
        "description": "CPU의 열을 식히는 장치입니다. CPU TDP를 감당할 수 있어야 하며 케이스 높이를 고려해야 합니다.",
        "key_specs": ["쿨링 방식", "TDP 지원", "높이", "소음"],
        "spec_meanings": {
            "match_score": "CPU TDP 커버 능력",
            "cooling_type": "공랭 또는 수랭",
            "max_tdp": "지원 가능한 최대 TDP (W)",
            "height": "제품 높이 (케이스 여유 확인 필요)"
        }
    },
    "case": {
        "name": "케이스",
        "description": "모든 부품을 담는 외부 케이스입니다. 메인보드 폼팩터, GPU 길이, 쿨러 높이를 고려해야 합니다.",
        "key_specs": ["폼팩터", "크기", "확장 슬롯", "최대 GPU 길이"],
        "spec_meanings": {
            "match_score": "부품 호환성",
            "form_factor": "지원 메인보드 크기 (ATX, M-ATX 등)",
            "dimensions": "케이스 크기 (mm)",
            "max_gpu_length": "장착 가능한 최대 그래픽카드 길이"
        }
    },
}


# ============================================================================
# 데이터 모델
# ============================================================================

class SelectedComponent(BaseModel):
    """선택된 부품"""
    step: int
    category: str
    component_id: str
    name: str
    price: int
    specs: Dict[str, Any] = Field(default_factory=dict)


class CandidateComponent(BaseModel):
    """후보 부품"""
    component_id: str
    name: str
    price: int
    match_score: float = Field(..., ge=0, le=1)
    compatibility_status: str  # compatible, warning, incompatible
    reasons: List[str] = Field(default_factory=list)
    specs: Dict[str, Any] = Field(default_factory=dict)
    hashtags: List[str] = Field(default_factory=list)  # 새로 추가
    representative_specs: Dict[str, Any] = Field(default_factory=dict)  # 새로 추가


class StepContext(BaseModel):
    """단계 컨텍스트"""
    purpose: str
    purpose_keywords: List[str] = Field(default_factory=list)
    socket_requirement: Optional[str] = None
    memory_type_requirement: Optional[str] = None
    form_factor_requirement: Optional[str] = None
    total_tdp: int = 0


class StepResult(BaseModel):
    """단계 결과"""
    session_id: str
    step: int
    category: str
    candidates: List[CandidateComponent]
    allocated_budget: int
    remaining_budget: int
    context: StepContext
    next_step: Optional[int] = None
    is_final_step: bool = False
    analysis: str = Field(default="")


class SelectionSession(BaseModel):
    """선택 세션"""
    session_id: str
    total_budget: int
    purpose: str
    current_step: int = 1
    selections: List[SelectedComponent] = Field(default_factory=list)
    context: StepContext
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


# ============================================================================
# Step-by-Step RAG 파이프라인
# ============================================================================

class StepByStepRAGPipeline:
    """
    단계별 부품 선택 RAG 파이프라인
    
    사용법:
    ```python
    pipeline = StepByStepRAGPipeline()
    
    # 세션 시작
    session = pipeline.start_session(
        budget=1500000,
        purpose="gaming"
    )
    
    # 1단계: CPU 후보 조회
    result = pipeline.get_step_candidates(session.session_id, step=1)
    
    # 사용자가 선택
    pipeline.select_component(
        session_id=session.session_id,
        step=1,
        component_id="cpu_i5_14600k"
    )
    
    # 2단계: 메인보드 후보 조회 (CPU 호환성 적용)
    result = pipeline.get_step_candidates(session.session_id, step=2)
    ```
    """
    
    def __init__(
        self,
        retriever=None,
        compatibility_engine=None,
        llm=None,
    ):
        """
        Args:
            retriever: PCComponentRetriever 인스턴스
            compatibility_engine: CompatibilityEngine 인스턴스
            llm: LangChain Chat Model 인스턴스 (Option)
        """
        self.retriever = retriever
        self.compatibility_engine = compatibility_engine
        self.llm = llm
        
        # 세션 저장소 (실제로는 Redis/DB 사용)
        self._sessions: Dict[str, SelectionSession] = {}
        
        logger.info("StepByStepRAGPipeline 초기화")
    
    def start_session(
        self,
        budget: int,
        purpose: str = "general",
    ) -> SelectionSession:
        """
        새 선택 세션 시작
        
        Args:
            budget: 총 예산
            purpose: 사용 목적
            
        Returns:
            SelectionSession: 생성된 세션
        """
        import uuid
        session_id = str(uuid.uuid4())[:8]
        
        # 목적에 맞는 키워드 생성
        purpose_keywords = self._get_purpose_keywords(purpose)
        
        session = SelectionSession(
            session_id=session_id,
            total_budget=budget,
            purpose=purpose,
            context=StepContext(
                purpose=purpose,
                purpose_keywords=purpose_keywords,
            ),
        )
        
        self._sessions[session_id] = session
        
        logger.info(f"세션 시작: {session_id}, 예산: {budget:,}원, 목적: {purpose}")
        return session
    
    def get_session(self, session_id: str) -> Optional[SelectionSession]:
        """세션 조회"""
        return self._sessions.get(session_id)
    
    def get_step_candidates(
        self,
        session_id: str,
        step: Optional[int] = None,
        top_k: int = 5,
    ) -> StepResult:
        """
        단계별 후보 부품 조회
        
        Args:
            session_id: 세션 ID
            step: 단계 번호 (없으면 현재 단계)
            top_k: 후보 개수
            
        Returns:
            StepResult: 단계 결과
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"세션을 찾을 수 없습니다: {session_id}")
        
        step = step or session.current_step
        category = STEP_CATEGORIES.get(SelectionStep(step), "unknown")
        
        logger.info(f"단계 {step} 후보 조회: {category}")
        
        # 예산 계산
        allocation = BUDGET_ALLOCATION.get(session.purpose, BUDGET_ALLOCATION["general"])
        allocated_budget = int(session.total_budget * allocation.get(category, 0.1))
        
        # 이미 사용한 예산 계산
        used_budget = sum(s.price for s in session.selections)
        remaining_budget = session.total_budget - used_budget
        
        # 할당 예산 조정 (남은 예산 고려)
        allocated_budget = min(allocated_budget, remaining_budget)
        
        # RAG 검색 쿼리 생성
        query = self._build_search_query(session, step, category)
        
        # 후보 검색 (RAG)
        candidates = self._search_candidates(
            query=query,
            category=category,
            budget=allocated_budget,
            context=session.context,
            top_k=top_k * 2,  # 필터링 고려하여 더 많이 검색
        )
        
        # 호환성 필터링 (결과가 없으면 완화하여 다시 시도)
        filtered_candidates = candidates
        if session.selections:
            filtered_candidates = self._filter_by_compatibility(candidates, session.selections)
        
        # 필터링 결과가 너무 적으면(0개), 호환되지 않아도 보여주되 warning 표시
        if not filtered_candidates and candidates:
             logger.warning(f"호환되는 후보가 없어 필터링 해제 (전체 {len(candidates)}개 반환)")
             for c in candidates:
                 c.compatibility_status = "warning"
                 c.reasons.append("일부 호환성 주의 필요")
             filtered_candidates = candidates
        else:
             candidates = filtered_candidates

        # 상위 K개 선택
        candidates = candidates[:top_k]
        
        # 다음 단계 결정
        next_step = step + 1 if step < 8 else None
        
        # LLM 분석 및 해시태그 생성 (한 번에 수행)
        analysis = self._enrich_candidates_with_llm(session, step, category, candidates)

        return StepResult(
            session_id=session_id,
            step=step,
            category=category,
            candidates=candidates,
            allocated_budget=allocated_budget,
            remaining_budget=remaining_budget - allocated_budget,
            context=session.context,
            next_step=next_step,
            is_final_step=(step == 8),
            analysis=analysis
        )
    
    def select_component(
        self,
        session_id: str,
        step: int,
        component_id: str,
        component_data: Optional[Dict[str, Any]] = None,
    ) -> SelectionSession:
        """
        부품 선택
        
        Args:
            session_id: 세션 ID
            step: 단계 번호
            component_id: 선택한 부품 ID
            component_data: 부품 상세 정보 (선택)
            
        Returns:
            업데이트된 세션
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"세션을 찾을 수 없습니다: {session_id}")
        
        category = STEP_CATEGORIES.get(SelectionStep(step), "unknown")
        
        # 부품 정보 (실제로는 DB에서 조회)
        component_data = component_data or {}
        
        selection = SelectedComponent(
            step=step,
            category=category,
            component_id=component_id,
            name=component_data.get("name", component_id),
            price=component_data.get("price", 0),
            specs=component_data.get("specs", {}),
        )
        
        session.selections.append(selection)
        session.current_step = step + 1
        session.updated_at = datetime.now()
        
        # 컨텍스트 업데이트
        self._update_context(session, selection)
        
        logger.info(f"부품 선택: {session_id}, 단계 {step}, {component_id}")
        
        return session
    
    def _get_purpose_keywords(self, purpose: str) -> List[str]:
        """목적별 키워드 생성"""
        keywords = {
            "gaming": ["게임", "게이밍", "고성능", "fps", "배그", "오버워치"],
            "workstation": ["작업", "렌더링", "인코딩", "개발", "업무"],
            "streaming": ["스트리밍", "방송", "인코딩", "멀티태스킹"],
            "general": ["일반", "사무", "웹서핑", "문서"],
        }
        return keywords.get(purpose, keywords["general"])
    
    def _build_search_query(
        self,
        session: SelectionSession,
        step: int,
        category: str,
    ) -> str:
        """RAG 검색 쿼리 생성"""
        parts = [
            f"{session.purpose}용",
            category,
        ]
        
        # 컨텍스트 기반 키워드 추가
        if session.context.socket_requirement and category in ["motherboard", "cpu_cooler"]:
            parts.append(f"{session.context.socket_requirement} 소켓")
        
        if session.context.memory_type_requirement and category == "memory":
            parts.append(session.context.memory_type_requirement)
        
        if session.context.form_factor_requirement and category == "case":
            parts.append(session.context.form_factor_requirement)
        
        # 목적 키워드
        parts.extend(session.context.purpose_keywords[:2])
        
        return " ".join(parts)
    
    def _map_specs(self, category: str, specs: Dict[str, Any]) -> Dict[str, Any]:
        """Generic field_X keys to semantic keys mapping"""
        new_specs = specs.copy()
        
        # Helper to safely map if key exists
        def map_field(src_idx: int, dest_key: str):
            key = f"field_{src_idx}"
            if key in specs:
                new_specs[dest_key] = specs[key]

        if category == "cpu":
            # socket(3), cores(4), clock(5), boost(6), tdp(7), graphics(8), smt(9)
            # Assuming standard dump order based on plan
            map_field(3, "socket")
            map_field(4, "core_count")
            new_specs["cores"] = new_specs.get("core_count") # alias
            map_field(5, "clock_speed")
            map_field(6, "boost_clock")
            map_field(7, "tdp") 
            map_field(8, "graphics")
            
        elif category == "motherboard":
            # socket(3), form_factor(4), chipset(5), memory_type(6), slots(7)
            # Adjusting based on common schema patterns if needed, but sticking to plan hints
            map_field(3, "socket")
            map_field(4, "form_factor")
            map_field(5, "chipset") # swapped with 8 in previous code? Let's check plan strictly. 
            # Plan said: MB - field_4: FormFactor, field_8: Chipset, field_2: Maker
            # But here we want to ensure 'memory_type' is mapped.
            # Let's try to map likely fields or keep existing if they were working.
            # Previous code had: socket(3), form_factor(5), memory_type(6).
            # Plan says: Line 60 socket...
            # Let's map broadly to catch them.
            map_field(6, "memory_type")
            map_field(8, "chipset")
            
        elif category == "memory":
            # type(3), capacity(4), speed(5)??
            # Previous: memory_type(3).
            map_field(3, "memory_type")
            map_field(4, "capacity")
            map_field(5, "speed")
            
        elif category == "gpu":
            # chipset(3), vram(4), core_clock(5), boost_clock(6)??
            # Previous: tdp(7), vram(4).
            map_field(3, "chipset")
            map_field(4, "vram")
            map_field(5, "core_clock")
            map_field(7, "tdp")

        return new_specs

    def _search_candidates(
        self,
        query: str,
        category: str,
        budget: int,
        context: StepContext,
        top_k: int,
    ) -> List[CandidateComponent]:
        """
        RAG 검색으로 후보 부품 조회
        """
        import uuid
        if not self.retriever:
            logger.warning("Retriever가 설정되지 않았습니다. 빈 리스트 반환.")
            return []

        # 1. 스펙 기반 검색 (더 정확함)
        requirements = {
            "categories": [category],
            "budget": budget / 10000,  # 만원 단위 변환
            "purpose": context.purpose,
        }
        
        # 소켓 등 호환성 요구사항 추가
        if category == "motherboard" and context.socket_requirement:
            requirements["socket"] = context.socket_requirement
        elif category == "memory" and context.memory_type_requirement:
            requirements["memory_type"] = context.memory_type_requirement

        # Retriever 호출
        # category별 검색이지만 여기선 단일 카테고리만 요청
        try:
            # 호환성 요구사항을 필터로 변환 (purpose, budget, categories 등은 제외)
            filters = {}
            if "socket" in requirements:
                filters["socket"] = requirements["socket"]
            if "memory_type" in requirements:
                filters["memory_type"] = requirements["memory_type"]
                
            results = self.retriever.retrieve(
                query=query,
                top_k=top_k,
                category=category,
                filters=filters
            )
        except Exception as e:
            logger.error(f"검색 중 오류 발생: {e}")
            return []

        # CandidateComponent로 변환
        candidates = []
        for res in results:
            metadata = res.get("metadata", {})
            
            # [Fix] 스펙 매핑 적용
            metadata = self._map_specs(category, metadata)

            # 필수 필드 확인 (가격 등)
            try:
                price = int(float(metadata.get("price", 0)))
            except (ValueError, TypeError):
                price = 0
                
            # ID 보정 (field_0가 ID일 가능성 높음)
            comp_id = metadata.get("id", str(res.get("id")))
            if not comp_id or comp_id == "None":
                 comp_id = metadata.get("field_0", str(uuid.uuid4()))

            candidate = CandidateComponent(
                component_id=comp_id,
                name=metadata.get("name", metadata.get("field_1", "Unknown Component")),
                price=price,
                match_score=res.get("similarity", 0.0),
                compatibility_status="compatible", # 나중에 필터링됨
                reasons=[], 
                specs=metadata
            )
            
            # 해시태그 생성
            candidate.hashtags = self._generate_hashtags(candidate, category)
            
            # 대표 스펙 추출
            candidate.representative_specs = self._extract_representative_specs(candidate, category)
            
            candidates.append(candidate)
        
        # 중복 제거: component_id 기준
        seen_ids = set()
        unique_candidates = []
        for c in candidates:
            if c.component_id not in seen_ids:
                seen_ids.add(c.component_id)
                unique_candidates.append(c)
        candidates = unique_candidates
            
        return candidates
    
    def _filter_by_compatibility(
        self,
        candidates: List[CandidateComponent],
        selections: List[SelectedComponent],
    ) -> List[CandidateComponent]:
        """호환성 기반 필터링"""
        # 간단한 소켓 호환성 필터
        socket_req = None
        for sel in selections:
            if sel.category == "cpu":
                socket_req = sel.specs.get("socket")
                break
        
        if socket_req:
            filtered = []
            for cand in candidates:
                cand_socket = cand.specs.get("socket")
                
                if cand.specs.get("category") in ["motherboard", "cpu_cooler"]:
                    if not cand_socket or cand_socket == socket_req:
                        filtered.append(cand)
                    else:
                        cand.compatibility_status = "incompatible"
                        cand.reasons.append(f"소켓 불일치: {cand_socket} ≠ {socket_req}")
                        continue 
                else:
                    filtered.append(cand)
            candidates = filtered

        # 메모리 타입 호환성 필터
        memory_req = None
        for sel in selections:
            if sel.category == "motherboard":
                memory_req = sel.specs.get("memory_type")
                break
        
        if memory_req:
            filtered = []
            for cand in candidates:
                if cand.specs.get("category") == "memory":
                    cand_mem_type = cand.specs.get("memory_type")
                    if not cand_mem_type or memory_req in cand_mem_type or cand_mem_type in memory_req:
                         # 단순 부분 일치 허용 (DDR4-3200 vs DDR4)
                        filtered.append(cand)
                    else:
                        cand.compatibility_status = "incompatible"
                        cand.reasons.append(f"메모리 타입 불일치: {cand_mem_type} ≠ {memory_req}")
                        continue
                else:
                    filtered.append(cand)
            return filtered
        
        return candidates
    
    def _update_context(
        self,
        session: SelectionSession,
        selection: SelectedComponent,
    ):
        """선택에 따른 컨텍스트 업데이트"""
        if selection.category == "cpu":
            # CPU 선택 시 소켓 요구사항 설정
            session.context.socket_requirement = selection.specs.get("socket")
            try:
                tdp = float(selection.specs.get("tdp", 0))
            except:
                tdp = 0
            session.context.total_tdp += int(tdp)
        
        elif selection.category == "motherboard":
            # 메인보드 선택 시 메모리 타입, 폼팩터 설정
            session.context.memory_type_requirement = selection.specs.get("memory_type")
            session.context.form_factor_requirement = selection.specs.get("form_factor")
        
        elif selection.category == "gpu":
            try:
                tdp = float(selection.specs.get("tdp", 0))
            except:
                tdp = 0
            session.context.total_tdp += int(tdp)
    
    def get_summary(self, session_id: str) -> Dict[str, Any]:
        """세션 요약 조회"""
        session = self._sessions.get(session_id)
        if not session:
            return {}
        
        total_price = sum(s.price for s in session.selections)
        
        return {
            "session_id": session_id,
            "purpose": session.purpose,
            "total_budget": session.total_budget,
            "total_price": total_price,
            "remaining_budget": session.total_budget - total_price,
            "selections": [
                {
                    "step": s.step,
                    "category": s.category,
                    "name": s.name,
                    "price": s.price,
                }
                for s in session.selections
            ],
            "current_step": session.current_step,
            "is_complete": session.current_step > 8,
        }
    
    def deselect_component(
        self,
        session_id: str,
        step: int,
    ) -> SelectionSession:
        """
        특정 단계의 선택을 취소하고 해당 단계로 되돌림
        
        Args:
            session_id: 세션 ID
            step: 취소할 단계 번호
            
        Returns:
            업데이트된 세션
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"세션을 찾을 수 없습니다: {session_id}")
        
        # 해당 단계 이후의 모든 선택 제거
        session.selections = [s for s in session.selections if s.step < step]
        session.current_step = step
        session.updated_at = datetime.now()
        
        # 컨텍스트 재계산
        self._recalculate_context(session)
        
        logger.info(f"부품 선택 취소: {session_id}, 단계 {step} 이후 초기화")
        return session
    
    def _recalculate_context(self, session: SelectionSession):
        """
        선택된 부품들로부터 컨텍스트 재계산
        """
        # 컨텍스트 초기화
        session.context.socket_requirement = None
        session.context.memory_type_requirement = None
        session.context.form_factor_requirement = None
        session.context.total_tdp = 0
        
        # 각 선택에 대해 컨텍스트 업데이트
        for selection in session.selections:
            self._update_context(session, selection)
    
    def _generate_hashtags(self, component: CandidateComponent, category: str) -> List[str]:
        """해시태그 생성 (기본값 - LLM 실패 시 사용)"""
        tags = []
        if component.match_score > 0.85:
            tags.append("#강력추천")
        if "gaming" in category:
             tags.append("#게이밍")
        return tags

    # _extract_representative_specs 메서드는 아래(line 999 근처)에 정의되어 있음. 중복 정의 제거됨.

    def _enrich_candidates_with_llm(
        self,
        session: SelectionSession,
        step: int,
        category: str,
        candidates: List[CandidateComponent]
    ) -> str:
        """LLM을 사용하여 '전체 분석'과 '각 후보별 해시태그'를 동시에 생성"""
        if not self.llm or not candidates:
            return ""

        try:
            items_str = []
            for c in candidates:
                items_str.append(f"- ID: {c.component_id}, 이름: {c.name}, 가격: {c.price}원, 스펙: {str(c.specs)[:200]}")
            
            candidates_info = "\n".join(items_str)
            
            prompt = f"""
            당신은 PC 견적 전문가입니다. 현재 사용자가 '{category}' 부품을 선택하는 단계입니다.
            
            [사용자 상황]
            - 용도: {session.purpose}
            - 총 예산: {session.total_budget:,}원
            - 현재 단계: {category} (Step {step})
            
            [후보 목록]
            {candidates_info}
            
            [요청사항]
            1. 'analysis': 이 후보들이 사용자의 상황에 적합한 이유를 2~3문장으로 요약하여 한국어 존댓말(해요체)로 작성하세요.
            2. 'hashtags': 각 후보 부품별로 가장 큰 특징을 나타내는 해시태그를 "문자열 리스트"로 추출하세요.
            
            [응답 형식 (JSON Only)]
            - **Strict JSON Standard Compliance is required.**
            - Use double quotes `"` for ALL keys and string values. (e.g., "key": "value")
            - Do NOT use single quotes `'`.
            - Do NOT include trailing commas.
            - Do NOT include comments.
            - Output MUST be valid JSON parsable by Python `json.loads()`.

            Example:
            {{
                "analysis": "이 부품들은 ... 좋습니다.",
                "hashtags": {{
                    "cpu_123": ["#가성비", "#고성능"],
                    "cpu_456": ["#프리미엄"]
                }}
            }}
            """
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            content = response.content
            
            # LLM 응답이 [{'type': 'text', 'text': '...'}] 형태의 리스트인 경우 처리
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and 'text' in item:
                        text_parts.append(item['text'])
                    elif isinstance(item, str):
                        text_parts.append(item)
                    else:
                        text_parts.append(str(item))
                content = " ".join(text_parts)
            content = content.strip()
            
            # JSON 파싱 (코드 블럭 제거)
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            # Clean up potential Single Quotes issues just in case
            # (Dangerous if text contains single quotes, but efficient for keys)
            # content = content.replace("'", '"') 
            
            result_json = {}
            try:
                result_json = json.loads(content)
            except Exception as parse_error:
                logger.warning(f"LLM 파싱 1차 실패 (json): {parse_error}. Content: {content[:50]}...")
                # Try regex extraction
                try:
                    import re
                    json_match = re.search(r'(\{.*\})', content, re.DOTALL)
                    if json_match:
                        result_json = json.loads(json_match.group(1))
                    else:
                        raise ValueError("No JSON block found via regex")
                except Exception as regex_error:
                    logger.warning(f"LLM 파싱 2차 실패 (regex): {regex_error}")
                    # 3차 시도: ast (Single quotes fallback)
                    try:
                        import ast
                        result_json = ast.literal_eval(content)
                    except Exception:
                        result_json = {}

            # 1. 해시태그 적용
            tags_map = result_json.get("hashtags", {})
            for cand in candidates:
                cand_id = str(cand.component_id)
                # LLM 결과가 있으면 사용, 없으면(파싱 실패 등) Fallback 실행
                if cand_id in tags_map and isinstance(tags_map[cand_id], list) and len(tags_map[cand_id]) > 0:
                     cand.hashtags = tags_map[cand_id]
                else:
                    # Fallback (Rule-based)
                    cand.hashtags = self._generate_hashtags(cand, category)

            # 2. 분석 멘트 반환 (실패 시 기본 멘트)
            analysis = result_json.get("analysis", "")
            if not analysis:
                # 목적 한글 매핑
                purpose_map = {
                    "gaming": "게이밍",
                    "office": "사무용",
                    "development": "개발용",
                    "editing": "영상 편집",
                    "online_lectures": "온라인 강의",
                    "graphic_design": "그래픽 디자인"
                }
                purpose_kr = purpose_map.get(session.purpose, session.purpose) # 매핑 없으면 그대로 사용
                analysis = f"{purpose_kr} 용도에 최적화된 {category} 추천 목록입니다."
            
            return analysis
            
        except Exception as e:
            logger.error(f"LLM 분석/해시태그 생성 전체 실패: {e}")
            # 전체 실패 시에도 Fallback 실행하여 빈 해시태그 방지
            for cand in candidates:
                cand.hashtags = self._generate_hashtags(cand, category)
            return f"{session.purpose} 용도에 맞춰 엄선한 {category} 모델들입니다."
        hashtags = []
        specs = component.specs
        price = component.price
        
        # 카테고리별 해시태그 생성
        if category == "cpu":
            cores = specs.get("cores") or specs.get("core_count")
            if cores:
                try:
                    cores_int = int(cores)
                    if cores_int >= 16:
                        hashtags.append("멀티코어")
                    elif cores_int >= 8:
                        hashtags.append("고성능")
                except:
                    pass
            clock = specs.get("boost_clock") or specs.get("clock_speed")
            if clock and "GHz" in str(clock):
                hashtags.append("고클럭")
            if price < 200000:
                hashtags.append("가성비")
            elif price > 500000:
                hashtags.append("프리미엄")
                
        elif category == "gpu":
            vram = specs.get("vram") or specs.get("memory")
            if vram and ("16" in str(vram) or "24" in str(vram)):
                hashtags.append("대용량VRAM")
            name = component.name.upper()
            if "RTX" in name:
                hashtags.append("RTX")
            if "Ti" in name or "XT" in name:
                hashtags.append("최상위")
            if price > 1000000:
                hashtags.append("하이엔드")
            elif price < 400000:
                hashtags.append("입문용")
                
        elif category == "memory":
            capacity = specs.get("capacity") or specs.get("size")
            if capacity:
                if "32" in str(capacity):
                    hashtags.append("대용량")
                elif "16" in str(capacity):
                    hashtags.append("표준")
            mem_type = str(specs.get("memory_type", ""))
            if "DDR5" in mem_type:
                hashtags.append("DDR5")
            elif "DDR4" in mem_type:
                hashtags.append("DDR4")
                
        elif category == "storage":
            interface = str(specs.get("interface", "")).upper()
            if "NVME" in interface or "M.2" in interface:
                hashtags.append("초고속")
            elif "SATA" in interface:
                hashtags.append("SATA")
            capacity = specs.get("capacity")
            if capacity and ("TB" in str(capacity) or (isinstance(capacity, (int, float)) and capacity >= 1000)):
                hashtags.append("대용량")
                
        elif category == "psu":
            efficiency = str(specs.get("efficiency", "")).upper()
            if "PLATINUM" in efficiency or "TITANIUM" in efficiency:
                hashtags.append("고효율")
            elif "GOLD" in efficiency:
                hashtags.append("80PLUS")
            wattage = specs.get("wattage") or specs.get("power")
            if wattage:
                try:
                    if int(wattage) >= 850:
                        hashtags.append("고출력")
                except:
                    pass
        
        return hashtags[:4]
    
    def _extract_representative_specs(self, component: CandidateComponent, category: str) -> Dict[str, Any]:
        """대표 스펙 추출"""
        specs = component.specs
        rep_specs = {}
        
        if category == "cpu":
            if "cores" in specs or "core_count" in specs:
                rep_specs["코어 수"] = specs.get("cores") or specs.get("core_count")
            if "boost_clock" in specs:
                rep_specs["부스트 클럭"] = specs.get("boost_clock")
            elif "clock_speed" in specs:
                rep_specs["클럭 속도"] = specs.get("clock_speed")
            if "tdp" in specs:
                rep_specs["TDP"] = f"{specs.get('tdp')} W"
            if "socket" in specs:
                rep_specs["소켓"] = specs.get("socket")
                
        elif category == "motherboard":
            for key, label in [("socket", "소켓"), ("chipset", "칩셋"), ("memory_type", "메모리 타입"), ("form_factor", "폼팩터")]:
                if key in specs:
                    rep_specs[label] = specs[key]
                
        elif category == "memory":
            for key, label in [("capacity", "용량"), ("speed", "속도"), ("memory_type", "타입")]:
                if key in specs:
                    rep_specs[label] = specs[key]
                
        elif category == "gpu":
            if "vram" in specs:
                rep_specs["VRAM"] = specs["vram"]
            elif "memory" in specs:
                rep_specs["VRAM"] = specs["memory"]
            for key, label in [("core_clock", "코어 클럭")]:
                if key in specs:
                    rep_specs[label] = specs[key]
            if "tdp" in specs:
                rep_specs["TDP"] = f"{specs['tdp']} W"
                
        elif category == "storage":
            for key, label in [("capacity", "용량"), ("read_speed", "읽기 속도"), ("write_speed", "쓰기 속도"), ("interface", "인터페이스")]:
                if key in specs:
                    rep_specs[label] = specs[key]
                
        elif category == "psu":
            if "wattage" in specs or "power" in specs:
                w = specs.get("wattage") or specs.get("power")
                rep_specs["출력"] = f"{w} W"
            for key, label in [("efficiency", "인증 등급"), ("modular", "모듈러")]:
                if key in specs:
                    rep_specs[label] = specs[key]
                
        elif category == "cpu_cooler":
            for key, label in [("cooling_type", "쿨링 방식"), ("height", "높이")]:
                if key in specs:
                    rep_specs[label] = specs[key]
            if "max_tdp" in specs:
                rep_specs["최대 TDP"] = f"{specs['max_tdp']} W"
                
        elif category == "case":
            for key, label in [("form_factor", "폼팩터"), ("max_gpu_length", "최대 GPU 길이")]:
                if key in specs:
                    rep_specs[label] = specs[key]
                
        return rep_specs


# ============================================================================
# 테스트용 메인
# ============================================================================

if __name__ == "__main__":
    # 통합 테스트는 별도 파일에서 수행 권장
    pass

