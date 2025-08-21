import os
import sys
from pathlib import Path
import django

# Django 프로젝트 경로 설정
BASE_DIR = Path(__file__).resolve().parents[2]  # Finnect/
DJANGO_ROOT = BASE_DIR / "backend"
for path in [str(DJANGO_ROOT), str(DJANGO_ROOT / "core"), str(DJANGO_ROOT / "finnect_admin")]:
    if path not in sys.path:
        sys.path.insert(0, path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "finnect_admin.settings")
django.setup()

# 모델 불러오기
from core.models import UploadRecord, ChatRecord, FAQ
from django.contrib.auth import get_user_model

User = get_user_model()

# -----------------------------
# 유틸 함수
# -----------------------------
def get_upload_record_model():
    """UploadRecord 모델 반환"""
    return UploadRecord

def get_chat_models():
    """ChatRecord, FAQ, User 모델 반환"""
    return ChatRecord, FAQ, User

def get_or_create_user_by_username(username: str):
    """JWT username → Django User 객체 반환"""
    if not username:
        return None
    user, _ = User.objects.get_or_create(username=username)
    return user
