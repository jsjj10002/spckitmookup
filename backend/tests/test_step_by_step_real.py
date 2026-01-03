
import sys
import os
import json
from pathlib import Path
from loguru import logger

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_path))

from rag.pipeline import RAGPipeline
from rag.step_by_step import StepByStepRAGPipeline, SelectionStep

def test_step_by_step_real():
    with open("debug_marker.txt", "w") as f:
        f.write("Script started")
        
    # Setup explicit file logging
    logger.add("test_result.log", rotation="10 MB")
    
    logger.info("Initializing RAG components...")
    
    # Initialize real RAG components
    rag_pipeline = RAGPipeline()
    retriever = rag_pipeline.retriever
    
    # Initialize Step-by-Step Pipeline with real retriever
    step_pipeline = StepByStepRAGPipeline(retriever=retriever)
    
    # Start Session
    session = step_pipeline.start_session(budget=2000000, purpose="gaming")
    logger.info(f"Session started: {session.session_id}")
    
    # Step 1: CPU
    logger.info("Step 1: Fetching CPU candidates...")
    cpu_result = step_pipeline.get_step_candidates(session.session_id, step=1)
    
    if not cpu_result.candidates:
        logger.error("No CPU candidates found! Real retrieval failed.")
        return False
        
    logger.info(f"Found {len(cpu_result.candidates)} CPU candidates.")
    for cand in cpu_result.candidates:
        logger.info(f"  - {cand.name}: {cand.price:,} won")
        
    # Select first CPU
    selected_cpu = cpu_result.candidates[0]
    step_pipeline.select_component(
        session.session_id, 
        step=1, 
        component_id=selected_cpu.component_id,
        component_data={"name": selected_cpu.name, "price": selected_cpu.price, "specs": selected_cpu.specs}
    )
    logger.info(f"Selected CPU: {selected_cpu.name}")
    
    # Step 2: Motherboard (should filter by compatibility)
    logger.info("Step 2: Fetching Motherboard candidates...")
    mb_result = step_pipeline.get_step_candidates(session.session_id, step=2)
    
    if not mb_result.candidates:
        logger.error("No Motherboard candidates found!")
        return False
        
    logger.info(f"Found {len(mb_result.candidates)} Motherboard candidates.")
    logger.info(f"Socket Requirement: {mb_result.context.socket_requirement}")
    
    for cand in mb_result.candidates:
        status = cand.compatibility_status
        logger.info(f"  - {cand.name} ({status}): {cand.specs.get('socket', 'Unknown Socket')}")
        
        # Verify compatibility filter works (at least check if socket matches)
        # Note: existing logic filters OUT incompatible ones, so we expect compatible ones
        if status == 'compatible':
            if str(cand.specs.get('socket')) != str(mb_result.context.socket_requirement):
                 logger.warning(f"  [WARNING] Socket mismatch for compatible item! {cand.specs.get('socket')} vs {mb_result.context.socket_requirement}")

    return True

if __name__ == "__main__":
    if test_step_by_step_real():
        sys.exit(0)
    else:
        sys.exit(1)
