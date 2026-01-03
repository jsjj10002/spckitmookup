
import sys
import os
from pathlib import Path
from loguru import logger

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_path))

from rag.vector_store import PCComponentVectorStore

def verify_db():
    logger.info("Initializing Vector Store...")
    vector_store = PCComponentVectorStore()
    
    count = vector_store.collection.count()
    logger.info(f"Total documents in DB: {count}")
    
    if count == 0:
        logger.error("Database is empty! Run data ingestion first.")
        return False
        
    # Check categories
    stats = vector_store.get_stats()
    logger.info(f"Stats: {stats}")
    
    return True

if __name__ == "__main__":
    if verify_db():
        sys.exit(0)
    else:
        sys.exit(1)
