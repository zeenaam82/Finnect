from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional
from app.services.chatbot_service import get_chatbot_answer

router = APIRouter()

@router.post("/chatbot/")
async def chatbot_endpoint(
    query: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    # 파일이 선택되지 않았거나 빈 파일("")이면 None 처리
    if file and getattr(file, "filename", "") == "":
        file = None

    # 디버깅용 로그
    print("endpoint query:", query)
    print("endpoint file 타입:", type(file), "값:", file)

    answer = await get_chatbot_answer(query=query, file=file)

    print("최종 답변:", answer)
    return {"answer": answer}
