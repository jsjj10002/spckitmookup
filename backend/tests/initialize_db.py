
import sys
import os
from pathlib import Path
from loguru import logger

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_path))

from rag.pipeline import RAGPipeline

def init_db():
    logger.info("Starting RAG Pipeline initialization...")
    pipeline = RAGPipeline()
    
    # Force rebuild to ensure fresh data
    result = pipeline.initialize_database(force_rebuild=True)
    
    logger.info(f"Initialization Result: {result}")
    
    if result["status"] == "success":
        return True
    return False

if __name__ == "__main__":
    if init_db():
        sys.exit(0)
    else:
        sys.exit(1)
