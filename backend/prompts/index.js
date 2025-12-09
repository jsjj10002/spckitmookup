/**
 * 프롬프트 모듈 통합
 * 모든 프롬프트 관련 기능을 한 곳에서 관리합니다.
 */

export { SYSTEM_INSTRUCTION } from './system-instruction.js';
export { buildPCRecommendationPrompt } from './user-prompt-template.js';

/**
 * Gemini API 요청을 위한 전체 프롬프트 구성
 * @param {string} userMessage - 사용자 메시지
 * @returns {Object} Gemini API 요청 형식의 프롬프트 객체
 */
export async function buildGeminiRequest(userMessage) {
  const { buildPCRecommendationPrompt } = await import('./user-prompt-template.js');
  const { SYSTEM_INSTRUCTION } = await import('./system-instruction.js');
  
  return {
    contents: [{
      parts: [{
        text: buildPCRecommendationPrompt(userMessage)
      }]
    }],
    generationConfig: {
      temperature: 0.7,
      topK: 40,
      topP: 0.95,
      maxOutputTokens: 2048,
      responseMimeType: "application/json"
    },
    systemInstruction: {
      parts: [{
        text: SYSTEM_INSTRUCTION
      }]
    }
  };
}

