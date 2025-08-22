# chatbot_service.py
from app.services.data_service import predict_image, get_latest_csv_stats, process_csv
from app.services.csv_convert import convert_xlsx_to_csv
from app.core.config import settings
import openai
import logging
from io import BytesIO
from fastapi import UploadFile

openai.api_key = settings.OPENAI_API_KEY
logger = logging.getLogger("chatbot")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

USE_FAQ_CONTEXT = True
FAQ_LIMIT = 10

def _build_messages(query: str) -> list[dict]:
    messages = [{"role": "system", "content": "당신은 회사 내부 고객지원 챗봇입니다. 간결하고 정확하게 한국어로 답변하세요."}]
    if USE_FAQ_CONTEXT:
        from app.integrations.django_bridge import get_chat_models
        _, FAQ, _ = get_chat_models()
        faqs = FAQ.objects.filter(active=True)[:FAQ_LIMIT]
        if faqs:
            context = "\n\n".join([f"Q: {f.question}\nA: {f.answer}" for f in faqs])
            messages.append({"role": "system", "content": f"다음은 관리자 등록 FAQ입니다. 가능하면 이를 우선 참고해 답하세요:\n{context}"})
    messages.append({"role": "user", "content": query})
    return messages

def call_openai_api(query: str) -> str:
    try:
        messages = _build_messages(query)
        print("OpenAI 호출 메시지:", messages)
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.2,
            max_tokens=400,
        )
        answer = resp.choices[0].message.content.strip()
        print("OpenAI 응답:", answer)
        return answer
    except Exception as e:
        logger.error(f"OpenAI API 호출 오류: {e}")
        return "죄송합니다. 현재 답변을 생성할 수 없습니다."

async def get_chatbot_answer(query: str | None = None, file: UploadFile | None = None) -> str:
    query_clean = (query or "").strip()

    # 파일 처리
    if file is not None:
        content_type = getattr(file, "content_type", "")
        content_bytes = BytesIO(await file.read())

        # 이미지 처리
        if content_type.startswith("image/"):
            result = predict_image(content_bytes)
            return f"이미지 분석 결과: {result.get('prediction','error')} (신뢰도 {result.get('confidence',0.0):.2f})"

        # XLSX 처리 → CSV 변환
        elif content_type in [
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel"
        ]:
            csv_buffer = convert_xlsx_to_csv(content_bytes)
            stats = process_csv(csv_buffer)
            if query_clean:
                for key, value in stats.items():
                    if key.lower() in query_clean.lower():
                        return f"{key}는 현재 {value}입니다."
            return "CSV 파일이 처리되었습니다."

        # CSV 처리
        elif content_type == "text/csv":
            stats = process_csv(content_bytes)
            if query_clean:
                for key, value in stats.items():
                    if key.lower() in query_clean.lower():
                        return f"{key}는 현재 {value}입니다."
            return "CSV 파일이 처리되었습니다."

        else:
            return "지원하지 않는 파일 형식입니다."

    # CSV 통계 처리 (파일 없이 최신 통계 조회)
    if query_clean:
        csv_stats = get_latest_csv_stats()
        for key, value in csv_stats.items():
            if key.lower() in query_clean.lower():
                return f"{key}는 현재 {value}입니다."

    # OpenAI 호출
    if query_clean:
        return call_openai_api(query_clean)

    return "질문 내용을 입력해주세요."

