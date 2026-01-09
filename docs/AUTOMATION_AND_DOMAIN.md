# 자동 배포 및 도메인 연결 가이드

이 문서는 **자동 배포(CI/CD) 설정**과 **커스텀 도메인(spckit.ai) 연결** 방법을 안내합니다.

---

## 1. 백엔드 자동 배포 설정 (Cloud Build)

GitHub에 코드를 푸시할 때마다 Goolge Cloud Run 서버가 자동으로 업데이트되도록 설정합니다.
이미 프로젝트에 `cloudbuild.yaml` 파일이 준비되어 있으므로, **GCP 콘솔에서 트리거(Trigger)**만 연결하면 됩니다.

### 1-1. GitHub 저장소 연결
1. [Google Cloud Console - Cloud Build - 트리거](https://console.cloud.google.com/cloud-build/triggers) 페이지로 이동합니다.
2. 상단의 **"저장소 관리(Manage Repositories)"** 또는 **"저장소 연결(Connect Repository)"**을 클릭합니다.
3. 소스로 **GitHub**를 선택하고, 본인의 GitHub 계정을 인증한 뒤 `spckitmookup` 저장소를 선택하여 연결합니다.

### 1-2. 트리거 생성
1. 다시 **"트리거(Triggers)"** 페이지에서 **"트리거 만들기(Create Trigger)"**를 클릭합니다.
2. 다음 항목을 입력합니다:
    *   **이름**: `auto-deploy-backend` (자유롭게 입력)
    *   **이벤트**: `주 분기로 푸시(Push to a branch)`
    *   **소스**:
        *   저장소: 방금 연결한 저장소 선택
        *   분기(Branch): `^main$` 또는 `^master$` (메인 브랜치 이름)
    *   **구성(Configuration)**: `Cloud Build 구성 파일(yaml 또는 json)` 선택 (중요!)
    *   **위치(Location)**: `cloudbuild.yaml` (기본값 유지)
3. **"만들기(Create)"** 버튼을 누릅니다.

### 1-3. 서비스 계정 권한 설정 (중요)
Cloud Build가 Cloud Run에 배포하려면 추가 권한이 필요합니다.
1. [IAM 및 관리자](https://console.cloud.google.com/iam-admin/iam) 페이지로 이동합니다.
2. `[PROJECT_NUMBER]@cloudbuild.gserviceaccount.com` 형식의 이메일을 가진 **Cloud Build Service Account**를 찾습니다.
3. 연필 아이콘(수정)을 누르고 다음 **역할(Role)**을 추가합니다:
    *   **Cloud Run 관리자 (Cloud Run Admin)**: 배포를 위해 필요
    *   **서비스 계정 사용자 (Service Account User)**: Cloud Run 실행 계정을 사용하기 위해 필요
4. 저장합니다.

### 1-4. 테스트
*   이제 로컬에서 코드를 조금 수정하고(`README.md` 등) `git push`를 해보세요.
*   Cloud Build 기록 탭에서 자동으로 빌드가 시작되고, 몇 분 뒤 Cloud Run에 새 버전이 배포되는지 확인합니다.

---

## 2. 도메인 연결 (spckit.ai)

`spckit.ai` 같은 나만의 도메인을 갖기 위해서는 **도메인 구입**과 **DNS 설정**이 필요합니다.

### 2-1. 도메인 구입
도메인 등록 업체(Registrar)에서 도메인을 구매해야 합니다. `.ai` 도메인은 보통 연간 $60~$100 정도로 가격대가 있는 편입니다.
*   **추천 업체**: 가비아(Gabia), 호스팅케이알(Hosting.kr), Google Domains, Namecheap 등
*   원하는 업체에서 `spckit.ai` 검색 후 구매를 진행합니다.

### 2-2. 백엔드 연결 (Cloud Run)
Cloud Run 서버(`...run.app`)에 도메인을 연결합니다. (예: `api.spckit.ai`)

1. [Cloud Run 콘솔](https://console.cloud.google.com/run)에서 서비스(`spckit-backend`)를 클릭합니다.
2. 상단의 **"통합(Integrations)"** 또는 **"커스텀 도메인 관리(Manage Custom Domains)"**를 찾습니다.
3. **"매핑 추가(Add Mapping)"**를 클릭합니다.
4. **"서비스 도메인 확인(Verify service domain)"** 절차를 따릅니다.
    *   Google Search Console을 통해 도메인 소유권을 확인해야 합니다.
    *   제공되는 **TXT 레코드**를 도메인 구입처(가비아 등)의 **DNS 설정** 페이지에 추가합니다.
5. 소유권 확인 후, `api.spckit.ai` 같은 서브 도메인을 입력하여 매핑합니다.
6. Cloud Run이 제공하는 **A 레코드** 또는 **CNAME 레코드** 값을 복사하여, 다시 도메인 구입처의 DNS 설정에 추가합니다.
    *   적용까지 10분~24시간이 걸릴 수 있습니다.

### 2-3. 프론트엔드 연결 (Vercel)
Vercel에 배포된 프론트엔드(`...vercel.app`)에 메인 도메인(`spckit.ai`)을 연결합니다.

1. [Vercel 대시보드](https://vercel.com/dashboard)에서 프로젝트를 선택합니다.
2. **Settings** -> **Domains** 메뉴로 이동합니다.
3. 입력창에 `spckit.ai`를 입력하고 **Add**를 누릅니다.
4. Vercel이 제안하는 **DNS 설정 값(A Record 또는 CNAME)**을 확인합니다.
    *   **Type**: `A`
    *   **Name**: `@` (또는 빈칸)
    *   **Value**: `76.76.21.21` (Vercel IP)
5. 도메인 구입처(가비아 등)의 DNS 설정 페이지에 가서 이 레코드를 추가합니다.

### 요약: DNS 설정 예시 (도메인 구입처에서 설정)

| 타입 | 호스트(Name) | 값(Value) | 설명 |
| --- | --- | --- | --- |
| **A** | `@` | `76.76.21.21` | 메인 도메인(`spckit.ai`) -> 프론트엔드(Vercel) |
| **CNAME** | `www` | `cname.vercel-dns.com` | `www.spckit.ai` -> 프론트엔드(Vercel) |
| **A** | `api` | `216.239.32.21` | 백엔드 API(`api.spckit.ai`) -> Cloud Run (IP는 실제 콘솔 값 확인 필요) |

> **참고**: 백엔드 도메인을 연결했다면, 꼭 Vercel의 환경 변수(`VITE_API_BASE_URL`)도 `https://api.spckit.ai`로 업데이트해줘야 합니다!
