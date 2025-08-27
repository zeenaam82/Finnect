import os
from pathlib import Path
from dotenv import load_dotenv

# --------------------------
# 기본 경로
# --------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # Finnect/
load_dotenv(BASE_DIR / ".env")

# --------------------------
# 보안/디버그
# --------------------------
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "change-me")
DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"
ALLOWED_HOSTS = ["*"]

# --------------------------
# 앱 등록
# --------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
]

# --------------------------
# 미들웨어
# --------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

# --------------------------
# URL/WSGI
# --------------------------
ROOT_URLCONF = "finnect_admin.urls"
WSGI_APPLICATION = "finnect_admin.wsgi.application"

# --------------------------
# 데이터베이스
# --------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB"),
        "USER": os.environ.get("POSTGRES_USER"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD"),
        "HOST": os.environ.get("POSTGRES_HOST", "db"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

# SQLAlchemy 호환용 URL (FastAPI에서 사용)
# DATABASE_URL = "postgresql+psycopg2://finnect_user:finnect_pass@localhost:5432/finnect_db"

# --------------------------
# 국제화
# --------------------------
LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

# --------------------------
# 정적 파일
# --------------------------
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------------
# 템플릿
# --------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],  # 커스텀 템플릿 디렉토리
        "APP_DIRS": True,  # 앱 내부 templates 탐색
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
