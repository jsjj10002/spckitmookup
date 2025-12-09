# 프론트엔드 v2 디자인 - 필요한 파일 목록

## 📋 개요

모든 아이콘을 SVG 형식으로 통일하여 확장성과 품질을 향상시켰습니다.

---

## ✅ CDN으로 해결된 항목 (별도 파일 불필요)

다음 소셜 아이콘들은 **Simple Icons CDN**을 통해 자동으로 로드되므로 별도 파일이 필요하지 않습니다:

- ✅ **Discord 아이콘** - `https://cdn.jsdelivr.net/npm/simple-icons@v11/icons/discord.svg`
- ✅ **X (Twitter) 아이콘** - `https://cdn.jsdelivr.net/npm/simple-icons@v11/icons/x.svg`
- ✅ **Reddit 아이콘** - `https://cdn.jsdelivr.net/npm/simple-icons@v11/icons/reddit.svg`

**참고:** CDN 대신 로컬 파일을 사용하고 싶다면, 위 SVG 파일들을 다운로드하여 `images/` 폴더에 저장하고 HTML의 `src` 경로를 수정하세요.

---

## 📁 준비해야 할 파일 목록

다음 파일들은 **반드시 준비**해야 합니다:

### 1. 메인 로고 (필수)

**파일 경로:** `front_v2/images/spckit-logo.svg`

**설명:**
- Spckit의 메인 로고를 SVG 형식으로 준비
- 헤더 좌측 상단에 표시됨
- 권장 크기: 가로 82px × 세로 42px (현재 CSS 기준)

**현재 상태:** 
- ❌ 파일 없음 (필요)
- 기존 `spckit logo.png`가 있다면 SVG로 변환 필요

---

### 2. 배경 이미지 (필수)

**파일 경로:** `front_v2/images/round.png`

**설명:**
- 메인 배경에 사용되는 원형 그라데이션 배경 이미지
- 현재 PNG 형식으로 사용 중
- SVG로 변환 가능하나, 그라데이션 효과를 고려하면 PNG 유지 권장

**현재 상태:**
- ❓ 파일 존재 여부 확인 필요

---

### 3. 아바타 이미지 (선택 - figma-design2.html용)

**파일 경로:** `front_v2/images/user-avatar.svg` 또는 `front_v2/images/user-avatar.png`

**설명:**
- `figma-design2.html`의 헤더 브레드크럼에 사용되는 사용자 아바타
- 현재는 외부 서비스(`pravatar.cc`) 사용 중
- 로컬 파일로 교체 가능 (선택사항)

**현재 상태:**
- ✅ 외부 CDN 사용 중 (교체 불필요하나, 원하면 로컬 파일로 교체 가능)

---

## 📂 디렉토리 구조

```
front_v2/
├── images/
│   ├── spckit-logo.svg      ← 준비 필요
│   └── round.png            ← 준비 필요 (또는 기존 파일 확인)
├── figma-design.html
├── figma-design.css
├── figma-design2.html
├── figma-design2.css
└── REQUIRED_FILES.md        (이 파일)
```

---

## 🔧 적용된 변경사항

### HTML 변경사항 (`figma-design.html`)

1. **메인 로고:** PNG → SVG 경로로 변경
   ```html
   <!-- 변경 전 -->
   <img src="images\spckit logo.png" alt="로고" />
   
   <!-- 변경 후 -->
   <img src="images/spckit-logo.svg" alt="Spckit 로고" />
   ```

2. **소셜 아이콘:** PNG → Simple Icons CDN SVG로 변경
   - Discord, X(Twitter), Reddit 모두 CDN 링크 사용
   - 별도 파일 다운로드 불필요

### CSS 변경사항 (`figma-design.css`)

1. **소셜 아이콘 스타일 추가:**
   - SVG 아이콘을 흰색으로 표시하기 위한 필터 적용
   - 호버 효과 개선

---

## 📝 추가 참고사항

### Simple Icons CDN 사용법

현재 소셜 아이콘은 Simple Icons CDN을 사용하고 있습니다. 

**로컬 파일로 전환하려면:**

1. Simple Icons에서 SVG 파일 다운로드:
   - https://simpleicons.org/icons/discord.html
   - https://simpleicons.org/icons/x.html
   - https://simpleicons.org/icons/reddit.html

2. `front_v2/images/` 폴더에 저장:
   - `discord.svg`
   - `x.svg`
   - `reddit.svg`

3. HTML 파일의 `src` 경로 수정:
   ```html
   <!-- CDN 사용 -->
   <img src="https://cdn.jsdelivr.net/npm/simple-icons@v11/icons/discord.svg" />
   
   <!-- 로컬 파일 사용 -->
   <img src="images/discord.svg" />
   ```

### 로고 파일 변환 가이드

기존 PNG 로고가 있다면 SVG로 변환하는 방법:

1. **온라인 변환 도구 사용:**
   - https://convertio.co/kr/png-svg/
   - https://cloudconvert.com/png-to-svg

2. **벡터화 도구 사용 (더 나은 품질):**
   - Adobe Illustrator의 Image Trace 기능
   - Inkscape (무료)

3. **직접 SVG 제작:**
   - Figma에서 SVG로 Export
   - Adobe Illustrator에서 SVG로 저장

---

## ✅ 체크리스트

프로젝트를 완료하기 위해 다음 항목들을 확인하세요:

- [ ] `front_v2/images/spckit-logo.svg` 파일 준비
- [ ] `front_v2/images/round.png` 파일 확인 또는 준비
- [ ] (선택) 소셜 아이콘을 로컬 파일로 전환할 경우 SVG 파일 다운로드
- [ ] 모든 이미지 파일이 올바른 경로에 있는지 확인
- [ ] 브라우저에서 이미지가 정상적으로 표시되는지 테스트

---

## 🎨 디자인 참고

- 모든 아이콘은 SVG 형식으로 통일되어 확대/축소 시에도 선명함을 유지합니다
- 소셜 아이콘은 흰색으로 표시되며, 호버 시 더 밝아집니다
- 메인 로고는 헤더와 푸터에서 사용됩니다

---

**최종 업데이트:** 2025-01-XX
**작성자:** AI Assistant

