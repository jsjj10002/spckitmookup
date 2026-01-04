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

// =============================================================================
// Step-by-Step API 함수
// =============================================================================

/**
 * Step-by-Step 세션 시작
 * @param {number} budget - 총 예산 (원)
 * @param {string} purpose - 사용 목적 (gaming, workstation, general)
 * @returns {Promise<Object>} 세션 정보 및 CPU 후보 목록
 */
export async function startStepSession(budget, purpose = 'general') {
  const url = `${API_BASE_URL}/step/start`;
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: API_HEADERS,
      body: JSON.stringify({ budget, purpose }),
    });
    
    if (!response.ok) {
      const text = await response.text();
      console.error(`[API] Step 세션 시작 실패: ${response.status}`, text);
      throw new Error('세션 시작에 실패했습니다.');
    }
    
    return response.json();
  } catch (error) {
    console.error('[API] Step 세션 시작 오류', error);
    throw error;
  }
}

/**
 * 현재 단계의 후보 부품 조회
 * @param {string} sessionId - 세션 ID
 * @param {number} step - 단계 번호 (선택, 없으면 현재 단계)
 * @param {number} topK - 조회할 후보 수 (기본 5)
 * @returns {Promise<Object>} 후보 부품 목록
 */
export async function getStepCandidates(sessionId, step = null, topK = 5) {
  let url = `${API_BASE_URL}/step/${sessionId}/candidates?top_k=${topK}`;
  if (step !== null) {
    url += `&step=${step}`;
  }
  
  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: API_HEADERS,
    });
    
    if (!response.ok) {
      const text = await response.text();
      console.error(`[API] 후보 조회 실패: ${response.status}`, text);
      throw new Error('후보 조회에 실패했습니다.');
    }
    
    return response.json();
  } catch (error) {
    console.error('[API] 후보 조회 오류', error);
    throw error;
  }
}

/**
 * 부품 선택 및 다음 단계로 진행
 * @param {string} sessionId - 세션 ID
 * @param {number} step - 현재 단계 번호
 * @param {string} componentId - 선택한 부품 ID
 * @param {Object} componentData - 부품 상세 정보 (선택)
 * @returns {Promise<Object>} 다음 단계 정보 또는 완료 요약
 */
export async function selectComponent(sessionId, step, componentId, componentData = null) {
  const url = `${API_BASE_URL}/step/${sessionId}/select`;
  
  const payload = {
    step,
    component_id: componentId,
    component_data: componentData,
  };
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: API_HEADERS,
      body: JSON.stringify(payload),
    });
    
    if (!response.ok) {
      const text = await response.text();
      console.error(`[API] 부품 선택 실패: ${response.status}`, text);
      throw new Error('부품 선택에 실패했습니다.');
    }
    
    return response.json();
  } catch (error) {
    console.error('[API] 부품 선택 오류', error);
    throw error;
  }
}

/**
 * 세션 요약 조회 (현재까지 선택한 부품 목록 및 총 가격)
 * @param {string} sessionId - 세션 ID
 * @returns {Promise<Object>} 세션 요약
 */
export async function getSessionSummary(sessionId) {
  const url = `${API_BASE_URL}/step/${sessionId}/summary`;
  
  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: API_HEADERS,
    });
    
    if (!response.ok) {
      const text = await response.text();
      console.error(`[API] 요약 조회 실패: ${response.status}`, text);
      throw new Error('요약 조회에 실패했습니다.');
    }
    
    return response.json();
  } catch (error) {
    console.error('[API] 요약 조회 오류', error);
    throw error;
  }
}

export { API_BASE_URL };

