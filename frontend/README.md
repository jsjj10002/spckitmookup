# Spckit AI: PC Builder V2

PC 부품 추천 AI 어시스턴트 - HTML/CSS/JavaScript 버전

## 🚀 주요 기능

- **AI 기반 부품 추천**: Gemini AI를 활용한 맞춤형 PC 부품 추천
- **4분할 인터페이스**: 
  - 왼쪽: 채팅 영역
  - 오른쪽 위 왼쪽: 선택된 부품 리스트
  - 오른쪽 위 오른쪽: 3D 미리보기 (준비 중)
  - 오른쪽 아래: 추천 부품 목록
- **실시간 타이핑 애니메이션**: AI 응답의 자연스러운 표시
- **부품 선택 및 관리**: 클릭으로 부품 선택, 총 가격 자동 계산

## 📁 프로젝트 구조

```
front_v2/
├── index.html          # 랜딩 페이지 (초기 화면)
├── builder.html        # 빌더 페이지 (4분할 인터페이스)
├── landing.css         # 랜딩 페이지 스타일
├── builder.css         # 빌더 페이지 스타일
├── js/
│   ├── landing.js      # 랜딩 페이지 로직
│   ├── builder.js      # 빌더 페이지 메인 로직
│   └── api.js          # API 통신 모듈
└── images/
    ├── spckit-logo.svg # 로고
    └── round.png       # 배경 이미지
```

## 🛠️ 설치 및 실행

### 사전 요구사항

- Node.js 18 이상
- Gemini API 키 ([발급 받기](https://aistudio.google.com/app/apikey))

### 설치

```bash
# 의존성 설치
npm install

# 환경 변수 설정
cp .env.example .env
# .env 파일에 API 키 입력
```

### 개발 서버 실행

```bash
npm run dev
```

브라우저에서 자동으로 `http://localhost:3000` 열림

### 빌드

```bash
npm run build
```

빌드 결과물은 `dist/` 폴더에 생성됩니다.

## 🎨 디자인

Bolt.new 스타일을 기반으로 한 모던한 UI/UX:
- 다크 모드 테마
- 블러 효과 및 그라데이션
- 부드러운 애니메이션
- 반응형 레이아웃

## 🔧 기술 스택

- **프론트엔드**: HTML5, CSS3, JavaScript (ES6+)
- **빌드 도구**: Vite
- **AI**: Google Gemini 2.0 Flash
- **스타일**: 커스텀 CSS (CSS Variables, Flexbox, Grid)

## 📝 API 사용법

### Gemini API 연동

`js/api.js` 파일에서 Gemini API와 통신합니다:

```javascript
import { getPCRecommendation } from './api.js';

// PC 부품 추천 요청
const response = await getPCRecommendation('게임용 PC 추천해주세요, 예산은 200만원입니다');

// 응답 구조
{
  analysis: "상세한 분석 내용...",
  components: [
    {
      category: "CPU",
      name: "AMD Ryzen 7 7800X3D",
      price: "약 450,000원",
      features: ["최고의 게이밍 성능", "8코어 16스레드"]
    },
    // ...
  ]
}
```

## 🔄 페이지 흐름

1. **랜딩 페이지** (`index.html`)
   - 사용자가 초기 메시지 입력
   - "추천 받기" 버튼 클릭
   
2. **빌더 페이지** (`builder.html`)
   - URL 파라미터로 메시지 전달
   - 자동으로 AI에게 요청 전송
   - 채팅 형식으로 대화 진행
   - 추천 부품을 클릭하여 선택
   - 선택된 부품 리스트 및 총 가격 확인

## 🎯 향후 계획

- [ ] 3D 부품 미리보기 기능 구현
- [ ] 부품 호환성 검사
- [ ] 성능 벤치마크 비교
- [ ] 견적서 PDF 다운로드
- [ ] 사용자 계정 시스템
- [ ] 저장된 견적 관리

## 📄 라이선스

MIT License

## 👥 기여

기여는 언제나 환영합니다! Pull Request를 보내주세요.

