from app.services.data_service import predict_image, get_latest_csv_stats
from app.core.config import settings
import openai
from app.integrations.django_bridge import get_chat_models, get_or_create_user_by_username
import logging

openai.api_key = settings.OPENAI_API_KEY
logger = logging.getLogger("chatbot")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

USE_FAQ_CONTEXT = True
FAQ_LIMIT = 10

def _build_messages(query: str) -> list[dict]:
    ChatRecord, FAQ, User = get_chat_models()
    messages = [{"role": "system", "content": "당신은 회사 내부 고객지원 챗봇입니다. 간결하고 정확하게 한국어로 답변하세요."}]
    if USE_FAQ_CONTEXT:
        faqs = FAQ.objects.filter(active=True)[:FAQ_LIMIT]
        if faqs:
            context = "\n\n".join([f"Q: {f.question}\nA: {f.answer}" for f in faqs])
            messages.append({"role": "system", "content": f"다음은 관리자 등록 FAQ입니다. 가능하면 이를 우선 참고해 답하세요:\n{context}"})
    messages.append({"role": "user", "content": query})
    return messages

def call_openai_api(query: str) -> str:
    try:
        messages = _build_messages(query)
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.2,
            max_tokens=400,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"OpenAI API 호출 오류: {e}")
        return "죄송합니다. 현재 답변을 생성할 수 없습니다."

def get_chatbot_answer(query: str, image_file=None, user_email: str | None = None) -> str:
    ChatRecord, FAQ, User = get_chat_models()
    query_clean = (query or "").strip()
    if not query_clean and not image_file:
        return "질문 내용을 입력해주세요."

    user_obj = get_or_create_user_by_username(user_email) if user_email else None

    # 이미지 처리
    if image_file:
        result = predict_image(image_file)
        answer = f"이미지 분석 결과: {result['prediction']} (신뢰도 {result['confidence']:.2f})"
        ChatRecord.objects.create(user=user_obj, query=query_clean or "[image-only]", answer=answer, has_image=True)
        return answer

    # CSV 통계
    csv_stats = get_latest_csv_stats()
    for key, value in csv_stats.items():
        if key.lower() in query_clean.lower():
            answer = f"{key}는 현재 {value}입니다."
            ChatRecord.objects.create(user=user_obj, query=query_clean, answer=answer, has_image=False)
            return answer

    # OpenAI 호출
    answer = call_openai_api(query_clean)
    ChatRecord.objects.create(user=user_obj, query=query_clean, answer=answer, has_image=False)
    return answer
