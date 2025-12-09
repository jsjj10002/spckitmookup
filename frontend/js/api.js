/**
 * API 통신 모듈
 * FastAPI 백엔드 API 서버와 연결하여 추천 결과를 가져옵니다.
 * Vite 환경 변수에 `VITE_API_BASE_URL`이 설정되어 있으면 해당 값을 우선 사용합니다.
 */
// [수정] 개발 모드일 땐 localhost:8000, 배포 시엔 빈 문자열(상대 경로) 사용
const isDev = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const DEFAULT_API_BASE_URL = isDev ? 'http://localhost:8000' : '';

const API_BASE_URL = (() => {
  if (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE_URL) {
    const candidate = import.meta.env.VITE_API_BASE_URL;
    if (typeof candidate === 'string' && candidate.trim()) {
      return candidate.trim();
    }
  }
  return DEFAULT_API_BASE_URL;
})();

const API_HEADERS = {
  'Content-Type': 'application/json',
};

async function fetchBackendRecommendation(payload) {
  const url = `${API_BASE_URL}/query`;

  let response;
  try {
    response = await fetch(url, {
      method: 'POST',
      headers: API_HEADERS,
      body: JSON.stringify(payload),
    });
  } catch (error) {
    console.error('[API] 백엔드 서버 연결 실패', error);
    throw new Error('백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.');
  }

  if (!response.ok) {
    const text = await response.text();
    console.error(`[API] ${response.status} ${response.statusText}: ${text}`);
    throw new Error('백엔드 API가 오류를 반환했습니다. 콘솔 로그를 확인하세요.');
  }

  return response.json();
}

/**
 * 사용자의 질문을 FastAPI `/query` 엔드포인트로 전달하고
 * 추천 결과를 반환합니다.
 */
export async function getPCRecommendation(userMessage, options = {}) {
  const query = (userMessage || '').trim();
  if (!query) {
    throw new Error('질문을 입력해주세요.');
  }

  const sanitizedTopK =
    typeof options.top_k === 'number'
      ? Math.max(1, Math.min(20, Math.floor(options.top_k)))
      : 5;

  const payload = {
    query,
    top_k: sanitizedTopK,
    category: options.category,
    include_context: options.include_context ?? false,
  };

  const data = await fetchBackendRecommendation(payload);

  const recommendation = data?.recommendation ?? data;
  if (!recommendation || typeof recommendation !== 'object') {
    console.error('[API] 추천 응답이 유효하지 않습니다.', data);
    throw new Error('백엔드에서 추천 데이터를 받아올 수 없습니다.');
  }

  if (!Array.isArray(recommendation.components)) {
    console.warn('[API] 컴포넌트 리스트가 없습니다.', recommendation);
    recommendation.components = [];
  }

  return recommendation;
}

/**
 * 가격 문자열에서 정수만 추출합니다.
 */
export function extractPrice(priceStr) {
  if (!priceStr || typeof priceStr !== 'string') {
    return 0;
  }

  const digits = priceStr.replace(/[^\d]/g, '');
  const parsed = parseInt(digits, 10);
  return Number.isNaN(parsed) ? 0 : parsed;
}

/**
 * 숫자를 원화 문자열로 포맷합니다.
 */
export function formatPrice(price) {
  const numeric = typeof price === 'number' ? price : extractPrice(price);
  if (numeric === 0) {
    return '0원';
  }
  return `${numeric.toLocaleString('ko-KR')}원`;
}

export { API_BASE_URL };
