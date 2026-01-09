"""
FastAPI 기반 RAG API 서버
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles  # <--- 추가
from fastapi.responses import FileResponse   # <--- 추가
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from loguru import logger
import sys
import os

from rag.pipeline import RAGPipeline
from rag.step_by_step import StepByStepRAGPipeline, CATEGORY_INFO
from modules.multi_agent.orchestrator import AgentOrchestrator, RecommendationResult
from modules.genai.image_generator import ImageGenerator
from langchain_google_genai import ChatGoogleGenerativeAI

# 로깅 설정
logger.remove()
logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
)

# FastAPI 앱 생성
app = FastAPI(
    title="Spckit AI - PC 부품 추천 API",
    description="RAG 기반 PC 부품 추천 시스템",
    version="1.0.0",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# RAG 파이프라인 전역 인스턴스
pipeline: Optional[RAGPipeline] = None
step_pipeline: Optional[StepByStepRAGPipeline] = None
orchestrator: Optional[AgentOrchestrator] = None
image_generator: Optional[ImageGenerator] = None


# Pydantic 모델 정의
class QueryRequest(BaseModel):
    query: str = Field(..., description="사용자 쿼리", min_length=1)
    top_k: int = Field(5, description="검색할 부품 수", ge=1, le=20)
    category: Optional[str] = Field(None, description="특정 카테고리로 제한")
    include_context: bool = Field(False, description="검색된 원본 데이터 포함 여부")


class SpecsRequest(BaseModel):
    budget: Optional[int] = Field(None, description="예산 (만원)")
    purpose: Optional[str] = Field(None, description="사용 목적")
    categories: List[str] = Field(
        ["cpu", "gpu", "memory"], description="검색할 카테고리 리스트"
    )
    preferences: Optional[str] = Field(None, description="추가 선호사항")
    top_k: int = Field(3, description="각 카테고리별 검색 결과 수", ge=1, le=10)


class CompareRequest(BaseModel):
    component_ids: List[str] = Field(..., description="비교할 부품 ID 리스트", min_items=2)


# Step-by-Step 관련 모델
class StepStartRequest(BaseModel):
    budget: int = Field(..., description="총 예산 (원)", ge=100000)
    purpose: str = Field("general", description="사용 목적 (gaming, workstation, general)")


class StepSelectRequest(BaseModel):
    step: int = Field(..., description="현재 단계 번호", ge=1, le=8)
    component_id: str = Field(..., description="선택한 부품 ID")
    component_data: Optional[Dict[str, Any]] = Field(None, description="부품 상세 정보")


class AgentChatRequest(BaseModel):
    query: str = Field(..., description="사용자 요청 메시지")
    budget: Optional[int] = Field(None, description="예산 (원)")
    purpose: Optional[str] = Field(None, description="주용도 (gaming, workstation, etc)")
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict, description="추가 선호사항")


# Step-by-Step 새 API 모델
class StepRequest(BaseModel):
    """단계별 부품 선택 요청"""
    session_id: Optional[str] = Field(None, description="세션 ID (첫 호출 시 None)")
    query: str = Field(..., description="초기 요구사항 또는 선택 의도")
    current_step: int = Field(0, description="현재 단계 (0: 세션 시작, 1-8: 각 단계)", ge=0, le=8)
    selected_component_id: Optional[str] = Field(None, description="이전 단계에서 선택한 부품 ID")
    budget: Optional[int] = Field(None, description="예산 (원)")
    purpose: Optional[str] = Field(None, description="목적 (gaming, workstation, etc)")


class ComponentCandidate(BaseModel):
    """부품 후보 정보"""
    id: str
    name: str
    price: int
    category: str
    match_score: float
    specs: Dict[str, Any] = Field(default_factory=dict)
    hashtags: List[str] = Field(default_factory=list)
    representative_specs: Dict[str, Any] = Field(default_factory=dict)
    compatibility_status: str = Field("compatible", description="compatible, warning, incompatible")
    danawa_url: Optional[str] = Field(None, description="다나와 제품 페이지 URL")
    image_url: Optional[str] = Field(None, description="제품 이미지 URL")


class StepResponse(BaseModel):
    """단계별 응답"""
    session_id: str
    step: int
    step_name: str
    candidates: List[ComponentCandidate]
    analysis: str
    is_final: bool
    total_price: int = 0
    category_description: Optional[str] = None
    category_description: Optional[str] = None
    spec_meanings: Optional[Dict[str, str]] = None


class GenerateImageRequest(BaseModel):
    """이미지 생성 요청"""
    components: List[Dict[str, Any]] = Field(..., description="선택된 부품 목록")
    purpose: str = Field("gaming", description="사용 목적")


# 이벤트 핸들러
@app.on_event("startup")
async def startup_event():
    """앱 시작 시 RAG 파이프라인 초기화 및 벡터 DB 자동 초기화"""
    global pipeline, step_pipeline, orchestrator  # [수정] orchestrator 추가
    logger.info("=" * 60)
    logger.info("🚀 RAG 파이프라인 초기화 중...")
    logger.info("=" * 60)
    
    try:
        # 환경 확인
        environment = os.getenv("ENVIRONMENT", "development")
        auto_init = os.getenv("AUTO_INIT_DB", "true" if environment == "development" else "false")
        auto_init = auto_init.lower() == "true"
        
        # RAG 파이프라인 초기화
        pipeline = RAGPipeline()
        
        # 벡터 DB 상태 확인
        try:
            stats = pipeline.get_stats()
            doc_count = stats.get("total_documents", 0)
        except Exception:
            doc_count = 0
        
        # 벡터 DB가 비어있고 자동 초기화가 활성화된 경우
        if doc_count == 0:
            if auto_init:
                logger.warning("⚠️  벡터 데이터베이스가 비어있습니다.")
                logger.info("🔧 개발 모드: 자동 초기화를 시작합니다...")
                logger.info("⏱️  이 작업은 약 10-15분이 소요될 수 있습니다.")
                logger.info("📊 135,660개의 문서를 임베딩하는 중입니다...")
                logger.info("")
                
                try:
                    result = pipeline.initialize_database(force_rebuild=True)
                    logger.info("")
                    logger.success("✅ 벡터 데이터베이스 초기화 완료!")
                    logger.info(f"📈 총 문서 수: {result.get('total_documents', 0)}개")
                except Exception as init_error:
                    logger.error("❌ 벡터 DB 자동 초기화 실패")
                    logger.error(f"오류 내용: {str(init_error)}")
                    logger.error("")
                    logger.error("수동으로 초기화하려면 다음 명령어를 실행하세요:")
                    logger.error("  python backend/scripts/init_database.py")
                    raise RuntimeError(f"벡터 DB 자동 초기화 실패: {str(init_error)}")
            else:
                logger.error("❌ 벡터 데이터베이스가 비어있습니다!")
                logger.error("")
                logger.error("다음 명령어로 수동 초기화하세요:")
                logger.error("  python backend/scripts/init_database.py")
                logger.error("")
                logger.error("또는 환경 변수를 설정하세요:")
                logger.error("  AUTO_INIT_DB=true")
                raise RuntimeError("벡터 데이터베이스가 초기화되지 않았습니다.")
        else:
            logger.success(f"✅ RAG 파이프라인 초기화 완료!")
            logger.info(f"📊 벡터 DB 문서 수: {doc_count}개")
        
        # LLM 모델 초기화
        llm_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        llm = None
        if llm_api_key:
            llm = ChatGoogleGenerativeAI(
                model=os.getenv("GENERATION_MODEL", "gemini-1.5-flash"),
                temperature=0.7,
                google_api_key=llm_api_key
            )

        # Step-by-Step 파이프라인 초기화
        step_pipeline = StepByStepRAGPipeline(
            retriever=pipeline.retriever,
            compatibility_engine=None,
            llm=llm
        )
        logger.info("✅ Step-by-Step 파이프라인 초기화 완료!")

        # 이미지 생성기 초기화
        image_generator = ImageGenerator(api_key=llm_api_key)
        logger.info("🎨 이미지 생성기 초기화 완료!")

        # 멀티 에이전트 오케스트레이터 초기화
        orchestrator = AgentOrchestrator(verbose=True)
        logger.info("🤖 멀티 에이전트 오케스트레이터 초기화 완료!")
        
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ RAG 파이프라인 초기화 실패: {str(e)}")
        logger.error("=" * 60)
        raise


# API 엔드포인트
@app.get("/")
async def root():
    """헬스 체크"""
    return {
        "service": "Spckit AI - PC Component Recommendation API",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/health")
async def health_check():
    """시스템 상태 확인"""
    if pipeline is None:
        raise HTTPException(status_code=503, detail="RAG 파이프라인이 초기화되지 않았습니다.")

    try:
        stats = pipeline.get_stats()
        return {
            "status": "healthy",
            "pipeline": "initialized",
            "database": stats,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상태 확인 실패: {str(e)}")


@app.post("/query")
async def query_components(request: QueryRequest) -> Dict[str, Any]:
    """
    PC 부품 추천 쿼리

    사용자의 자연어 쿼리를 받아 관련 부품을 검색하고 추천을 생성합니다.
    """
    if pipeline is None:
        raise HTTPException(status_code=503, detail="RAG 파이프라인이 초기화되지 않았습니다.")

    try:
        logger.info(f"쿼리 요청: '{request.query}'")
        result = pipeline.query(
            user_query=request.query,
            top_k=request.top_k,
            category=request.category,
            include_context=request.include_context,
        )
        return result
    except Exception as e:
        logger.error(f"쿼리 처리 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"쿼리 처리 실패: {str(e)}")


@app.post("/query-by-specs")
async def query_by_specifications(request: SpecsRequest) -> Dict[str, Any]:
    """
    사양 기반 부품 추천

    예산, 목적 등의 사양을 기반으로 최적의 부품 조합을 추천합니다.
    """
    if pipeline is None:
        raise HTTPException(status_code=503, detail="RAG 파이프라인이 초기화되지 않았습니다.")

    try:
        requirements = {
            "budget": request.budget,
            "purpose": request.purpose,
            "categories": request.categories,
            "preferences": request.preferences,
        }

        logger.info(f"사양 기반 쿼리: {requirements}")
        result = pipeline.query_by_specs(
            requirements=requirements,
            top_k=request.top_k,
        )
        return result
    except Exception as e:
        logger.error(f"사양 기반 쿼리 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"쿼리 처리 실패: {str(e)}")


@app.post("/compare")
async def compare_components(request: CompareRequest) -> Dict[str, Any]:
    """
    부품 비교

    여러 부품을 비교 분석하여 각각의 장단점과 추천 대상을 제시합니다.
    """
    if pipeline is None:
        raise HTTPException(status_code=503, detail="RAG 파이프라인이 초기화되지 않았습니다.")

    try:
        logger.info(f"부품 비교: {len(request.component_ids)}개")
        result = pipeline.compare_components(component_ids=request.component_ids)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"부품 비교 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"비교 실패: {str(e)}")


@app.get("/stats")
async def get_statistics() -> Dict[str, Any]:
    """
    시스템 통계 조회

    벡터 데이터베이스의 통계 정보를 반환합니다.
    """
    if pipeline is None:
        raise HTTPException(status_code=503, detail="RAG 파이프라인이 초기화되지 않았습니다.")

    try:
        stats = pipeline.get_stats()
        return stats
    except Exception as e:
        logger.error(f"통계 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")


# =============================================================================
# Step-by-Step API 엔드포인트
# =============================================================================

@app.post("/step/start")
async def start_step_session(request: StepStartRequest) -> Dict[str, Any]:
    """
    Step-by-Step 세션 시작
    
    예산과 목적을 받아 새 세션을 생성하고 CPU 선택 단계를 시작합니다.
    """
    if step_pipeline is None:
        raise HTTPException(status_code=503, detail="Step-by-Step 파이프라인이 초기화되지 않았습니다.")
    
    try:
        logger.info(f"Step 세션 시작: 예산={request.budget:,}원, 목적={request.purpose}")
        session = step_pipeline.start_session(
            budget=request.budget,
            purpose=request.purpose
        )
        
        # 첫 단계(CPU) 후보 자동 조회
        candidates_result = step_pipeline.get_step_candidates(
            session_id=session.session_id,
            step=1
        )
        
        return {
            "session_id": session.session_id,
            "step": 1,
            "category": "cpu",
            "candidates": [c.model_dump() for c in candidates_result.candidates],
            "allocated_budget": candidates_result.allocated_budget,
            "remaining_budget": candidates_result.remaining_budget,
            "next_step": candidates_result.next_step,
            "message": "CPU 선택 단계입니다. 위 후보 중 하나를 선택해주세요."
        }
        
    except Exception as e:
        logger.error(f"Step 세션 시작 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"세션 시작 실패: {str(e)}")


@app.get("/step/{session_id}/candidates")
async def get_step_candidates(
    session_id: str,
    step: Optional[int] = None,
    top_k: int = 5
) -> Dict[str, Any]:
    """
    현재 단계의 후보 부품 조회
    """
    if step_pipeline is None:
        raise HTTPException(status_code=503, detail="Step-by-Step 파이프라인이 초기화되지 않았습니다.")
    
    try:
        result = step_pipeline.get_step_candidates(
            session_id=session_id,
            step=step,
            top_k=top_k
        )
        
        # 카테고리 정보 추가
        category_info = CATEGORY_INFO.get(result.category, {})
        
        return {
            "session_id": result.session_id,
            "step": result.step,
            "category": result.category,
            "category_name": category_info.get("name", result.category),
            "category_description": category_info.get("description", ""),
            "key_specs": category_info.get("key_specs", []),
            "spec_meanings": category_info.get("spec_meanings", {}),
            "candidates": [c.model_dump() for c in result.candidates],
            "allocated_budget": result.allocated_budget,
            "remaining_budget": result.remaining_budget,
            "next_step": result.next_step,
            "is_final_step": result.is_final_step
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"후보 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"후보 조회 실패: {str(e)}")


@app.post("/step/{session_id}/select")
async def select_component(
    session_id: str,
    request: StepSelectRequest
) -> Dict[str, Any]:
    """
    부품 선택 및 다음 단계로 진행
    """
    if step_pipeline is None:
        raise HTTPException(status_code=503, detail="Step-by-Step 파이프라인이 초기화되지 않았습니다.")
    
    try:
        logger.info(f"부품 선택: 세션={session_id}, 단계={request.step}, ID={request.component_id}")
        
        session = step_pipeline.select_component(
            session_id=session_id,
            step=request.step,
            component_id=request.component_id,
            component_data=request.component_data
        )
        
        # 다음 단계 후보 자동 조회 (8단계 완료 시 제외)
        if session.current_step <= 8:
            next_result = step_pipeline.get_step_candidates(
                session_id=session_id,
                step=session.current_step
            )
            
            # 카테고리 정보 추가
            category_info = CATEGORY_INFO.get(next_result.category, {})
            
            return {
                "session_id": session_id,
                "selected_step": request.step,
                "next_step": session.current_step,
                "category": next_result.category,
                "category_name": category_info.get("name", next_result.category),
                "category_description": category_info.get("description", ""),
                "key_specs": category_info.get("key_specs", []),
                "spec_meanings": category_info.get("spec_meanings", {}),
                "candidates": [c.model_dump() for c in next_result.candidates],
                "allocated_budget": next_result.allocated_budget,
                "remaining_budget": next_result.remaining_budget,
                "is_final_step": next_result.is_final_step,
                "selections_count": len(session.selections)
            }
        else:
            # 모든 단계 완료
            summary = step_pipeline.get_summary(session_id)
            return {
                "session_id": session_id,
                "status": "completed",
                "message": "모든 부품 선택이 완료되었습니다!",
                "summary": summary
            }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"부품 선택 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"부품 선택 실패: {str(e)}")


@app.get("/step/{session_id}/summary")
async def get_session_summary(session_id: str) -> Dict[str, Any]:
    """
    세션 요약 (현재까지 선택한 부품 목록 및 총 가격)
    """
    if step_pipeline is None:
        raise HTTPException(status_code=503, detail="Step-by-Step 파이프라인이 초기화되지 않았습니다.")
    
    try:
        summary = step_pipeline.get_summary(session_id)
        if not summary:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        return summary
        
    except Exception as e:
        logger.error(f"요약 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"요약 조회 실패: {str(e)}")


@app.delete("/step/{session_id}/select/{step}")
async def deselect_component(session_id: str, step: int) -> Dict[str, Any]:
    """
    특정 단계의 선택을 취소하고 해당 단계로 되돌림
    
    해당 단계 및 이후 선택된 모든 부품이 제거됩니다.
    """
    if step_pipeline is None:
        raise HTTPException(status_code=503, detail="Step-by-Step 파이프라인이 초기화되지 않았습니다.")
    
    try:
        session = step_pipeline.deselect_component(session_id=session_id, step=step)
        
        # 해당 단계의 후보를 다시 조회하여 반환
        step_result = step_pipeline.get_step_candidates(
            session_id=session_id,
            step=step,
            top_k=5
        )
        
        category_info = CATEGORY_INFO.get(step_result.category, {})
        
        return {
            "session_id": session_id,
            "step": step,
            "category": step_result.category,
            "category_name": category_info.get("name", step_result.category),
            "category_description": category_info.get("description", ""),
            "candidates": [c.model_dump() for c in step_result.candidates],
            "message": f"단계 {step} 이후의 선택이 취소되었습니다."
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"선택 취소 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"선택 취소 실패: {str(e)}")

# =============================================================================
# Multi-Agent API 엔드포인트
# =============================================================================

@app.post("/agent/chat")
async def agent_chat(request: AgentChatRequest) -> Dict[str, Any]:
    """
    멀티 에이전트와의 대화 (자동 PC 견적)
    
    사용자의 자연어 요청을 분석하여, Multi-Agent 시스템이 'Auto PC Builder Tool'을 통해
    CPU부터 케이스까지 완벽한 호환성을 갖춘 PC를 자동으로 구성해줍니다.
    """
    if orchestrator is None:
        logger.error("DEBUG: orchestrator is None in /agent/chat handler!")
        raise HTTPException(status_code=503, detail="멀티 에이전트 시스템이 초기화되지 않았습니다.")
    
    try:
        logger.info(f"에이전트 요청: {request.query}")
        
        # 오케스트레이터 실행
        result = orchestrator.run({
            "query": request.query,
            "budget": request.budget,
            "purpose": request.purpose,
            "preferences": request.preferences
        })
        
        return result.dict()
        
    except Exception as e:
        logger.error(f"에이전트 실행 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"에이전트 실행 실패: {str(e)}")


@app.post("/step/next", response_model=StepResponse)
async def step_next(request: StepRequest):
    """
    단계별 부품 선택 (인터랙티브)
    
    - 세션 시작 (step=0): 초기 요구사항 분석 및 첫 번째 부품(CPU) 리스트 반환
    - 부품 선택 (step=1-8): 선택된 부품을 저장하고 다음 단계 부품 리스트 반환
    """
    global step_pipeline
    
    if step_pipeline is None:
        raise HTTPException(status_code=503, detail="Step-by-Step 파이프라인이 초기화되지 않았습니다.")
    
    try:
        import uuid
        
        # 세션 시작 (첫 호출 또는 new session)
        if request.session_id is None or request.current_step == 0:
            # 예산 필수 체크 (기본값 제거)
            if not request.budget:
                raise HTTPException(status_code=400, detail="예산 정보가 필요합니다.")
                
            budget = request.budget
            purpose = request.purpose or "general"
            
            # 세션 생성 (session_id는 자동 생성됨)
            session = step_pipeline.start_session(
                budget=budget,
                purpose=purpose
            )
            
            session_id = session.session_id
            logger.info(f"새 세션 시작: {session_id}, 예산: {budget:,}원, 목적: {purpose}")
            
            # 첫 번째 단계 (CPU) 후보 조회
            step_result = step_pipeline.get_step_candidates(session_id, step=1, top_k=5)
            
            # 응답 변환
            candidates = [
                ComponentCandidate(
                    id=c.component_id,
                    name=c.name,
                    price=c.price,
                    category=step_result.category,
                    match_score=c.match_score,
                    specs=c.specs,
                    hashtags=getattr(c, "hashtags", []),
                    representative_specs=getattr(c, "representative_specs", {}),
                    compatibility_status=getattr(c, "compatibility_status", "compatible"),
                    danawa_url=getattr(c, "danawa_url", None),
                    image_url=getattr(c, "image_url", None)
                )
                for c in step_result.candidates
            ]
            
            purpose_kr = {"general": "일반/가정", "gaming": "게이밍", "workstation": "작업", "streaming": "방송"}.get(purpose, purpose)

            
            analysis_msg = step_result.analysis if hasattr(step_result, "analysis") and step_result.analysis else f"{purpose_kr} 용도에 적합한 CPU 후보입니다. 예산은 {budget:,}원입니다."

            # 카테고리 정보 가져오기 (step_result.category는 "CPU" 등)
            cat_name = step_result.category
            cat_info = CATEGORY_INFO.get(cat_name, {})
            
            return StepResponse(
                session_id=session_id,
                step=1,
                step_name="CPU",
                candidates=candidates,
                analysis=analysis_msg,
                is_final=False,
                total_price=0,
                category_description=cat_info.get("description", ""),
                spec_meanings=cat_info.get("spec_meanings", {})
            )
        
        # 부품 선택 및 다음 단계
        else:
            session_id = request.session_id
            session = step_pipeline.get_session(session_id)
            
            if session is None:
                raise HTTPException(status_code=404, detail=f"세션을 찾을 수 없습니다: {session_id}")
            
            # 이전 단계에서 선택한 부품 저장
            if request.selected_component_id:
                # [Fix] Use request.current_step directly as the selection step
                current_step_for_selection = request.current_step if request.current_step >= 1 else session.current_step
                
                # 선택한 부품 정보 조회 필요 (간단히 빈 데이터로 처리, 실제로는 DB에서 조회)
                component_data = {"id": request.selected_component_id}
                
                step_pipeline.select_component(
                    session_id=session_id,
                    step=current_step_for_selection,
                    component_id=request.selected_component_id,
                    component_data=component_data
                )
                
                logger.info(f"부품 선택: step={current_step_for_selection}, id={request.selected_component_id}")
            
            else:
                # [Fix] 선택 없이 건너뛰기 (Skip)
                current_step_for_selection = request.current_step if request.current_step >= 1 else session.current_step
                step_pipeline.skip_step(session_id=session_id, step=current_step_for_selection)
                logger.info(f"단계 건너뛰기: step={current_step_for_selection}")
            
            # [Fix] Re-fetch session after selection to get updated current_step
            session = step_pipeline.get_session(session_id)
            next_step = session.current_step
            
            if next_step > 8:
                # 모든 단계 완료
                total_price = sum(s.price for s in session.selections)
                return StepResponse(
                    session_id=session_id,
                    step=8,
                    step_name="완료",
                    candidates=[],
                    analysis="PC 구성이 완료되었습니다!",
                    is_final=True,
                    total_price=total_price
                )
            
            step_result = step_pipeline.get_step_candidates(session_id, step=next_step, top_k=5)
            
            # 응답 변환
            candidates = [
                ComponentCandidate(
                    id=c.component_id,
                    name=c.name,
                    price=c.price,
                    category=step_result.category,
                    match_score=c.match_score,
                    specs=c.specs,
                    hashtags=getattr(c, "hashtags", []),
                    representative_specs=getattr(c, "representative_specs", {}),
                    compatibility_status=getattr(c, "compatibility_status", "compatible"),
                    danawa_url=getattr(c, "danawa_url", None),
                    image_url=getattr(c, "image_url", None)
                )
                for c in step_result.candidates
            ]
            
            total_price = sum(s.price for s in session.selections)
            step_name_map = {1: "CPU", 2: "메인보드", 3: "RAM", 4: "GPU", 5: "SSD", 6: "파워", 7: "쿨러", 8: "케이스"}
            next_step_name = step_name_map.get(next_step, "부품")
            
            analysis_msg = step_result.analysis if hasattr(step_result, "analysis") and step_result.analysis else f"{step_result.category} 후보입니다. 현재까지 {total_price:,}원 사용했습니다."
            
            cat_name = step_result.category
            cat_info = CATEGORY_INFO.get(cat_name, {})

            return StepResponse(
                session_id=session_id,
                step=next_step,
                step_name=next_step_name,
                candidates=candidates,
                analysis=analysis_msg,
                is_final=False,
                total_price=total_price,
                category_description=cat_info.get("description", ""),
                spec_meanings=cat_info.get("spec_meanings", {})
            )
            
    except Exception as e:
        logger.error(f"Step 처리 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Step 처리 실패: {str(e)}")


@app.post("/generate/pc-image")
async def generate_pc_image(request: GenerateImageRequest):
    """
    선택된 부품을 기반으로 PC 조립 이미지를 생성합니다.
    """
    global image_generator
    
    if not image_generator or not image_generator.client:
        raise HTTPException(status_code=503, detail="Image generation service is not available (Check API Key)")
        
    try:
        image_base64 = image_generator.generate_pc_image(
            components=request.components,
            purpose=request.purpose
        )
        
        if not image_base64:
             raise HTTPException(status_code=500, detail="Failed to generate image")
             
        import base64
        if isinstance(image_base64, bytes):
            image_base64 = base64.b64encode(image_base64).decode('utf-8')
            
        return {
            "image_url": f"data:image/png;base64,{image_base64}"
        }
        
    except Exception as e:
        logger.error(f"Image generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent/status")
async def agent_status():
    """디버그용 orchestrator 상태 확인 엔드포인트"""
    global orchestrator
    return {
        "status": "ok" if orchestrator else "error",
        "orchestrator_initialized": orchestrator is not None
    }


# 개발 서버 실행 (직접 실행 시)
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )



# 루트 경로 (API 서버 정보)
@app.get("/")
async def root():
    return {
        "service": "Spckit AI - PC 부품 추천 API",
        "version": "2.0.0 (VERIFIED NEW VERSION)",
        "status": "If you see this, Backend is updated",
        "docs": "/docs",
        "version": "1.0.0",
        "docs": "/docs",
        "frontend": "npm run dev (port 3000)"
    }
