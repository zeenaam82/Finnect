# Finnect

Finnect는 **FastAPI**와 **Django**를 연동하여 내부 고객 지원 챗봇과 이미지/CSV 업로드 분석 기능을 제공하는 프로젝트입니다.  
FastAPI는 API 서버 및 JWT 인증을 담당하며, Django는 업로드 기록과 챗봇 기록 저장 및 관리자용 UI를 제공합니다.

---

## 기능
### 1. 사용자 인증
- FastAPI JWT 기반 로그인
- 관리자/일반 사용자 권한 구분
- OAuth2PasswordRequestForm 기반 토큰 발급

### 2. 파일 업로드 및 분석
- **이미지 업로드**
  - ONNX 모델 기반 AI 추론
  - 예측 결과 및 신뢰도 반환
  - Redis 캐싱 지원
- **CSV/XLSX 업로드**
  - Dask 기반 대용량 CSV 처리
  - 주요 통계(METRICS) 자동 계산: 총매출, 고객 수, 인보이스 수, 총수량 등
  - Redis에 통계값 캐싱
  - 관리자 대시보드 연동

### 3. 챗봇
- FastAPI 챗봇 엔드포인트 `/chatbot/`
- Intent 기반 응답 및 FAQ 참조
- 최신 업로드 CSV/이미지 결과 활용
- Redis 캐싱으로 응답 속도 향상

### 4. 관리자 대시보드
- HTML 기반 대시보드 렌더링
- Plotly 차트로 CSV 분석 통계 시각화
- JWT 로그인 후 차트 데이터 조회
- Django Admin과 연동하여 업로드 기록, FAQ, Intent 관리

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
3. 의존성 설치
```bash
pip install --upgrade pip
pip install -r requirements.txt
```
4. Django 마이그레이션
```bash
cd backend
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 8001
```
5. 환경 변수 설정
.env 파일 생성 후 필수 값 입력:
```bash
SECRET_KEY=your_jwt_secret
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/dbname
OPENAI_API_KEY=your_openai_key
POSTGRES_DB=finnect_db
POSTGRES_USER=finnect_user
POSTGRES_PASSWORD=finnect_pass
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DJANGO_SECRET_KEY=django_secret
```
6. AI 모델 학습 및 ONNX 변환 및 인텐트 초기화
```bash
cd scripts
python train_and_convert.py
python init_intents.py
python create_test_users.py
```
7. FastAPI 실행
```bash
python -m main:app
```

---

## 참고
FastAPI Swagger: http://127.0.0.1:8000/docs
Django Admin: http://127.0.0.1:8001/admin