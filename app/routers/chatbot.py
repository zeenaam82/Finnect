from fastapi import APIRouter, Form
from typing import Optional
from app.services.chatbot_service import get_chatbot_answer
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/chatbot/")
async def chatbot_endpoint(query: Optional[str] = Form(None)):
    logger.info(f"질문: {query}")
    answer = await get_chatbot_answer(query=query)
    logger.info(f"답변: {answer}")
    return {"answer": answer}
