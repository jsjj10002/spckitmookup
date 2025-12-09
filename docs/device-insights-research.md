### 브라우저 기반 장비 신호 수집 리서치 (요약)

#### 수집 가능 신호(동의/비식별 우선)
- RAM 대략값: `navigator.deviceMemory` (버킷 단위 0.5/1/2/4/8/16+) [MDN]
- CPU 스레드 수: `navigator.hardwareConcurrency` [MDN]
- 저장소 사용/할당: `navigator.storage.estimate()` → { usage, quota } [MDN]
- WebGPU 지원/리밋: `navigator.gpu` → `adapter.limits`(지원 시) [MDN]
- 화면정보: `window.devicePixelRatio`, `screen.width/height`
- (옵션) GPU 벤더/렌더러: WebGL `WEBGL_debug_renderer_info` 확장 [MDN]
  - 프라이버시/지문채취 우려로 일부 브라우저 미지원 또는 무력화
- UA-CH 고엔트로피: `navigator.userAgentData.getHighEntropyValues([...])` [MDN]
  - 서버에서 CH 요청 헤더 설정 필요, 지문채취 최소화 정책 필요

#### 비권장/제한 신호
- Battery Status API: 폐지/비활성 추세(프라이버시 이슈)
- Network Information API: 브라우저별 지원 불균일, 신뢰성 낮음
- `performance.memory`: Chrome 한정·비표준(신뢰도/이식성 낮음)

#### 프라이버시 가드레일
- 민감값 버킷팅: RAM(예: 4/8/16+), 스레드(2/4/8+), 저장소 사용률(%)
- GPU 문자열은 벤더/클래스만 축약 저장 또는 해시 후 일시 보관(세션)
- 명시적 동의 모달: 수집 항목·목적·보존기간·거부 대안(설문) 고지
- 서버: IP 비저장/익명화, UA-CH는 opt-in 헤더로만 요청, 이벤트 비식별 키

#### 참고 문서(근거)
- MDN: Navigator.deviceMemory, Device Memory API, hardwareConcurrency, StorageManager.estimate(), WEBGL_debug_renderer_info, WebGPU API, UA-CH
- W3C: Device Memory, Quota Management/Storage API 초안
- 브라우저 동향: Battery Status/Network Information 비권장, Fingerprinting 최소화 정책

#### 적용 요약
- 라이트 수집(A): deviceMemory/cores/storage/WebGPU/화면 + (가능 시) GPU 벤더
- 마이크로 벤치(B): 짧은 CPU/GPU/IO 측정으로 등급화(동의 후)
- 결과는 용도 프로필과 비교해 과사양/병목/저활용 조언 카드로 매핑


