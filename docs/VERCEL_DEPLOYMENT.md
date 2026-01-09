# Vercel 배포 가이드

프론트엔드를 Vercel에 배포하고 Cloud Run 백엔드와 연동하는 방법입니다.

## 1. GitHub 푸시
먼저 로컬의 변경 사항(특히 `package.json` 수정본)을 GitHub에 푸시해야 합니다.
```bash
git add .
git commit -m "Fix build script and config for Vercel"
git push
```

## 2. Vercel 프로젝트 생성
1. [Vercel 대시보드](https://vercel.com/dashboard)에 접속합니다.
2. **"Add New..."** 버튼을 누르고 **"Project"**를 선택합니다.
3. 연결된 GitHub 계정에서 `spckitmookup` 저장소를 찾아 **"Import"**를 누릅니다.

## 3. 배포 설정 (Configuration) - **중요**
`Configure Project` 화면에서 아래 항목들을 꼭 설정해주세요.

### 3-1. Framework Preset
- **Vite** (자동으로 감지될 것입니다. 만약 안 되면 선택해주세요.)

### 3-2. Build and Output Settings
- 기본값(`npm run build`, `dist`)을 그대로 두시면 됩니다.
- (방금 `package.json`을 수정해서 `vite build`가 실행되도록 만들었습니다.)

### 3-3. Environment Variables (환경 변수)
펼치기 버튼을 누르고 다음 변수를 추가합니다. 백엔드와 프론트엔드를 연결하는 핵심 고리입니다.

- **Key**: `VITE_API_BASE_URL`
- **Value**: `https://spckit-backend-498365125219.asia-northeast3.run.app`
  (백엔드 Cloud Run 주소입니다. 마지막에 `/`는 빼주세요.)

## 4. 배포 시작 (Deploy)
- 하단의 **"Deploy"** 버튼을 클릭합니다.
- 약 1분 정도 기다리면 배포가 완료되고 축하 화면이 나옵니다.
- **Preview** 이미지를 클릭해서 사이트로 이동해 봅니다.

## 5. 테스트
- 검색창에 "배그용 컴퓨터 견적 내줘" 같은 질문을 입력해 봅니다.
- 정상적으로 답변이 오면 성공입니다.

### 트러블슈팅
- **API 오류 발생 시**: 브라우저 개발자 도구(F12) -> Console 탭을 확인합니다.
    - 404/500 오류: 백엔드 서버 로그(GCP Console)를 확인합니다.
    - CORS 오류: 백엔드 `main.py`의 CORS 설정을 확인합니다.
- **화면이 안 나올 때**: Vercel의 `Deployments` 탭 -> 해당 배포 클릭 -> `Building` 로그를 확인하여 빌드 에러가 없는지 봅니다.
