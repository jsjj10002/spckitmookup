# 빠른 시작 가이드

## 🚀 자동 설정 (권장) - 5분 안에 완료!

팀원 개발자들을 위한 **완전 자동화된 설정 스크립트**를 제공합니다.

### Windows 사용자

```bash
# 1. 저장소 클론 후 프로젝트 루트에서 실행
setup_dev.bat
```

이 스크립트가 자동으로:
- ✅ uv 설치 확인 및 설치
- ✅ 가상 환경 생성
- ✅ 의존성 설치
- ✅ .env 파일 생성 (API 키 입력)
- ✅ 벡터 DB 초기화 (선택사항)

### Linux/Mac 사용자

```bash
# 실행 권한 부여 (최초 1회)
chmod +x setup_dev.sh

# 실행
./setup_dev.sh
```

### 설정 완료 후

```bash
# Windows - 백엔드와 프론트엔드를 모두 실행합니다
run_dev.bat

# Linux/Mac
chmod +x run_dev.sh
./run_dev.sh
```

**서버가 시작되면:**
- 🌐 **웹 페이지**: http://localhost:3000 (프론트엔드)
- 🔧 **백엔드 API**: http://localhost:8000
- 📚 **API 문서**: http://localhost:8000/docs
- 💚 **헬스 체크**: http://localhost:8000/health
- 📊 **통계**: http://localhost:8000/stats

> 💡 **참고**: 
> - 벡터 DB가 없으면 API 서버 시작 시 자동으로 초기화됩니다 (약 10-15분 소요)
> - 프론트엔드 서버는 별도 창에서 실행됩니다 (Windows) 또는 백그라운드에서 실행됩니다 (Linux/Mac)

---

## 🛠 수동 설정 (고급 사용자용)

### 1단계: 가상 환경 생성 및 의존성 설치 (2분)

```bash
# backend 디렉토리로 이동
cd backend

# 가상 환경 생성
uv venv

# 가상 환경 활성화 (Windows)
.venv\Scripts\activate

# 또는 (Linux/Mac)
source .venv/bin/activate

# 의존성 설치
uv pip install -e .
```

**출력 예시:**
```
Resolved 108 packages in 123ms
Installed 108 packages in 5.73s
 + spckit-ai-backend==0.1.0
 + chromadb==1.3.5
 + google-generativeai==0.8.5
 ...
```

### 2단계: 환경 변수 설정 (30초)

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집하여 API 키 입력
# Windows: notepad .env
# Linux/Mac: nano .env
```

`.env` 파일 내용:
```env
GEMINI_API_KEY="여기에_실제_API_키_입력"
VITE_GEMINI_API_KEY="여기에_실제_API_키_입력"
```

> 💡 **API 키 받는 방법**: https://aistudio.google.com/apikey

### 3단계: 벡터 데이터베이스 초기화 (10-30분)

```bash
# 프로젝트 루트로 이동
cd ..

# 초기화 스크립트 실행
python backend/scripts/init_database.py
```

**진행 상황:**
```
==========================================
PC 부품 벡터 데이터베이스 초기화 시작
==========================================
SQL 파일: backend\data\pc_data_dump.sql

Step 1: SQL 데이터 파싱
파싱 완료: 8개 테이블, 총 2,456개 레코드

Step 2: 문서 생성
cpu 테이블 처리 중: 234개 레코드
gpu 테이블 처리 중: 189개 레코드
...
총 2,456개의 문서 생성 완료

Step 3: 벡터 데이터베이스에 추가
2456개의 문서를 추가 중...
배치 1: 임베딩 생성 중...
진행: 100/2456 (4.1%)
...
문서 추가 완료. 총 아이템 수: 2456

==========================================
벡터 데이터베이스 초기화 완료
총 문서 수: 2456
==========================================
```

### 4단계: 시스템 테스트 (1분)

```bash
python backend/scripts/test_rag.py
```

**출력 예시:**
```
============================================================
쿼리: 게임용 고성능 그래픽카드 추천해줘
============================================================

검색된 부품 수: 5

추천 결과:
{
  "analysis": "게임용으로는 높은 성능의 GPU가 필요합니다...",
  "components": [
    {
      "category": "gpu",
      "name": "NVIDIA RTX 4090",
      "price": "250",
      "features": ["4K 게이밍", "레이트레이싱", "DLSS 3.0"]
    }
  ]
}
```

### 5단계: API 서버 실행 (즉시)

#### 방법 1: 자동 스크립트 사용 (권장)

```bash
# Windows
run_dev.bat

# Linux/Mac
./run_dev.sh
```

#### 방법 2: 수동 실행

```bash
cd backend
.venv\Scripts\activate  # Windows
# 또는
source .venv/bin/activate  # Linux/Mac

python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**브라우저에서 확인:**
- 🌐 API 문서: http://localhost:8000/docs
- 💚 헬스 체크: http://localhost:8000/health
- 📊 통계: http://localhost:8000/stats

> ⚠️ **주의**: 벡터 DB가 없으면 서버 시작 시 자동으로 초기화됩니다 (약 10-15분 소요)

## 📝 첫 API 요청 보내기

### cURL로 테스트

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "게임용 CPU 추천",
    "top_k": 5
  }'
```

### Python으로 테스트

```python
import requests

response = requests.post(
    "http://localhost:8000/query",
    json={
        "query": "150만원 예산으로 게이밍 PC 조립",
        "top_k": 5
    }
)

print(response.json())
```

### JavaScript (프론트엔드)로 테스트

```javascript
const response = await fetch('http://localhost:8000/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: '영상 편집용 워크스테이션',
    top_k: 5
  })
});

const data = await response.json();
console.log(data.recommendation);
```

## ⚡ 일반적인 문제 해결

### Q1: "GEMINI_API_KEY가 설정되지 않았습니다" 오류

```bash
# .env 파일이 backend 디렉토리에 있는지 확인
ls backend/.env

# 없다면 생성
cp backend/.env.example backend/.env

# API 키 확인
cat backend/.env
```

### Q2: SQL 파일을 찾을 수 없음

```bash
# 파일 존재 확인
ls backend/data/pc_data_dump.sql

# 없다면 경로 확인
python backend/scripts/init_database.py --sql-file "절대경로/pc_data_dump.sql"
```

### Q3: ChromaDB 초기화 실패

```bash
# ChromaDB 디렉토리 삭제 후 재시도
rm -rf backend/chroma_db  # Linux/Mac
rmdir /s backend\chroma_db  # Windows

# 재초기화
python backend/scripts/init_database.py --force
```

### Q4: 포트 8000이 이미 사용 중

```bash
# 다른 포트 사용
uvicorn main:app --reload --port 8001
```

### Q5: 가상 환경이 활성화되지 않음

**Windows:**
```bash
# PowerShell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.venv\Scripts\activate

# CMD
.venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

## 🎯 다음 단계

1. **API 탐색**: http://localhost:8000/docs에서 모든 엔드포인트 확인
2. **프론트엔드 연동**: `frontend/js/api.js`에서 API 호출
3. **커스터마이징**: `backend/rag/config.py`에서 설정 조정
4. **배포**: Vercel (프론트) + Cloud Run (백엔드)

## 📚 추가 문서

- [전체 가이드](./RAG_GUIDE.md): 심화 사용법 및 고급 기능
- [백엔드 README](./README.md): 상세 아키텍처 및 API 레퍼런스
- [문제 해결](./RAG_GUIDE.md#문제-해결): 일반적인 문제 및 해결책

## 🆘 도움이 필요하신가요?

1. **로그 확인**: `--log-level DEBUG` 옵션으로 상세 로그 확인
2. **통계 확인**: `curl http://localhost:8000/stats`로 시스템 상태 확인
3. **이슈 보고**: GitHub Issues에 문제 보고

---

**팁**: 초기 설정만 하면 다음부터는 2-3분 안에 시스템을 시작할 수 있습니다!

