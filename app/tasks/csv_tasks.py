import json
from celery import shared_task

from app.core.redis import redis_client_sync  # 동기 Redis
from app.services.csv_convert import convert_xlsx_to_csv
from app.services.data_service import process_csv
from app.integrations.django_bridge import get_upload_record_model
from app.core.s3_manager import s3_manager

UploadRecord = get_upload_record_model()

@shared_task(bind=True)
def process_csv_task(self, s3_key: bytes, filename: str, record_id: int):
    record = UploadRecord.objects.get(id=record_id)
    cache_key = f"csv_file:{filename}"

    try:
        # Redis 캐시 확인
        cached_stats = redis_client_sync.get(cache_key)
        if cached_stats:
            stats = json.loads(cached_stats)
            record.statistics = cached_stats
            record.status = "SUCCESS"
            record.save()
            return {"record_id": record.id, "statistics": stats, "source": "redis"}
        
        # S3에서 파일 다운로드 (Worker 메모리로 로드)
        file_obj = s3_manager.read_file(s3_key)

        # 파일 사이즈 업데이트
        file_size = file_obj.getbuffer().nbytes
        record.file_size = file_size
        record.save()

        # CSV 처리
        if filename.lower().endswith(".xlsx"):
            csv_file = convert_xlsx_to_csv(file_obj)
            stats = process_csv(csv_file)
        else:
            stats = process_csv(file_obj)

        stats_json = json.dumps(stats)

        # DB 저장
        record.statistics = stats_json
        record.status = "SUCCESS"
        record.save()

        # Redis 저장 (1시간 TTL)
        redis_client_sync.set(cache_key, stats_json, ex=3600)
        for col, value in stats.items():
            redis_client_sync.set(f"csv_col:{col}", value, ex=3600)

        return {"record_id": record.id, "statistics": stats, "source": "db"}

    except Exception as e:
        record.status = "FAILURE"
        record.statistics = json.dumps({"error": str(e)})
        record.save()
        return {"error": str(e)}
