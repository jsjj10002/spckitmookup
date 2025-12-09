/**
 * 경량 장비 프로브: 브라우저에서 합법적으로 접근 가능한 신호만 수집한다.
 * - 반환값은 민감 정보 최소화(버킷/불리언/요약치) 원칙을 따른다.
 */
export async function probeLight() {
  const cores = typeof navigator.hardwareConcurrency === 'number'
    ? navigator.hardwareConcurrency
    : null;

  const deviceMemoryRaw = typeof navigator.deviceMemory === 'number'
    ? navigator.deviceMemory
    : null;

  // RAM 버킷팅(대략 GiB 단위): 2/4/8/16+
  const deviceMemoryBucket = (function bucketizeRam(gib) {
    if (gib == null) return null;
    if (gib < 3) return '≤2GB';
    if (gib < 6) return '4GB';
    if (gib < 12) return '8GB';
    if (gib < 24) return '16GB';
    return '24GB+';
  })(deviceMemoryRaw);

  let storageUsagePct = null;
  try {
    if (navigator.storage && navigator.storage.estimate) {
      const { usage, quota } = await navigator.storage.estimate();
      if (typeof usage === 'number' && typeof quota === 'number' && quota > 0) {
        storageUsagePct = Math.round((usage / quota) * 100);
      }
    }
  } catch { /* 무시: 브라우저별 권한/구현 차이 */ }

  const webgpu = !!(navigator && navigator.gpu);

  // (옵션) GPU 벤더: WebGL debug 확장 사용 가능 시에만 벤더 문자열 일부 축약
  let gpuVendor = null;
  try {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    if (gl) {
      const ext = gl.getExtension('WEBGL_debug_renderer_info');
      if (ext) {
        const vendor = gl.getParameter(ext.UNMASKED_VENDOR_WEBGL) || '';
        // 축약(벤더만): NVIDIA/AMD/Intel/Apple/Unknown
        const v = vendor.toLowerCase();
        if (v.includes('nvidia')) gpuVendor = 'NVIDIA';
        else if (v.includes('amd') || v.includes('ati')) gpuVendor = 'AMD';
        else if (v.includes('intel')) gpuVendor = 'Intel';
        else if (v.includes('apple')) gpuVendor = 'Apple';
        else gpuVendor = 'Unknown';
      }
    }
  } catch { /* 일부 브라우저에서 비활성/차단됨 */ }

  const screenInfo = {
    width: (window.screen && window.screen.width) || null,
    height: (window.screen && window.screen.height) || null,
    dpr: typeof window.devicePixelRatio === 'number' ? window.devicePixelRatio : null,
  };

  return {
    cores,
    deviceMemoryBucket,
    storageUsagePct,
    webgpu,
    screen: screenInfo,
    gpuVendor, // null 가능
  };
}


