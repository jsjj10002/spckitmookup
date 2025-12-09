# 프롬프트 관리

AI 프롬프트를 중앙에서 관리하는 디렉토리입니다.

## 파일 구조

```
prompts/
├── system-instruction.js    # 시스템 프롬프트 (AI 역할 정의)
├── user-prompt-template.js  # 사용자 프롬프트 템플릿
├── index.js                 # 통합 모듈
└── README.md               # 이 파일
```

## 사용법

### 시스템 프롬프트

```javascript
import { SYSTEM_INSTRUCTION } from './prompts/system-instruction.js';
```

AI의 역할과 행동 지침을 정의합니다.

### 사용자 프롬프트 템플릿

```javascript
import { buildPCRecommendationPrompt } from './prompts/user-prompt-template.js';

const prompt = buildPCRecommendationPrompt('게임용 PC 추천해주세요');
```

사용자 메시지를 AI 요청 형식으로 변환합니다.

### 전체 요청 구성

```javascript
import { buildGeminiRequest } from './prompts/index.js';

const request = await buildGeminiRequest('게임용 PC 추천해주세요');
// Gemini API에 바로 전달 가능한 형식
```

## 향후 계획

- [ ] 프롬프트 버전 관리
- [ ] A/B 테스트를 위한 프롬프트 변형
- [ ] 프롬프트 성능 모니터링
- [ ] 다국어 프롬프트 지원

