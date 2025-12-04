from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routers import auth, upload, chatbot, admin_plotly, admin_dashboard, train
from app.services.data_service import initialize_onnx
from dotenv import load_dotenv
import uvicorn

# lifespan 컨텍스트 매니저
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 앱 시작 시 실행
    load_dotenv()
    initialize_onnx()
    yield

app = FastAPI(
    title="Finnect AI API",
    description="AI 이미지/CSV 분석 + 챗봇 통합 서비스",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    lifespan=lifespan,
    servers=[{"url": "/"}],
)


# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(chatbot.router)
app.include_router(train.router)
app.include_router(admin_plotly.router)
app.include_router(admin_dashboard.router)

@app.get("/")
def root():
    return {"message": "Finnect AI API 서비스입니다."}

# python -m app.main
# if __name__ == "__main__":
#     uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
