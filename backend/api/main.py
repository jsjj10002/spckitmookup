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
from rag.step_by_step import StepByStepRAGPipeline

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


# 이벤트 핸들러
@app.on_event("startup")
async def startup_event():
    """앱 시작 시 RAG 파이프라인 초기화 및 벡터 DB 자동 초기화"""
    global pipeline, step_pipeline
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
        
        # Step-by-Step 파이프라인 초기화
        step_pipeline = StepByStepRAGPipeline(
            retriever=pipeline.retriever,
            compatibility_engine=None  # 필요시 추가
        )
        logger.info("✅ Step-by-Step 파이프라인 초기화 완료!")
        
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
        
        return {
            "session_id": result.session_id,
            "step": result.step,
            "category": result.category,
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
            
            return {
                "session_id": session_id,
                "selected_step": request.step,
                "next_step": session.current_step,
                "category": next_result.category,
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
        "version": "1.0.0",
        "docs": "/docs",
        "frontend": "npm run dev (port 3000)"
    }
