# Finnect

Finnect는 **FastAPI**와 **Django**를 연동하여 내부 고객 지원 챗봇과 이미지/CSV 업로드 분석 기능을 제공하는 프로젝트입니다.  
FastAPI는 API 서버 및 JWT 인증을 담당하며, Django는 업로드 기록과 챗봇 기록 저장 및 관리자용 UI를 제공합니다.

---

## 프로젝트 주요 개선 내용

이 버전은 대용량 파일 처리 및 AI 모델 학습 과정을 개선하여 안정성과 확장성을 확보했습니다.

* **S3 기반 데이터 파이프라인 구축:** 이미지 추론 모델, 학습 데이터셋, 분석 결과를 Amazon S3에서 관리합니다.
* **Celery 기반 모델 학습 시스템:**
    * S3에 저장된 MVTec AD 데이터셋을 Celery Worker가 로컬 임시 폴더로 다운로드하여 TensorFlow 모델을 학습합니다.
    * 학습된 모델은 ONNX 형식으로 변환되어 다시 S3에 저장됩니다.
* **메모리 효율성 향상:** TensorFlow가 S3를 직접 접근할 때 발생하는 문제를 해결하고, Docker Compose에서 Celery Worker의 메모리 할당량을 명시적으로 설정하여 Out Of Memory (OOM) 오류를 방지했습니다.

---

## 기능

### 1. 사용자 인증
-   FastAPI JWT 기반 로그인
-   관리자/일반 사용자 권한 구분
-   OAuth2PasswordRequestForm 기반 토큰 발급

### 2. 파일 업로드 및 분석
-   **이미지 업로드**
    -   ONNX 모델 기반 AI 추론 (모델은 S3에서 로드)
    -   예측 결과 및 신뢰도 반환
    -   Redis 캐싱 지원
-   **CSV/XLSX 업로드**
    -   Dask 기반 대용량 CSV 처리
    -   Celery 기반 비동기 처리 적용
    -   Redis에 통계값 캐싱 및 관리자 대시보드 연동

### 3. 챗봇
-   FastAPI 챗봇 엔드포인트 `/chatbot/`
-   Intent 기반 응답 및 FAQ 참조
-   최신 업로드 CSV/이미지 결과 활용
-   Redis 캐싱으로 응답 속도 향상

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

## 설치 및 환경 설정 (Docker 기반)

프로젝트는 Docker Compose를 사용하여 모든 서비스를 통합 실행합니다.

### 1. 환경 준비

1.  Python 3.11 이상 및 Docker 설치 필수
2.  **`.env` 파일 생성 및 설정**
    * 프로젝트 루트 디렉터리에 `.env` 파일을 생성하고 필수 값을 입력합니다.

| 환경 변수 | 설명 |
| :--- | :--- |
| `SECRET_KEY` | JWT/FastAPI 보안 키 |
| `POSTGRES_DB` / `USER` / `PASSWORD` | PostgreSQL 접속 정보 |
| `DJANGO_SECRET_KEY` | Django 보안 키 |
| `OPENAI_API_KEY` | 챗봇용 OpenAI 키 |
| `BUCKET_NAME` | AWS S3 버킷 이름 (필수) |
| **`AWS_ACCESS_KEY`** | **AWS 인증 Access Key** |
| **`AWS_SECRET_KEY`** | **AWS 인증 Secret Key** |
| `RAW_DATASET_FOLDER` | S3 원본 데이터셋 루트 폴더 이름 (예: `data`) |
| `TRAINING_DATA_FOLDER` | S3 학습 데이터 폴더 이름 (예: `train`) |
| `RAW_FOLDER` | S3 업로드 원본 폴더 (예: `uploads/raw`) |
| `PROCESSED_FOLDER` | S3 처리 완료 폴더 (예: `uploads/processed`) |


3.  **Docker 이미지 빌드**
    ```bash
    docker-compose build
    ```

### 2. 서비스 실행 및 초기화 (실행 순서)

1.  **컨테이너 실행**
    * DB, Redis, API, Worker 컨테이너를 모두 띄웁니다.
    ```bash
    docker-compose up -d
    ```

2.  **Django 마이그레이션 (API 컨테이너 내부)**
    ```bash
    docker exec -it finnect_api python backend/manage.py migrate
    ```

3.  **초기화 스크립트 실행 (Worker 컨테이너 내부)**
    * Worker 컨테이너에 접속하여 초기 데이터 설정 및 모델 학습을 실행합니다.
    ```bash
    # Worker 컨테이너 접속
    docker exec -it celery_worker /bin/bash

    # 1. 인텐트 및 테스트 유저 생성 (관리자 계정 포함)
    python scripts/init_intents.py
    python scripts/create_test_users.py

    # 2. AI 모델 학습 및 ONNX 변환 (S3 데이터 사용)
    # Warning: 이 스크립트는 S3 데이터를 다운로드하므로 시간이 소요됩니다.
    python scripts/train_and_convert.py

    # 컨테이너에서 나옴
    exit
    ```

---

## 챗봇 API 인텐트 매핑
챗봇에서 사용자가 입력하는 자연어 질문과 내부 데이터 필드 매핑:  

Image
| 사용자 입력 | 내부 필드 |
| :--- | :--- |
| 이미지상태 | prediction |
| 신뢰도     | confidence |

CSV
| 사용자 입력 | 내부 필드 |
| :--- | :--- |
| 총매출     | total_revenue |
| 고객수     | num_customers |
| 인보이스수 | num_invoices |
| 총수량     | total_quantity |

---

## 참고
> FastAPI Swagger: http://13.124.90.238:8000/docs  
> Django Admin: http://13.124.90.238:8001/admin (메모리 부족으로 EC2 무료 프리티어 환경에서는 실행되지 않음)  
> 현재 서비스는 무료 프리티어 환경에서 운영 중이며, 다수 동시 접속 또는 대용량 요청 시 지연이나 오류가 발생할 수 있음.
> 로컬 개발용 docker-compose를 그대로 사용했으며, 배포용으로는 보안·네트워크 설정을 추가할 수 있음.
> Celery worker를 통해 CSV 업로드 처리 속도가 개선됨. (EC2 무료 프리티어에서는 메모리 부족으로 Celery worker 미실행)
> 현재 모델 학습 및 Celery 비동기 처리 과정은 TensorFlow와 S3 파일 다운로드로 인해 **상당한 메모리(RAM)를 요구**합니다.
> **EC2 무료 프리티어 환경(1GB RAM)**에서는 Celery Worker가 메모리 부족으로 인해 **`SIGKILL` 오류로 강제 종료**되므로, 개선된 시스템을 실행할 수 없습니다.
> 로컬 환경에서 실행하는 경우, `docker-compose.yml` 파일에서 `worker` 서비스에 **최소 8GB 이상(`8192m`)**의 메모리 제한(`deploy.resources.limits.memory`)을 명시적으로 설정해야 안정적으로 동작합니다.