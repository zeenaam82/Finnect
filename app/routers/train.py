from fastapi import APIRouter, HTTPException
import logging

from app.tasks.model_tasks import trigger_training_task 

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/train", tags=["training"])


@router.post("/start")
def start_model_training(category: str):
    if not category:
        # 카테고리가 없으면 400 Bad Request 응답
        raise HTTPException(status_code=400, detail="학습할 카테고리 이름을 지정해야 합니다.")

    try:
        # Celery Task에 학습할 카테고리 이름을 인자로 전달하여 비동기 실행
        result = trigger_training_task.apply_async((category,)) 
        
        logger.info(f"학습 태스크 요청 완료. Category: {category}, Task ID: {result.id}")
        
        # FastAPI는 즉시 응답을 반환하여 블로킹을 방지합니다.
        return {
            "message": f"'{category}' 모델 학습이 백그라운드에서 시작되었습니다.",
            "task_id": result.id,
            "status": "PENDING"
        }

    except Exception as e:
        logger.error(f"학습 시작 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail="모델 학습 태스크 시작에 실패했습니다.")