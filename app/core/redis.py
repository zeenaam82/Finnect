import redis.asyncio as redis

# 전역 Redis 클라이언트
redis_client = redis.Redis(
    host="localhost",   
    port=6379,
    db=0,
    decode_responses=True 
)

# docker exec -it redis redis-cli
# docker run -d -p 6379:6379 redis