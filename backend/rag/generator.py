"""
Gemini API를 사용한 추천 응답 생성기 (New SDK)
"""
from google import genai
from google.genai import types
from typing import List, Dict, Any, Optional
from loguru import logger
import json

from .config import GEMINI_API_KEY, GENERATION_MODEL


class PCRecommendationGenerator:
    """검색된 부품 정보를 기반으로 사용자에게 추천 응답을 생성하는 클래스"""

    def __init__(
        self,
        api_key: str = GEMINI_API_KEY,
        model: str = GENERATION_MODEL,
        temperature: float = 0.7,
    ):
        """
        Args:
            api_key: Gemini API 키
            model: 생성 모델 이름
            temperature: 생성 온도 (0~1, 높을수록 창의적)
        """
        self.api_key = api_key
        self.model_name = model
        self.temperature = temperature

        # Gemini API 클라이언트 초기화 (google-genai SDK)
        self.client = genai.Client(api_key=self.api_key)
        
        logger.info(f"PCRecommendationGenerator 초기화: model={model} (SDK: google-genai)")

    def generate_recommendation(
        self,
        user_query: str,
        retrieved_components: List[Dict[str, Any]],
        system_instruction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        사용자 쿼리와 검색된 부품 정보를 기반으로 추천 생성
        """
        # 컨텍스트 구성
        context = self._build_context(retrieved_components)

        # 프롬프트 생성
        prompt = self._build_prompt(user_query, context, system_instruction)

        try:
            # Gemini API 호출 (Google Search 도구 활성화)
            # 검색 도구 설정
            tools = [types.Tool(google_search=types.GoogleSearch())]
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=self.temperature,
                    max_output_tokens=8192,
                    response_mime_type="application/json",
                    tools=tools,  # Google Search 도구 적용
                ),
            )

            # 응답 텍스트 추출 및 로깅
            generated_text = response.text
            
            # response.text가 None인 경우 candidates에서 직접 추출 시도 (MAX_TOKENS 등으로 중단된 경우)
            if generated_text is None and response.candidates:
                try:
                    part = response.candidates[0].content.parts[0]
                    if part.text:
                        generated_text = part.text
                        logger.warning("response.text가 비어있어 candidate에서 텍스트를 추출했습니다.")
                except (AttributeError, IndexError):
                    pass
            
            logger.info(f"Gemini 응답 텍스트 타입: {type(generated_text)}")
            
            # 응답 유효성 검사
            if not generated_text:
                finish_reason = "Unknown"
                if response.candidates and response.candidates[0].finish_reason:
                    finish_reason = response.candidates[0].finish_reason
                
                logger.error(f"Gemini API 응답이 비어있습니다. 종료 원인: {finish_reason}")
                return {
                    "analysis": "AI 응답을 생성하지 못했습니다.",
                    "components": [],
                    "total_price": "0",
                    "additional_notes": f"API 응답 오류 (종료 원인: {finish_reason})"
                }

            # 응답 파싱
            result = json.loads(generated_text)
            
            logger.info(f"추천 생성 완료: '{user_query[:50]}...'")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 실패: {str(e)}")
            # JSON이 아닌 경우 텍스트 그대로 반환 시도
            return {
                "analysis": getattr(response, 'text', "응답을 처리할 수 없습니다."),
                "components": [],
                "total_price": "0",
                "additional_notes": "JSON 형식이 아닙니다."
            }
        except Exception as e:
            logger.error(f"추천 생성 실패: {str(e)}")
            raise

    def _build_context(self, components: List[Dict[str, Any]]) -> str:
        """
        검색된 부품 정보를 컨텍스트 문자열로 변환
        """
        if not components:
            return "검색된 부품이 없습니다."

        context_parts = ["### 검색된 PC 부품 정보:"]
        
        for i, comp in enumerate(components, 1):
            metadata = comp.get("metadata", {})
            similarity = comp.get("similarity", 0)

            part = [
                f"\n[부품 {i}]",
                f"- 카테고리: {metadata.get('category', 'N/A')}",
                f"- 제품명: {metadata.get('name', 'N/A')}",
                f"- 유사도: {similarity:.2%}",
            ]

            # 주요 스펙 추가
            for key, value in metadata.items():
                if key not in ["category", "name", "id", "source", "created_at", "updated_at"]:
                    if value:
                        part.append(f"- {key}: {value}")

            context_parts.append("\n".join(part))

        return "\n".join(context_parts)

    def _build_prompt(
        self,
        user_query: str,
        context: str,
        system_instruction: Optional[str] = None,
    ) -> str:
        """
        프롬프트 생성
        """
        default_instruction = """당신은 'Spckit AI'입니다. 사용자의 요구사항, 예산, 사용 목적에 따라 맞춤형 PC 부품을 추천하는 전문 AI 어시스턴트입니다. 
항상 한국어로 답변하고, 검색된 부품 정보를 기반으로 정확하고 상세한 추천을 제공하세요."""

        instruction = system_instruction or default_instruction

        prompt = f"""{instruction}

{context}

사용자 요청: "{user_query}"

위의 검색된 부품 정보를 참고하여, 사용자의 요청에 맞는 PC 부품을 추천해주세요.
**중요**: 가격 정보가 없거나 불확실한 경우, Google Search 도구를 사용하여 최신 가격을 검색해서 채워넣으세요.

응답 속도를 높이기 위해 분석과 이유는 짧고 간결하게 작성하세요.

다음 JSON 형식으로 응답해주세요:
{{
    "analysis": "짧은 분석 (100자 이내)",
    "components": [
        {{
            "category": "부품 카테고리 (예: CPU)",
            "name": "제품명",
            "price": "가격 (예: 350,000원)",
            "hashtags": ["#특징1", "#특징2"], 
            "features": ["짧은 특징1"],
            "reason": "짧은 추천 이유"
        }}
    ],
    "total_price": "총 예상 가격",
    "additional_notes": "짧은 팁"
}}

**스타일 가이드**:
1. 'hashtags'는 제품의 핵심 특징을 짧은 키워드로 2~3개만 작성하세요.
2. 'price'는 가능한 정확한 한국 원화 가격을 검색하여 기입하세요.
3. 설명은 최대한 간결하게 작성하여 응답 속도를 최적화하세요."""

        return prompt

    def generate_comparison(
        self,
        components_to_compare: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        여러 부품을 비교 분석
        """
        context = self._build_context(components_to_compare)

        prompt = f"""다음 PC 부품들을 비교 분석해주세요:

{context}

각 부품의 장단점, 가격 대비 성능, 추천 대상을 JSON 형식으로 정리해주세요:

{{
    "comparison": [
        {{
            "component_name": "제품명",
            "pros": ["장점1", "장점2"],
            "cons": ["단점1", "단점2"],
            "value_for_money": "가격 대비 성능 평가",
            "recommended_for": "추천 대상"
        }}
    ],
    "best_choice": "최고의 선택과 이유",
    "budget_choice": "가성비 선택과 이유"
}}"""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.5,
                    max_output_tokens=8192,  # 토큰 제한 증가
                    response_mime_type="application/json",
                ),
            )

            # 응답 텍스트 추출 안전장치
            generated_text = response.text
            if generated_text is None and response.candidates:
                try:
                    part = response.candidates[0].content.parts[0]
                    if part.text:
                        generated_text = part.text
                except (AttributeError, IndexError):
                    pass
            
            if not generated_text:
                raise ValueError("생성된 텍스트가 없습니다.")

            return json.loads(generated_text)

        except Exception as e:
            logger.error(f"비교 분석 실패: {str(e)}")
            raise
