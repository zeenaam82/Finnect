from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app.core.security import get_current_user
from app.services.data_service import predict_image, process_csv
from app.services.csv_convert import convert_xlsx_to_csv
from pydantic import BaseModel
from io import BytesIO
from app.integrations.django_bridge import get_upload_record_model, get_or_create_user_by_username

router = APIRouter(prefix="/upload", tags=["upload"])
UploadRecord = get_upload_record_model()

class ImageUploadResponse(BaseModel):
    user: str
    prediction: str
    confidence: float

class CSVUploadResponse(BaseModel):
    user: str
    statistics: dict

@router.post("/image", response_model=ImageUploadResponse)
def upload_image(file: UploadFile = File(...), user=Depends(get_current_user)):
    try:
        image_bytes = file.file.read()
        result = predict_image(BytesIO(image_bytes))

        user_obj = get_or_create_user_by_username(user.sub)

        UploadRecord.objects.create(
            user=user_obj,
            file_type="image",
            file_name=file.filename,
            prediction=result
        )
        return {"user": user.sub, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/csv", response_model=CSVUploadResponse)
def upload_csv(file: UploadFile = File(...), user=Depends(get_current_user)):
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

        user_obj = get_or_create_user_by_username(user.sub)

        UploadRecord.objects.create(
            user=user_obj,
            file_type="csv",
            file_name=file.filename,
            statistics=stats
        )
        return {"user": user.sub, "statistics": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
