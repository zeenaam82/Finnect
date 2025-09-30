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
  - Celery 기반 비동기 처리 적용
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
   - 링크: [MVTec AD Dataset](https://www.mvtec.com/downloads)
   
2. **Kaggle Customer Segmentation Dataset**
   - 고객 세분화 및 CSV 통계 예제용
   - 링크: [Customer Segmentation Dataset](https://www.kaggle.com/datasets/yasserh/customer-segmentation-dataset)

> 데이터셋은 `data/` 폴더에 위치시켜야 합니다.

---

## 설치 및 환경 설정

1. Python 3.11 이상 권장
2. 가상환경 생성
```bash
python3 -m venv venv
source venv/Scripts/activate  # Windows
source venv/bin/activate     # Linux / Mac
```
3. 의존성 설치 및 실행
```bash
docker build -t finnect .        # Docker 이미지 빌드
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
# JWT / FastAPI
SECRET_KEY=your_jwt_secret
# PostgreSQL
POSTGRES_DB=finnect_db
POSTGRES_USER=finnect_user
POSTGRES_PASSWORD=finnect_pass
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/dbname
# Django
DJANGO_SECRET_KEY=django_secret
# OpenAI
OPENAI_API_KEY=your_openai_key
```
6. AI 모델 학습 및 ONNX 변환, 인텐트 초기화, 테스트 유저 추가
```bash
cd scripts
python train_and_convert.py
python init_intents.py
python create_test_users.py
```
7. 서버 실행
```bash
docker-compose up --build  # 컨테이너 실행
```

---

## 챗봇 API 인텐트 매핑
챗봇에서 사용자가 입력하는 자연어 질문과 내부 데이터 필드 매핑:  

Image
| 사용자 입력 | 내부 필드 |
|------------|-----------|
| 이미지상태 | prediction |
| 신뢰도     | confidence |

CSV
| 사용자 입력 | 내부 필드 |
|------------|-----------|
| 총매출     | total_revenue |
| 고객수     | num_customers |
| 인보이스수 | num_invoices |
| 총수량     | total_quantity |

---

## 참고
> FastAPI Swagger: http://13.124.90.238:8000/docs  
> Django Admin: http://13.124.90.238:8001/admin (메모리 부족으로 EC2 무료 프리티어 환경에서는 실행되지 않음)  
> 현재 서비스는 무료 프리티어 환경에서 운영 중이며, 다수 동시 접속 또는 대용량 요청 시 지연이나 오류가 발생할 수 있습니다.
> Celery worker를 통해 CSV 업로드 처리 속도가 개선됨. (EC2 무료 프리티어에서는 메모리 부족으로 Celery worker 미실행)