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
