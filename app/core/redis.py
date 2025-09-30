import os
import redis
import redis.asyncio as aioredis

# -----------------------------
# 환경변수
# -----------------------------
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB   = int(os.getenv("REDIS_DB", 0))

# -----------------------------
# 동기 Redis (Celery / 동기 코드용)
# -----------------------------
redis_client_sync = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True
)

# -----------------------------
# 비동기 Redis (FastAPI / async 코드용)
# -----------------------------
redis_client_async = aioredis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True
)
