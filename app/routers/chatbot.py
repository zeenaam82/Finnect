from fastapi import APIRouter, Depends, UploadFile, Form, File
from typing import Optional
from app.schemas.chatbot import ChatbotResponse
from app.services.chatbot_service import get_chatbot_answer
from app.core.security import get_current_user

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

@router.post("/", response_model=ChatbotResponse)
async def chatbot(
    query: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    user=Depends(get_current_user)
):
    try:
        file_bytes = image.file if image else None
        answer = get_chatbot_answer(query or "", file_bytes, user_email=user.sub)
        return ChatbotResponse(answer=answer)
    except Exception as e:
        return ChatbotResponse(answer=f"오류 발생: {e}")
