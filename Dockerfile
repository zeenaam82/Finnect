# 베이스 이미지
FROM python:3.11
# FROM python:3.11-slim

# 환경 변수
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 복사 및 설치
COPY requirements.txt .
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt

# entrypoint.sh 복사 및 실행 권한
COPY ./backend/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# wait-for-it.sh 복사 및 실행 권한 부여
COPY ./wait-for-it.sh /app/wait-for-it.sh
RUN chmod +x /app/wait-for-it.sh

# 프로젝트 전체 복사
COPY ./app ./app
COPY ./backend ./backend
COPY ./scripts ./scripts