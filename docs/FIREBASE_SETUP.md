# Firebase 구글 로그인 설정 가이드

이 문서는 **구글 로그인(Google Login)** 기능을 위해 Firebase 프로젝트를 만들고, API 키를 발급받는 방법을 안내합니다.

---

## 1. Firebase 프로젝트 생성
1. [Firebase Console](https://console.firebase.google.com/)에 접속하여 구글 계정으로 로그인합니다.
2. **"프로젝트 추가"** 버튼을 클릭합니다.
3. 프로젝트 이름(예: `spckit-auth`)을 입력하고 계속 진행합니다.
4. "Google 애널리틱스"는 사용 안 함으로 설정해도 됩니다. **"프로젝트 만들기"**를 완료합니다.

## 2. 웹 앱 등록 및 키 확인
1. 프로젝트 개요 페이지 중앙에 있는 **웹 아이콘(</>)**을 클릭합니다.
2. 앱 닉네임(예: `spckit-web`)을 입력하고 **"앱 등록"**을 누릅니다. (호스팅 설정은 체크 안 해도 됨)
3. **"SDK 추가 및 구성"** 화면에 나오는 코드 중 `const firebaseConfig = { ... }` 부분을 찾습니다.
    *   `apiKey`, `authDomain`, `projectId` 등의 값이 들어있습니다.
    *   **이 값들을 복사해두세요.** (나중에 `frontend/js/firebase-config.js` 파일에 넣어야 합니다.)

## 3. 인증(Authentication) 설정
1. 왼쪽 메뉴에서 **"빌드"** -> **"Authentication"**을 클릭합니다.
2. **"시작하기"** 버튼을 누릅니다.
3. **"Sign-in method"** 탭에서 **"Google"**을 선택합니다.
4. **"사용 설정"** 토글을 켜고, **프로젝트 지원 이메일**을 선택한 뒤 **"저장"**합니다.

## 4. 도메인 승인 (중요!)
로그인이 허용될 도메인을 추가해야 합니다.
1. Authentication 페이지의 **"설정(Settings)"** -> **"승인된 도메인(Authorized domains)"** 탭으로 이동합니다.
2. **"도메인 추가"**를 클릭하고 다음 도메인들을 각각 추가합니다.
    *   `localhost` (기본으로 있음)
    *   `spckit.xyz` (구매한 도메인)
    *   `scpkitai.vercel.app` (Vercel 도메인)

---

## 5. 코드 적용 방법
1. 프로젝트의 `frontend/js/firebase-config.js` 파일을 엽니다.
2. 위 2번 단계에서 복사한 `firebaseConfig` 내용을 붙여넣습니다.

```javascript
// 예시
const firebaseConfig = {
  apiKey: "AIzaSy...",
  authDomain: "spckit-auth.firebaseapp.com",
  projectId: "spckit-auth",
  // ...
};
```
