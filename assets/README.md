# Assets

정적 에셋 파일 디렉토리입니다.

## 디렉토리 구조

```
assets/
├── 3d-models/          # 3D 모델 파일 (GLTF/GLB)
│   ├── cpu/           # CPU 모델
│   ├── gpu/           # GPU 모델
│   ├── motherboard/   # 메인보드 모델
│   ├── memory/        # 메모리 모델
│   ├── storage/       # 저장장치 모델
│   ├── psu/           # 파워서플라이 모델
│   └── case/          # 케이스 모델
├── textures/          # 텍스처 파일
└── images/            # 일반 이미지 파일
```

## 3D 모델 형식

- **권장 형식**: GLTF/GLB (압축 효율, 웹 최적화)
- **텍스처**: KTX2 또는 Basis Universal (압축)

## 배포 전략

- **개발 환경**: 로컬 파일 시스템
- **프로덕션**: GCP Cloud Storage + CDN 또는 Vercel Blob Storage

