#!/usr/bin/env python
"""
백엔드 모듈 개발 환경 설정 스크립트
===================================

새로운 팀원이 빠르게 개발 환경을 설정할 수 있도록 도와주는 스크립트.

사용법:
    python backend/scripts/setup_modules.py [옵션]
    
옵션:
    --all           모든 모듈 의존성 설치
    --module NAME   특정 모듈만 설치 (multi-agent, price-prediction, recommendation, ontology)
    --check         설치된 의존성 확인만
    --test          테스트 실행

예시:
    # 기본 온보딩 (개발 도구 + 기본 모듈)
    python backend/scripts/setup_modules.py
    
    # 특정 모듈만 설치
    python backend/scripts/setup_modules.py --module recommendation
    
    # 모든 의존성 설치
    python backend/scripts/setup_modules.py --all
"""

import subprocess
import sys
import argparse
from pathlib import Path


# 색상 출력 헬퍼
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


def print_success(text: str):
    print(f"{Colors.GREEN}[OK]{Colors.RESET} {text}")


def print_warning(text: str):
    print(f"{Colors.YELLOW}[WARNING]{Colors.RESET} {text}")


def print_error(text: str):
    print(f"{Colors.RED}[ERROR]{Colors.RESET} {text}")


def print_info(text: str):
    print(f"{Colors.BLUE}[INFO]{Colors.RESET} {text}")


def run_command(cmd: list, description: str) -> bool:
    """명령 실행"""
    print_info(f"{description}...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"{description} 완료")
            return True
        else:
            print_error(f"{description} 실패")
            if result.stderr:
                print(f"  {result.stderr[:200]}")
            return False
    except Exception as e:
        print_error(f"{description} 오류: {e}")
        return False


def check_uv_installed() -> bool:
    """uv 설치 확인"""
    try:
        result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"uv 설치됨: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print_warning("uv가 설치되지 않았습니다.")
    print_info("설치 방법: curl -LsSf https://astral.sh/uv/install.sh | sh")
    return False


def check_python_version() -> bool:
    """Python 버전 확인"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print_success(f"Python 버전: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python 3.10 이상이 필요합니다 (현재: {version.major}.{version.minor})")
        return False


def check_env_file() -> bool:
    """환경 변수 파일 확인"""
    project_root = Path(__file__).parent.parent.parent
    env_file = project_root / ".env"
    
    if env_file.exists():
        print_success(".env 파일 존재")
        return True
    else:
        print_warning(".env 파일이 없습니다")
        
        # 템플릿 생성
        env_template = """# Spckit AI 환경 변수
# 복사하여 .env 파일로 저장하세요

# Gemini API 키 (필수)
GEMINI_API_KEY=your_api_key_here

# 환경 설정
ENVIRONMENT=development
AUTO_INIT_DB=true

# 모델 설정 (선택)
# GENERATION_MODEL=gemini-2.5-pro
# EMBEDDING_MODEL=models/text-embedding-004
"""
        env_example = project_root / ".env.example"
        if not env_example.exists():
            with open(env_example, "w") as f:
                f.write(env_template)
            print_info(f".env.example 파일 생성됨: {env_example}")
        
        print_info("GEMINI_API_KEY를 설정해야 합니다")
        return False


def install_base() -> bool:
    """기본 의존성 설치"""
    print_header("기본 의존성 설치")
    
    backend_dir = Path(__file__).parent.parent
    
    # uv로 설치
    return run_command(
        ["uv", "pip", "install", "-e", str(backend_dir)],
        "기본 패키지 설치"
    )


def install_dev() -> bool:
    """개발 도구 설치"""
    print_header("개발 도구 설치")
    
    backend_dir = Path(__file__).parent.parent
    
    return run_command(
        ["uv", "pip", "install", "-e", f"{backend_dir}[dev]"],
        "개발 도구 설치"
    )


def install_onboarding() -> bool:
    """온보딩용 패키지 설치"""
    print_header("온보딩용 추가 패키지 설치")
    
    backend_dir = Path(__file__).parent.parent
    
    return run_command(
        ["uv", "pip", "install", "-e", f"{backend_dir}[onboarding]"],
        "온보딩 패키지 설치"
    )


def install_module(module_name: str) -> bool:
    """특정 모듈 의존성 설치"""
    print_header(f"모듈 설치: {module_name}")
    
    valid_modules = ["multi-agent", "price-prediction", "recommendation", "ontology"]
    
    if module_name not in valid_modules:
        print_error(f"유효하지 않은 모듈: {module_name}")
        print_info(f"사용 가능한 모듈: {', '.join(valid_modules)}")
        return False
    
    backend_dir = Path(__file__).parent.parent
    
    return run_command(
        ["uv", "pip", "install", "-e", f"{backend_dir}[{module_name}]"],
        f"{module_name} 모듈 설치"
    )


def install_all() -> bool:
    """모든 의존성 설치"""
    print_header("전체 의존성 설치")
    
    backend_dir = Path(__file__).parent.parent
    
    return run_command(
        ["uv", "pip", "install", "-e", f"{backend_dir}[all]"],
        "전체 패키지 설치"
    )


def check_installed_packages():
    """설치된 패키지 확인"""
    print_header("설치된 주요 패키지")
    
    packages = [
        "google-genai",
        "chromadb",
        "fastapi",
        "pydantic",
        "loguru",
        "pytest",
        "networkx",
        "scikit-learn",
        "crewai",
        "torch",
        "prophet",
    ]
    
    for pkg in packages:
        try:
            result = subprocess.run(
                ["uv", "pip", "show", pkg],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                # 버전 추출
                for line in result.stdout.split('\n'):
                    if line.startswith('Version:'):
                        version = line.split(':')[1].strip()
                        print_success(f"{pkg}: {version}")
                        break
            else:
                print_warning(f"{pkg}: 미설치")
        except Exception:
            print_warning(f"{pkg}: 확인 불가")


def run_tests() -> bool:
    """테스트 실행"""
    print_header("테스트 실행")
    
    backend_dir = Path(__file__).parent.parent
    tests_dir = backend_dir / "tests"
    
    if not tests_dir.exists():
        print_error("tests 디렉토리가 없습니다")
        return False
    
    return run_command(
        ["pytest", str(tests_dir), "-v", "--tb=short"],
        "테스트 실행"
    )


def print_next_steps():
    """다음 단계 안내"""
    print_header("다음 단계")
    
    print("""
1. 환경 변수 설정
   - .env 파일을 생성하고 GEMINI_API_KEY 설정
   
2. 벡터 DB 초기화 (처음 실행 시)
   python backend/scripts/init_database.py
   
3. 개발 서버 실행
   uvicorn backend.api.main:app --reload --port 8000
   
4. 테스트 실행
   pytest backend/tests/ -v

5. 모듈 문서 확인
   backend/modules/README.md
""")


def main():
    parser = argparse.ArgumentParser(description="백엔드 모듈 개발 환경 설정")
    parser.add_argument("--all", action="store_true", help="모든 모듈 의존성 설치")
    parser.add_argument("--module", type=str, help="특정 모듈만 설치")
    parser.add_argument("--check", action="store_true", help="설치된 의존성 확인만")
    parser.add_argument("--test", action="store_true", help="테스트 실행")
    
    args = parser.parse_args()
    
    print_header("Spckit AI 백엔드 개발 환경 설정")
    
    # 기본 확인
    if not check_python_version():
        sys.exit(1)
    
    if not check_uv_installed():
        print_info("pip로 대체하여 설치할 수 있습니다")
    
    check_env_file()
    
    # 확인만 모드
    if args.check:
        check_installed_packages()
        sys.exit(0)
    
    # 테스트만 모드
    if args.test:
        success = run_tests()
        sys.exit(0 if success else 1)
    
    # 설치 모드
    if args.all:
        # 전체 설치
        success = install_all()
    elif args.module:
        # 특정 모듈 설치
        success = install_base() and install_module(args.module)
    else:
        # 기본 온보딩
        success = install_base() and install_dev() and install_onboarding()
    
    if success:
        check_installed_packages()
        print_next_steps()
        print_success("설정 완료!")
    else:
        print_error("일부 설치 실패. 로그를 확인하세요.")
        sys.exit(1)


if __name__ == "__main__":
    main()
