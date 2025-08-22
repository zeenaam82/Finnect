from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.data_service import predict_image, process_csv
from app.services.csv_convert import convert_xlsx_to_csv
from pydantic import BaseModel
from io import BytesIO
from app.integrations.django_bridge import get_upload_record_model

router = APIRouter(prefix="/upload", tags=["upload"])
UploadRecord = get_upload_record_model()

class ImageUploadResponse(BaseModel):
    filename: str
    uploaded_at: str
    file_size: int
    prediction: dict | None = None  # 예측 결과 optional

class CSVUploadResponse(BaseModel):
    filename: str
    uploaded_at: str
    file_size: int
    statistics: dict | None = None

@router.post("/image", response_model=ImageUploadResponse)
def upload_image(file: UploadFile = File(...)):
    try:
        file_bytes = file.file.read()
        result = predict_image(BytesIO(file_bytes))

        record = UploadRecord.objects.create(
            filename=file.filename,
            file_size=len(file_bytes)
        )

        return {
            "filename": record.filename,
            "uploaded_at": record.uploaded_at.isoformat(),
            "file_size": record.file_size,
            "prediction": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/csv", response_model=CSVUploadResponse)
def upload_csv(file: UploadFile = File(...)):
    try:
        filename = file.filename.lower()
        file_bytes = file.file.read()
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

        record = UploadRecord.objects.create(
            filename=file.filename,
            file_size=len(file_bytes)
        )

        return {
            "filename": record.filename,
            "uploaded_at": record.uploaded_at.isoformat(),
            "file_size": record.file_size,
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
