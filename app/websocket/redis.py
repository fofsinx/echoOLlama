# websocket/redis.py
import redis

redis_client = redis.Redis(host="localhost", port=6379, db=0)