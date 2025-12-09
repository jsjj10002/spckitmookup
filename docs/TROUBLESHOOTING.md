# 문제 해결 가이드

## ❌ 일반적인 오류와 해결 방법

### 1. ModuleNotFoundError: No module named 'google.generativeai'

**증상:**
```
ModuleNotFoundError: No module named 'google.generativeai'
```

**원인:** 가상 환경이 활성화되지 않았거나, 의존성이 설치되지 않음

**해결 방법:**

#### Windows:
```bash
# 방법 1: 가상 환경 활성화 (권장)
cd backend
.venv\Scripts\activate
cd ..
python backend\scripts\init_database.py

# 방법 2: 배치 파일 사용 (가장 쉬움)
python backend/scripts/init_database.py

# 방법 3: 가상 환경의 Python 직접 사용
backend\.venv\Scripts\python.exe backend\scripts\init_database.py
```

#### Linux/Mac:
```bash
# 방법 1: 가상 환경 활성화
cd backend
source .venv/bin/activate
cd ..
python backend/scripts/init_database.py

# 방법 2: 가상 환경의 Python 직접 사용
backend/.venv/bin/python backend/scripts/init_database.py
```

#### 의존성 재설치:
```bash
cd backend
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
uv pip install -e .
```

---

### 2. ValueError: 생성된 문서가 없습니다

**증상:**
```
ValueError: 생성된 문서가 없습니다.
```

**원인:** SQL 파일 파싱 실패

**해결 방법:**

1. **SQL 파일 확인:**
```bash
# Windows
backend\.venv\Scripts\python.exe backend\scripts\check_sql.py

# Linux/Mac
backend/.venv/bin/python backend/scripts/check_sql.py
```

2. **SQL 파일 인코딩 확인:**
SQL 파일이 UTF-8로 인코딩되어 있는지 확인

3. **로그 레벨 증가:**
```bash
python backend\scripts\init_database.py --log-level DEBUG
```

4. **수동 SQL 파일 지정:**
```bash
python backend\scripts\init_database.py --sql-file "절대경로\pc_data_dump.sql"
```

---

### 3. GEMINI_API_KEY가 설정되지 않았습니다

**증상:**
```
ValueError: GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.
```

**해결 방법:**

1. **.env 파일 생성:**
```bash
cd backend
cp .env.example .env
```

2. **.env 파일 편집:**
```env
GEMINI_API_KEY=여기에_실제_API_키_입력
VITE_GEMINI_API_KEY=여기에_실제_API_키_입력
```

3. **API 키 발급:**
https://aistudio.google.com/apikey

4. **.env 파일 위치 확인:**
```bash
# .env 파일은 backend 디렉토리에 있어야 함
ls backend/.env  # Linux/Mac
dir backend\.env  # Windows
```

---

### 4. ChromaDB 초기화 실패

**증상:**
```
sqlite3.OperationalError: unable to open database file
```

**해결 방법:**

1. **기존 ChromaDB 삭제:**
```bash
# Windows
rmdir /s /q backend\chroma_db

# Linux/Mac
rm -rf backend/chroma_db
```

2. **재초기화:**
```bash
python backend\scripts\init_database.py --force
```

3. **권한 확인:**
backend 디렉토리에 쓰기 권한이 있는지 확인

---

### 5. 포트 8000이 이미 사용 중

**증상:**
```
ERROR: [Errno 10048] error while attempting to bind on address
```

**해결 방법:**

1. **다른 포트 사용:**
```bash
uvicorn main:app --reload --port 8001
```

2. **사용 중인 프로세스 종료:**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <프로세스ID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

---

### 6. PowerShell 실행 정책 오류

**증상:**
```
.venv\Scripts\activate : 이 시스템에서 스크립트를 실행할 수 없으므로...
```

**해결 방법:**

```powershell
# PowerShell을 관리자 권한으로 실행
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 그래도 안 되면 CMD 사용
.venv\Scripts\activate.bat
```

---

### 7. UnicodeEncodeError (Windows 콘솔)

**증상:**
```
UnicodeEncodeError: 'cp949' codec can't encode character
```

**해결 방법:**

1. **콘솔 인코딩 변경:**
```bash
chcp 65001
```

2. **환경 변수 설정:**
```bash
set PYTHONIOENCODING=utf-8
python backend\scripts\init_database.py
```

3. **배치 파일 사용 (권장):**
```bash
python backend/scripts/init_database.py
```

---

### 8. 가상 환경 생성 실패

**증상:**
```
error: Failed to create virtual environment
```

**해결 방법:**

1. **uv 업데이트:**
```bash
pip install --upgrade uv
```

2. **Python 버전 확인:**
```bash
python --version
# Python 3.10 이상 필요
```

3. **수동 venv 생성:**
```bash
python -m venv backend/.venv
backend\.venv\Scripts\activate
pip install -e backend/
```

---

## 🔍 디버깅 체크리스트

실행 전 확인사항:

- [ ] backend 디렉토리에 `.venv` 폴더가 있는가?
- [ ] 가상 환경이 활성화되었는가? (프롬프트에 `(.venv)` 표시)
- [ ] backend 디렉토리에 `.env` 파일이 있는가?
- [ ] `.env` 파일에 `GEMINI_API_KEY`가 설정되었는가?
- [ ] `backend/data/pc_data_dump.sql` 파일이 존재하는가? (11MB)
- [ ] 프로젝트 루트에서 실행하고 있는가?

---

## 📞 추가 도움

위 방법으로 해결되지 않으면:

1. **로그 확인:**
```bash
python backend\scripts\init_database.py --log-level DEBUG > debug.log 2>&1
```

2. **시스템 정보 확인:**
```bash
python --version
uv --version
pip list
```

3. **GitHub Issues 보고**

