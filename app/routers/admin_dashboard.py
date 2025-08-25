from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/admin", tags=["admin_dashboard"])
templates = Jinja2Templates(directory="app/templates")  # templates 폴더 경로

@router.get("/dashboard/", response_class=HTMLResponse)
def dashboard(request: Request):
    """
    JWT 없이 HTML만 렌더링
    Plotly 데이터는 JS에서 API 호출
    """
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})
