# 베이스 이미지
FROM python:3.11-slim

# 환경 변수
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 복사 및 설치
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트 전체 복사
COPY ./app ./app
COPY ./backend ./backend
COPY ./scripts ./scripts

# FastAPI 실행
CMD ["python", "-m", "app.main"]
