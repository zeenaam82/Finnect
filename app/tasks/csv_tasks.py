import json
from io import BytesIO
from celery import shared_task

from app.core.redis import redis_client_sync  # 동기 Redis
from app.services.csv_convert import convert_xlsx_to_csv
from app.services.data_service import process_csv
from app.integrations.django_bridge import get_upload_record_model

UploadRecord = get_upload_record_model()

@shared_task(bind=True)
def process_csv_task(self, file_bytes: bytes, filename: str, record_id: int):
    record = UploadRecord.objects.get(id=record_id)
    cache_key = f"csv_file:{filename}"

    try:
        # 1. Redis 캐시 확인
        cached_stats = redis_client_sync.get(cache_key)
        if cached_stats:
            stats = json.loads(cached_stats)
            record.statistics = cached_stats
            record.status = "SUCCESS"
            record.save()
            return {"record_id": record.id, "statistics": stats, "source": "redis"}

        # 2. CSV 처리
        file_obj = BytesIO(file_bytes)
        if filename.endswith(".xlsx"):
            csv_file = convert_xlsx_to_csv(file_obj)
            stats = process_csv(csv_file)
        else:
            stats = process_csv(file_obj)

        stats_json = json.dumps(stats)

        # 3. DB 저장
        record.statistics = stats_json
        record.status = "SUCCESS"
        record.save()

        # 4. Redis 저장 (1시간 TTL)
        redis_client_sync.set(cache_key, stats_json, ex=3600)
        for col, value in stats.items():
            redis_client_sync.set(f"csv_col:{col}", value, ex=3600)

        return {"record_id": record.id, "statistics": stats, "source": "db"}

    except Exception as e:
        record.status = "FAILURE"
        record.statistics = json.dumps({"error": str(e)})
        record.save()
        return {"error": str(e)}
