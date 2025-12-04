from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from io import BytesIO
import logging
import json
import datetime
from asgiref.sync import sync_to_async

from app.core.redis import redis_client_async
from app.tasks.csv_tasks import process_csv_task
from app.integrations.django_bridge import get_upload_record_model
from app.services.data_service import predict_image
from app.tasks.model_tasks import process_image_dataset_task
from app.core.s3_manager import s3_manager
from app.core.config import settings

router = APIRouter(prefix="/upload", tags=["upload"])
UploadRecord = get_upload_record_model()
logger = logging.getLogger(__name__)

# ----------------
# Response Models
# ----------------
class UploadResponse(BaseModel):
    filename: str
    uploaded_at: datetime.datetime
    file_size: int | None = None
    prediction: dict | None = None
    status: str | None = None

# ---------------------
# 이미지 데이터셋 업로드
# ---------------------
@router.post("/images_dataset", response_model=UploadResponse)
def upload_images_dataset(file: UploadFile = File(...)):
    # 대용량 이미지 압축 파일을 S3에 업로드하고, Celery에게 학습 데이터 처리 및 학습 작업을 위임.
    if not file.filename.lower().endswith(('.zip', '.tar', '.gz')):
        raise HTTPException(status_code=400, detail="압축 파일 형식(ZIP, TAR, GZ 등)만 지원됩니다.")

    try:
        # DB 레코드 생성 (상태: PENDING)
        record = UploadRecord.objects.create(
            filename=file.filename,
            file_size=0, # 파일 크기는 Celery가 S3에서 확인 후 업데이트
            status="PENDING_DATA_UPLOAD" # 학습 데이터 업로드 대기 상태
        )
        
        # FastAPI 메모리에 올리지 않고 S3의 'raw-datasets' 폴더로 스트리밍
        s3_key = s3_manager.upload_fileobj(file.file, settings.S3_RAW_DATASET_FOLDER, file.filename)

        # Celery Task에 S3 주소와 DB ID 전달
        # Celery Task는 압축 해제, 파일 정리, S3 재업로드, 학습 지시 등을 처리.
        process_image_dataset_task.apply_async((s3_key, record.id, file.filename))
        
        logger.info(f"이미지 데이터셋 S3 업로드 및 태스크 요청 완료: {s3_key}")
        return UploadResponse(filename=record.filename, uploaded_at=record.uploaded_at, status=record.status)
        
    except Exception as e:
        logger.exception("이미지 데이터셋 업로드 처리 오류")
        raise HTTPException(status_code=500, detail=str(e))

# -------------
# 이미지 업로드
# -------------
@router.post("/image", response_model=UploadResponse)
async def upload_image(file: UploadFile = File(...)):
    # 이미지 추론을 위한 단일 파일 처리.
    try:
        file_bytes = await file.read()
        file_size = len(file_bytes)
        result = predict_image(BytesIO(file_bytes))

        record = await sync_to_async(UploadRecord.objects.create)(
            filename=file.filename, file_size=file_size, prediction=result.get("prediction"), confidence=result.get("confidence")
        )
        await redis_client_async.set(f"image:{record.id}", json.dumps(result), ex=3600)

        return UploadResponse(
            filename=record.filename, uploaded_at=record.uploaded_at, file_size=record.file_size, prediction=result
        )

    except Exception as e:
        logger.exception("이미지 업로드 처리 오류")
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------
# CSV 업로드 (Celery 비동기)
# -------------------------
@router.post("/csv")
def upload_csv(file: UploadFile = File(...)):
    # S3로 스트리밍 업로드 후, Celery에게 처리(다운로드+분석)를 위임합니다.
    try:
        # DB 레코드 생성 (상태: PENDING)
        record = UploadRecord.objects.create(
            filename=file.filename,
            file_size=0, # 사이즈는 Celery가 S3에서 확인 후 업데이트
            status="PENDING"
        )

        # FastAPI 메모리에 다 올리지 않고 S3로 바로 보냄
        # file.file은 임시 파일 객체이므로 바로 boto3에 넘길 수 있음
        s3_key = s3_manager.upload_fileobj(file.file, settings.S3_RAW_FOLDER, file.filename)

        # Celery에는 거대한 파일 대신 'S3 주소(Key)'만 전달
        process_csv_task.apply_async((s3_key, file.filename, record.id))
        
        logger.info(f"CSV S3 업로드 및 태스크 요청 완료: {s3_key}")
        return {"record_id": record.id, "status": record.status}
        
    except Exception as e:
        logger.exception("CSV 업로드 처리 오류")
        raise HTTPException(status_code=500, detail=str(e))

# -------------
# CSV 기록 조회
# -------------
@router.get("/csv_record/{record_id}")
def get_csv_record(record_id: int):
    try:
        record = UploadRecord.objects.get(id=record_id)
        logger.info("CSV 기록 조회 결과")
        return {
            "record_id": record.id,
            "filename": record.filename,
            "file_size": record.file_size,
            "status": record.status,
            "statistics": record.statistics
        }
    except UploadRecord.DoesNotExist:
        raise HTTPException(status_code=404, detail="CSV record not found")