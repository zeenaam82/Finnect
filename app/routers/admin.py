from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from io import BytesIO
from pydantic import BaseModel
from app.services.data_service import process_csv
from app.services.csv_convert import convert_xlsx_to_csv
from app.core.security import require_admin
from app.integrations.django_bridge import get_upload_record_model, get_or_create_user_by_username

router = APIRouter(prefix="/admin/upload", tags=["admin_upload"])

class AdminCSVResponse(BaseModel):
    user: str
    statistics: dict

@router.post("/csv", response_model=AdminCSVResponse)
def admin_upload_csv(file: UploadFile = File(...), user=Depends(require_admin)):
    """
    관리자 전용 CSV 업로드 및 통계 처리
    """
    UploadRecord = get_upload_record_model()
    try:
        django_user = get_or_create_user_by_username(user.sub)
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
            raise HTTPException(status_code=400, detail="CSV 또는 XLSX만 허용")

        UploadRecord.objects.create(
            user=django_user,
            file_name=file.filename,
            file_type="csv",
            stats=stats
        )
        return {"user": user.sub, "statistics": stats}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
