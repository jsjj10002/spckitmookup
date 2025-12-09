/**
 * Landing 페이지 스크립트
 * 초기 화면에서 메시지 입력 후 builder 페이지로 전환
 */

// DOM 요소
const chatInput = document.getElementById('landing-chat-input');
const sendBtn = document.getElementById('landing-send-btn');
const mySpecsBtn = document.getElementById('my-specs-btn');

/**
 * 초기화
 */
function init() {
  // 이벤트 리스너 등록
  sendBtn.addEventListener('click', handleSendClick);
  chatInput.addEventListener('keydown', handleKeyDown);
  
  if (mySpecsBtn) {
    mySpecsBtn.addEventListener('click', handleMySpecsClick);
  }
  
  // 입력 포커스
  chatInput.focus();
}

/**
 * 전송 버튼 클릭 핸들러
 */
function handleSendClick() {
  // contenteditable 요소이므로 innerText로 값을 가져옴
  const message = chatInput.innerText.trim();
  if (message) {
    navigateToBuilder(message);
  }
}

/**
 * "내 사양" 버튼 클릭 핸들러
 */
function handleMySpecsClick() {
    // 이미 태그가 존재하는지 확인 (HTML 내용 검사)
    if (!chatInput.innerHTML.includes('tag-spec')) {
        const tagHtml = '<span class="tag-spec" contenteditable="false">@내사양</span>&nbsp;';
        
        // 기존 텍스트 내용 유지 (태그 텍스트 제거 후)
        const currentText = chatInput.innerText.replace('@내사양', '').trim();
        
        // 태그 삽입
        chatInput.innerHTML = tagHtml + currentText;
        
        // 커서를 맨 뒤로 이동
        placeCaretAtEnd(chatInput);
    }
    chatInput.focus();
}

/**
 * 커서를 요소의 맨 끝으로 이동시키는 유틸리티 함수
 */
function placeCaretAtEnd(el) {
    el.focus();
    if (typeof window.getSelection != "undefined"
            && typeof document.createRange != "undefined") {
        var range = document.createRange();
        range.selectNodeContents(el);
        range.collapse(false);
        var sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
    }
}

/**
 * 키보드 이벤트 핸들러 (Enter로 전송)
 */
function handleKeyDown(e) {
  if (e.key === 'Enter') {
    e.preventDefault(); // 줄바꿈 방지
    handleSendClick();
  }
}

/**
 * Builder 페이지로 이동
 * @param {string} message - 사용자 메시지
 */
function navigateToBuilder(message) {
  // URL 파라미터로 메시지 전달
  const url = new URL('builder.html', window.location.origin + window.location.pathname.replace('index.html', ''));
  url.searchParams.set('message', message);
  window.location.href = url.toString();
}

// 초기화 실행
init();
