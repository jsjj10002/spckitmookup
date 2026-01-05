from typing import Type, List, Dict, Any, Optional
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from backend.rag.retriever import PCComponentRetriever
from backend.modules.compatibility.engine import CompatibilityEngine
import json

class SearchPartsToolInput(BaseModel):
    """Input schema for SearchPartsTool."""
    category: str = Field(..., description="The category of the component to search for (e.g., 'gpu', 'cpu', 'motherboard', 'memory', 'storage', 'case', 'psu').")
    query: str = Field(..., description="A natural language query describing the desired component (e.g., 'RTX 4060 8GB', 'i5-13400F', 'DDR5 32GB').")
    budget: Optional[int] = Field(None, description="The budget constraint for the component in KRW.")

class SearchPartsTool(BaseTool):
    name: str = "PC Component Search Tool"
    description: str = "Search for PC components in the database based on category and natural language query. Returns a list of available components with their specs and prices."
    args_schema: Type[BaseModel] = SearchPartsToolInput
    retriever: Optional[PCComponentRetriever] = None

    def __init__(self, retriever: PCComponentRetriever):
        super().__init__()
        self.retriever = retriever

    def _run(self, category: str, query: str, budget: Optional[int] = None) -> str:
        if not self.retriever:
            return "Error: Retriever not initialized."
        
        try:
            # Combine query with budget info if provided
            full_query = f"{query}"
            if budget:
                full_query += f" budget under {budget}"

            results = self.retriever.retrieve(
                query=full_query,
                category=category,
                top_k=5
            )
            
            if not results:
                return f"No components found for category '{category}' matching query '{query}'."
            
            # Format results for the agent
            formatted_results = []
            for item in results:
                formatted_results.append({
                    "name": item.get("name"),
                    "price": item.get("price"),
                    "specs": item.get("specs"),
                    "similarity": item.get("similarity")
                })
            
            return json.dumps(formatted_results, ensure_ascii=False, indent=2)
        except Exception as e:
            return f"Error occurred during search: {str(e)}"

class CompatibilityCheckToolInput(BaseModel):
    """Input schema for CompatibilityCheckTool."""
    components: List[Dict[str, Any]] = Field(..., description="List of components to check. Each component must have 'category', 'name', and 'specs' keys.")

class CompatibilityCheckTool(BaseTool):
    name: str = "PC Compatibility Check Tool"
    description: str = "Check physical and logical compatibility between a list of PC components. Returns a validation report with pass/fail status and warnings."
    args_schema: Type[BaseModel] = CompatibilityCheckToolInput
    engine: Optional[CompatibilityEngine] = None

    def __init__(self, engine: CompatibilityEngine):
        super().__init__()
        self.engine = engine

    def _run(self, components: List[Dict[str, Any]]) -> str:
        if not self.engine:
            return "Error: Compatibility Engine not initialized."
        
        try:
            result = self.engine.check_all(components)
            
            # Serialize the result using Pydantic's model_dump/dict
            # Check if result is a Pydantic model
            if hasattr(result, 'model_dump'):
                result_dict = result.model_dump()
            elif hasattr(result, 'dict'):
                result_dict = result.dict()
            else:
                result_dict = result # Assuming it's already a dict or similar

            return json.dumps(result_dict, ensure_ascii=False, indent=2)
        except Exception as e:
            return f"Error occurred during compatibility check: {str(e)}"

class AutoStepBuilderToolInput(BaseModel):
    """Input schema for AutoStepBuilderTool."""
    budget: int = Field(..., description="Total budget for the PC build in KRW.")
    purpose: str = Field(..., description="The main purpose of the PC (e.g., 'gaming', 'workstation', 'general').")

class AutoStepBuilderTool(BaseTool):
    name: str = "Auto PC Builder Tool (Step-by-Step)"
    description: str = "Automatically builds a complete PC configuration by selecting compatible components step-by-step (CPU -> Mainboard -> RAM -> GPU -> ...) based on budget and purpose. Use this for full system recommendations."
    args_schema: Type[BaseModel] = AutoStepBuilderToolInput
    pipeline: Any = None  # StepByStepRAGPipeline

    def __init__(self, pipeline: Any):
        super().__init__()
        self.pipeline = pipeline

    def _run(self, budget: int, purpose: str) -> str:
        if not self.pipeline:
            return "Error: Step-by-Step Pipeline not initialized."
        
        try:
            # 1. 세션 시작
            session = self.pipeline.start_session(budget=budget, purpose=purpose)
            session_id = session.session_id
            
            logs = []
            logs.append(f"Session started: {session_id}")
            
            # 2. 1단계부터 8단계까지 순차 진행
            for step in range(1, 9):
                # 후보 조회
                result = self.pipeline.get_step_candidates(session_id=session_id, step=step, top_k=1)
                
                if not result.candidates:
                    logs.append(f"Step {step} ({result.category}): No candidates found.")
                    break
                
                # 최적의 후보 선택 (첫 번째)
                best_candidate = result.candidates[0]
                
                # 선택 실행
                self.pipeline.select_component(
                    session_id=session_id,
                    step=step,
                    component_id=best_candidate.component_id,
                    component_data=best_candidate.dict() # assuming pydantic model
                )
                
                logs.append(f"Step {step} ({result.category}): Selected {best_candidate.name} ({best_candidate.price:,} KRW)")
            
            # 3. 최종 요약 반환
            summary = self.pipeline.get_summary(session_id)
            return json.dumps(summary, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return f"Error during auto build: {str(e)}"
