#!/bin/sh
set -e  # 에러 시 종료

# migrate
python manage.py migrate --noinput

# runserver 실행
exec python manage.py runserver 0.0.0.0:8000
