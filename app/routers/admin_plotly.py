from fastapi import APIRouter, Depends
from app.core.security import require_admin
from app.services.data_service import get_latest_csv_stats
from app.services.plotly_service import create_defect_pie
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/admin/plotly", tags=["admin_plotly"])

@router.get("/defect_distribution")
def defect_distribution(user=Depends(require_admin)):
    stats = get_latest_csv_stats()
    fig = create_defect_pie(stats)
    if not fig:
        return {"error": "업로드된 CSV 통계가 없습니다."}
    return JSONResponse(content=fig.to_dict())
