from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from io import BytesIO
import logging
import json
from asgiref.sync import sync_to_async

from app.core.redis import redis_client_async
from app.tasks.csv_tasks import process_csv_task
from app.integrations.django_bridge import get_upload_record_model
from app.services.image_service import predict_image

router = APIRouter(prefix="/upload", tags=["upload"])
UploadRecord = get_upload_record_model()
logger = logging.getLogger(__name__)

# ----------------------------
# Response Models
# ----------------------------
class ImageUploadResponse(BaseModel):
    filename: str
    uploaded_at: str
    file_size: int
    prediction: dict | None = None

# -------------------
# 이미지 업로드 (동기)
# -------------------
@router.post("/image", response_model=ImageUploadResponse)
async def upload_image(file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()
        result = predict_image(BytesIO(file_bytes))

        # ORM 저장
        record = await sync_to_async(UploadRecord.objects.create)(
            filename=file.filename,
            file_size=len(file_bytes),
            prediction=result.get("prediction"),
            confidence=result.get("confidence")
        )

        # Redis 캐싱 (1시간)
        await redis_client_async.set(
            f"image:{record.id}",
            json.dumps(result),
            ex=3600
        )

        logger.info("이미지 업로드 완료")
        return {
            "filename": record.filename,
            "uploaded_at": record.uploaded_at.isoformat(),
            "file_size": record.file_size,
            "prediction": result
        }

    except Exception as e:
        logger.exception("이미지 업로드 처리 오류")
        raise HTTPException(status_code=500, detail=str(e))

# -------------------
# CSV 업로드 (Celery 비동기)
# -------------------
@router.post("/csv")
def upload_csv(file: UploadFile = File(...)):
    try:
        file_bytes = file.file.read()
        record = UploadRecord.objects.create(
            filename=file.filename,
            file_size=len(file_bytes),
            status="PENDING"
        )

        # Celery task 비동기 실행
        process_csv_task.apply_async((file_bytes, file.filename, record.id))
        logger.info("CSV 업로드 완료")
        return {"record_id": record.id, "status": record.status}
    except Exception as e:
        logger.exception("CSV 업로드 처리 오류")
        raise HTTPException(status_code=500, detail=str(e))

# -------------------
# CSV 기록 조회
# -------------------
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
