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
  // [수정] 멀티 에이전트 엔드포인트 사용
  const url = `${API_BASE_URL}/agent/chat`;

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
 * 사용자의 질문을 FastAPI `/agent/chat` 엔드포인트로 전달하고
 * 추천 결과를 반환합니다.
 */
export async function getPCRecommendation(userMessage, options = {}) {
  const query = (userMessage || '').trim();
  if (!query) {
    throw new Error('질문을 입력해주세요.');
  }

  // AgentChatRequest 형식에 맞춤
  // AgentChatRequest 형식에 맞춤
  const payload = {
    query,
    budget: options.budget || null,
    purpose: options.purpose || null,
    preferences: options.preferences || {}
  };

  const data = await fetchBackendRecommendation(payload);

  // [수정] RecommendationResult 형식 처리
  // data 구조: { status, agent_logs, total_price, components, compatibility_check }

  if (!data || typeof data !== 'object') {
    console.error('[API] 추천 응답이 유효하지 않습니다.', data);
    throw new Error('백엔드에서 추천 데이터를 받아올 수 없습니다.');
  }

  // agent_logs 배열을 합쳐서 하나의 분석 텍스트로 만듦
  const analysisText = Array.isArray(data.agent_logs) ? data.agent_logs.join('\n\n') : '';

  return {
    analysis: analysisText,
    components: data.components || [],
    total_price: data.total_price,
    status: data.status,
    compatibility: data.compatibility_check,
    extracted_requirements: data.extracted_requirements
  };
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

/**
 * 단계별 부품 후보 조회 (새로운 Step-by-Step API)
 * @param {Object} stepRequest - { query, session_id, current_step, selected_component_id, budget, purpose }
 * @returns {Promise<Object>} StepResponse
 */
export async function getStepCandidates(stepRequest) {
  const url = `${API_BASE_URL}/step/next`;

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: API_HEADERS,
      body: JSON.stringify(stepRequest),
    });

    if (!response.ok) {
      const text = await response.text();
      console.error(`[API] ${response.status} ${response.statusText}: ${text}`);
      throw new Error('Step 후보 조회 실패');
    }

    return await response.json();
  } catch (error) {
    console.error('[API] getStepCandidates 실패', error);
    throw error;
  }
}

/**
 * 부품 선택 및 다음 단계로 진행
 * @param {string} sessionId 
 * @param {string} componentId 
 * @returns {Promise<Object>} StepResponse for next step
 */
export async function selectComponent(sessionId, componentId, currentStep) {
  return getStepCandidates({
    session_id: sessionId,
    query: "다음 단계",
    current_step: currentStep,
    selected_component_id: componentId
  });
}

export { API_BASE_URL };
