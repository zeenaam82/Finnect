from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from io import BytesIO
import json
import logging

from app.services.data_service import predict_image, process_csv
from app.services.csv_convert import convert_xlsx_to_csv
from app.integrations.django_bridge import get_upload_record_model
from app.core.redis import redis_client
from asgiref.sync import sync_to_async

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

class CSVUploadResponse(BaseModel):
    filename: str
    uploaded_at: str
    file_size: int
    statistics: dict | None = None

# ----------------------------
# Image Upload Endpoint
# ----------------------------
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
        await redis_client.set(
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

# ----------------------------
# CSV Upload Endpoint
# ----------------------------
@router.post("/csv", response_model=CSVUploadResponse)
async def upload_csv(file: UploadFile = File(...)):
    try:
        filename = file.filename.lower()
        file_bytes = await file.read()
        file_obj = BytesIO(file_bytes)

        if filename.endswith(".xlsx"):
            file_obj.seek(0)
            csv_file = convert_xlsx_to_csv(file_obj)
            stats = process_csv(csv_file)
        elif filename.endswith(".csv"):
            file_obj.seek(0)
            stats = process_csv(file_obj)
        else:
            raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식")

        # sync_to_async로 ORM 호출
        record = await sync_to_async(UploadRecord.objects.create)(
            filename=file.filename,
            file_size=len(file_bytes),
            statistics=stats
        )

        # Redis에 컬럼명 기준으로 저장 (1시간)
        for col, value in stats.items():
            await redis_client.set(f"csv_col:{col}", value, ex=3600)

        logger.info("CSV 업로드 완료")
        return {
            "filename": record.filename,
            "uploaded_at": record.uploaded_at.isoformat(),
            "file_size": record.file_size,
            "statistics": stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
