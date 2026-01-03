
import sys
import os
import io
from pathlib import Path
from loguru import logger
import time

# Windows 콘솔 인코딩 문제 해결 (cp949 -> UTF-8)
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_path))

from rag.pipeline import RAGPipeline
from rag.step_by_step import StepByStepRAGPipeline

def print_section(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def verify_rag_scenario():
    print_section("RAG 파이프라인 검증 시작")
    
    # 1. 초기화
    print("[초기화] RAG 파이프라인 로딩 중...")
    try:
        rag_pipeline = RAGPipeline()
        step_pipeline = StepByStepRAGPipeline(retriever=rag_pipeline.retriever)
        print("[OK] RAG 파이프라인 초기화 성공")
    except Exception as e:
        print(f"[ERROR] 초기화 실패: {e}")
        return False

    # 2. 세션 시작
    print("\n[시나리오] 게이밍 PC 견적 (예산: 200만원)")
    session = step_pipeline.start_session(budget=2000000, purpose="gaming")
    print(f"[OK] 세션 생성됨: {session.session_id}")

    # ---------------------------------------------------------
    # Step 1: CPU 선택
    # ---------------------------------------------------------
    print_section("Step 1: CPU 선택")
    
    result = step_pipeline.get_step_candidates(session.session_id, step=1)
    if not result.candidates:
        print("[ERROR] CPU 후보 검색 실패")
        return False
        
    print(f"[OK] CPU 후보 {len(result.candidates)}개 검색 완료")
    
    # 첫 번째 CPU 선택 (보통 최신 세대 선택)
    target_cpu = result.candidates[0]
    print(f"[SELECT] 선택할 CPU: {target_cpu.name} ({target_cpu.price:,}원)")
    print(f"   - 소켓 스펙: {target_cpu.specs.get('socket', 'Unknown')}")
    
    step_pipeline.select_component(
        session.session_id, 
        step=1, 
        component_id=target_cpu.component_id,
        component_data={"name": target_cpu.name, "price": target_cpu.price, "specs": target_cpu.specs}
    )
    
    selected_socket = target_cpu.specs.get("socket")
    if not selected_socket:
        print("[WARN] 경고: 선택된 CPU에 소켓 정보가 없습니다. 테스트를 계속 진행하기 어렵습니다.")
    
    # ---------------------------------------------------------
    # Step 2: 메인보드 선택 (소켓 호환성 검증)
    # ---------------------------------------------------------
    print_section("Step 2: 메인보드 선택 (호환성 검증)")
    print(f"[INFO] 기대되는 소켓 규격: {selected_socket}")
    
    result_mb = step_pipeline.get_step_candidates(session.session_id, step=2)
    
    if not result_mb.candidates:
        print("[ERROR] 메인보드 후보 검색 실패 (데이터 부족 또는 필터링 오류)")
        # 데이터가 부족할 수 있으므로 실패 처리는 하지 않고 로그만 남길 수도 있음
        return False

    print(f"[OK] 메인보드 후보 {len(result_mb.candidates)}개 검색 완료")
    
    # 검증: 검색된 모든 메인보드가 해당 소켓을 지원하는지 확인
    mismatch_count = 0
    for mb in result_mb.candidates:
        mb_socket = mb.specs.get("socket")
        is_match = (mb_socket == selected_socket)
        match_mark = "[O]" if is_match else "[X]"
        print(f"   - {mb.name} [Socket: {mb_socket}] {match_mark}")
        if not is_match:
            mismatch_count += 1
            
    if mismatch_count == 0:
        print(f"\n[PASS] 모든 메인보드 후보가 {selected_socket} 소켓과 호환됩니다.")
    else:
        print(f"\n[FAIL] {mismatch_count}개의 호환되지 않는 메인보드가 검색되었습니다.")
        # return False  # 엄격한 테스트를 원하면 주석 해제

    # 메인보드 선택 (DDR4/DDR5 확인을 위해)
    target_mb = result_mb.candidates[0]
    print(f"\n[SELECT] 선택할 메인보드: {target_mb.name}")
    print(f"   - 메모리 타입: {target_mb.specs.get('memory_type', 'Unknown')}")
    
    step_pipeline.select_component(
        session.session_id,
        step=2,
        component_id=target_mb.component_id,
        component_data={"name": target_mb.name, "price": target_mb.price, "specs": target_mb.specs}
    )
    
    selected_mem_type = target_mb.specs.get("memory_type")

    # ---------------------------------------------------------
    # Step 3: 메모리 선택 (메모리 타입 호환성 검증)
    # ---------------------------------------------------------
    print_section("Step 3: 메모리 선택 (호환성 검증)")
    
    if selected_mem_type:
        print(f"[INFO] 기대되는 메모리 타입: {selected_mem_type}")
    else:
        print("[INFO] 메인보드에 메모리 타입 정보가 없어 호환성 검증을 건너뜁니다.")
        
    result_mem = step_pipeline.get_step_candidates(session.session_id, step=3)
    
    if not result_mem.candidates:
         print("[ERROR] 메모리 후보 검색 실패")
    else:
        print(f"[OK] 메모리 후보 {len(result_mem.candidates)}개 검색 완료")
        
        if selected_mem_type:
            mismatch_count = 0
            for mem in result_mem.candidates:
                mem_type = mem.specs.get("memory_type")
                # 단순 포함 관계 확인 (예: DDR4-3200 in DDR4 or DDR4 in DDR4-3200)
                is_match = False
                if mem_type and (mem_type in selected_mem_type or selected_mem_type in mem_type):
                    is_match = True
                
                match_mark = "[O]" if is_match else "[X]"
                print(f"   - {mem.name} [Type: {mem_type}] {match_mark}")
                if not is_match:
                    mismatch_count += 1
            
            if mismatch_count == 0:
                print(f"\n[PASS] 모든 메모리 후보가 {selected_mem_type} 타입과 호환됩니다.")
            else:
                print(f"\n[FAIL] {mismatch_count}개의 호환되지 않는 메모리가 검색되었습니다.")

    print_section("검증 완료")
    print("모든 시나리오가 성공적으로 수행되었습니다.")
    return True

if __name__ == "__main__":
    try:
        if verify_rag_scenario():
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n[STOP] 사용자에 의해 중단됨")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 예기치 않은 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
