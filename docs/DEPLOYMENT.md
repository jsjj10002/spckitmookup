# 배포 가이드

Spckit AI v2 배포를 위한 가이드입니다.

## 🚀 배포 전 체크리스트

- [ ] Gemini API 키가 환경 변수로 설정되어 있는지 확인
- [ ] 프로덕션 빌드 테스트 완료
- [ ] 모든 이미지 파일이 `frontend/images/` 에 있는지 확인
- [ ] CORS 설정 확인 (Gemini API 호출)

## 📦 빌드

### 로컬 빌드

```bash
# 프로덕션 빌드
npm run build

# 빌드 결과물 확인
cd dist
```

## 🌐 정적 호스팅 배포

### Vercel 배포

1. **Vercel 계정 연결**
```bash
npm install -g vercel
vercel login
```

2. **프로젝트 설정**
- Root Directory: `./`
- Build Command: `npm run build`
- Output Directory: `dist`

3. **환경 변수 설정**
- `VITE_GEMINI_API_KEY`: Gemini API 키

4. **배포**
```bash
vercel --prod
```

### Netlify 배포

1. **netlify.toml 생성** (프로젝트 루트에)
```toml
[build]
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200

[build.environment]
  NODE_VERSION = "18"
```

2. **Netlify CLI 설치 및 배포**
```bash
npm install -g netlify-cli
netlify login
netlify init
netlify deploy --prod
```

3. **환경 변수 설정** (Netlify 대시보드)
- `VITE_GEMINI_API_KEY`: Gemini API 키

### GitHub Pages 배포

1. **gh-pages 브랜치 생성**
```bash
npm install -g gh-pages
npm run build
gh-pages -d dist
```

2. **GitHub 설정**
- Repository Settings > Pages
- Source: `gh-pages` branch
- Root: `/`

**주의**: GitHub Pages는 서버사이드 환경 변수를 지원하지 않으므로, API 키를 클라이언트 코드에 직접 포함해야 합니다. (보안상 권장하지 않음)

## 🐳 Docker 배포

### Dockerfile 작성

```dockerfile
# Build stage
FROM node:18-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### nginx.conf

```nginx
server {
    listen 80;
    server_name localhost;
    
    root /usr/share/nginx/html;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
}
```

### Docker 빌드 및 실행

```bash
# 이미지 빌드
docker build -t spckit-ai:v2 .

# 컨테이너 실행
docker run -d -p 8080:80 spckit-ai:v2
```

## 🔒 보안 고려사항

### API 키 보호

1. **절대 클라이언트 코드에 하드코딩하지 마세요**
   - 현재 `api.js`의 임시 키는 개발용입니다
   - 프로덕션에서는 반드시 환경 변수 사용

2. **백엔드 프록시 사용 (권장)**
   - Gemini API 호출을 서버사이드에서 처리
   - 클라이언트는 자체 백엔드 API만 호출
   - API 키가 노출되지 않음

### CORS 설정

Gemini API는 CORS를 지원하지만, 프로덕션에서는 백엔드 프록시 사용을 권장합니다.

## 📊 모니터링

### 추천 도구

- **Google Analytics**: 사용자 행동 분석
- **Sentry**: 에러 모니터링
- **Lighthouse**: 성능 측정

## 🔄 CI/CD 설정

### GitHub Actions 예시

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        
    - name: Install dependencies
      run: npm ci
      
    - name: Build
      run: npm run build
      env:
        VITE_API_KEY: ${{ secrets.VITE_API_KEY }}
        
    - name: Deploy to Vercel
      uses: amondnet/vercel-action@v20
      with:
        vercel-token: ${{ secrets.VERCEL_TOKEN }}
        vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
        vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
        working-directory: ./
```

## 📝 배포 후 테스트

1. 랜딩 페이지 로드 확인
2. 채팅 입력 및 빌더 페이지 전환 테스트
3. AI 응답 받기 테스트
4. 부품 선택 및 가격 계산 테스트
5. 모바일 반응형 테스트

## 🐛 문제 해결

### "API 키가 유효하지 않습니다"

- 환경 변수가 올바르게 설정되었는지 확인
- `VITE_` 접두사가 있는지 확인 (Vite 환경 변수)
- 빌드 시 환경 변수가 주입되었는지 확인

### "CORS 에러"

- Gemini API는 브라우저에서 직접 호출 시 CORS 제한이 있을 수 있음
- 백엔드 프록시를 통한 호출 권장

### 빌드 오류

```bash
# 캐시 삭제 후 재빌드
rm -rf node_modules dist
npm install
npm run build
```

## 📞 지원

문제가 발생하면 GitHub Issues에 등록해주세요.

