import os
import sys
from pathlib import Path
import django
from asgiref.sync import sync_to_async

# Django 프로젝트 경로 설정
BASE_DIR = Path(__file__).resolve().parents[2]  # Finnect/
DJANGO_ROOT = BASE_DIR / "backend"
for path in [str(DJANGO_ROOT), str(DJANGO_ROOT / "core"), str(DJANGO_ROOT / "finnect_admin")]:
    if path not in sys.path:
        sys.path.insert(0, path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "finnect_admin.settings")
django.setup()

# ----------------
# 모델 import
# ----------------
from core.models import UploadRecord, ChatRecord, FAQ, Intent, User as core_models_user
from django.contrib.auth import get_user_model
User = get_user_model()

# ----------------
# UploadRecord 관련
# ----------------
def get_upload_record_model():
    """UploadRecord 모델 반환"""
    return UploadRecord


# ----------------
# Chat / FAQ 관련
# ----------------
def get_chat_models():
    """ChatRecord, FAQ, User 모델 반환"""
    return ChatRecord, FAQ, User


def get_or_create_user_by_username(username: str):
    """JWT username → Django User 객체 반환"""
    if not username:
        return None
    user, _ = User.objects.get_or_create(username=username)
    return user


# ----------------
# Intent 관련
# ----------------
def get_intent_response(user_message: str) -> str | None:
    """패턴 기반 Intent 조회 후 응답 반환"""
    intents = Intent.objects.filter(active=True)
    for intent in intents:
        keywords = [k.strip() for k in intent.keywords.split(",")]
        if any(k in user_message for k in keywords):
            return intent.response
    return None


async def get_intent_response_async(user_message: str):
    """비동기 Intent 호출"""
    return await sync_to_async(get_intent_response)(user_message)


# ----------------
# FAQ 관련
# ----------------
def get_faqs_sync(limit: int = 10):
    """동기 ORM 호출 (limit 타입 안전)"""
    try:
        limit = int(limit)  # str로 들어와도 안전
    except (ValueError, TypeError):
        limit = 10
    return list(FAQ.objects.filter(active=True)[:limit])


async def get_faqs_async(limit: int = 10):
    """비동기 ORM 호출"""
    return await sync_to_async(get_faqs_sync)(limit)


get_intent_response_async = sync_to_async(get_intent_response)
get_faqs_async = sync_to_async(get_faqs_sync)

