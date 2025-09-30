import logging
from typing import Optional, Dict, Any
import json

from asgiref.sync import sync_to_async

from app.integrations.django_bridge import get_upload_record_model, get_intent_response_async, get_faqs_async
from app.core.redis import redis_client_async

logger = logging.getLogger("chatbot")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

UploadRecord = get_upload_record_model()


# ----------------------------
# Redis helper
# ----------------------------
async def _cache_get(key: str) -> Optional[str]:
    value = await redis_client_async.get(key)
    if value is None:
        return None
    return value.decode() if isinstance(value, bytes) else value

async def _cache_set(key: str, value: str, ex: int = 3600):
    await redis_client_async.set(key, value, ex=ex)


# ----------------------------
# Context for templates
# ----------------------------
async def _build_context() -> Dict[str, Any]:
    """
    Intent 템플릿 치환용 컨텍스트 구성
    최신 CSV 통계 + 이미지 예측값
    """
    ctx: Dict[str, Any] = {}

    # 최신 CSV 통계
    latest_csv = await sync_to_async(
        lambda: UploadRecord.objects.filter(statistics__isnull=False).order_by("-uploaded_at").first()
    )()
    if latest_csv and latest_csv.statistics:
        stats_dict = latest_csv.statistics
        if isinstance(stats_dict, str):
            stats_dict = json.loads(stats_dict)
        ctx.update(stats_dict)

    # 최신 이미지 예측
    latest_img = await sync_to_async(
        lambda: UploadRecord.objects.filter(prediction__isnull=False).order_by("-uploaded_at").first()
    )()
    if latest_img:
        ctx["prediction"] = latest_img.prediction
        ctx["confidence"] = latest_img.confidence

    # 한국어 alias
    alias = {
        "총매출": "total_revenue",
        "고객수": "num_customers",
        "인보이스수": "num_invoices",
        "총수량": "total_quantity",
        "이미지상태": "prediction",
        "신뢰도": "confidence",
    }
    for ko, en in alias.items():
        if en in ctx:
            ctx[ko] = ctx[en]

    return ctx


# ----------------------------
# Safe template rendering
# ----------------------------
class _SafeDict(dict):
    def __missing__(self, key):
        return "데이터 없음"

def _render_template(template: str, context: Dict[str, Any]) -> str:
    safe_ctx = {}
    for k, v in context.items():
        if isinstance(v, float):
            safe_ctx[k] = f"{v:.3f}"
        else:
            safe_ctx[k] = v
    return template.format_map(_SafeDict(safe_ctx))


# ----------------------------
# Main chatbot logic
# ----------------------------
async def get_chatbot_answer(query: Optional[str] = None) -> str:
    query_clean = (query or "").strip()
    if not query_clean:
        return "질문 내용을 입력해주세요."

    cached = await _cache_get(query_clean)
    if cached:
        return cached

    # 통합된 context 가져오기
    ctx = await _build_context()

    # CSV 통계 매칭
    for k, v in ctx.items():
        if k.lower() in query_clean.lower() and k not in ["prediction", "confidence"]:
            ans = f"{k}는 현재 {v}입니다."
            await _cache_set(query_clean, ans)
            return ans

    # 이미지 결과 매칭
    if any(kw in query_clean.lower() for kw in ["이미지", "불량", "양품", "상태", "defect", "normal"]):
        if "prediction" in ctx:
            ans = f"최근 업로드된 이미지 결과: {ctx['prediction']} (신뢰도 {ctx.get('confidence', 0):.2f})"
            await _cache_set(query_clean, ans)
            return ans

    # Intent / FAQ
    intent_template = await get_intent_response_async(query_clean)
    if intent_template:
        rendered = _render_template(intent_template, ctx)
        await _cache_set(query_clean, rendered)
        return rendered

    faqs = await get_faqs_async(limit=10)
    for faq in faqs:
        if query_clean.lower() in faq.question.lower():
            await _cache_set(query_clean, faq.answer)
            return faq.answer

    return "관련된 데이터가 없습니다."

