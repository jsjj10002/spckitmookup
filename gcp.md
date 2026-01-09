# **GCP Cloud Run 배포 가이드**

백엔드 서버를 Google Cloud Run에 배포하고, 로컬의 대용량 데이터(ChromaDB)를 Google Cloud Storage(GCS)와 연동하는 방법을 안내합니다.

## **1. Google Cloud 프로젝트 준비**

### **1-1. 프로젝트 생성 및 Billing 확인**

1. [Google Cloud Console](https://console.cloud.google.com/)에 접속합니다.
2. 새 프로젝트를 생성하거나 기존 프로젝트를 선택합니다.
3. *Billing(결제)**이 프로젝트에 연결되어 있는지 확인합니다.

### **1-2. GCS 버킷 생성 및 데이터 업로드**

Cloud Run은 로컬 파일 저장이 초기화되므로, 벡터 데이터를 GCS에 올려두고 시작할 때 다운로드해야 합니다.

1. **Google Cloud Storage** 메뉴로 이동합니다.
2. *버킷 생성(Create Bucket)**을 클릭합니다.
    - 이름 예시: `spckit-data` (전역적으로 고유해야 함)
    - 위치: `asia-northeast3` (서울) 권장
    - 나머지는 기본값 유지 후 생성합니다.
3. 로컬의 `backend/chroma_db` 폴더를 압축합니다.
    - 파일명: `chroma_db.zip` (이 이름이 중요합니다!)
    - **중요**: 압축을 풀었을 때 `chroma.sqlite3` 파일이 바로 나오거나 `chroma_db` 폴더 안에 있도록 구조를 확인하세요. 스크립트는 `/tmp/chroma_db`에 해제합니다.
    - `backend/chroma_db` 폴더 *안의 내용물*을 압축하는 것이 가장 안전합니다. (즉, zip 파일 최상위에 `chroma.sqlite3`가 위치)
    - 만약 폴더째로 압축했다면 `backend/scripts/download_data.py`가 자동으로 `chroma_db` 폴더 구조를 감지하지 못할 수 있으니, **폴더 안의 내용물들을 선택해서 zip으로 압축**해주세요.
4. 생성한 버킷에 `chroma_db.zip` 파일을 업로드합니다.

## **2. 권한 설정 (Service Account)**

Cloud Run이 GCS 버킷에 접근할 수 있도록 권한이 필요합니다.

1. **IAM 및 관리** 메뉴로 이동합니다.
2. Cloud Run이 사용할 서비스 계정(기본적으로 `Default Compute Service Account`)을 확인합니다.
3. 해당 계정에 **Storage Object Viewer** (스토리지 개체 뷰어) 권한을 추가합니다.
    - 또는 버킷 자체의 권한 탭에서 해당 이메일을 추가하고 `Storage Object Viewer` 권한을 줘도 됩니다.

## **3. Docker 이미지 빌드 및 푸시**

터미널에서 다음 명령어를 실행합니다. (Google Cloud SDK가 설치되어 있어야 합니다)

```
# 1. GCP 로그인
gcloud auth login
gcloudconfigsetproject [YOUR_PROJECT_ID]

# 2. Artifact Registry 생성 (최초 1회)
gcloudartifactsrepositoriescreatemy-repo--repository-format=docker\
--location=asia-northeast3--description="Docker repository"

# 3. 이미지 빌드 및 푸시 (Google Cloud Build 사용)
# 시간이 조금 걸립니다.
gcloudbuildssubmit--tagasia-northeast3-docker.pkg.dev/[YOUR_PROJECT_ID]/my-repo/spckit-backend.

```

> Note: [YOUR_PROJECT_ID]는 실제 프로젝트 ID로 바꿔주세요.
> 

## **4. Cloud Run 서비스 배포**

### **4-1. 서비스 생성**

1. **Cloud Run** 메뉴로 이동하여 **서비스 만들기(Create Service)**를 클릭합니다.
2. **컨테이너 이미지 URL**에 위에서 빌드한 이미지 경로를 선택합니다.
    - 예: `asia-northeast3-docker.pkg.dev/[YOUR_PROJECT_ID]/my-repo/spckit-backend`

### **4-2. 환경 변수 설정 (중요!)**

**변수 및 비밀** 탭에서 다음 환경 변수를 추가합니다.

| **변수명** | **값** | **설명** |
| --- | --- | --- |
| `USE_GCS_DATA` | `true` | GCS 다운로드 활성화 |
| `GCS_BUCKET_NAME` | `[생성한 버킷 이름]` | 예: `spckit-data` |
| `CHROMA_PERSIST_DIRECTORY` | `/tmp/chroma_db` | 쓰기 가능한 임시 경로 |
| `GEMINI_API_KEY` | `[API 키]` | Gemini API 키 |
| `GOOGLE_API_KEY` | `[API 키]` | (위와 동일) |
| `ENVIRONMENT` | `production` | 프로덕션 모드 |

### **4-3. 리소스 설정**

**컨테이너, 볼륨, 네트워킹, 보안** 탭에서:

- **메모리**: 최소 **4GB** 이상 권장 (벡터 데이터 로딩 및 Gemini 모델 통신)
- **CPU**: 1 또는 2
- **실행 환경**: 기본값 (1세대)

### **4-4. 배포**

- *만들기(Create)**를 클릭하여 배포를 시작합니다. 배포 로그에서 `Starting download from GCS bucket...` 메시지가 뜨고 성공적으로 서버가 뜨는지 확인합니다.

## **5. 프론트엔드 연동**

배포가 완료되면 **서비스 URL** (예: `https://spckit-backend-xyz.a.run.app`)이 생성됩니다. Vercel에 배포할 프론트엔드의 `.env` 또는 환경 설정에서 `VITE_API_URL`을 이 주소로 변경해주면 됩니다

코드 변경 시 자동으로 배포되도록 하려면 **Google Cloud Build 트리거(Trigger)**를 설정해야 합니다. 이를 위해 방금 프로젝트 루트에

cloudbuild.yaml 파일을 생성해 두었습니다. 이 파일은 "코드가 변경되면 이미지를 빌드하고 -> 푸시하고 -> Cloud Run에 새 버전을 배포하라"는 명령서입니다.

이제 GCP 콘솔에서 다음 설정을 한 번만 해주시면 됩니다:

1. **GitHub 연결**:
    - [**Cloud Build > 트리거(Triggers)**](https://console.cloud.google.com/cloud-build/triggers) 메뉴로 이동합니다.
    - *저장소 연결(Connect Repository)**를 클릭하고 GitHub 저장소를 선택하여 연결합니다.
2. **트리거 생성**:
    - *트리거 만들기(Create Trigger)**를 클릭합니다.
    - **이름**:  (자유롭게 입력)
        
        ```
        auto-deploy-trigger
        ```
        
    - **이벤트**:  선택
        
        ```
        주 분기로 푸시(Push to a branch)
        ```
        
    - **소스**: 연결한 GitHub 저장소 및 브랜치(**main** 또는 ) 선택
        
        ```
        master
        ```
        
    - **구성(Configuration)**:  선택
        
        ```
        Cloud Build 구성 파일(yaml 또는 json)
        ```
        
    - **위치**: **cloudbuild.yaml** (기본값)

이제 로컬에서 코드를 수정하고

```
git push
```

를 하면, Cloud Build가 자동으로 감지하여 새 버전을 배포합니다.

**참고**:

cloudbuild.yaml 파일 내의

```
my-repo
```

와

```
spckit-backend
```

이름은 앞서 가이드에서 생성한 Artifact Registry 저장소 이름 및 Cloud Run 서비스 이름과 일치해야 합니다. (혹시 다르게 만드셨다면

**cloudbuild.yaml**

파일을 열어서 수정해주세요.)