import os, sys
from pathlib import Path
import django

BASE_DIR = Path(__file__).resolve().parents[1]  # Finnect/
DJANGO_ROOT = BASE_DIR / "backend"
sys.path.insert(0, str(DJANGO_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "finnect_admin.settings")
django.setup()

from core.models import User

users = [
    {"email": "user@example.com", "password": "secret123", "role": "user"},
    {"email": "admin@example.com", "password": "adminsecret", "role": "admin"},
]

for u in users:
    if not User.objects.filter(email=u["email"]).exists():
        user = User(email=u["email"], role=u["role"])
        user.set_password(u["password"])
        user.save()

print("Users created!")

# SELECT * FROM core_user;