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
from loguru import logger
from pydantic import BaseModel, Field

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
    CASE = 7
    CPU_COOLER = 8


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
    ):
        """
        Args:
            retriever: PCComponentRetriever 인스턴스
            compatibility_engine: CompatibilityEngine 인스턴스
        """
        self.retriever = retriever
        self.compatibility_engine = compatibility_engine
        
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
        
        # 호환성 필터링
        if session.selections:
            candidates = self._filter_by_compatibility(
                candidates,
                session.selections,
            )
        
        # 상위 K개 선택
        candidates = candidates[:top_k]
        
        # 다음 단계 결정
        next_step = step + 1 if step < 8 else None
        
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
            
            # 필수 필드 확인 (가격 등)
            try:
                price = int(metadata.get("price", 0))
            except (ValueError, TypeError):
                price = 0
                
            candidates.append(
                CandidateComponent(
                    component_id=metadata.get("id", str(res.get("id"))),
                    name=metadata.get("name", "Unknown Component"),
                    price=price,
                    match_score=res.get("similarity", 0.0),
                    compatibility_status="compatible", # 나중에 필터링됨
                    reasons=[], # AI가 생성하거나 룰베이스로 추가 가능
                    specs=metadata
                )
            )
            
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


# ============================================================================
# 테스트용 메인
# ============================================================================

if __name__ == "__main__":
    # 통합 테스트는 별도 파일에서 수행 권장
    pass

