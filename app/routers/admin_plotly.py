from fastapi import APIRouter, Depends
import plotly.express as px
import pandas as pd
from app.core.security import require_admin
from app.services.data_service import get_latest_csv_stats

router = APIRouter(prefix="/admin/plotly", tags=["admin_plotly"])

@router.get("/defect_distribution")
def defect_distribution(user=Depends(require_admin)):
    """
    관리자용 불량률 분포 Plotly 시각화
    """
    stats = get_latest_csv_stats()
    if not stats:
        return {"error": "업로드된 CSV 통계가 없습니다."}

    df = pd.DataFrame({
        "category": ["normal", "defect"],
        "count": [
            stats.get("num_invoices", 0) - stats.get("total_quantity", 0),
            stats.get("total_quantity", 0)
        ]
    })
    fig = px.pie(df, names="category", values="count", title="불량률 분포")
    return fig.to_json()
