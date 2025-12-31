import sys
import os
from pathlib import Path
from unittest.mock import MagicMock

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_path))

from rag.pipeline import RAGPipeline

def test_force_generation():
    print("Testing RAG Pipeline force generation...")
    
    # Mock dependencies
    mock_embedder = MagicMock()
    mock_vector_store = MagicMock()
    mock_retriever = MagicMock()
    mock_generator = MagicMock()
    
    # Setup mock retriever to return empty list
    mock_retriever.retrieve.return_value = []
    
    # Setup mock generator to return a dummy recommendation
    mock_generator.generate_recommendation.return_value = {
        "analysis": "Test Analysis",
        "components": [{"name": "Test Component", "price": "10000"}],
        "total_price": "10000"
    }
    
    # Initialize pipeline with mocks
    pipeline = RAGPipeline(
        embedder=mock_embedder,
        vector_store=mock_vector_store,
        retriever=mock_retriever,
        generator=mock_generator
    )
    
    # Execute query
    result = pipeline.query("test query")
    
    # Verify results
    with open("verification_result.txt", "w", encoding="utf-8") as f:
        print(f"Retrieved count: {result['retrieved_count']}")
        f.write(f"Retrieved count: {result['retrieved_count']}\n")
        
        if result['retrieved_count'] == 0 and result['recommendation']['components']:
            print("SUCCESS: Recommendation generated despite 0 retrieved components.")
            f.write("SUCCESS: Recommendation generated despite 0 retrieved components.\n")
            return True
        else:
            print("FAILURE: Recommendation not generated or unexpected state.")
            print(f"Result: {result}")
            f.write("FAILURE: Recommendation not generated or unexpected state.\n")
            f.write(f"Result: {result}\n")
            return False

if __name__ == "__main__":
    if test_force_generation():
        sys.exit(0)
    else:
        sys.exit(1)
