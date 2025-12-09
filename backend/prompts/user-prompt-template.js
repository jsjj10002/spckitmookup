/**
 * 사용자 프롬프트 템플릿
 * 사용자 메시지를 AI 요청 형식으로 변환합니다.
 */

/**
 * PC 부품 추천 요청 프롬프트 생성
 * @param {string} userMessage - 사용자 입력 메시지
 * @returns {string} 포맷된 프롬프트
 */
export function buildPCRecommendationPrompt(userMessage) {
  return `사용자 요청: "${userMessage}". 

이 요청에 따라 PC 부품 견적을 맞춰주세요. 상세한 분석과 함께 추천 부품 목록을 제공해주세요.

JSON 형식으로 응답해주세요:
{
  "analysis": "상세 분석 내용 (사용자의 요구사항, 예산, 사용 목적을 종합적으로 분석한 내용)",
  "components": [
    {
      "category": "부품 카테고리 (예: CPU, GPU, RAM, 메인보드, SSD, 케이스, 파워)",
      "name": "제품명 (정확한 제품명)",
      "price": "가격 (예: '약 450,000원')",
      "features": ["특징1", "특징2", "특징3"]
    }
  ]
}

주의사항:
- 모든 부품 카테고리를 포함해야 합니다 (CPU, GPU, RAM, 메인보드, SSD, 케이스, 파워)
- 가격은 원화(KRW)로 표시하세요
- features는 3-5개의 핵심 특징을 키워드로 제공하세요
- 부품 간 호환성을 고려하세요`;
}

