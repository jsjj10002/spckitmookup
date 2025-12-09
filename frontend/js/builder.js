/**
 * Builder 페이지 메인 스크립트
 * 채팅, 부품 추천, 선택 기능 등을 관리한다
 */

import { getPCRecommendation, extractPrice, formatPrice } from './api.js';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

// DOM 요소
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const terminalContent = document.getElementById('terminal-content'); // 추천 부품 (터미널)
const fileList = document.getElementById('file-list'); // 선택된 부품 (파일 트리)
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

/**
 * 로컬 스토리지 키
 */
const STORAGE_KEY = 'spckit_builder_state';

/**
 * 초기화
 */
function init() {
  // 0. 새 세션인지 확인 (URL에 new=true 파라미터가 있거나, 세션 스토리지에 플래그가 없으면 초기화)
  const urlParams = new URLSearchParams(window.location.search);
  const isNewSession = urlParams.get('new') === 'true' || !sessionStorage.getItem('spckit_session_started');
  
  if (isNewSession) {
    // 새 세션 시작: 모든 상태 초기화
    localStorage.removeItem(STORAGE_KEY);
    chatHistory = [];
    selectedParts = [];
    currentPhase = 'requirements';
    buildStageIndex = 0;
    sessionStorage.setItem('spckit_session_started', 'true');
    
    // 채팅 메시지 영역 초기화
    chatMessages.innerHTML = '';
    
    console.log('새 세션 시작: 모든 상태 초기화됨');
  } else {
    // 기존 세션: 상태 복원
    loadState();
  }

  // 1. URL 파라미터 처리
  const initialMessage = urlParams.get('message');

  if (initialMessage) {
    // 히스토리가 비어있거나, 마지막 메시지와 다른 경우에만 처리 (새로고침 중복 방지)
    const lastMsg = chatHistory.length > 0 ? chatHistory[chatHistory.length - 1] : null;
    if (!lastMsg || (lastMsg.role === 'user' && lastMsg.text !== initialMessage) || (lastMsg.role === 'model')) {
        // 약간의 딜레이를 주어 로드 완료 후 실행
        setTimeout(() => handleSendMessage(initialMessage), 100);
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
    // 홈으로 이동 시 세션 플래그 제거하여 다음 방문 시 새 세션으로 시작
    sessionStorage.removeItem('spckit_session_started');
    window.location.href = 'index.html';
  });
  
  // 페이지 로드 시 새 세션으로 시작하려면 URL에 ?new=true 추가
  // 또는 브라우저 새 탭/새 창에서 열면 자동으로 새 세션 시작
  
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
 * 메시지 전송 및 AI 응답 처리
 */
async function handleSendMessage(message) {
  if (isLoading) return;

  isLoading = true;
  updateSendButtonState();

  // 사용자 메시지 UI 추가
  addMessage(message, 'user');
  chatHistory.push({ role: 'user', text: message });
  saveState(); // 상태 저장

  // 실제 백엔드로 보낼 쿼리 구성
  let queryToSend = message;
  
  // @내사양 태그 감지 및 처리
  if (message.includes('@내사양')) {
      const specs = getSystemSpecs();
      queryToSend = `${message}\n\n[System Info]\n${specs}`;
  }

  // 요구사항 분석 단계일 때도 바로 첫 번째 단계(CPU) 추천으로 진입
  if (currentPhase === 'requirements') {
      currentPhase = 'building';
      buildStageIndex = 0;
      saveState();

      const loadingMessage = addMessage('', 'ai', true);
      
      try {
        // 바로 CPU(첫 번째 단계) 추천 요청
        const currentStage = BUILD_STAGES[buildStageIndex];
        // 쿼리는 그대로 보내되, 카테고리를 명시하여 해당 부품만 검색
        const response = await getPCRecommendation(queryToSend, { category: currentStage });
        
        stopDynamicLoadingText();
        loadingMessage.remove();

        await addMessageWithTyping(response.analysis, 'ai');
        chatHistory.push({ role: 'model', text: response.analysis });
        saveState(); // 응답 저장
        
        // 1단계 부품 리스트 표시
        if (response.components && response.components.length > 0) {
            displayRecommendations(response.components);
        } else {
            // 검색 결과가 없는 경우 처리
            terminalContent.innerHTML = `<div class="terminal-line">추천된 ${currentStage}가 없습니다.</div>`;
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
  } else {
      // 이미 빌드 진행 중인 경우 (추가 질문이나 다음 단계)
      // 현재 단계의 부품에 대한 질문으로 간주
      const loadingMessage = addMessage('', 'ai', true);
      try {
          // 현재 단계의 컨텍스트를 포함하여 질의
          const currentStage = BUILD_STAGES[buildStageIndex];
          const response = await getPCRecommendation(queryToSend, { category: currentStage });
          
          stopDynamicLoadingText();
          loadingMessage.remove();
          
          await addMessageWithTyping(response.analysis, 'ai');
          chatHistory.push({ role: 'model', text: response.analysis });
          saveState(); // 응답 저장
          
          // 부품 리스트 업데이트
          if (response.components && response.components.length > 0) {
              displayRecommendations(response.components);
          }

      } catch (error) {
        console.error('오류:', error);
        stopDynamicLoadingText();
        loadingMessage.remove();
        addMessage('처리 중 오류가 발생했습니다.', 'error');
      } finally {
        isLoading = false;
        updateSendButtonState();
      }
  }
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
    terminalContent.innerHTML = ''; // 기존 리스트 초기화

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
        terminalContent.innerHTML = `<div class="terminal-line error">Failed to load ${stage} recommendations.</div>`;
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
        terminalContent.innerHTML = '<div class="terminal-line success">All steps completed! Check your build summary.</div>';
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
      terminalContent.innerHTML = '';
  }

  if (!components || components.length === 0) {
    terminalContent.innerHTML = '<div class="terminal-line">추천 부품이 없습니다</div>';
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

  terminalContent.appendChild(list);
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

  // 카테고리 대소문자 처리 및 매핑
  const categoryKey = Object.keys(COMPONENT_ICONS).find(key =>
    component.category.toLowerCase().includes(key.toLowerCase())
  ) || 'Default';

  const iconSvg = COMPONENT_ICONS[categoryKey];

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
    <div class="card-main-content">
        <div class="card-header">
        <div class="card-icon">${iconSvg}</div>
        <div class="card-info">
            <div class="card-category">${component.category}</div>
            <div class="card-name" title="${component.name}">${component.name}</div>
        </div>
        </div>
        <div class="card-details">
        <div class="card-tags">
            ${tagsHtml}
        </div>
        <div class="card-price">${component.price}</div>
        <button class="card-details-toggle" title="상세 정보">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M6 9l6 6 6-6"/>
            </svg>
        </button>
        </div>
    </div>
    <div class="card-expanded-panel">
        <div class="ai-summary">
            <div class="ai-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 18a8 8 0 1 1 8-8 8 8 0 0 1-8 8z"/>
                    <path d="M12 6v6l4 2"/>
                </svg>
            </div>
            <div class="ai-text"></div>
        </div>
        <div class="analysis-charts">
            <div class="chart-container">
                <div class="chart-title">가격 예측 추이</div>
                <div class="chart-wrapper">
                    <canvas class="price-chart"></canvas>
                </div>
            </div>
            <div class="chart-container">
                <div class="chart-title">성능 호환성 분석</div>
                <div class="chart-wrapper">
                    <canvas class="radar-chart"></canvas>
                </div>
            </div>
        </div>
    </div>
  `;

  // 클릭 이벤트 - 부품 선택 (메인 콘텐츠 영역만)
  const mainContent = card.querySelector('.card-main-content');
  mainContent.addEventListener('click', (e) => {
    // 토글 버튼 클릭은 제외
    if (e.target.closest('.card-details-toggle')) return;
    
    // 이미 선택된 경우 무시
    if (card.classList.contains('selected')) return;
    
    handleCardClick(e, card, component);
  });

  // 토글 버튼 이벤트
  const toggleBtn = card.querySelector('.card-details-toggle');
  toggleBtn.addEventListener('click', (e) => {
      e.stopPropagation(); // 카드 선택 방지
      const isExpanded = card.classList.toggle('expanded');
      
      if (isExpanded) {
          renderCardDetails(card, component);
      }
  });

  return card;
}

/**
 * 카드 상세 정보 렌더링 (AI 요약 & 차트)
 */
async function renderCardDetails(cardElement, component) {
    const aiTextEl = cardElement.querySelector('.ai-text');
    const priceCanvas = cardElement.querySelector('.price-chart');
    const radarCanvas = cardElement.querySelector('.radar-chart');
    
    // 1. AI 요약 텍스트 시뮬레이션 (타이핑 효과)
    if (!aiTextEl.dataset.loaded) {
        aiTextEl.textContent = '';
        const summary = generateMockAISummary(component);
        let i = 0;
        const typeInterval = setInterval(() => {
            aiTextEl.textContent += summary.charAt(i);
            i++;
            if (i >= summary.length) {
                clearInterval(typeInterval);
                aiTextEl.dataset.loaded = 'true';
            }
        }, 20);
    }

    // 2. 차트 렌더링 (Chart.js)
    if (!priceCanvas.dataset.loaded) {
        renderPriceChart(priceCanvas);
        priceCanvas.dataset.loaded = 'true';
    }
    
    if (!radarCanvas.dataset.loaded) {
        renderRadarChart(radarCanvas);
        radarCanvas.dataset.loaded = 'true';
    }
}

// 목업 AI 요약 생성기 (전문성 강화 - 카테고리별 맞춤)
function generateMockAISummary(component) {
    const category = component.category?.toUpperCase() || '';
    const benchScore = Math.floor(Math.random() * 8000) + 15000;
    const tdp = Math.floor(Math.random() * 50) + 65;
    const clockSpeed = (Math.random() * 1.5 + 4.0).toFixed(1);
    const temp = Math.floor(Math.random() * 15) + 55;
    
    const categoryTemplates = {
        'CPU': [
            `Cinebench R23 멀티: ${benchScore.toLocaleString()}점 | 싱글: ${Math.floor(benchScore/10)}점. 부스트 ${clockSpeed}GHz, TDP ${tdp}W. 풀로드 ${temp}°C 수준으로 공랭 쿨러로 충분히 대응 가능합니다.`,
            `PassMark ${benchScore.toLocaleString()}점. ${clockSpeed}GHz 터보, ${tdp}W 설계. 게이밍 144Hz 안정 | 멀티태스킹 우수. 가성비 최상위 등급입니다.`
        ],
        'GPU': [
            `3DMark Time Spy ${benchScore.toLocaleString()}점. VRAM 활용률 최적화로 1440p Ultra 90+ FPS, 4K 60 FPS 안정 지원. TGP ${tdp + 100}W, 듀얼팬 쿨링 시스템.`,
            `1440p 게이밍 타겟 최적 모델. DLSS 3.0/FSR 2.0 지원으로 실효 성능 30% 향상. 레이트레이싱 코어 탑재.`
        ],
        'RAM': [
            `XMP 3.0 지원, 지연 시간 CL${Math.floor(Math.random()*6)+14}. 듀얼채널 최대 대역폭 ${benchScore/500 | 0}GB/s. 게이밍/작업 병행 환경 권장.`,
            `DDR5 최적화 다이, 저전압(1.1V) 동작. 오버클럭 잠재력 우수, 히트스프레더 장착으로 안정성 확보.`
        ],
        'SSD': [
            `순차 읽기 ${(benchScore/3).toFixed(0)}MB/s | 쓰기 ${(benchScore/4).toFixed(0)}MB/s. NVMe Gen4 x4, DRAM 캐시 탑재. 내구성 TBW ${Math.floor(Math.random()*400)+600}TB.`,
            `PCIe 4.0 풀스펙. 랜덤 4K 성능 최적화로 OS/게임 로딩 체감 속도 우수. SLC 캐싱으로 대용량 복사 시에도 속도 유지.`
        ],
        'MAINBOARD': [
            `VRM ${Math.floor(Math.random()*4)+10}+2페이즈 설계. DDR5 최대 ${Math.floor(Math.random()*1400)+6400}MHz 지원. M.2 슬롯 ${Math.floor(Math.random()*2)+2}개, USB 3.2 Gen2 다수 제공.`,
            `오버클럭 지원 칩셋. BIOS 최적화로 안정성 우수. 통합 I/O 쉴드, RGB 헤더 3개 제공.`
        ]
    };
    
    // 카테고리에 맞는 템플릿 선택 또는 기본 템플릿
    const templates = categoryTemplates[category] || [
        `벤치마크 점수 ${benchScore.toLocaleString()}점 기록. 동급 대비 ${Math.floor(Math.random()*15)+10}% 높은 효율. TDP ${tdp}W 설계로 전성비 우수.`,
        `성능/가격 균형 최적화 제품. 실사용 테스트에서 안정성 검증 완료. 3년 무상 A/S 지원.`
    ];
    
    return templates[Math.floor(Math.random() * templates.length)];
}

// 가격 추이 차트 (Line - 직선형, 현재 시점 + 1개월 뒤 예측)
function renderPriceChart(canvas) {
    const labels = ['5개월 전', '4개월 전', '3개월 전', '2개월 전', '1개월 전', '현재', '1개월 뒤(예측)'];
    const basePrice = Math.floor(Math.random() * 50000) + 180000;
    
    // 과거 데이터 생성 (현재 기준 변동)
    const data = [];
    for (let i = 5; i >= 1; i--) {
        const variation = Math.floor(Math.random() * 20000) - 10000;
        data.push(basePrice + variation);
    }
    data.push(basePrice); // 현재 가격
    
    // 1개월 뒤 예측 (약간의 하락 트렌드 시뮬레이션)
    const predictedPrice = basePrice - Math.floor(Math.random() * 8000) - 2000;
    data.push(predictedPrice);
    
    const chart = new Chart(canvas, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: '가격 변동',
                data: data,
                borderColor: '#1488fc',
                backgroundColor: 'rgba(20, 136, 252, 0.08)',
                borderWidth: 1.5,
                tension: 0, // 직선형
                fill: true,
                pointRadius: (ctx) => {
                    if (ctx.dataIndex === 5) return 5; // 현재 시점
                    if (ctx.dataIndex === 6) return 4; // 예측
                    return 2;
                },
                pointBackgroundColor: (ctx) => {
                    if (ctx.dataIndex === 5) return '#fff'; // 현재
                    if (ctx.dataIndex === 6) return '#5af78e'; // 예측 (녹색)
                    return '#1488fc';
                },
                pointBorderColor: (ctx) => ctx.dataIndex === 6 ? '#5af78e' : '#1488fc',
                pointBorderWidth: 1.5,
                segment: {
                    borderDash: (ctx) => ctx.p1DataIndex === 6 ? [4, 4] : undefined // 예측 구간 점선
                }
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { 
                    mode: 'index', 
                    intersect: false,
                    backgroundColor: 'rgba(11, 12, 15, 0.95)',
                    titleColor: '#fff',
                    bodyColor: '#ccc',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1,
                    titleFont: { size: 10 },
                    bodyFont: { size: 10 },
                    padding: 6,
                    callbacks: {
                        label: (ctx) => `${ctx.parsed.y.toLocaleString()}원`
                    }
                }
            },
            scales: {
                x: { 
                    display: true,
                    grid: { display: false },
                    ticks: { 
                        color: '#73737b', 
                        font: { size: 8 },
                        maxRotation: 45,
                        minRotation: 0
                    }
                },
                y: { 
                    display: false,
                    min: Math.min(...data) * 0.95,
                    max: Math.max(...data) * 1.05
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
    
    // 리사이즈 처리를 위해 canvas에 차트 인스턴스 저장
    canvas._chartInstance = chart;
}

// 성능 분석 차트 (Horizontal Bar - 가로 바 차트)
function renderRadarChart(canvas) {
    const chart = new Chart(canvas, {
        type: 'bar',
        data: {
            labels: ['게이밍', '작업 효율', '발열', '전력 효율', '가성비'],
            datasets: [{
                label: '성능 지수',
                data: [
                    Math.floor(Math.random() * 20) + 80,
                    Math.floor(Math.random() * 30) + 70,
                    Math.floor(Math.random() * 20) + 80,
                    Math.floor(Math.random() * 20) + 80,
                    Math.floor(Math.random() * 15) + 85
                ],
                backgroundColor: [
                    'rgba(20, 136, 252, 0.85)',
                    'rgba(90, 247, 142, 0.85)', 
                    'rgba(255, 200, 60, 0.85)',
                    'rgba(154, 237, 254, 0.85)',
                    'rgba(255, 99, 132, 0.85)'
                ],
                borderRadius: 3,
                barThickness: 10
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(11, 12, 15, 0.95)',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1,
                    titleFont: { size: 10 },
                    bodyFont: { size: 10 },
                    padding: 6,
                    callbacks: {
                        label: (ctx) => `${ctx.parsed.x}점`
                    }
                }
            },
            scales: {
                x: {
                    display: false,
                    max: 100
                },
                y: {
                    grid: { display: false },
                    ticks: { 
                        color: '#b0b0b0',
                        font: { size: 9, weight: '500' }
                    }
                }
            }
        }
    });
    
    canvas._chartInstance = chart;
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

  // 2. 원본 카드는 선택 상태로 변경 (숨기지 않고 흐리게 처리 or 체크 표시)
  // 기획 의도: "선택된 리스트 창으로 쑤욱 들어가서 선택 추천 창에는 없고"
  // -> Slide Out 후 display: none
  cardElement.style.transform = 'translateX(100px)';
  cardElement.style.opacity = '0';
  setTimeout(() => {
    cardElement.style.display = 'none'; 
    cardElement.classList.add('selected'); // 상태 마킹
  }, 300);

  // 3. 애니메이션 종료 후 실제 데이터 처리
  setTimeout(() => {
    flyingElement.remove();
    selectPart(component);
  }, 600);
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
  fileList.innerHTML = '';

  if (selectedParts.length === 0) {
    fileList.innerHTML = '<div class="file-item" style="color: var(--color-text-muted); padding: 8px;">No parts selected</div>';
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
    fileList.appendChild(item);
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
  fileList.appendChild(totalLine);
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
    const cards = terminalContent.querySelectorAll('.recommendation-card');
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
 * 3D 뷰어 초기화 함수 (개선된 버전)
 * ======================================== */
let viewerState = {
    scene: null,
    camera: null,
    renderer: null,
    controls: null,
    model: null,
    container: null,
    currentBackground: 0,
    initialCameraPosition: null,
    initialCameraTarget: null
};

// 배경 옵션 정의
const BACKGROUND_OPTIONS = [
    { name: '검은 공간', type: 'color', value: 0x000000 },
    { name: '탁상 위', type: 'desk', value: null },
    { name: '흰 배경', type: 'color', value: 0xffffff },
    { name: '모니터와 함께', type: 'monitor', value: null },
    { name: '방 인테리어', type: 'room', value: null }
];

// 3D 뷰어 초기화 함수
async function init3DViewer() {
    const container = document.getElementById('model-viewer');
    if (!container) {
        console.error('3D 뷰어 컨테이너를 찾을 수 없습니다');
        return;
    }
    
    try {
        console.log('3D 뷰어 초기화 시작...');
        viewerState.container = container;
        
        // 컨테이너 스크롤 방지
        container.style.overflow = 'hidden';
        container.style.position = 'relative';
        
        // Scene 설정
        const scene = new THREE.Scene();
        viewerState.scene = scene;
        setBackground(0); // 초기 배경 설정

        // Camera 설정
        const camera = new THREE.PerspectiveCamera(
            50,
            container.clientWidth / container.clientHeight,
            0.1,
            1000
        );
        camera.position.set(0, 2, 5);
        camera.lookAt(0, 0, 0);
        viewerState.camera = camera;

        // Renderer 설정
        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        
        // 기존 캔버스 제거 후 추가 (재진입 안전장치)
        while (container.firstChild) {
            container.removeChild(container.firstChild);
        }
        container.appendChild(renderer.domElement);
        viewerState.renderer = renderer;
        
        // Canvas 스타일 설정
        renderer.domElement.style.display = 'block';
        renderer.domElement.style.width = '100%';
        renderer.domElement.style.height = '100%';

        // OrbitControls 추가
        const controls = new OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        controls.minDistance = 0.5;
        controls.maxDistance = 50;
        controls.enablePan = true;
        viewerState.controls = controls;

        // 컨트롤 설정 (이벤트 리스너)
        setupControls(renderer.domElement, controls);
        
        // 조명 설정
        setupLights(scene);

        // UI 생성
        create3DUI(container);

        // GLB 모델 로드
        const loader = new GLTFLoader();
        
        console.log('GLB 파일 로드 시작: ./images/custom_gaming_pc.glb');
        loader.load(
            './images/custom_gaming_pc.glb',
            (gltf) => {
                console.log('GLB 로드 성공!');
                const model = gltf.scene;
                scene.add(model);
                viewerState.model = model;
                
                // 모델 크기 및 카메라 조정
                fitCameraToModel(camera, controls, model);
                
                console.log('3D 모델 로드 및 설정 완료');
            },
            undefined,
            (error) => {
                console.error('3D 모델 로드 오류:', error);
                const errorMsg = document.createElement('div');
                errorMsg.style.cssText = 'position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); color:#ff6b6b; background:rgba(0,0,0,0.8); padding:10px; border-radius:4px;';
                errorMsg.textContent = '3D 모델을 불러올 수 없습니다.';
                container.appendChild(errorMsg);
            }
        );

        // 애니메이션 루프
        function animate() {
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }
        animate();

        // 리사이즈 처리
        const handleResize = () => {
            if (!container || !camera || !renderer) return;
            const width = container.clientWidth;
            const height = container.clientHeight;
            
            if (width > 0 && height > 0) {
                camera.aspect = width / height;
                camera.updateProjectionMatrix();
                renderer.setSize(width, height);
            }
        };
        
        if (typeof ResizeObserver !== 'undefined') {
            const resizeObserver = new ResizeObserver(handleResize);
            resizeObserver.observe(container);
        } else {
            window.addEventListener('resize', handleResize);
        }

        console.log('3D 뷰어 초기화 완료');
    } catch (error) {
        console.error('3D 뷰어 초기화 오류:', error);
        container.innerHTML = `<div style="color:red; padding:20px;">Viewer Error: ${error.message}</div>`;
    }
}

// 컨트롤 이벤트 설정
function setupControls(domElement, controls) {
    let isCtrlPressed = false;
    
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey || e.metaKey) {
            isCtrlPressed = true;
            controls.enableRotate = false;
            controls.enablePan = true;
        }
    });
    
    document.addEventListener('keyup', (e) => {
        if (!e.ctrlKey && !e.metaKey) {
            isCtrlPressed = false;
            controls.enableRotate = true;
            controls.enablePan = false;
        }
    });
}

// 카메라를 모델에 맞게 자동 조정
function fitCameraToModel(camera, controls, model) {
    const box = new THREE.Box3().setFromObject(model);
    const size = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z);
    
    // 모델 스케일 조정 (약 3단위 크기로 맞춤)
    const targetSize = 3;
    const scale = targetSize / maxDim;
    model.scale.setScalar(scale);
    
    // 스케일 적용 후 다시 박스 계산하여 중앙 정렬
    box.setFromObject(model);
    const center = box.getCenter(new THREE.Vector3());
    model.position.sub(center);
    
    // 카메라 위치 설정
    camera.position.set(3, 3, 5);
    camera.lookAt(0, 0, 0);
    
    controls.target.set(0, 0, 0);
    controls.update();
    
    viewerState.initialCameraPosition = camera.position.clone();
    viewerState.initialCameraTarget = controls.target.clone();
}

// 조명 설정 함수
function setupLights(scene) {
    // 기존 조명 제거
    const lightsToRemove = [];
    scene.traverse((child) => {
        if (child instanceof THREE.Light) {
            lightsToRemove.push(child);
        }
    });
    lightsToRemove.forEach(light => scene.remove(light));

    // 새로운 조명 추가
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.5);
    scene.add(ambientLight);

    const directionalLight1 = new THREE.DirectionalLight(0xffffff, 2.0);
    directionalLight1.position.set(5, 5, 5);
    directionalLight1.castShadow = true;
    scene.add(directionalLight1);

    const directionalLight2 = new THREE.DirectionalLight(0xffffff, 1.5);
    directionalLight2.position.set(-5, 3, -5);
    scene.add(directionalLight2);

    const directionalLight3 = new THREE.DirectionalLight(0xffffff, 1.0);
    directionalLight3.position.set(0, -5, 5);
    scene.add(directionalLight3);
}

// 배경 설정 함수
function setBackground(index) {
    if (!viewerState.scene) return;
    
    viewerState.currentBackground = index;
    const option = BACKGROUND_OPTIONS[index];
    
    if (option.type === 'color') {
        viewerState.scene.background = new THREE.Color(option.value);
        viewerState.scene.environment = null;
    } else {
        // 복잡한 배경은 나중에 구현 (일단 검은색으로)
        viewerState.scene.background = new THREE.Color(0x1a1a1a);
        viewerState.scene.environment = null;
    }
}

// 3D UI 생성 함수
function create3DUI(container) {
    // 상단 가이드 (플로팅) - 전문적인 마우스/키캡 아이콘으로 변경
    const topGuide = document.createElement('div');
    topGuide.id = 'viewer-top-guide';
    topGuide.className = 'viewer-guide-top';
    topGuide.innerHTML = `
        <div class="guide-item">
            <div class="guide-icon-group">
                <div class="keycap">Ctrl</div>
                <span>+</span>
                <svg class="mouse-icon" viewBox="0 0 24 32">
                    <rect x="2" y="2" width="20" height="28" rx="10" ry="10" />
                    <line x1="12" y1="2" x2="12" y2="14" />
                    <line x1="2" y1="14" x2="22" y2="14" />
                    <path class="active" d="M2 14h10v-12c-5 0 -10 5 -10 12z" />
                </svg>
            </div>
            <span>시점 이동</span>
        </div>
        <div class="guide-item">
            <div class="guide-icon-group">
                <svg class="mouse-icon" viewBox="0 0 24 32">
                    <rect x="2" y="2" width="20" height="28" rx="10" ry="10" />
                    <line x1="12" y1="2" x2="12" y2="14" />
                    <line x1="2" y1="14" x2="22" y2="14" />
                    <rect class="wheel active" x="10.5" y="6" width="3" height="6" rx="1.5" />
                </svg>
            </div>
            <span>확대/축소</span>
        </div>
        <div class="guide-item">
            <div class="guide-icon-group">
                <svg class="mouse-icon" viewBox="0 0 24 32">
                    <rect x="2" y="2" width="20" height="28" rx="10" ry="10" />
                    <line x1="12" y1="2" x2="12" y2="14" />
                    <line x1="2" y1="14" x2="22" y2="14" />
                    <path class="active" d="M2 14h10v-12c-5 0 -10 5 -10 12z" />
                </svg>
            </div>
            <span>회전</span>
        </div>
    `;
    container.appendChild(topGuide);

    // 우측 하단 컨트롤 (플로팅)
    const bottomControls = document.createElement('div');
    bottomControls.id = 'viewer-bottom-controls';
    bottomControls.className = 'viewer-controls-bottom';
    bottomControls.innerHTML = `
        <button id="viewer-reset-btn" class="viewer-btn-reset" title="시점 초기화">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
                <path d="M21 3v5h-5"/>
                <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
                <path d="M3 21v-5h5"/>
            </svg>
        </button>
        <div class="viewer-bg-selector">
            ${BACKGROUND_OPTIONS.map((opt, idx) => `
                <button class="viewer-bg-btn ${idx === 0 ? 'active' : ''}" 
                        data-bg-index="${idx}" 
                        title="${opt.name}">
                    <span class="bg-indicator"></span>
                </button>
            `).join('')}
        </div>
    `;
    container.appendChild(bottomControls);

    // 이벤트 리스너
    const resetBtn = document.getElementById('viewer-reset-btn');
    resetBtn.addEventListener('click', resetViewpoint);

    const bgButtons = bottomControls.querySelectorAll('.viewer-bg-btn');
    bgButtons.forEach((btn, idx) => {
        btn.addEventListener('click', () => {
            bgButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            setBackground(idx);
        });
    });
}

// 시점 최적화 함수
function resetViewpoint() {
    if (!viewerState.camera || !viewerState.controls || !viewerState.model) return;
    
    fitCameraToModel(viewerState.camera, viewerState.controls, viewerState.model);
}

// 이 부분도 제거 (3D 뷰어 호출)
setTimeout(() => {
    init3DViewer();
}, 100);

