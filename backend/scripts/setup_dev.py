"""
개발 환경 자동 설정 스크립트

팀원 개발자들이 쉽게 개발 환경을 설정할 수 있도록 도와주는 스크립트입니다.
"""
import sys
import os
import subprocess
from pathlib import Path
from typing import Optional

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def print_header(text: str):
    """헤더 출력"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")

def print_step(step: int, total: int, text: str):
    """단계 출력"""
    print(f"[{step}/{total}] {text}")

def print_success(text: str):
    """성공 메시지 출력"""
    print(f"✅ {text}")

def print_error(text: str):
    """에러 메시지 출력"""
    print(f"❌ {text}")

def print_warning(text: str):
    """경고 메시지 출력"""
    print(f"⚠️  {text}")

def print_info(text: str):
    """정보 메시지 출력"""
    print(f"ℹ️  {text}")

def check_command(command: str, check_output: bool = False) -> bool:
    """명령어가 설치되어 있는지 확인"""
    try:
        if check_output:
            subprocess.run(
                command, 
                shell=True, 
                check=True, 
                capture_output=True,
                text=True
            )
        else:
            subprocess.run(
                command, 
                shell=True, 
                check=True, 
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def run_command(command: str, description: str, check: bool = True) -> bool:
    """명령어 실행"""
    print(f"   실행 중: {command}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=check,
            capture_output=True,
            text=True,
            cwd=project_root
        )
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        return False

def get_user_input(prompt: str, default: Optional[str] = None) -> str:
    """사용자 입력 받기"""
    if default:
        full_prompt = f"{prompt} (기본값: {default}): "
    else:
        full_prompt = f"{prompt}: "
    
    user_input = input(full_prompt).strip()
    return user_input if user_input else (default or "")

def create_env_file(api_key: str, env_path: Path):
    """환경 변수 파일 생성"""
    # API 키 유효성 간단 검사
    if not api_key or len(api_key.strip()) < 10:
        print_error("API 키가 유효하지 않습니다.")
        return False
    
    env_content = f"""# Gemini API 설정
# Google AI Studio (https://aistudio.google.com/app/apikey)에서 발급받으세요
GEMINI_API_KEY={api_key.strip()}
VITE_GEMINI_API_KEY={api_key.strip()}

# 환경 설정 (development, staging, production)
ENVIRONMENT=development

# 벡터 DB 자동 초기화 (true/false)
# 개발 환경에서는 true로 설정하면 벡터 DB가 없을 때 자동으로 생성됩니다
AUTO_INIT_DB=true

# ChromaDB 설정 (선택사항)
# CHROMA_PERSIST_DIRECTORY=backend/chroma_db
# CHROMA_COLLECTION_NAME=pc_components

# 임베딩 모델 설정 (선택사항)
# EMBEDDING_MODEL=models/text-embedding-004

# 생성 모델 설정 (선택사항)
# GENERATION_MODEL=gemini-3.0-pro

# 로그 레벨 (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
"""
    
    try:
        # 디렉토리가 없으면 생성
        env_path.parent.mkdir(parents=True, exist_ok=True)
        env_path.write_text(env_content, encoding="utf-8")
        return True
    except Exception as e:
        print_error(f".env 파일 생성 실패: {str(e)}")
        print_info(f"경로: {env_path}")
        return False

def main():
    """메인 함수"""
    print_header("Spckit AI 개발 환경 자동 설정")
    print("이 스크립트는 개발 환경을 자동으로 설정합니다.")
    print("다음 단계를 진행합니다:")
    print("  1. uv 설치 확인 및 설치")
    print("  2. 가상 환경 생성")
    print("  3. 의존성 설치")
    print("  4. 환경 변수 파일 생성")
    print("  5. 벡터 DB 초기화 (필요시)")
    print()
    print("💡 벡터 DB가 없으면 자동으로 초기화됩니다.")
    print("   (약 10-15분 소요, Enter만 누르면 자동 진행)")
    print()
    
    input("계속하려면 Enter 키를 누르세요...")
    
    backend_dir = project_root / "backend"
    venv_dir = backend_dir / ".venv"
    env_file = project_root / ".env"
    
    step = 1
    total_steps = 4
    
    # 1단계: uv 설치 확인
    print_step(step, total_steps, "uv 설치 확인 중...")
    step += 1
    
    if not check_command("uv --version", check_output=True):
        print_warning("uv가 설치되어 있지 않습니다.")
        print_info("uv는 빠른 Python 패키지 관리자입니다.")
        print_info("설치 방법: https://github.com/astral-sh/uv")
        print()
        
        install_uv = get_user_input("uv를 자동으로 설치하시겠습니까? (y/n)", "y")
        if install_uv.lower() == "y":
            print_info("uv 설치 중...")
            # Windows용 설치 명령어
            if sys.platform == "win32":
                install_cmd = 'powershell -c "irm https://astral.sh/uv/install.ps1 | iex"'
            else:
                install_cmd = 'curl -LsSf https://astral.sh/uv/install.sh | sh'
            
            if not run_command(install_cmd, "uv 설치"):
                print_error("uv 설치 실패. 수동으로 설치해주세요.")
                print_info("Windows: powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\"")
                print_info("Linux/Mac: curl -LsSf https://astral.sh/uv/install.sh | sh")
                return False
            
            print_success("uv 설치 완료!")
            print_warning("새 터미널을 열어서 다시 실행해주세요.")
            return False
        else:
            print_error("uv가 필요합니다. 설치 후 다시 실행해주세요.")
            return False
    else:
        print_success("uv가 설치되어 있습니다.")
    
    # 2단계: 가상 환경 생성
    print_step(step, total_steps, "가상 환경 확인 중...")
    step += 1
    
    if not venv_dir.exists():
        print_info("가상 환경이 없습니다. 생성 중...")
        if not run_command("cd backend && uv venv", "가상 환경 생성"):
            print_error("가상 환경 생성 실패")
            return False
        print_success("가상 환경 생성 완료!")
    else:
        print_success("가상 환경이 이미 존재합니다.")
    
    # 3단계: 의존성 설치
    print_step(step, total_steps, "의존성 설치 중...")
    step += 1
    
    # uv를 사용하여 설치 (더 빠름)
    print_info("uv를 사용하여 의존성 설치 중...")
    uv_cmd = "cd backend && uv pip install -e ."
    
    if not run_command(uv_cmd, "의존성 설치"):
        print_warning("uv 설치 실패. pip로 재시도 중...")
        # 폴백: pip 사용
        if sys.platform == "win32":
            pip_cmd = "backend\\.venv\\Scripts\\python.exe -m pip install -e backend/"
        else:
            pip_cmd = "backend/.venv/bin/python -m pip install -e backend/"
        
        if not run_command(pip_cmd, "의존성 설치 (pip 사용)"):
            print_error("의존성 설치 실패")
            return False
    
    print_success("의존성 설치 완료!")
    
    # 4단계: 환경 변수 파일 생성
    print_step(step, total_steps, "환경 변수 파일 설정 중...")
    step += 1
    
    # 통합 .env 파일
    if env_file.exists():
        print_warning(".env 파일이 이미 존재합니다.")
        overwrite = get_user_input("덮어쓰시겠습니까? (y/n)", "n")
        if overwrite.lower() != "y":
            print_info("기존 .env 파일을 유지합니다.")
            # 기존 파일에서 API 키 읽기
            try:
                existing_content = env_file.read_text(encoding="utf-8")
                for line in existing_content.split("\n"):
                    if line.startswith("GEMINI_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
                else:
                    api_key = None
            except:
                api_key = None
        else:
            api_key = get_user_input("Gemini API 키를 입력하세요")
            if not api_key:
                print_error("API 키가 필요합니다.")
                return False
            
            if not create_env_file(api_key, env_file):
                return False
            print_success(".env 파일 생성 완료!")
    else:
        print_info("Gemini API 키가 필요합니다.")
        print_info("발급 방법: https://aistudio.google.com/app/apikey")
        print()
        
        api_key = get_user_input("Gemini API 키를 입력하세요")
        if not api_key:
            print_error("API 키가 필요합니다.")
            return False
        
        if not create_env_file(api_key, env_file):
            return False
        print_success(".env 파일 생성 완료!")

    # 5단계: 벡터 DB 초기화 확인 (이전 단계 유지)

    print_step(step, total_steps, "벡터 데이터베이스 확인 중...")
    
    chroma_db_dir = backend_dir / "chroma_db"
    has_data = False
    
    if chroma_db_dir.exists():
        try:
            # chroma.sqlite3 파일이나 하위 디렉토리가 있는지 확인
            items = list(chroma_db_dir.iterdir())
            has_data = len(items) > 0 and any(
                item.is_file() and item.name.endswith('.sqlite3') or item.is_dir()
                for item in items
            )
        except Exception:
            has_data = False
    
    if not has_data:
        print_warning("벡터 데이터베이스가 없습니다.")
        print_info("")
        print_info("💡 벡터 DB 초기화 옵션:")
        print_info("   1. 지금 초기화 (약 10-15분 소요) - 권장")
        print_info("   2. API 서버 실행 시 자동 초기화")
        print_info("")
        print_info("   ⚠️  초기화에는 약 10-15분이 소요되며,")
        print_info("   135,660개의 문서를 임베딩합니다.")
        print_info("   💡 지금 초기화하면 나중에 바로 개발을 시작할 수 있습니다.")
        print()
        
        init_now = get_user_input("지금 초기화하시겠습니까? (y/n)", "y")
        if init_now.lower() == "y":
            print()
            print_info("=" * 60)
            print_info("벡터 데이터베이스 초기화 시작...")
            print_info("=" * 60)
            print_info("이 작업은 시간이 걸릴 수 있습니다...")
            print_info("진행 상황은 터미널에 표시됩니다.")
            print()
            
            if sys.platform == "win32":
                python_cmd = "backend\\.venv\\Scripts\\python.exe"
            else:
                python_cmd = "backend/.venv/bin/python"
            
            print_info("초기화 스크립트 실행 중...")
            success = run_command(
                f"{python_cmd} backend/scripts/init_database.py",
                "벡터 DB 초기화",
                check=False
            )
            
            if success:
                print()
                print_success("벡터 데이터베이스 초기화 완료!")
            else:
                print()
                print_warning("초기화 중 오류가 발생했을 수 있습니다.")
                print_info("API 서버 실행 시 자동으로 재시도됩니다.")
                print_info("또는 수동으로 실행하세요:")
                print_info(f"  {python_cmd} backend/scripts/init_database.py")
        else:
            print_info("API 서버 실행 시 자동으로 초기화됩니다.")
            print_info("서버 시작 명령어: backend\\run_dev.bat (Windows) 또는 ./backend/run_dev.sh (Linux/Mac)")
    else:
        print_success("벡터 데이터베이스가 준비되어 있습니다.")
        try:
            # 문서 수 확인 시도
            if sys.platform == "win32":
                python_cmd = "backend\\.venv\\Scripts\\python.exe"
            else:
                python_cmd = "backend/.venv/bin/python"
            
            result = subprocess.run(
                f'{python_cmd} -c "from backend.rag.pipeline import RAGPipeline; p = RAGPipeline(); print(p.get_stats().get(\"total_documents\", 0))"',
                shell=True,
                capture_output=True,
                text=True,
                cwd=project_root
            )
            if result.returncode == 0:
                doc_count = result.stdout.strip()
                if doc_count.isdigit():
                    print_info(f"문서 수: {doc_count}개")
        except Exception:
            pass  # 문서 수 확인 실패해도 계속 진행
    
    # 완료 메시지
    print_header("설정 완료!")
    print_success("개발 환경 설정이 완료되었습니다! 🎉")
    print()
    print("=" * 70)
    print("  다음 단계")
    print("=" * 70)
    print()
    print("1️⃣  백엔드 API 서버 실행:")
    if sys.platform == "win32":
        print("   📝 명령어: backend\\run_dev.bat")
        print("   또는 더블클릭: backend\\run_dev.bat")
    else:
        print("   📝 명령어: ./backend/run_dev.sh")
        print("   또는: cd backend && source .venv/bin/activate && python -m uvicorn backend.api.main:app --reload")
    print()
    print("   ⚠️  벡터 DB가 없으면 서버 시작 시 자동으로 초기화됩니다.")
    print("   ⏱️  초기화에는 약 10-15분이 소요됩니다.")
    print()
    print("2️⃣  프론트엔드 개발 서버 실행 (별도 터미널):")
    print("   📝 명령어: npm install && npm run dev")
    print()
    print("3️⃣  브라우저에서 확인:")
    print("   🌐 API 문서: http://localhost:8000/docs")
    print("   💚 헬스 체크: http://localhost:8000/health")
    print("   📊 통계: http://localhost:8000/stats")
    print()
    print("=" * 70)
    print()
    print("💡 도움이 필요하시면 docs/QUICK_START.md를 참조하세요.")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n설정이 취소되었습니다.")
        sys.exit(1)
    except Exception as e:
        print_error(f"예상치 못한 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

