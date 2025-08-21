from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, upload, chatbot, admin_plotly

app = FastAPI(
    title="Finnect AI API",
    description="AI 이미지/CSV 분석 + 챗봇 통합 서비스",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs"  # Swagger UI
)

# CORS 설정 예시
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
app.include_router(admin_plotly.router)

@app.get("/")
def root():
    return {"message": "Finnect AI API 서비스입니다."}

# python -m app.main
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)