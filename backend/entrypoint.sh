#!/bin/sh
set -e  # 에러 시 종료

# DB가 준비될 때까지 대기 (wait-for-it.sh 필요)
bash /app/wait-for-it.sh db:5432 --timeout=30 --strict -- echo "DB is up"

# migrate
python /app/backend/manage.py migrate --noinput

# runserver 실행
exec python /app/backend/manage.py runserver 0.0.0.0:8000
