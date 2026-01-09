import { auth, provider } from './firebase-config.js';
import { signInWithPopup, signOut, onAuthStateChanged } from "firebase/auth";

// 현재 로그인한 사용자 정보 저장
let currentUser = null;

// 로그인 함수
export async function loginWithGoogle() {
    try {
        const result = await signInWithPopup(auth, provider);
        const user = result.user;
        console.log("Logged in user:", user.displayName);
        return user;
    } catch (error) {
        console.error("Login failed:", error);
        alert("로그인에 실패했습니다: " + error.message);
        throw error;
    }
}

// 로그아웃 함수
export async function logout() {
    try {
        await signOut(auth);
        console.log("User logged out");
        // 페이지 새로고침으로 상태 초기화
        window.location.reload();
    } catch (error) {
        console.error("Logout failed:", error);
    }
}

// 로그인 상태 감지 및 UI 업데이트
export function setupAuthListener(updateUIParams) {
    // updateUIParams: { loginBtnId, profileImgIDs, onLogin, onLogout }

    onAuthStateChanged(auth, (user) => {
        currentUser = user;
        if (user) {
            console.log("Auth State: Logged In", user.displayName);
            if (updateUIParams.onLogin) updateUIParams.onLogin(user);
        } else {
            console.log("Auth State: Logged Out");
            if (updateUIParams.onLogout) updateUIParams.onLogout();
        }
    });
}

// 현재 사용자 가져오기
export function getCurrentUser() {
    return currentUser;
}

// 채팅 등 작업 전 로그인 체크 (로그인 안되어있으면 로그인 창 띄움)
export async function ensureLoggedIn(msg = "이 기능을 사용하려면 로그인이 필요합니다.") {
    if (currentUser) return currentUser;

    const confirmLogin = confirm(`${msg}\n지금 로그인 하시겠습니까?`);
    if (confirmLogin) {
        return await loginWithGoogle();
    }
    return null;
}
