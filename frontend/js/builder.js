/**
 * Builder 페이지 메인 스크립트
 * 채팅, 부품 추천, 선택 기능 등을 관리한다
 */

import { getPCRecommendation, extractPrice, formatPrice } from './api.js';

// DOM 요소
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const terminalContent = document.getElementById('terminal-content'); // 선택된 부품 (넰미널)
const fileList = document.getElementById('file-list'); // 추천 부품 (파일 트리)
const homeBtn = document.getElementById('home-btn');
const startBuildBtn = document.getElementById('start-build-btn');
const nextStepBtn = document.getElementById('next-step-btn');
const terminalLoading = document.getElementById('terminal-loading');
const terminalLoadingText = document.getElementById('terminal-loading-text');

// 상태 관리
let selectedParts = [];
let isLoading = false;
let chatHistory = [];
const CATEGORY_ORDER = ['CPU', 'Mainboard', 'RAM', 'GPU', 'SSD', 'Power', 'Case', 'Cooler'];

// 빌드 상태 관리
let currentPhase = 'requirements'; // 'requirements' | 'building'
let buildStageIndex = 0;
const BUILD_STAGES = ['CPU', 'Mainboard', 'RAM', 'GPU', 'SSD', 'Power', 'Case', 'Cooler'];

// Step-by-Step 상태 관리
let stepSessionId = null;  // Step-by-step 세션 ID
let currentStep = 0;       // 현재 단계 (0: 초기, 1-8: 부품 선택)
let isInStepMode = false;  // Step-by-step 모드 활성화 여부

/**
 * 로컬 스토리지 키
 */
const STORAGE_KEY = 'spckit_builder_state';

/**
 * 초기화
 */
function init() {
  // 1. 상태 복원
  loadState();

  // 1.5 성능 패널 준비
  ensurePerformancePanel();

  // 2. URL 파라미터 처리
  const urlParams = new URLSearchParams(window.location.search);
  const initialMessage = urlParams.get('message');

  if (initialMessage) {
    // [수정] URL 파라미터가 있는 경우 = landing.js에서 새로 시작한 것
    // landing.js에서 이미 localStorage를 초기화했으므로 chatHistory는 비어있어야 함
    // 만약 비어있지 않다면 (뒤로가기 등) 무시

    if (chatHistory.length === 0) {
      // URL 파라미터 정리 (중복 실행 방지)
      const newUrl = window.location.pathname;
      window.history.replaceState({}, document.title, newUrl);

      // 초기 메시지 처리
      setTimeout(() => handleSendMessage(initialMessage), 100);
    } else {
      // 이미 chatHistory가 있다면 (뒤로가기 등) URL만 정리
      const newUrl = window.location.pathname;
      window.history.replaceState({}, document.title, newUrl);
    }
  } else if (chatHistory.length === 0) {
    // 히스토리가 없고 초기 메시지도 없으면 환영 메시지
    // addMessage('안녕하세요! 어떤 PC를 맞추고 싶으신가요?', 'ai');
  }

  // UI 복원 (선택된 부품 등)
  updateSelectedParts();

  // 이벤트 리스너 등록
  sendBtn.addEventListener('click', handleSendClick);
  chatInput.addEventListener('keydown', handleKeyDown);
  homeBtn.addEventListener('click', () => {
    window.location.href = 'index.html';
  });

  // Start Build 버튼 리스너
  if (startBuildBtn) {
    startBuildBtn.addEventListener('click', startBuildProcess);
  }

  // Next Step 버튼 리스너
  if (nextStepBtn) {
    nextStepBtn.addEventListener('click', handleNextStep);
  }
}

/**
 * 시스템 사양 가져오기 (브라우저 정보 기반)
 */
function getSystemSpecs() {
  const specs = [];

  // 1. User Agent (OS, Browser)
  if (navigator.userAgent) {
    specs.push(`OS/Browser: ${navigator.userAgent}`);
  }

  // 2. CPU Cores (Logical Processors)
  if (navigator.hardwareConcurrency) {
    specs.push(`CPU Cores: ${navigator.hardwareConcurrency}`);
  }

  // 3. RAM (Device Memory in GB - 대략적인 값)
  if (navigator.deviceMemory) {
    specs.push(`RAM: ~${navigator.deviceMemory}GB`);
  }

  // 4. GPU (WebGL Renderer)
  try {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    if (gl) {
      const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
      if (debugInfo) {
        const renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
        specs.push(`GPU Renderer: ${renderer}`);
      }
    }
  } catch (e) {
    console.warn("GPU info not available", e);
  }

  return specs.join('\n');
}

/**
 * 상태 저장
 */
function saveState() {
  const state = {
    chatHistory,
    selectedParts,
    currentPhase,
    buildStageIndex
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

/**
 * 상태 불러오기
 */
function loadState() {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved) {
    try {
      const state = JSON.parse(saved);
      chatHistory = state.chatHistory || [];
      selectedParts = state.selectedParts || [];
      currentPhase = state.currentPhase || 'requirements';
      buildStageIndex = state.buildStageIndex || 0;

      // 채팅 UI 복원
      chatMessages.innerHTML = ''; // 초기화
      chatHistory.forEach(msg => {
        // AI 메시지 복원 시 타이핑 효과 없이 즉시 추가
        if (msg.role === 'user') {
          addMessage(msg.text, 'user');
        } else {
          // AI 메시지는 단순 텍스트로 복원
          const messageDiv = document.createElement('div');
          messageDiv.className = `message ai-message`;

          const header = document.createElement('div');
          header.className = 'message-header';
          header.innerHTML = `
                      <svg class="icon-bolt-small" width="40" height="14" viewBox="0 0 40 14" fill="currentColor">
                        <text x="0" y="12" font-size="14" font-family="Inter" font-weight="700">Spckit AI</text>
                      </svg>
                    `;
          messageDiv.appendChild(header);

          const bubble = document.createElement('div');
          bubble.className = 'message-bubble';
          bubble.textContent = msg.text;
          messageDiv.appendChild(bubble);

          chatMessages.appendChild(messageDiv);
        }
      });
      chatMessages.scrollTop = chatMessages.scrollHeight;

    } catch (e) {
      console.error("Failed to load state:", e);
      localStorage.removeItem(STORAGE_KEY);
    }
  }
}

/**
 * 전송 버튼 클릭 핸들러
 */
function handleSendClick() {
  const message = chatInput.value.trim();
  if (message && !isLoading) {
    handleSendMessage(message);
    chatInput.value = '';
  }
}

/**
 * 키보드 이벤트 핸들러 (Enter로 전송)
 */
function handleKeyDown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleSendClick();
  }
}

/**
 * 메시지 전송 및 AI 응답 처리 (Dual-AI 라우팅)
 */
async function handleSendMessage(message) {
  if (isLoading) return;

  isLoading = true;
  updateSendButtonState();

  // 사용자 메시지 UI 추가
  addMessage(message, 'user');
  chatHistory.push({ role: 'user', text: message });
  saveState(); // 상태 저장

  // 메시지 타입 감지: 빌드 요청 vs 대화
  const isBuildRequest = detectBuildRequest(message);

  const loadingMessage = addMessage('', 'ai', true);

  try {
    if (isBuildRequest && !isInStepMode) {
      // Step-by-Step 모드 시작
      const { getStepCandidates } = await import('./api.js');

      // 초기 세션 시작
      const stepResponse = await getStepCandidates({
        query: message,
        current_step: 0,
        budget: extractBudgetFromMessage(message),
        purpose: extractPurposeFromMessage(message)
      });

      stopDynamicLoadingText();
      loadingMessage.remove();

      // Step 모드 활성화
      isInStepMode = true;
      stepSessionId = stepResponse.session_id;
      currentStep = stepResponse.step;

      // AI 분석 메시지
      await addMessageWithTyping(stepResponse.analysis, 'ai');
      chatHistory.push({ role: 'model', text: stepResponse.analysis });

      // 부품 후보 표시
      displayRecommendations(stepResponse.candidates);
      saveState();

    } else if (isInStepMode) {
      // Step 모드 활성 중 - 대화는 Multi-Agent로
      stopDynamicLoadingText();
      loadingMessage.remove();

      const response = await getPCRecommendation(message);

      if (response.analysis) {
        await addMessageWithTyping(response.analysis, 'ai');
        chatHistory.push({ role: 'model', text: response.analysis });
      }
      saveState();

    } else {
      // 일반 대화 모드
      const response = await getPCRecommendation(message);

      stopDynamicLoadingText();
      loadingMessage.remove();

      if (response.analysis) {
        await addMessageWithTyping(response.analysis, 'ai');
        chatHistory.push({ role: 'model', text: response.analysis });
      }

      if (response.components && response.components.length > 0) {
        displayRecommendations(response.components);
      }

      saveState();
    }

  } catch (error) {
    console.error('메시지 전송 오류:', error);
    stopDynamicLoadingText();
    loadingMessage.remove();
    addMessage(error.message || '오류가 발생했습니다', 'error');
  } finally {
    isLoading = false;
    updateSendButtonState();
  }
}

/**
 * 빌드 요청 감지
 */
function detectBuildRequest(message) {
  const buildKeywords = ['견적', 'pc', 'PC', '추천', '맞춰', '조립', '구성'];
  return buildKeywords.some(keyword => message.includes(keyword));
}

/**
 * 메시지에서 예산 추출
 */
function extractBudgetFromMessage(message) {
  const match = message.match(/(\d+)만원/);
  if (match) {
    return parseInt(match[1]) * 10000;
  }
  const match2 = message.match(/(\d+)원/);
  if (match2) {
    return parseInt(match2[1]);
  }
  return null;
}

/**
 * 메시지에서 목적 추출
 */
function extractPurposeFromMessage(message) {
  if (message.includes('게임') || message.includes('게이밍')) return 'gaming';
  if (message.includes('작업') || message.includes('워크스테이션')) return 'workstation';
  return 'general';
}

/**
 * 빌드 프로세스 시작 (Plan/Start 버튼 클릭 시)
 */
async function startBuildProcess() {
  if (currentPhase === 'building') return; // 이미 진행 중이면 무시

  currentPhase = 'building';
  buildStageIndex = 0; // CPU부터 시작
  saveState();

  // UI 업데이트
  addMessageWithTyping("네, 알겠습니다. 이제 본격적으로 부품을 하나씩 맞춰볼까요? 먼저 **CPU**부터 살펴보겠습니다.", 'ai');

  // 첫 단계 부품 로드
  await loadStageComponents(BUILD_STAGES[buildStageIndex]);
}

/**
 * 특정 단계(Category)의 부품 로드
 */
async function loadStageComponents(stage) {
  if (!stage) return;

  // 터미널 로딩 표시
  showTerminalLoading(`Searching for ${stage}...`);
  fileList.innerHTML = ''; // 기존 리스트 초기화

  try {
    // 이전 대화 맥락에서 쿼리 추출 (가장 최근 사용자 메시지 사용)
    // 전체 요구사항을 다 포함하는게 좋겠지만, 간단하게 최근 메시지로 처리
    // 더 좋은 방법: chatHistory 전체를 요약하거나 system prompt에 포함

    // 여기서는 "단계별"이므로 이전 단계에서 선택한 부품 정보도 포함하면 좋음 (호환성 위해)
    // 하지만 백엔드가 아직 호환성 체크 로직이 완벽하지 않으므로 단순 쿼리

    const lastUserMsg = chatHistory.filter(m => m.role === 'user').pop()?.text || "가성비 좋은 PC";
    const query = `${lastUserMsg}`;

    const response = await getPCRecommendation(query, { category: stage });

    hideTerminalLoading();

    // 추천 목록 표시
    displayRecommendations(response.components);

    // 선택된 부품이 있다면 표시 (이전 단계에서 돌아왔을 때 등)
    highlightSelectedInRecommendation();

  } catch (error) {
    console.error(`Failed to load ${stage}:`, error);
    hideTerminalLoading();
    fileList.innerHTML = `<div class="file-item error">Failed to load ${stage} recommendations.</div>`;
  }
}

/**
 * 다음 단계로 이동 (Next Step 버튼)
 */
async function handleNextStep() {
  // 현재 단계에서 선택된 부품이 있는지 확인
  const currentStage = BUILD_STAGES[buildStageIndex];
  const isSelected = selectedParts.some(p => p.category.toLowerCase().includes(currentStage.toLowerCase()));

  if (!isSelected) {
    await addMessageWithTyping(`${currentStage}를 선택하지 않으셨네요. 다음 단계로 넘어갑니다.`, 'ai');
  } else {
    await addMessageWithTyping(`${currentStage} 선택 완료! 다음 부품을 보시죠.`, 'ai');
  }

  buildStageIndex++;
  saveState();

  if (buildStageIndex >= BUILD_STAGES.length) {
    await addMessageWithTyping("모든 부품 선택이 완료되었습니다! 견적을 확인해보세요.", 'ai');
    fileList.innerHTML = '<div class="file-item success">All steps completed! Check your build summary.</div>';
    return;
  }

  const nextStage = BUILD_STAGES[buildStageIndex];
  await addMessageWithTyping(`다음은 **${nextStage}**입니다.`, 'ai');
  await loadStageComponents(nextStage);
}


/**
 * 채팅 메시지 추가
 */
function addMessage(text, type = 'user', isLoading = false) {
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${type}-message`;

  if (type === 'ai') {
    const header = document.createElement('div');
    header.className = 'message-header';
    header.innerHTML = `
      <svg class="icon-bolt-small" width="40" height="14" viewBox="0 0 40 14" fill="currentColor">
        <text x="0" y="12" font-size="14" font-family="Inter" font-weight="700">Spckit AI</text>
      </svg>
    `;
    messageDiv.appendChild(header);
  }

  if (isLoading) {
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'thinking-indicator';
    loadingDiv.innerHTML = `
      <svg class="spinner" width="18" height="18" viewBox="0 0 18 18">
        <circle cx="9" cy="9" r="7" stroke="currentColor" stroke-width="2" fill="none" opacity="0.3"/>
        <path d="M9 2a7 7 0 0 1 7 7" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" />
      </svg>
      <span class="thinking-text">분석 중...</span>
    `;
    messageDiv.appendChild(loadingDiv);

    // 동적 로딩 텍스트 시작
    startDynamicLoadingText(messageDiv.querySelector('.thinking-text'));

  } else {
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.textContent = text;
    messageDiv.appendChild(bubble);
  }

  chatMessages.appendChild(messageDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;

  return messageDiv;
}

/**
 * 동적 로딩 텍스트 애니메이션 (멀티 에이전트 시뮬레이션)
 */
let loadingInterval;
function startDynamicLoadingText(element) {
  const steps = [
    "요구사항 분석 중...",
    "부품 검색 중...",
    "최적의 부품 선별 중...",
    "답변 생성 중..."
  ];
  let index = 0;

  // 초기 텍스트 설정
  element.textContent = steps[0];

  if (loadingInterval) clearInterval(loadingInterval);

  loadingInterval = setInterval(() => {
    index = (index + 1) % steps.length;

    // 텍스트 변경 애니메이션
    element.style.opacity = '0';
    element.style.transform = 'translateY(5px)';

    setTimeout(() => {
      element.textContent = steps[index];
      element.style.opacity = '1';
      element.style.transform = 'translateY(0)';
    }, 300);

  }, 1500); // 1.5초 간격 (더 빠르게)
}

function stopDynamicLoadingText() {
  if (loadingInterval) {
    clearInterval(loadingInterval);
    loadingInterval = null;
  }
}

/**
 * 타이핑 효과로 메시지 추가
 */
async function addMessageWithTyping(text, type = 'ai') {
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${type}-message`;

  if (type === 'ai') {
    const header = document.createElement('div');
    header.className = 'message-header';
    header.innerHTML = `
      <svg class="icon-bolt-small" width="40" height="14" viewBox="0 0 40 14" fill="currentColor">
        <text x="0" y="12" font-size="14" font-family="Inter" font-weight="700">Spckit AI</text>
      </svg>
    `;
    messageDiv.appendChild(header);
  }

  const bubble = document.createElement('div');
  bubble.className = 'message-bubble';
  messageDiv.appendChild(bubble);

  chatMessages.appendChild(messageDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;

  let charIndex = 0;
  // 타이핑 속도 개선 (기존 15ms -> 8ms)
  const typingSpeed = 8;

  return new Promise((resolve) => {
    const intervalId = setInterval(() => {
      if (charIndex < text.length) {
        bubble.textContent = text.substring(0, charIndex + 1);
        charIndex++;
        chatMessages.scrollTop = chatMessages.scrollHeight;
      } else {
        clearInterval(intervalId);
        resolve();
      }
    }, typingSpeed);
  });
}

// 아이콘 정의
const COMPONENT_ICONS = {
  'CPU': '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M9 1v3M15 1v3M9 20v3M15 20v3M20 9h3M20 14h3M1 9h3M1 14h3"/></svg>',
  'GPU': '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="11" cy="12" r="2"/><circle cx="17" cy="12" r="2"/><path d="M2 10h4v4H2z"/></svg>',
  'RAM': '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 4v16h20V4H2zm4 16V4m4 16V4m4 16V4m4 16V4"/></svg>',
  'SSD': '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="6" width="16" height="12" rx="2"/><path d="M6 10h12M6 14h12"/></svg>',
  'Mainboard': '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="16" height="16" rx="2"/><path d="M8 8h2v2H8zm4 0h4v4h-4zM8 14h2v2H8z"/></svg>',
  'Power': '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="16" height="16" rx="2"/><path d="M12 12h.01"/><circle cx="12" cy="12" r="4"/></svg>',
  'Case': '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="6" y="2" width="12" height="20" rx="2"/><path d="M10 6h4"/></svg>',
  'Cooler': '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="8"/><path d="M12 4v16M4 12h16"/></svg>',
  'Default': '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/></svg>'
};

/**
 * 추천 부품 표시 (카드 스타일)
 */
function displayRecommendations(components) {
  // 로딩 중이 아닐 때만 내용 지우기 (중복 방지)
  if (!terminalLoading.style.display || terminalLoading.style.display === 'none') {
    fileList.innerHTML = '';
  }

  if (!components || components.length === 0) {
    fileList.innerHTML = '<div class="file-item">추천 부품이 없습니다</div>';
    return;
  }

  const list = document.createElement('div');
  list.className = 'recommendation-list';

  components.forEach((component, index) => {
    const card = createRecommendationCard(component);
    // 순차적 등장 애니메이션 딜레이 (속도 개선)
    card.style.animationDelay = `${index * 0.05}s`;
    card.classList.add('animate-in');

    // 이미 선택된 부품인지 확인하여 스타일 적용
    const isSelected = selectedParts.some(p => p.name === component.name && p.category === component.category);
    if (isSelected) {
      card.classList.add('selected');
      card.style.opacity = '0.5'; // 선택된 것은 흐리게
    }

    list.appendChild(card);
  });

  fileList.appendChild(list);
}

/**
 * 추천 카드 생성
 */
function createRecommendationCard(component) {
  const card = document.createElement('div');
  card.className = 'recommendation-card';
  // 데이터 속성으로 식별자 저장 (재선택/해제용)
  card.dataset.name = component.name;
  card.dataset.category = component.category;

  // 아이콘 처리 - 이미지가 있으면 이미지, 없으면 SVG
  let iconHtml;
  const category = (component.category || '').toLowerCase();
  let componentImage = null;

  if (component.image || component.imageUrl) {
    componentImage = component.image || component.imageUrl;
  } else if (category.includes('cpu')) {
    componentImage = 'images/computer/cpu.jpg';
  } else if (category.includes('memory') || category.includes('ram')) {
    componentImage = 'images/computer/memory.jpg';
  } else if (category.includes('graphics') || category.includes('gpu') || category.includes('rtx') || category.includes('그래픽')) {
    componentImage = 'images/computer/rtx5060.jpg';
  } else if (category.includes('power') || category.includes('supply') || category.includes('파워')) {
    componentImage = 'images/computer/ssd.jpg';
  } else if (category.includes('motherboard') || category.includes('메인보드')) {
    componentImage = 'images/computer/asrock .jpg';
  }

  if (componentImage) {
    iconHtml = `<img src="${componentImage}" alt="${component.name}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 8px;">`;
  } else {
    const categoryKey = Object.keys(COMPONENT_ICONS).find(key =>
      category.includes(key.toLowerCase())
    ) || 'Default';
    iconHtml = COMPONENT_ICONS[categoryKey];
  }

  // 해시태그 처리 (hashtags가 없으면 features 사용)
  const tags = component.hashtags && component.hashtags.length > 0
    ? component.hashtags
    : (component.features || []);

  const tagsHtml = tags
    .slice(0, 3) // 최대 3개
    .map(tag => {
      const text = tag.startsWith('#') ? tag : `#${tag}`;
      return `<span class="tag">${text}</span>`;
    })
    .join('');

  card.innerHTML = `
    <div class="card-header">
      <div class="card-icon">${iconHtml}</div>
      <div class="card-info">
        <div class="card-category">${component.category}</div>
        <div class="card-name" title="${component.name}">${component.name}</div>
        <div class="card-tags">
          ${tagsHtml}
        </div>
      </div>
      <div class="card-price">${component.price}</div>
    </div>
    <div class="card-actions">
      <button class="info-btn" type="button" aria-label="성능 그래프 보기">
        <span class="info-dot">i</span>
        <span class="info-label">정보</span>
      </button>
    </div>
  `;

  // 정보 아이콘 클릭 시 성능 그래프 패널 표시
  const infoBtn = card.querySelector('.info-btn');
  if (infoBtn) {
    infoBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      showPerformancePanel(component);
    });
  }

  // 클릭 이벤트 - 부품 선택
  card.addEventListener('click', (e) => {
    // 이미 선택된 경우 무시하거나 해제 로직을 넣을 수 있음
    if (card.classList.contains('selected')) return;

    handleCardClick(e, card, component);
  });

  return card;
}

/**
 * 성능 그래프 패널 생성 (최초 1회)
 */
function ensurePerformancePanel() {
  const editorContent = document.querySelector('.editor-content');
  if (!editorContent) return;

  if (document.getElementById('performance-panel')) return;

  const panel = document.createElement('div');
  panel.id = 'performance-panel';
  panel.innerHTML = `
    <div class="perf-header">
      <div>
        <div class="perf-label">성능 그래프</div>
        <div class="perf-name"></div>
        <div class="perf-category"></div>
      </div>
      <button class="perf-close" aria-label="성능 패널 닫기">×</button>
    </div>
    <div class="perf-body"></div>
  `;

  panel.querySelector('.perf-close').addEventListener('click', () => {
    panel.classList.remove('visible');
  });

  editorContent.appendChild(panel);
}

/**
 * 성능 그래프 패널 표시
 */
function showPerformancePanel(component) {
  ensurePerformancePanel();
  const panel = document.getElementById('performance-panel');
  if (!panel) return;

  panel.classList.add('visible');
  panel.querySelector('.perf-name').textContent = component.name;
  panel.querySelector('.perf-category').textContent = component.category;

  const perfBody = panel.querySelector('.perf-body');
  perfBody.innerHTML = '';

  // ----- 가격 추적 그래프 (라인) -----
  const rawHistory = component.priceHistory || component.history || component.trend;
  const fallbackHistory = [
    { label: '6개월 전', value: 720000 },
    { label: '4개월 전', value: 780000 },
    { label: '3개월 전', value: 650000 },
    { label: '2개월 전', value: 840000 },
    { label: '1개월 전', value: 800000 },
    { label: '오늘', value: 760000 },
    { label: '다음 분기', value: 700000 },
  ];
  const history = Array.isArray(rawHistory) && rawHistory.length >= 3 ? rawHistory : fallbackHistory;

  const lineSection = document.createElement('div');
  lineSection.className = 'perf-section line-section';
  lineSection.innerHTML = `
    <div class="section-title">가격 예측 추이</div>
    <div class="line-chart">
      <svg preserveAspectRatio="none"></svg>
      <div class="line-x-labels"></div>
    </div>
  `;

  const svg = lineSection.querySelector('svg');
  const xLabelsContainer = lineSection.querySelector('.line-x-labels');
  const width = 1000; // virtual width for scaling
  const height = 260;
  const padding = { top: 24, right: 24, bottom: 50, left: 70 };
  const innerWidth = width - padding.left - padding.right;
  const innerHeight = height - padding.top - padding.bottom;
  svg.setAttribute('viewBox', `0 0 ${width} ${height}`);

  const values = history.map(h => Number.isFinite(h.value) ? h.value : 0);
  const maxV = 1000000;
  const minV = 0;
  const span = Math.max(1, maxV - minV);

  const points = values.map((v, i) => {
    const x = padding.left + (i / Math.max(1, history.length - 1)) * innerWidth;
    const y = padding.top + innerHeight - ((v - minV) / span) * innerHeight;
    return { x, y, v };
  });

  const polyline = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
  polyline.setAttribute('fill', 'none');
  polyline.setAttribute('stroke', '#3fa9f5');
  polyline.setAttribute('stroke-width', '4');
  polyline.setAttribute('points', points.map(p => `${p.x},${p.y}`).join(' '));

  const gradient = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
  gradient.id = 'lineGradient';
  gradient.setAttribute('x1', '0%');
  gradient.setAttribute('x2', '0%');
  gradient.setAttribute('y1', '0%');
  gradient.setAttribute('y2', '100%');
  const stop1 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
  stop1.setAttribute('offset', '0%');
  stop1.setAttribute('stop-color', '#3fa9f5');
  const stop2 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
  stop2.setAttribute('offset', '100%');
  stop2.setAttribute('stop-color', '#3fa9f5');
  gradient.appendChild(stop1);
  gradient.appendChild(stop2);

  const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
  defs.appendChild(gradient);

  svg.appendChild(defs);
  svg.appendChild(polyline);

  // Y축 라벨 (가격)
  const yTicks = [maxV, minV + span * 0.5, minV];
  yTicks.forEach(val => {
    const y = padding.top + innerHeight - ((val - minV) / span) * innerHeight;
    const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    t.setAttribute('x', padding.left - 10);
    t.setAttribute('y', y + 4);
    t.setAttribute('text-anchor', 'end');
    t.setAttribute('fill', 'var(--color-text-muted)');
    t.setAttribute('font-size', '12');
    t.setAttribute('font-weight', '700');
    t.setAttribute('font-family', 'inherit');
    t.textContent = `₩${Math.round(val)}`;
    svg.appendChild(t);
  });

  // 데이터 포인트 + 가격 라벨
  points.forEach((p, i) => {
    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('cx', p.x);
    circle.setAttribute('cy', p.y);
    circle.setAttribute('r', '6');
    circle.setAttribute('fill', '#3fa9f5');
    circle.style.cursor = 'pointer';
    svg.appendChild(circle);

    const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    text.setAttribute('x', p.x);
    text.setAttribute('y', p.y - 22);
    text.setAttribute('text-anchor', 'middle');
    text.setAttribute('fill', 'var(--color-text-primary)');
    text.setAttribute('font-size', '14');
    text.setAttribute('font-weight', '700');
    text.textContent = `₩${Math.round(p.v).toLocaleString('ko-KR')}`;
    text.style.opacity = '0';
    text.style.transition = 'opacity 0.2s ease';
    svg.appendChild(text);

    circle.addEventListener('mouseenter', () => text.style.opacity = '1');
    circle.addEventListener('mouseleave', () => text.style.opacity = '0');
  });

  // X축 라벨 (날짜/시점) - 호버 시 금액 표시
  history.forEach((h, idx) => {
    const label = document.createElement('span');
    label.textContent = h.label || '';
    label.style.position = 'relative';
    label.style.cursor = 'pointer';

    // 호버 시 표시할 가격 tooltip
    const tooltip = document.createElement('div');
    tooltip.textContent = `₩${Math.round(h.value).toLocaleString('ko-KR')}`;
    tooltip.style.position = 'absolute';
    tooltip.style.bottom = '100%';
    tooltip.style.left = '50%';
    tooltip.style.transform = 'translateX(-50%)';
    tooltip.style.whiteSpace = 'nowrap';
    tooltip.style.background = 'rgba(63, 169, 245, 0.9)';
    tooltip.style.color = 'white';
    tooltip.style.padding = '4px 8px';
    tooltip.style.borderRadius = '4px';
    tooltip.style.fontSize = '11px';
    tooltip.style.fontWeight = '700';
    tooltip.style.marginBottom = '4px';
    tooltip.style.opacity = '0';
    tooltip.style.pointerEvents = 'none';
    tooltip.style.transition = 'opacity 0.2s ease';

    label.appendChild(tooltip);
    label.addEventListener('mouseenter', () => tooltip.style.opacity = '1');
    label.addEventListener('mouseleave', () => tooltip.style.opacity = '0');

    xLabelsContainer.appendChild(label);
  });

  perfBody.appendChild(lineSection);

  // ----- 성능 지표 (바) -----
  const rawMetrics = component.benchmarks || component.performance || component.metrics;
  const fallbackMetrics = [
    { label: '게임', value: 78 },
    { label: '작업 효율', value: 72 },
    { label: '발열', value: 65 },
    { label: '전력 효율', value: 88 },
    { label: '저장속도', value: 74 },
  ];

  const metrics = Array.isArray(rawMetrics) && rawMetrics.length > 0 ? rawMetrics : fallbackMetrics;
  const barColors = ['#3fa9f5', '#5af78e', '#f7d35a', '#7dd7f5', '#f582a7', '#9c7bff', '#8be9fd'];

  const barSection = document.createElement('div');
  barSection.className = 'perf-section bar-section';
  barSection.innerHTML = `
    <div class="section-title">성능 효율성 분석</div>
    <div class="perf-rows"></div>
  `;

  const rowsContainer = barSection.querySelector('.perf-rows');

  metrics.slice(0, 6).forEach((m, idx) => {
    const label = m.label || `Metric ${idx + 1}`;
    const value = Number.isFinite(m.value) ? Math.max(0, Math.min(100, m.value)) : 0;

    const row = document.createElement('div');
    row.className = 'perf-row';
    const barColor = barColors[idx % barColors.length];
    row.innerHTML = `
      <div class="perf-row-label">${label}</div>
      <div class="perf-bar"><span style="width:${value}%; background:${barColor};"></span></div>
      <div class="perf-value">${value}%</div>
    `;

    rowsContainer.appendChild(row);
  });

  perfBody.appendChild(barSection);
}

/**
 * 카드 클릭 핸들러 (애니메이션 + 선택 로직)
 */
function handleCardClick(e, cardElement, component) {
  // 1. 쑤욱 들어가는 애니메이션 (Fly Effect)
  const rect = cardElement.getBoundingClientRect();
  const targetRect = fileList.getBoundingClientRect();

  const flyingElement = cardElement.cloneNode(true);
  flyingElement.classList.add('flying-element');
  flyingElement.style.width = `${rect.width}px`;
  flyingElement.style.height = `${rect.height}px`;
  flyingElement.style.left = `${rect.left}px`;
  flyingElement.style.top = `${rect.top}px`;
  flyingElement.style.margin = '0';
  flyingElement.classList.remove('animate-in'); // 등장 애니메이션 제거

  document.body.appendChild(flyingElement);

  // 애니메이션 실행
  requestAnimationFrame(() => {
    flyingElement.style.left = `${targetRect.left + 20}px`; // 타겟 위치로 이동
    flyingElement.style.top = `${targetRect.top + targetRect.height / 2}px`; // 타겟 중앙쯤으로
    flyingElement.style.transform = 'scale(0.2) opacity(0)';
    flyingElement.style.opacity = '0';
  });

  // 애니메이션 완료 후 부품 선택
  setTimeout(async () => {
    flyingElement.remove();

    // 부품 선택 처리
    selectPart(component);

    // Step-by-Step 모드일 때 다음 단계로 진행
    if (isInStepMode && stepSessionId) {
      try {
        const { selectComponent } = await import('./api.js');

        // 로딩 표시
        const loadingMessage = addMessage('', 'ai', true);

        // 다음 단계 조회
        const stepResponse = await selectComponent(stepSessionId, component.id, currentStep);

        stopDynamicLoadingText();
        loadingMessage.remove();

        // 단계 업데이트
        currentStep = stepResponse.step;

        if (stepResponse.is_final) {
          // 빌드 완성
          isInStepMode = false;
          await addMessageWithTyping(`PC 구성이 완료되었습니다! 총 ${stepResponse.total_price.toLocaleString('ko-KR')}원입니다.`, 'ai');
        } else {
          // 다음 단계 부품 표시
          await addMessageWithTyping(stepResponse.analysis, 'ai');
          displayRecommendations(stepResponse.candidates);
        }

        saveState();

      } catch (error) {
        console.error('다음 단계 진행 오류:', error);
        addMessage('다음 단계로 진행하는 중 오류가 발생했습니다.', 'error');
      }
    }
  }, 500);

  // 원본 카드 제거 (애니메이션 효과)
  cardElement.classList.add('selected');
  setTimeout(() => {
    cardElement.remove();
  }, 300);
}

/**
 * 부품 선택 및 상태 업데이트
 */
function selectPart(component) {
  // 같은 카테고리 부품이 이미 있으면 교체
  const existingIndex = selectedParts.findIndex(p => p.category === component.category);

  if (existingIndex !== -1) {
    // 기존 부품 교체
    selectedParts[existingIndex] = component;
  } else {
    selectedParts.push(component);
  }

  updateSelectedParts();
  saveState();
}

/**
 * 선택된 부품 표시 업데이트 (파일 트리 스타일)
 */
function updateSelectedParts() {
  terminalContent.innerHTML = '';

  if (selectedParts.length === 0) {
    terminalContent.innerHTML = '<div class="terminal-line" style="color: var(--color-text-muted); padding: 8px;">No parts selected</div>';
    return;
  }

  // 카테고리 순서대로 정렬
  selectedParts.sort((a, b) => {
    const idxA = CATEGORY_ORDER.findIndex(c => a.category.includes(c));
    const idxB = CATEGORY_ORDER.findIndex(c => b.category.includes(c));
    return (idxA === -1 ? 99 : idxA) - (idxB === -1 ? 99 : idxB);
  });

  selectedParts.forEach((component, index) => {
    const item = createFileItem(component, index);
    terminalContent.appendChild(item);
  });

  // 총 가격 표시
  const totalLine = document.createElement('div');
  totalLine.className = 'file-item';
  totalLine.style.borderTop = '1px solid var(--color-border)';
  totalLine.style.marginTop = '8px';
  totalLine.style.paddingTop = '8px';
  totalLine.style.fontWeight = '700';
  totalLine.innerHTML = `
    <span style="color: var(--color-success);">Total:</span>
    <span style="color: var(--color-link); margin-left: 8px;">${calculateTotal()}</span>
  `;
  terminalContent.appendChild(totalLine);
}

/**
 * 파일 아이템 생성 (파일 트리 스타일 - 원본 디자인)
 */
function createFileItem(component, index) {
  const item = document.createElement('div');
  item.className = 'file-item';
  item.style.display = 'flex';
  item.style.alignItems = 'center';
  item.style.justifyContent = 'space-between';
  item.style.padding = '6px 8px';
  item.dataset.index = index;

  const leftSection = document.createElement('div');
  leftSection.style.flex = '1';
  leftSection.style.overflow = 'hidden';
  leftSection.style.display = 'flex';
  leftSection.style.alignItems = 'center';

  const categorySpan = document.createElement('span');
  categorySpan.style.color = 'var(--color-success)';
  categorySpan.style.fontWeight = '500';
  categorySpan.style.marginRight = '8px';
  categorySpan.style.fontSize = '12px';
  categorySpan.textContent = `[${component.category}]`;

  const nameSpan = document.createElement('span');
  nameSpan.style.color = 'var(--color-text-secondary)';
  nameSpan.style.fontSize = '13px';
  nameSpan.textContent = component.name;
  nameSpan.style.whiteSpace = 'nowrap';
  nameSpan.style.overflow = 'hidden';
  nameSpan.style.textOverflow = 'ellipsis';

  leftSection.appendChild(categorySpan);
  leftSection.appendChild(nameSpan);

  const rightSection = document.createElement('div');
  rightSection.style.display = 'flex';
  rightSection.style.alignItems = 'center';
  rightSection.style.gap = '8px';

  const priceSpan = document.createElement('span');
  priceSpan.style.color = 'var(--color-link)';
  priceSpan.style.fontSize = 'var(--font-size-xs)';
  priceSpan.textContent = component.price;

  const removeBtn = document.createElement('button');
  removeBtn.style.padding = '2px 6px';
  removeBtn.style.borderRadius = '4px';
  removeBtn.style.background = 'transparent';
  removeBtn.style.border = 'none';
  removeBtn.style.color = 'var(--color-text-muted)';
  removeBtn.style.cursor = 'pointer';
  removeBtn.style.fontSize = '16px';
  removeBtn.textContent = '×';
  removeBtn.addEventListener('mouseenter', () => {
    removeBtn.style.background = 'rgba(255, 255, 255, 0.1)';
    removeBtn.style.color = 'var(--color-text-primary)';
  });
  removeBtn.addEventListener('mouseleave', () => {
    removeBtn.style.background = 'transparent';
    removeBtn.style.color = 'var(--color-text-muted)';
  });

  // 삭제 버튼 클릭 핸들러
  removeBtn.addEventListener('click', (e) => {
    e.stopPropagation();

    item.classList.add('removing');
    item.addEventListener('animationend', () => {
      // 삭제 시 Panel 2에 해당 부품이 있다면 다시 보이게 처리
      restoreRecommendationCard(component);
      removePart(index);
    }, { once: true });
  });

  rightSection.appendChild(priceSpan);
  rightSection.appendChild(removeBtn);

  item.appendChild(leftSection);
  item.appendChild(rightSection);

  return item;
}

/**
 * 추천 카드 복구 (삭제 시)
 */
function restoreRecommendationCard(component) {
  const cards = fileList.querySelectorAll('.recommendation-card');
  cards.forEach(card => {
    if (card.dataset.name === component.name && card.dataset.category === component.category) {
      card.style.display = 'flex'; // 다시 보이기
      card.style.opacity = '0';
      card.style.transform = 'translateX(0)';
      card.classList.remove('selected');

      // 페이드 인
      requestAnimationFrame(() => {
        card.style.opacity = '1';
      });
    }
  });
}

/**
 * 부품 제거
 */
function removePart(index) {
  selectedParts.splice(index, 1);
  updateSelectedParts();
  saveState();
}

/**
 * 총 가격 계산
 */
function calculateTotal() {
  const total = selectedParts.reduce((sum, part) => {
    return sum + extractPrice(part.price);
  }, 0);

  return formatPrice(total);
}

/**
 * 전송 버튼 상태 업데이트
 */
function updateSendButtonState() {
  sendBtn.disabled = isLoading;
  sendBtn.style.opacity = isLoading ? '0.5' : '1';
  sendBtn.style.cursor = isLoading ? 'not-allowed' : 'pointer';
}

/**
 * 터미널 로딩 표시 (멀티 에이전트 느낌)
 */
function showTerminalLoading(text) {
  if (terminalLoading) {
    terminalLoading.style.display = 'flex';
    terminalLoadingText.textContent = text;
  }
}

function hideTerminalLoading() {
  if (terminalLoading) {
    terminalLoading.style.display = 'none';
  }
}

/**
 * 추천 목록에서 선택된 항목 하이라이트 (재로드 시)
 */
function highlightSelectedInRecommendation() {
  // displayRecommendations 안에서 이미 처리함
}

// 초기화 실행
init();

/* ========================================
 * 이 부분 제거하면 3D 모델 제거됨 (3/4)
 * init3DViewer() 함수 전체와 하단의 setTimeout 호출 제거
 * ======================================== */
// 3D 뷰어 초기화 함수
async function init3DViewer() {
  try {
    console.log('3D 뷰어 초기화 시작...');
    const container = document.getElementById('model-viewer');
    if (!container) {
      console.error('3D 뷰어 컨테이너를 찾을 수 없습니다');
      return;
    }
    console.log('컨테이너 찾음:', container.clientWidth, 'x', container.clientHeight);

    // Three.js 모듈 동적 import
    console.log('Three.js 로드 중...');
    const THREE = await import('three');
    console.log('Three.js 로드 완료');
    const { GLTFLoader } = await import('three/addons/loaders/GLTFLoader.js');
    console.log('GLTFLoader 로드 완료');
    const { OrbitControls } = await import('three/addons/controls/OrbitControls.js');
    console.log('OrbitControls 로드 완료');

    // Scene 설정
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1a1a1a);

    // Camera 설정
    const camera = new THREE.PerspectiveCamera(
      50,
      container.clientWidth / container.clientHeight,
      0.1,
      1000
    );
    camera.position.set(0, 2, 5);
    camera.lookAt(0, 0, 0);

    // Renderer 설정
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    // OrbitControls 추가 (마우스로 회전, 확대/축소 가능)
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true; // 부드러운 움직임
    controls.dampingFactor = 0.05;
    controls.minDistance = 0.5; // 최소 줌 거리 (더 가까이)
    controls.maxDistance = 50; // 최대 줌 거리 (더 멀리)
    controls.autoRotate = false; // 자동 회전 비활성화

    // 조명 추가 (PC 내부를 최대한 밝게)
    const ambientLight = new THREE.AmbientLight(0xffffff, 3.5); // 주변광 극대화
    scene.add(ambientLight);

    const directionalLight1 = new THREE.DirectionalLight(0xffffff, 3.5); // 메인 조명 극대화
    directionalLight1.position.set(5, 5, 5);
    scene.add(directionalLight1);

    const directionalLight2 = new THREE.DirectionalLight(0xffffff, 3.0); // 보조 조명 극대화
    directionalLight2.position.set(-5, 3, -5);
    scene.add(directionalLight2);

    const directionalLight3 = new THREE.DirectionalLight(0xffffff, 2.5); // 하단 조명 극대화
    directionalLight3.position.set(0, -5, 5);
    scene.add(directionalLight3);

    const directionalLight4 = new THREE.DirectionalLight(0xffffff, 2.5); // 정면 조명 극대화
    directionalLight4.position.set(0, 0, 8);
    scene.add(directionalLight4);

    const directionalLight5 = new THREE.DirectionalLight(0xffffff, 2.0); // 5번째 조명 (상단)
    directionalLight5.position.set(0, 8, 0);
    scene.add(directionalLight5);

    // GLB 모델 로드
    const loader = new GLTFLoader();
    let model = null;

    console.log('GLB 파일 로드 시작: ./images/custom_gaming_pc.glb');
    loader.load(
      './images/custom_gaming_pc.glb',
      (gltf) => {
        console.log('GLB 로드 성공!', gltf);
        model = gltf.scene;
        scene.add(model);

        // 모델 크기 조정
        const box = new THREE.Box3().setFromObject(model);
        const size = box.getSize(new THREE.Vector3());
        const maxDim = Math.max(size.x, size.y, size.z);
        const scale = 2 / maxDim;
        model.scale.setScalar(scale);
        console.log('모델 크기:', size, '스케일:', scale);

        // 모델 중앙 정렬
        const center = box.getCenter(new THREE.Vector3());
        model.position.sub(center.multiplyScalar(scale));

        console.log('3D 모델 로드 및 설정 완료');
      },
      (progress) => {
        if (progress.total > 0) {
          const percent = (progress.loaded / progress.total * 100).toFixed(2);
          console.log('로딩 중:', percent + '%');
        }
      },
      (error) => {
        console.error('3D 모델 로드 오류:', error);
        console.error('파일 경로 확인 필요: ./images/custom_gaming_pc.glb');
      }
    );

    // 애니메이션 루프
    function animate() {
      requestAnimationFrame(animate);

      // OrbitControls 업데이트 (자동 회전 포함)
      controls.update();

      renderer.render(scene, camera);
    }
    animate();

    // 리사이즈 처리
    window.addEventListener('resize', () => {
      const width = container.clientWidth;
      const height = container.clientHeight;

      camera.aspect = width / height;
      camera.updateProjectionMatrix();

      renderer.setSize(width, height);
    });

    console.log('3D 뷰어 초기화 완료');
  } catch (error) {
    console.error('3D 뷰어 초기화 오류:', error);
  }
}

// 이 부분도 제거 (3D 뷰어 호출)
setTimeout(() => {
  init3DViewer();
}, 100);

