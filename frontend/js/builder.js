/**
 * Builder 페이지 메인 스크립트
 * 채팅, 부품 추천, 선택 기능 등을 관리한다
 */

import { getPCRecommendation, extractPrice, formatPrice, getStepCandidates, API_BASE_URL } from './api.js';
import { ensureLoggedIn, setupAuthListener, logout } from './auth.js';
import { saveCurrentBuild, shareCurrentBuild } from './community.js';

// DOM 요소
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');

// Textarea 자동 높이 조절
function autoResizeTextarea(textarea) {
  textarea.style.height = 'auto';
  textarea.style.height = Math.min(textarea.scrollHeight, 400) + 'px';
}

if (chatInput) {
  chatInput.addEventListener('input', () => autoResizeTextarea(chatInput));
  // 초기 높이 설정
  autoResizeTextarea(chatInput);
}
const selectedPartsContainer = document.getElementById('selected-parts-panel'); // 선택된 부품 (에디터 영역)
const fileList = document.getElementById('file-list'); // 추천 부품 (파일 트리)
const resetBtn = document.getElementById('reset-btn'); // 초기화 버튼
const homeBtn = document.getElementById('home-btn');
const startBuildBtn = document.getElementById('start-build-btn');
const nextStepBtn = document.getElementById('next-step-btn');
const terminalLoading = document.getElementById('terminal-loading');
const terminalLoadingText = document.getElementById('terminal-loading-text');

// 상태 관리
let selectedParts = [];
let isLoading = false;
let chatHistory = [];
const CATEGORY_ORDER = ['CPU', 'Mainboard', 'RAM', 'GPU', 'SSD', 'HDD', 'Power', 'Cooler', 'Case'];

// 슬롯형 UI 표시용 카테고리 정의 (라벨 + 매칭 키워드)
const CATEGORY_SLOTS = [
  { label: 'CPU', match: ['cpu'] },
  { label: '메인보드', match: ['mainboard', 'motherboard', '메인보드'] },
  { label: '메모리', match: ['ram', 'memory', '메모리'] },
  { label: '그래픽카드', match: ['gpu', 'graphics', '그래픽'] },
  { label: 'SSD', match: ['ssd'] },
  { label: 'HDD', match: ['hdd', 'hard'] },
  { label: '파워', match: ['power', 'psu', '파워'] },
  { label: '쿨러/튜닝', match: ['cooler', '튜닝', 'fan'] },
  { label: '케이스', match: ['case', '케이스'] }
];

// 빌드 상태 관리
let currentPhase = 'requirements'; // 'requirements' | 'building'
let buildStageIndex = 0;
const BUILD_STAGES = ['CPU', 'Mainboard', 'RAM', 'GPU', 'SSD', 'HDD', 'Power', 'Cooler', 'Case'];

// Step-by-Step 상태 관리
let stepSessionId = null;  // Step-by-step 세션 ID
let currentStep = 0;       // 현재 단계 (0: 초기, 1-8: 부품 선택)
let isInStepMode = false;  // Step-by-step 모드 활성화 여부
let buildContext = { budget: null, purpose: null, preferences: {} }; // 빌드 요구사항 컨텍스트

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
    // 히스토리가 없고 초기 메시지도 없으면 환영 메시지 및 질문 유도
    setTimeout(() => {
      addMessageWithTyping('안녕하세요! AI PC 빌더입니다.\n어떤 용도의 PC를 찾으시나요? 예산은 어느 정도로 생각하시나요?\n(예: "배그용 150만원", "사무용 50만원")', 'ai');
    }, 500);
  }

  // UI 복원 (선택된 부품 등)
  updateSelectedParts();

  // 이벤트 리스너 등록
  sendBtn.addEventListener('click', handleSendClick);
  chatInput.addEventListener('keydown', handleKeyDown);
  homeBtn.addEventListener('click', () => {
    window.location.href = 'index.html';
  });

  // Auth Listener (프로필 이미지 업데이트 및 로그아웃 처리)
  setupAuthListener({
    onLogin: (user) => {
      // 아바타 업데이트
      const avatar = document.querySelector('.avatar');
      if (avatar && user.photoURL) {
        avatar.src = user.photoURL;
        avatar.title = user.displayName;
      }
      // 프로필 버튼 클릭 시 로그아웃 옵션 제공 (간단)
      const avatarBtn = document.querySelector('.avatar-btn');
      if (avatarBtn) {
        avatarBtn.onclick = () => {
          if (confirm(`${user.displayName}님, 로그아웃 하시겠습니까?`)) {
            logout();
          }
        };
      }
    },
    onLogout: () => {
      // 로그아웃 시 기본 이미지로 복귀? 혹은 강제 홈 이동?
      // 여기서는 그대로 유지하거나 기본값
    }
  });

  // Share 버튼 이벤트 위임 (action-btn pill-btn)
  // builder.html에 ID가 없으므로 클래스로 찾거나 이벤트 위임 사용
  document.addEventListener('click', (e) => {
    if (e.target.closest('.pill-btn') && e.target.innerText.includes('Share')) {
      shareCurrentBuild();
    }
  });

  // Start Build 버튼 리스너
  if (startBuildBtn) {
    startBuildBtn.addEventListener('click', startBuildProcess);
  }

  // Next Step 버튼 리스너
  if (nextStepBtn) {
    nextStepBtn.addEventListener('click', handleNextStep);
  }

  // 초기화 버튼 이벤트 리스너
  if (resetBtn) {
    resetBtn.addEventListener('click', resetAllParts);
  }

  // handleSkipStep을 전역으로 노출 (HTML onclick에서 호출 가능)
  window.handleSkipStep = handleSkipStep;
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
async function handleSendClick() {
  const message = chatInput.value.trim();
  if (message && !isLoading) {
    if (await ensureLoggedIn("채팅을 계속하려면 로그인이 필요합니다.")) {
      handleSendMessage(message);
      chatInput.value = '';
    }
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
    if (isInStepMode) {
      // Step 모드 활성 중 - 대화는 Multi-Agent로 (단순 채팅)
      // Step 진행(버튼 클릭)은 별도 핸들러가 처리함. 여기서 사용자가 타이핑한 메시지는 잡담/질문으로 처리.
      stopDynamicLoadingText();
      loadingMessage.remove();

      const { getPCRecommendation } = await import('./api.js');
      const response = await getPCRecommendation(message, buildContext);

      if (response.analysis) {
        await addMessageWithTyping(response.analysis, 'ai');
        chatHistory.push({ role: 'model', text: response.analysis });
      }
      saveState();

    } else {
      // 일반 대화 및 빌드 요청 (Agent가 판단)
      const { getPCRecommendation, getStepCandidates } = await import('./api.js');

      // Agent에게 쿼리 전송 (현재 Context 포함)
      const agentResponse = await getPCRecommendation(message, buildContext);

      stopDynamicLoadingText();
      loadingMessage.remove();

      // 1. Context 업데이트 (Agent가 추출한 정보 반영)
      if (agentResponse.extracted_requirements) {
        const req = agentResponse.extracted_requirements;
        if (req.budget) {
          // 예산 문자열("1,000,000원")을 정수로 변환
          const budgetStr = String(req.budget);
          const budgetInt = parseInt(budgetStr.replace(/[^0-9]/g, ''), 10);
          if (!isNaN(budgetInt)) {
            buildContext.budget = budgetInt;
          }
        }
        if (req.purpose) buildContext.purpose = req.purpose;
        if (req.preferences) Object.assign(buildContext.preferences, req.preferences);
      }

      // 2. 상태 분기 처리
      if (agentResponse.status === 'missing_info') {
        // 정보 부족 -> 질문 출력
        const reply = agentResponse.analysis || "죄송합니다. 조금 더 자세히 말씀해 주시겠어요?";
        await addMessageWithTyping(reply, 'ai');
        chatHistory.push({ role: 'model', text: reply });

      } else if (agentResponse.status === 'success' || agentResponse.status === 'completed') {
        // 정보 수집 완료 -> Step Mode 진입 트리거

        // Agent 멘트 출력 (예: "견적을 시작합니다")
        if (agentResponse.analysis) {
          await addMessageWithTyping(agentResponse.analysis, 'ai');
          chatHistory.push({ role: 'model', text: agentResponse.analysis });
        }

        // 로딩 메시지 출력 (빙글빙글 아이콘 사용)
        const loadingMsgDiv = addMessage('', 'ai', true);
        const loadingTextEl = loadingMsgDiv.querySelector('.thinking-text');
        if (loadingTextEl) {
          loadingTextEl.textContent = "고객님의 요구사항에 딱 맞는 부품을 찾고 있습니다...";
          // startDynamicLoadingText는 addMessage 내부에서 이미 호출됨 (텍스트 변경만 하면 됨)
        }

        // Step 1 API 호출 (추출된 budget/purpose 사용)
        const stepResponse = await getStepCandidates({
          query: message,
          current_step: 0,
          budget: buildContext.budget,
          purpose: buildContext.purpose || 'general'
        });

        // 상태 전환
        isInStepMode = true;
        stepSessionId = stepResponse.session_id;
        currentStep = stepResponse.step;

        // 가이드 출력
        if (stepResponse.category_description) {
          const categoryTitle = stepResponse.step_name || stepResponse.category_name || stepResponse.category || '부품';
          let guideMsg = `**${categoryTitle}**\n${stepResponse.category_description}`;
          if (stepResponse.spec_meanings && Object.keys(stepResponse.spec_meanings).length > 0) {
            guideMsg += '\n\n**주요 스펙 가이드:**\n';
            guideMsg += Object.entries(stepResponse.spec_meanings)
              .map(([key, desc]) => `- **${key}**: ${desc}`)
              .join('\n');
          }
          await addMessageWithTyping(guideMsg, 'ai');
          chatHistory.push({ role: 'model', text: guideMsg });
        }

        // 중복 메시지 방지 후 출력
        if (stepResponse.analysis && stepResponse.analysis !== agentResponse.analysis) {
          await addMessageWithTyping(stepResponse.analysis, 'ai');
          chatHistory.push({ role: 'model', text: stepResponse.analysis });
        }

        displayRecommendations(stepResponse.candidates);

      } else {
        // 그 외 (오류 또는 일반 대화만 지속)
        const reply = agentResponse.analysis || "죄송합니다. 처리에 문제가 발생했습니다.";
        await addMessageWithTyping(reply, 'ai');
        chatHistory.push({ role: 'model', text: reply });
      }

      saveState();
    }

  } catch (error) {
    console.error('메시지 전송 오류:', error);
    stopDynamicLoadingText();
    // 로딩 메시지를 찾아서 제거 (class로 찾기)
    const loadingMsg = chatMessages.querySelector('.thinking-text')?.closest('.message');
    if (loadingMsg) loadingMsg.remove();

    addMessage(error.message || '오류가 발생했습니다', 'error');
  } finally {
    // 모든 로딩 메시지 제거 (안전장치)
    const loadingMsgs = chatMessages.querySelectorAll('.thinking-text');
    loadingMsgs.forEach(el => el.closest('.message')?.remove());

    stopDynamicLoadingText();
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
  const msg = message.toLowerCase();

  // Gaming
  if (['게임', '게이밍', '배그', '롤', '오버워치', '발로란트', '스팀', 'game', 'gaming'].some(k => msg.includes(k))) return 'gaming';

  // Workstation
  if (['작업', '워크스테이션', '렌더링', '캐드', '영상', '편집', '포토샵', '프리미어', '코딩', '개발', '프로그래밍', '서버', '인공지능', '러닝', '학습', 'work', 'workstation', 'graphic', 'video'].some(k => msg.includes(k))) return 'workstation';

  // Streaming
  if (['방송', '스트리밍', '송출', '유튜브', '트위치', '치지직', 'stream', 'broadcast'].some(k => msg.includes(k))) return 'streaming';

  // General (Office/Home)
  if (['사무', '가정', '인강', '영화', '웹서핑', '일반', '한글', '엑셀', '문서', 'office', 'home'].some(k => msg.includes(k))) return 'general';

  return null;
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
 * 현재 단계 건너뛰기 (추천 부품이 없을 때)
 * Step-by-step 모드에서 선택 없이 다음 단계로 진행
 */
async function handleSkipStep() {
  if (!isInStepMode || !stepSessionId) {
    console.warn('[SKIP] Step 모드가 아니거나 세션이 없음');
    return;
  }

  try {
    // 1. 서버에 건너뛰기 요청 먼저 전송
    const stepResponse = await getStepCandidates({
      session_id: stepSessionId,
      query: '건너뛰기',
      current_step: currentStep,
      selected_component_id: null
    });

    // 2. 응답에 따라 메시지 분기 처리
    if (stepResponse.is_final) {
      isInStepMode = false;
      await addMessageWithTyping(`PC 구성이 완료되었습니다! 총 ${formatPrice(stepResponse.total_price)}입니다.`, 'ai');

      // Update Step
      currentStep = stepResponse.step;
      // Show Final Dashboard
      showFinalDashboard();

    } else {
      // 다음 단계가 있는 경우에만 건너뛰기 메시지 출력
      await addMessageWithTyping(`이 단계를 건너뛰고 다음으로 넘어갑니다.`, 'ai');
      chatHistory.push({ role: 'model', text: '이 단계를 건너뛰었습니다.' });

      currentStep = stepResponse.step;
      await addMessageWithTyping(stepResponse.analysis || '다음 부품을 선택해주세요.', 'ai');
      displayRecommendations(stepResponse.candidates);
    }

    saveState();

  } catch (error) {
    console.error('[SKIP ERROR]', error);
    addMessage('단계 건너뛰기 중 오류가 발생했습니다.', 'error');
  }
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
    // Format message for readability
    bubble.innerHTML = formatMessage(text);
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
  if (!element) return;

  const steps = [
    "요구사항 분석 중...",
    "부품 검색 중...",
    "최적의 부품 선별 중...",
    "답변 생성 중..."
  ];
  let index = 0;

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

  }, 1500); // 1.5초 간격
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
        // 타이핑 완료 후 마크다운 포맷팅 적용
        bubble.innerHTML = formatMessage(text);
        resolve();
      }
    }, typingSpeed);
  });
}

/**
 * 텍스트 포맷팅 (마크다운 -> HTML)
 * - **Bold**
 * - Newline (\n -> <br>)
 * - List (- item, 1. item)
 */
function formatMessage(text) {
  if (!text) return '';

  // 1. HTML Escape (보안)
  let html = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // 2. Bold (**text**)
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

  // 3. Newlines (\n)
  html = html.replace(/\n/g, '<br>');

  // 4. Bullet lists (- item) - 간단 변환
  // 줄 시작 또는 <br> 뒤에 오는 "- "를 "• "로 변경하고 들여쓰기 효과
  html = html.replace(/(?:^|<br>)-\s(.*?)(?=<br>|$)/g, '<br><span style="padding-left:10px">• $1</span>');

  // 5. Numbered lists (1. item)
  html = html.replace(/(?:^|<br>)(\d+)\.\s(.*?)(?=<br>|$)/g, '<br><span style="padding-left:10px">$1. $2</span>');

  // 4,5번 과정에서 생긴 불필요한 첫 줄 <br> 제거
  if (html.startsWith('<br>')) {
    html = html.substring(4);
  }

  return html;
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
  if (!terminalLoading || !terminalLoading.style.display || terminalLoading.style.display === 'none') {
    fileList.innerHTML = '';
  }

  if (!components || components.length === 0) {
    fileList.innerHTML = `
      <div class="empty-recommendation">
        <div class="empty-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 8v4M12 16h.01"/>
          </svg>
        </div>
        <h3>추천 가능한 부품이 없습니다</h3>
        <p>선택하신 사양과 호환되는 부품을 찾지 못했습니다.<br>
           (예: 내장 그래픽 사용 시 GPU 생략 가능)</p>
        <p class="auto-skip-msg" style="color: #4ade80; margin-top: 10px; font-weight: bold;">
          잠시 후 자동으로 다음 단계로 이동합니다...
        </p>
        <button class="skip-step-btn" onclick="handleSkipStep()">
          지금 건너뛰기
        </button>
      </div>
    `;

    // Auto-Skip (2초 후)
    setTimeout(() => {
      handleSkipStep();
    }, 2000);

    return;
  }

  const list = document.createElement('div');
  list.className = 'recommendation-list';

  // 카테고리 설명 메시지 출력 (한 번만)
  if (components.length > 0 && components[0].category) {
    // API 응답에 category_description 등이 포함되어 있다고 가정
    // 현재 구조상 API 응답 전체를 여기로 넘기지 않고 components만 넘기고 있음.
    // 따라서 handleSendMessage/handleCardClick에서 displayRecommendations 호출 전에 설명을 출력하는 것이 더 적절함.
    // 하지만 여기서 컴포넌트 데이터에 메타데이터가 있다면 활용 가능.
  }

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

  // 선택적 부품인 경우 '건너뛰기' 버튼 추가
  // components 배열이 비어있지 않다고 가정 (위에서 체크함)
  const currentCategorySlot = CATEGORY_SLOTS.find(s => components[0].category.toLowerCase().includes(s.match[0]));
  const currentCategoryLabel = currentCategorySlot ? currentCategorySlot.label : components[0].category;

  // 건너뛰기 허용 카테고리
  const OPTIONAL_CATEGORIES = ['SSD', 'HDD', 'ODD', 'Cooler', 'Software', 'Case'];
  const isOptional = OPTIONAL_CATEGORIES.some(cat =>
    currentCategoryLabel.toLowerCase().includes(cat.toLowerCase()) ||
    components[0].category.toLowerCase().includes(cat.toLowerCase())
  );

  if (isOptional) {
    const skipBtnContainer = document.createElement('div');
    skipBtnContainer.className = 'skip-section';
    skipBtnContainer.style.marginTop = '20px';
    skipBtnContainer.style.textAlign = 'center';
    skipBtnContainer.innerHTML = `
      <p style="color: var(--color-text-muted); font-size: 13px; margin-bottom: 10px;">
        이 부품은 선택사항입니다.
      </p>
      <button class="skip-step-btn secondary" onclick="handleSkipStep()">
        ${currentCategoryLabel} 건너뛰기
      </button>
    `;
    fileList.appendChild(skipBtnContainer);
  }
}

/**
 * 최종 대시보드 표시
 */
/**
 * 최종 대시보드 표시
 */
async function showFinalDashboard() {
  const totalPrice = selectedParts.reduce((sum, p) => {
    // 가격이 문자열일 경우 숫자만 추출, 숫자일 경우 그대로 사용
    const price = typeof p.price === 'number' ? p.price : extractPrice(p.price);
    return sum + price;
  }, 0);
  const formattedTotalPrice = formatPrice(totalPrice);

  // 전력 효율 계산 (파워 서플라이 등급 기반)
  const psu = selectedParts.find(p => p.category.toLowerCase().includes('power') || p.category.toLowerCase().includes('psu') || p.category.toLowerCase().includes('파워'));
  let efficiency = '중'; // 기본값 (80PLUS Standard/Bronze)

  if (psu) {
    const infoStr = (psu.name + ' ' + JSON.stringify(psu.specs || {})).toLowerCase();
    if (infoStr.includes('titanium') || infoStr.includes('platinum')) {
      efficiency = '상';
    } else if (infoStr.includes('gold') || infoStr.includes('silver')) {
      efficiency = '중';
    } else if (infoStr.includes('bronze') || infoStr.includes('standard')) {
      efficiency = '하';
    } else {
      efficiency = '하';
    }
  }

  fileList.innerHTML = `
    <div class="final-dashboard-container">
      <div class="dashboard-header">
        <h2 class="dashboard-title">나만의 PC 구성 완료</h2>
        <div class="dashboard-actions">
           <button class="action-btn primary" onclick="import('./community.js').then(m => m.saveCurrentBuild(selectedParts))">저장</button>
        </div>
      </div>
      
      <div class="dashboard-main-grid">
        <!-- 최종 스펙 및 가격 (단독 표시) -->
        <div class="dashboard-card specs-section">
          <h3 class="card-title">최종 견적 스펙</h3>
          
          <div class="key-specs-grid">
             <div class="key-spec-item">
               <span class="ks-label">CPU 코어</span>
               <span class="ks-value">${getSpecValue('cpu', ['코어', 'cores', 'core_count'], '-')}</span>
             </div>
             <div class="key-spec-item">
               <span class="ks-label">VRAM</span>
               <span class="ks-value">${getSpecValue('video_card', ['vram', 'memory'], getSpecValue('gpu', ['vram', 'memory'], '-'))}</span>
             </div>
             <div class="key-spec-item">
               <span class="ks-label">메모리 용량</span>
               <span class="ks-value">${getSpecValue('memory', ['용량', 'capacity'], '-')}</span>
             </div>
             <div class="key-spec-item">
               <span class="ks-label">저장 공간</span>
               <span class="ks-value">${getSpecValue('storage', ['용량', 'capacity'], getSpecValue('ssd', ['용량', 'capacity'], '-'))}</span>
             </div>
             <div class="key-spec-item">
               <span class="ks-label">전력 효율</span>
               <span class="ks-value efficiency-badge" data-grade="${efficiency}">${efficiency}</span>
             </div>
          </div>

          <div class="total-price-box">
             <span class="tp-label">총 견적</span>
             <span class="tp-value">${formattedTotalPrice}</span>
          </div>
        </div>
      </div>

      <!-- 3. Bottom: 가격 변동 예측 대시보드 -->
      <div class="dashboard-bottom-row">
        <div class="dashboard-card price-analysis-section">
           <h3 class="card-title">종합 가격 변동 예측 및 구매 적기 분석</h3>
           <div class="price-analysis-content">
              <div class="price-graph-container" id="price-prediction-graph"></div>
              <div class="price-table-container">
                 <table class="price-advice-table">
                   <thead>
                     <tr>
                       <th>부품</th>
                       <th>현재가</th>
                       <th>최적 구매 시기</th>
                       <th>예상 절약</th>
                       <th>상태</th>
                     </tr>
                   </thead>
                   <tbody>
                      ${generatePriceAdviceTable(selectedParts)}
                   </tbody>
                 </table>
              </div>
           </div>
        </div>
      </div>
    </div>

    <style>
      .final-dashboard-container {
        padding: 20px;
        animation: fadeIn 0.5s ease;
        max-width: 900px;
        margin: 0 auto;
        color: #fff;
      }
      .dashboard-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 24px;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        padding-bottom: 15px;
      }
      .dashboard-title {
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0;
        color: var(--color-accent, #3fa9f5);
      }
      .dashboard-main-grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 20px;
        margin-bottom: 20px;
        min-height: 500px; /* Taller for better image ratio */
      }
      .dashboard-card {
        background: rgba(30, 32, 44, 0.6);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 24px;
        backdrop-filter: blur(10px);
        display: flex;
        flex-direction: column;
      }
      .card-title {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 20px;
        color: #e2e8f0;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        padding-bottom: 12px;
      }
      
      /* Image Section */
      .ai-image-box {
        flex: 1;
        background: #000;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        min-height: 400px;
        position: relative;
      }
      .ai-generated-img {
        width: 100%;
        height: 100%;
        object-fit: cover; /* Cover usually looks better for hero images */
      }
      
      /* Specs Section */
      .specs-list {
        flex: 1;
        overflow-y: auto;
        margin-bottom: 20px;
        font-size: 0.9rem;
        max-height: 300px;
      }
      .spec-row {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid rgba(255,255,255,0.03);
      }
      .spec-category { color: #94a3b8; width: 30%; }
      .spec-name { 
          color: #f1f5f9; 
          text-align: right; 
          flex: 1; 
          white-space: nowrap; 
          overflow: hidden; 
          text-overflow: ellipsis; 
          max-width: 70%;
      }
      
      .key-specs-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        margin-bottom: 24px;
        background: rgba(0,0,0,0.2);
        padding: 16px;
        border-radius: 8px;
      }
      .key-spec-item {
        display: flex;
        flex-direction: column;
        align-items: center;
      }
      .ks-label { font-size: 0.8rem; color: #94a3b8; margin-bottom: 6px; }
      .ks-value { font-size: 1.1rem; font-weight: 700; color: #fff; }

      .total-price-box {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: auto;
        padding-top: 20px;
        border-top: 2px solid rgba(255,255,255,0.1);
      }
      .tp-label { font-size: 1.2rem; color: #e2e8f0; }
      .tp-value { font-size: 1.8rem; font-weight: 800; color: #4ade80; }

      /* Bottom: Price Analysis - STACKED */
      .dashboard-bottom-row {
        margin-top: 0;
      }
      .price-analysis-content {
        display: grid;
        grid-template-columns: 1fr; /* Stacked */
        gap: 30px;
      }
      .price-graph-container {
        height: 320px; /* Taller graph */
        background: rgba(0,0,0,0.2);
        border-radius: 8px;
        position: relative;
        padding: 10px;
      }
      .price-table-container {
        width: 100%;
        overflow-x: auto;
      }
      .price-advice-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.9rem;
      }
      .price-advice-table th {
        text-align: left;
        color: #94a3b8;
        padding: 12px;
        border-bottom: 1px solid rgba(255,255,255,0.1);
      }
      .price-advice-table td {
        padding: 12px;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        color: #e2e8f0;
      }
      .price-status {
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
      }
      .status-good { background: rgba(74, 222, 128, 0.2); color: #4ade80; }
      .status-wait { background: rgba(246, 173, 85, 0.2); color: #f6ad55; }
      .action-btn {
        padding: 10px 24px;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 600;
        transition: all 0.2s;
        border: none;
        font-size: 1rem;
      }
      .action-btn.primary {
        background: var(--color-accent, #3fa9f5);
        color: white;
      }
      .action-btn.primary:hover {
        background: #2b93db;
      }
      
      /* Efficiency Badge */
      .efficiency-badge {
        padding: 2px 12px;
        border-radius: 12px;
        min-width: 40px;
        text-align: center;
      }
      .efficiency-badge[data-grade="상"] { color: #4ade80; background: rgba(74, 222, 128, 0.15); border: 1px solid rgba(74, 222, 128, 0.3); }
      .efficiency-badge[data-grade="중"] { color: #f6ad55; background: rgba(246, 173, 85, 0.15); border: 1px solid rgba(246, 173, 85, 0.3); }
      .efficiency-badge[data-grade="하"] { color: #f87171; background: rgba(248, 113, 113, 0.15); border: 1px solid rgba(248, 113, 113, 0.3); }
      
      @media (max-width: 900px) {
        .dashboard-main-grid { grid-template-columns: 1fr; }
      }
    </style>
  `;

  // Render Price Graph
  renderPricePredictionGraph(document.getElementById('price-prediction-graph'), totalPrice);
}

/**
 * 가격 조언 테이블 생성
 */
function generatePriceAdviceTable(parts) {
  if (!parts || parts.length === 0) return '<tr><td colspan="5">데이터 없음</td></tr>';

  // 주요값 비싼 부품 위주로 5개만 표시
  const sorted = [...parts].sort((a, b) => extractPrice(b.price) - extractPrice(a.price)).slice(0, 5);

  return sorted.map(part => {
    const price = extractPrice(part.price);
    // Mock prediction logic
    const isGood = Math.random() > 0.4; // 60% chance good
    const status = isGood ? '<span class="price-status status-good">구매 적기</span>' : '<span class="price-status status-wait">대기 권장</span>';
    const bestTime = isGood ? '지금' : '2주 후';
    const saving = isGood ? '-' : `약 ${Math.round(price * 0.05).toLocaleString()}원`;

    return `
          <tr>
            <td style="max-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${part.name}</td>
            <td>${formatPrice(price)}</td>
            <td>${bestTime}</td>
            <td>${saving}</td>
            <td>${status}</td>
          </tr>
        `;
  }).join('');
}

/**
 * 가격 예측 그래프 렌더링 (SVG)
 */
function renderPricePredictionGraph(container, currentTotal) {
  if (!container) return;

  // Mock Data Generator: 3 months history, current, 1 month forecast
  const points = [];
  const now = new Date();
  // 3 months ago
  for (let i = -3; i <= 1; i++) { // -3(3mo ago) to +1(1mo future)
    const date = new Date();
    date.setMonth(now.getMonth() + i);
    const label = i === 0 ? '현재' : (i > 0 ? '익월 예상' : `${Math.abs(i)}개월 전`);

    // Random fluctuation +/- 10%
    const volatility = 0.1;
    const randomFactor = 1 + (Math.random() * volatility * 2 - volatility);
    let val = currentTotal * randomFactor;

    // Force forecast to be slightly lower (optimistic)
    if (i > 0) val = currentTotal * 0.95;
    if (i === 0) val = currentTotal;

    points.push({ label, value: val });
  }

  const maxVal = Math.max(...points.map(p => p.value)) * 1.1;
  const minVal = Math.min(...points.map(p => p.value)) * 0.9;
  const width = container.clientWidth || 600;
  const height = container.clientHeight || 250;
  const padding = { top: 20, right: 30, bottom: 30, left: 60 };

  const svgNs = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(svgNs, "svg");
  svg.setAttribute("width", "100%");
  svg.setAttribute("height", "100%");
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);

  // Draw Grid (Y-axis)
  const gridLines = 4;
  for (let i = 0; i <= gridLines; i++) {
    const val = minVal + (maxVal - minVal) * (i / gridLines);
    const y = height - padding.bottom - ((val - minVal) / (maxVal - minVal)) * (height - padding.top - padding.bottom);

    // Line
    const line = document.createElementNS(svgNs, "line");
    line.setAttribute("x1", padding.left);
    line.setAttribute("y1", y);
    line.setAttribute("x2", width - padding.right);
    line.setAttribute("y2", y);
    line.setAttribute("stroke", "rgba(255,255,255,0.1)");
    line.setAttribute("stroke-width", "1");
    svg.appendChild(line);

    // Label
    const text = document.createElementNS(svgNs, "text");
    text.setAttribute("x", padding.left - 10);
    text.setAttribute("y", y + 4);
    text.setAttribute("text-anchor", "end");
    text.setAttribute("fill", "#94a3b8");
    text.setAttribute("font-size", "10");
    text.textContent = Math.round(val / 10000) + "만";
    svg.appendChild(text);
  }

  // Draw Polyline
  const polylinePoints = points.map((p, i) => {
    const x = padding.left + (i / (points.length - 1)) * (width - padding.left - padding.right);
    const y = height - padding.bottom - ((p.value - minVal) / (maxVal - minVal)) * (height - padding.top - padding.bottom);
    return `${x},${y}`;
  }).join(" ");

  const polyline = document.createElementNS(svgNs, "polyline");
  polyline.setAttribute("points", polylinePoints);
  polyline.setAttribute("fill", "none");
  polyline.setAttribute("stroke", "#3fa9f5");
  polyline.setAttribute("stroke-width", "3");
  svg.appendChild(polyline);

  // Draw Points and X-Labels
  points.forEach((p, i) => {
    const x = padding.left + (i / (points.length - 1)) * (width - padding.left - padding.right);
    const y = height - padding.bottom - ((p.value - minVal) / (maxVal - minVal)) * (height - padding.top - padding.bottom);

    // Circle
    const circle = document.createElementNS(svgNs, "circle");
    circle.setAttribute("cx", x);
    circle.setAttribute("cy", y);
    circle.setAttribute("r", "4");
    circle.setAttribute("fill", i === points.length - 1 ? "#3fa9f5" : "#fff"); // Last point colored
    svg.appendChild(circle);

    // X Label
    const text = document.createElementNS(svgNs, "text");
    text.setAttribute("x", x);
    text.setAttribute("y", height - 5);
    text.setAttribute("text-anchor", "middle");
    text.setAttribute("fill", "#94a3b8");
    text.setAttribute("font-size", "11");
    text.textContent = p.label;
    svg.appendChild(text);
  });

  container.appendChild(svg);
}

/**
 * 스펙 값 추출 헬퍼
 */
function getSpecValue(categoryKey, specKeys, fallback) {
  const part = selectedParts.find(p => p.category.toLowerCase().includes(categoryKey));
  if (!part || !part.specs) return fallback;

  if (Array.isArray(specKeys)) {
    for (const key of specKeys) {
      // specs 키 중 key를 포함하는 것이 있는지 찾음
      const match = Object.keys(part.specs).find(k => k.toLowerCase().includes(key.toLowerCase()));
      if (match) return part.specs[match];
    }
    // 직접 키 매칭 시도
    for (const key of specKeys) {
      if (part.specs[key]) return part.specs[key];
    }
  }

  return fallback;
}

/**
 * AI 이미지 생성 요청
 */
async function generatePcImage() {
  const container = document.getElementById('ai-image-container');
  try {
    const response = await fetch(`${API_BASE_URL}/generate/pc-image`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        components: selectedParts,
        purpose: buildContext.purpose || 'gaming'
      })
    });

    const data = await response.json();
    if (data.image_url) {
      container.innerHTML = `<img src="${data.image_url}" alt="AI Generated PC Build" class="ai-generated-img" style="max-width: 100%; height: auto; border-radius: 4px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">`;
    } else {
      throw new Error('No image returned');
    }
  } catch (e) {
    console.error('Image generation failed:', e);
    container.innerHTML = `
      <div class="error-state" style="text-align: center; padding: 20px;">
        <p style="color: #ff6b6b; margin-bottom: 10px;">이미지 생성 실패</p>
        <button onclick="generatePcImage()" style="padding: 5px 10px; background: var(--color-bg-tertiary); border-radius: 4px;">재시도</button>
      </div>
    `;
  }
}

function copyLink() {
  alert('공유 링크가 클립보드에 복사되었습니다! (시뮬레이션)');
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

  // 호환성 경고 처리
  if (component.compatibility_status === 'warning') {
    card.classList.add('warning');
    card.title = "호환 이슈가 있을 수 있습니다 (예: 예산 초과, 소켓 불일치 등)";
  }

  // 아이콘 처리 - 이미지가 있으면 이미지, 없으면 SVG
  let iconHtml;
  const category = (component.category || '').toLowerCase();
  let componentImage = null;

  if (component.image_url || component.image || component.imageUrl) {
    componentImage = component.image_url || component.image || component.imageUrl;
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
    .slice(0, 4) // 최대 4개
    .map(tag => {
      const text = tag.startsWith('#') ? tag : `#${tag}`;
      // CSS 클래스 'hashtag' 사용 (builder.css에 추가됨)
      return `\u003cspan class=\"hashtag\"\u003e${text}\u003c/span\u003e`;
    })
    .join('');

  // 가격 표시
  const priceText = typeof component.price === 'number' && component.price > 0
    ? formatPrice(component.price)
    : '가격 정보 없음';

  card.innerHTML = `
    \u003cdiv class=\"card-header\"\u003e
      \u003cdiv class=\"card-icon\"\u003e${iconHtml}\u003c/div\u003e
      \u003cdiv class=\"card-info\"\u003e
        \u003cdiv class=\"card-category\"\u003e${component.category || '부품'}\u003c/div\u003e
        \u003cdiv class=\"card-name\" title=\"${component.name}\"\u003e${component.name}\u003c/div\u003e
        \u003cdiv class=\"component-hashtags\"\u003e
          ${tagsHtml}
        \u003c/div\u003e
      \u003c/div\u003e
      \u003cdiv class=\"card-right\"\u003e
        \u003cdiv class=\"card-price\"\u003e${priceText}\u003c/div\u003e
        \u003cbutton class=\"info-btn\" type=\"button\" aria-label=\"담기\"\u003e
          \u003cspan class=\"info-label\"\u003e담기\u003c/span\u003e
        \u003c/button\u003e
      \u003c/div\u003e
    \u003c/div\u003e
  `;

  // 담기 버튼 클릭 시 부품 선택 (애니메이션 포함)
  const infoBtn = card.querySelector('.info-btn');
  if (infoBtn) {
    infoBtn.addEventListener('click', (e) => {
      e.stopPropagation(); // 카드 클릭 이벤트 전파 방지
      if (card.classList.contains('selected')) return;
      handleCardClick(e, card, component);
    });
  }

  // 추천 카드 클릭 시 성능 그래프 팝업 표시
  card.addEventListener('click', () => {
    showPerformancePanel(component);
  });

  return card;
}

/**
 * 성능 그래프 패널 생성 (최초 1회)
 */
function ensurePerformancePanel() {
  let overlay = document.getElementById('performance-overlay');
  if (overlay) return overlay;

  overlay = document.createElement('div');
  overlay.id = 'performance-overlay';

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

  const closePanel = () => {
    overlay.classList.remove('visible');
    panel.classList.remove('visible');
  };

  panel.querySelector('.perf-close').addEventListener('click', closePanel);
  panel.querySelector('.perf-close').addEventListener('mousedown', (event) => {
    // 드래그 시작 방지 (닫기 버튼 클릭 시)
    event.stopPropagation();
  });

  overlay.addEventListener('click', (event) => {
    if (event.target === overlay) {
      closePanel();
    }
  });

  panel.addEventListener('click', (event) => {
    event.stopPropagation();
  });

  // 드래그 이동 처리
  const dragState = {
    dragging: false,
    startX: 0,
    startY: 0,
    offsetX: 0,
    offsetY: 0
  };

  const perfHeader = panel.querySelector('.perf-header');
  if (perfHeader) {
    perfHeader.addEventListener('mousedown', (event) => {
      dragState.dragging = true;
      const rect = panel.getBoundingClientRect();

      // 드래그 시작 시 현재 위치를 명시적으로 고정하고 transform 제거
      panel.style.transform = 'none';
      panel.style.left = `${rect.left}px`;
      panel.style.top = `${rect.top}px`;
      panel.style.position = 'absolute';

      dragState.startX = event.clientX;
      dragState.startY = event.clientY;
      dragState.offsetX = rect.left;
      dragState.offsetY = rect.top;

      event.preventDefault();
    });

    window.addEventListener('mousemove', (event) => {
      if (!dragState.dragging) return;
      const deltaX = event.clientX - dragState.startX;
      const deltaY = event.clientY - dragState.startY;
      panel.style.left = `${dragState.offsetX + deltaX}px`;
      panel.style.top = `${dragState.offsetY + deltaY}px`;
    });

    window.addEventListener('mouseup', () => {
      dragState.dragging = false;
    });
  }

  overlay.appendChild(panel);
  document.body.appendChild(overlay);
  return overlay;
}

/**
 * 성능 그래프 패널 표시
 */
/**
 * 성능 그래프 패널 표시 (Redesigned)
 */
function showPerformancePanel(component) {
  const overlay = ensurePerformancePanel();
  if (!overlay) return;
  const panel = overlay.querySelector('#performance-panel');
  if (!panel) return;

  overlay.classList.add('visible');

  // Helper for safe parsing
  function parseNumeric(val) {
    if (typeof val === 'number') return val;
    if (typeof val === 'string') return parseFloat(val.replace(/[^0-9.]/g, '')) || 0;
    return 0;
  }

  // --- 1. Header (Title & Close) ---
  // Clean up previous content but keep structure
  panel.innerHTML = '';

  const header = document.createElement('div');
  header.className = 'perf-header';
  header.innerHTML = `
    <div class="perf-title-group">
      <span class="perf-category">${component.category}</span>
      <h2 class="perf-name">${component.name}</h2>
    </div>
    <button class="perf-close" onclick="document.getElementById('performance-overlay').classList.remove('visible')">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M18 6L6 18M6 6l12 12"/>
      </svg>
    </button>
  `;
  panel.appendChild(header);

  const perfBody = document.createElement('div');
  perfBody.className = 'perf-body';
  panel.appendChild(perfBody);


  // --- 2. Key Specs Section (Grid) ---
  let repSpecs = component.representative_specs || {};

  // Create spec mapping if not exists
  if (Object.keys(repSpecs).length === 0 && component.specs) {
    const blockedKeys = ['id', 'name', 'price', 'image', 'imageUrl', 'category', 'description', 'link', 'mall_link', 'hashtags', 'compatibility_status', 'reasons', 'score', 'source', 'sql_database', 'embedding', 'metadata'];
    repSpecs = Object.entries(component.specs)
      .filter(([k, v]) => !blockedKeys.includes(k) && !k.startsWith('field_') && typeof v !== 'object' && v !== null)
      .slice(0, 4) // Show top 4
      .reduce((obj, [k, v]) => ({ ...obj, [k]: v }), {});
  }

  // Fallback if still empty
  if (Object.keys(repSpecs).length < 2) {
    repSpecs = { '기본 정보': '상세 스펙 확인 필요' };
  }

  // Common Spec Icons map (Simple text fallback)
  const SPEC_ICONS = {
    'cores': 'core', 'clock': 'clock', 'tdp': 'power', 'socket': 'cpu',
    'capacity': 'save', 'speed': 'activity', 'vram': 'monitor'
  };

  const specSection = document.createElement('div');
  specSection.className = 'perf-card';
  specSection.innerHTML = `<h3 class="perf-section-title">주요 사양</h3>`;

  const specGrid = document.createElement('div');
  specGrid.className = 'perf-spec-grid';

  Object.entries(repSpecs).slice(0, 4).forEach(([key, val]) => {
    const item = document.createElement('div');
    item.className = 'perf-spec-item';
    // Simple label mapping
    let label = key;
    if (key === 'cores' || key === 'core_count') label = '코어 수';
    if (key === 'clock') label = '부스트 클럭';
    if (key === 'tdp') label = 'TDP';
    if (key === 'socket') label = '소켓';
    if (key === 'capacity') label = '용량';

    item.innerHTML = `
        <span class="perf-spec-label">${label}</span>
        <span class="perf-spec-value">${val}</span>
      `;
    specGrid.appendChild(item);
  });

  specSection.appendChild(specGrid);
  perfBody.appendChild(specSection);


  // --- 3. Price History Graph (SVG) ---
  const priceSection = document.createElement('div');
  priceSection.className = 'perf-card';
  priceSection.innerHTML = `<h3 class="perf-section-title">가격 예측 추이</h3>`;

  const graphContainer = document.createElement('div');
  graphContainer.className = 'perf-price-graph';

  // Data Generation (Deterministic)
  const getHash = (str) => {
    let hash = 0;
    for (let i = 0; i < str.length; i++) hash = (hash << 5) - hash + str.charCodeAt(i) | 0;
    return Math.abs(hash);
  };
  const seed = getHash(component.name);
  const getRand = (offset) => {
    const x = Math.sin(seed + offset) * 10000;
    return x - Math.floor(x);
  };

  const basePrice = typeof component.price === 'number' ? component.price : parseFloat(String(component.price).replace(/[^0-9]/g, '')) || 500000;
  const history = [];
  for (let i = -5; i <= 1; i++) {
    let change = (getRand(i) - 0.5) * 0.15; // +/- 15%
    history.push({
      label: i === 0 ? '오늘' : (i > 0 ? '다음 분기' : `${Math.abs(i)}개월 전`),
      value: basePrice * (1 + change)
    });
  }

  // Draw SVG
  const maxP = Math.max(...history.map(d => d.value)) * 1.1;
  const minP = Math.min(...history.map(d => d.value)) * 0.9;

  let points = "";
  let width = 800; // virtual width
  let height = 200;

  history.forEach((d, i) => {
    const x = (i / (history.length - 1)) * width;
    const y = height - ((d.value - minP) / (maxP - minP)) * height;
    points += `${x},${y} `;
  });

  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("width", "100%");
  svg.setAttribute("height", "100%");
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.style.overflow = "visible";

  // Polyline
  const polyline = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
  polyline.setAttribute("points", points);
  polyline.setAttribute("class", "graph-line");
  svg.appendChild(polyline);

  // Dots
  history.forEach((d, i) => {
    const x = (i / (history.length - 1)) * width;
    const y = height - ((d.value - minP) / (maxP - minP)) * height;
    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("cx", x);
    circle.setAttribute("cy", y);
    circle.setAttribute("class", "graph-dot");
    svg.appendChild(circle);
  });

  // Y-Axis Labels
  const yAxis = document.createElement('div');
  yAxis.className = 'price-y-axis';
  yAxis.innerHTML = `
    <span>₩${Math.round(maxP / 10000) * 10000}</span>
    <span>₩${Math.round((maxP + minP) / 2 / 10000) * 10000}</span>
    <span>₩0</span>
  `;

  // X-Axis Labels
  const xAxis = document.createElement('div');
  xAxis.className = 'price-x-axis';
  history.forEach(d => {
    const span = document.createElement('span');
    span.textContent = d.label;
    xAxis.appendChild(span);
  });

  graphContainer.appendChild(yAxis);
  graphContainer.appendChild(svg);
  graphContainer.appendChild(xAxis);

  priceSection.appendChild(graphContainer);
  perfBody.appendChild(priceSection);


  // --- 4. Efficiency Analysis (Bars) ---
  const analysisSection = document.createElement('div');
  analysisSection.className = 'perf-card';
  analysisSection.innerHTML = `<h3 class="perf-section-title">성능 효율성 분석</h3>`;

  const analysisGrid = document.createElement('div');
  analysisGrid.className = 'perf-analysis-grid';

  // Mock Analysis Data derived from seed
  const metrics = [
    { label: '게임', color: 'fill-blue', val: 70 + getRand(10) * 29 },
    { label: '작업 효율', color: 'fill-green', val: 60 + getRand(20) * 39 },
    { label: '발열', color: 'fill-yellow', val: 50 + getRand(30) * 40 },
    { label: '전력 효율', color: 'fill-cyan', val: 65 + getRand(40) * 30 },
    { label: '저장 속도', color: 'fill-rose', val: 80 + getRand(50) * 19 }
  ];

  // Adjust based on category
  const cat = component.category.toLowerCase();
  if (cat.includes('ssd')) metrics[4].val = 95 + getRand(1) * 4;
  if (cat.includes('cool')) { metrics[2].val = 90; metrics[0].label = '쿨링 성능'; }

  metrics.forEach(m => {
    const row = document.createElement('div');
    row.className = 'analysis-row';
    const pct = Math.round(m.val);
    row.innerHTML = `
        <span class="analysis-label">${m.label}</span>
        <div class="analysis-bar-bg">
            <div class="analysis-bar-fill ${m.color}" style="width: 0%"></div>
        </div>
        <span class="analysis-val">${pct}%</span>
      `;
    // Animate
    setTimeout(() => {
      row.querySelector('.analysis-bar-fill').style.width = `${pct}%`;
    }, 300);

    analysisGrid.appendChild(row);
  });

  analysisSection.appendChild(analysisGrid);
  perfBody.appendChild(analysisSection);
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

        // 부품 ID 추출 (component_id 또는 id 필드 사용)
        const componentId = component.component_id || component.id || component.name;

        console.log('[DEBUG] 부품 선택:', {
          sessionId: stepSessionId,
          componentId,
          currentStep,
          component
        });

        // 로딩 표시
        const loadingMessage = addMessage('', 'ai', true);

        // 다음 단계 조회
        const stepResponse = await selectComponent(stepSessionId, componentId, currentStep);

        console.log('[DEBUG] API 응답:', stepResponse);

        stopDynamicLoadingText();
        loadingMessage.remove();

        // 단계 업데이트
        currentStep = stepResponse.step;

        // 1. 카테고리 설명 메시지 출력 (다음 단계 진입 시, 마지막 단계가 아닐 경우)
        if (!stepResponse.is_final_step && stepResponse.category_description) {
          const categoryTitle = stepResponse.step_name || stepResponse.category_name || stepResponse.category || '부품';
          let guideMsg = `**${categoryTitle}**\n${stepResponse.category_description}`;

          if (stepResponse.spec_meanings && Object.keys(stepResponse.spec_meanings).length > 0) {
            guideMsg += '\n\n**주요 스펙 가이드:**\n';
            guideMsg += Object.entries(stepResponse.spec_meanings)
              .map(([key, desc]) => `- **${key}**: ${desc}`)
              .join('\n');
          }

          await addMessageWithTyping(guideMsg, 'ai');
          chatHistory.push({ role: 'model', text: guideMsg });
        }

        if (stepResponse.is_final_step) {
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
        console.error('[ERROR] 다음 단계 진행 오류:', error);
        if (loadingMessage) loadingMessage.remove(); // 에러 시 로딩 제거
        stopDynamicLoadingText();
        addMessage(`다음 단계로 진행하는 중 오류가 발생했습니다: ${error.message}`, 'error');
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
  if (!selectedPartsContainer) return;
  selectedPartsContainer.innerHTML = '';

  // 슬롯 컨테이너 생성
  const slotsWrapper = document.createElement('div');
  slotsWrapper.className = 'category-slots';

  CATEGORY_SLOTS.forEach(slot => {
    const slotEl = document.createElement('div');
    slotEl.className = 'category-slot';

    // 매칭되는 부품 찾기
    const partIndex = selectedParts.findIndex(p => {
      const cat = (p.category || '').toLowerCase();
      return slot.match.some(keyword => cat.includes(keyword));
    });
    const part = partIndex >= 0 ? selectedParts[partIndex] : null;

    if (part) {
      slotEl.classList.add('filled');
    } else {
      slotEl.classList.add('empty');
    }

    const header = document.createElement('div');
    header.className = 'slot-header';

    const label = document.createElement('span');
    label.className = 'slot-label';
    label.textContent = slot.label;

    header.appendChild(label);

    if (part) {
      const price = document.createElement('span');
      price.className = 'slot-price';
      price.textContent = formatPrice(part.price);
      header.appendChild(price);

      const purchaseBtn = document.createElement('button');
      purchaseBtn.className = 'slot-purchase-btn';
      purchaseBtn.textContent = '구매하기';
      purchaseBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        // 다나와 URL이 있으면 다나와 페이지로 이동
        const danawaUrl = part.danawa_url || part.danawaUrl;
        if (danawaUrl) {
          window.open(danawaUrl, '_blank', 'noopener,noreferrer');
        } else {
          // 다나와 URL이 없으면 component_id를 이용해 기본 URL 생성
          const productId = part.id || part.component_id;
          if (productId) {
            window.open(`https://prod.danawa.com/info/?pcode=${productId}`, '_blank', 'noopener,noreferrer');
          } else {
            alert(`${part.name}에 대한 구매 링크가 없습니다.`);
          }
        }
      });
      header.appendChild(purchaseBtn);

      const removeBtn = document.createElement('button');
      removeBtn.className = 'slot-remove';
      removeBtn.textContent = '×';
      removeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        restoreRecommendationCard(part);
        removePart(partIndex);
      });
      header.appendChild(removeBtn);
    }

    const body = document.createElement('div');
    body.className = 'slot-body';

    if (part) {
      const name = document.createElement('div');
      name.className = 'slot-name';
      name.textContent = part.name;
      body.appendChild(name);

      // 수량 조절 버튼
      const quantityControl = document.createElement('div');
      quantityControl.className = 'quantity-control';

      const decreaseBtn = document.createElement('button');
      decreaseBtn.className = 'quantity-btn';
      decreaseBtn.textContent = '−';
      decreaseBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        let currentQty = part.quantity || 1;
        if (currentQty > 1) {
          part.quantity = currentQty - 1;
          quantityNum.textContent = part.quantity;
          document.querySelector('.total-value').textContent = calculateTotal();
          saveState();
        }
      });

      const quantityNum = document.createElement('span');
      quantityNum.className = 'quantity-num';
      if (!part.quantity) part.quantity = 1;
      quantityNum.textContent = part.quantity;

      const increaseBtn = document.createElement('button');
      increaseBtn.className = 'quantity-btn';
      increaseBtn.textContent = '+';
      increaseBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        let currentQty = part.quantity || 1;
        part.quantity = currentQty + 1;
        quantityNum.textContent = part.quantity;
        document.querySelector('.total-value').textContent = calculateTotal();
        saveState();
      });

      quantityControl.appendChild(decreaseBtn);
      quantityControl.appendChild(quantityNum);
      quantityControl.appendChild(increaseBtn);
      body.appendChild(quantityControl);
    } else {
      const placeholder = document.createElement('div');
      placeholder.className = 'slot-placeholder';
      placeholder.textContent = '담기 버튼으로 선택하세요';
      body.appendChild(placeholder);
    }

    slotEl.appendChild(header);
    slotEl.appendChild(body);
    slotsWrapper.appendChild(slotEl);
  });

  selectedPartsContainer.appendChild(slotsWrapper);

  // 총 가격 표시
  const totalLine = document.createElement('div');
  totalLine.className = 'file-item total-line';
  totalLine.innerHTML = `
    <div class="total-left">
      <span class="total-label">Total:</span>
      <span class="total-value">${calculateTotal()}</span>
    </div>
    <button class="total-print-btn" title="출력">
      <span class="print-icon" aria-hidden="true">🖨</span>
      <span class="print-text">출력</span>
    </button>
  `;
  selectedPartsContainer.appendChild(totalLine);
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
  nameSpan.style.whiteSpace = 'normal';
  nameSpan.style.overflow = 'hidden';
  nameSpan.style.textOverflow = 'ellipsis';
  nameSpan.style.display = '-webkit-box';
  nameSpan.style.webkitLineClamp = '2';
  nameSpan.style.webkitBoxOrient = 'vertical';
  nameSpan.style.lineHeight = '1.3';

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
 * 모든 선택된 부품 초기화
 */
function resetAllParts() {
  if (selectedParts.length === 0) {
    alert('선택된 부품이 없습니다.');
    return;
  }

  if (confirm('선택된 모든 부품을 초기화하시겠습니까?')) {
    // 모든 추천 카드 복원
    selectedParts.forEach(part => {
      restoreRecommendationCard(part);
    });

    // 선택된 부품 배열 초기화
    selectedParts.length = 0;

    // UI 업데이트
    updateSelectedParts();

    // 상태 저장
    saveState();

    // 사용자에게 피드백
    addMessageWithTyping('선택된 부품이 모두 초기화되었습니다.', 'ai');
  }
}

/**
 * 총 가격 계산
 */
function calculateTotal() {
  const total = selectedParts.reduce((sum, part) => {
    const price = extractPrice(part.price);
    const qty = part.quantity || 1;
    return sum + (price * qty);
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

