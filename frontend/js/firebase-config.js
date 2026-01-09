// Firebase Configuration
// TODO: docs/FIREBASE_SETUP.md 가이드를 보고 본인의 키로 교체하세요.
// Replace with your actual Firebase config keys

// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

const firebaseConfig = {
    apiKey: "AIzaSyARU8i1imh0hG_6ohQL7kD55VHubtN9vsE",
    authDomain: "spckit-auth.firebaseapp.com",
    projectId: "spckit-auth",
    storageBucket: "spckit-auth.firebasestorage.app",
    messagingSenderId: "285923044692",
    appId: "1:285923044692:web:35e78082e407b24e5dacc1"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();

export { auth, provider };
