# Finnect

Finnect는 **FastAPI**와 **Django**를 연동하여 내부 고객 지원 챗봇과 이미지/CSV 업로드 분석 기능을 제공하는 프로젝트입니다.  
FastAPI는 API 서버 및 JWT 인증을 담당하며, Django는 업로드 기록과 챗봇 기록 저장 및 관리자용 UI를 제공합니다.

---

## 데이터셋

1. **MVTec AD (Anomaly Detection)**
   - 단일 이미지 불량 판별용
   - 링크: [MVTec AD Dataset](https://www.mvtec.com/company/research/datasets/mvtec-ad/)
   
2. **Kaggle Customer Segmentation Dataset**
   - 고객 세분화 및 CSV 통계 예제용
   - 링크: [Customer Segmentation Dataset](https://www.kaggle.com/datasets/sid321axn/customer-segmentation)

> 데이터셋은 `data/` 폴더에 위치시켜야 합니다.

---

## 설치 및 환경 설정

1. Python 3.11 이상 권장
2. 가상환경 생성
```bash
python -m venv venv
source venv/Scripts/activate  # Windows
source venv/bin/activate     # Linux / Mac
```
3. 패키지 설치
```bash
pip install --upgrade pip
pip install -r requirements.txt
```
4. PostgreSQL DB 생성 및 설정 (settings.py 참고)
5. Django 마이그레이션
```bash
cd backend
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 8001
```
6. FastAPI 실행
```bash
cd app
uvicorn main:app --reload --port 8000
```

## 기능
- FastAPI
  - JWT 인증 기반 API
  - 이미지 업로드 → AI 모델 예측
  - CSV 업로드 → 통계 계산
  - 관리자 Plotly 시각화
  - 챗봇 OpenAI API 연동
- Django
  - 업로드 기록, 챗봇 기록 저장
  - 관리자 페이지 (/admin)
  - 사용자 계정 관리 (FastAPI 인증과 별도)

## 참고
FastAPI Swagger: http://127.0.0.1:8000/docs
Django Admin: http://127.0.0.1:8001/admin