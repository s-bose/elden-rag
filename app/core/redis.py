from typing import cast

from redis import Redis

from app.core.config import settings


class RedisClient:
    _instance: "RedisClient | None" = None
    _client: Redis

    def __new__(cls) -> "RedisClient":
        if cls._instance is None:
            instance = super().__new__(cls)
            instance._client = Redis.from_url(settings.redis_url, decode_responses=True)
            cls._instance = instance
        return cls._instance

    def add_to_set(self, key: str, value: str, ttl: int | None = None) -> bool:
        added = bool(self._client.sadd(key, value))
        if ttl is not None:
            self._client.expire(key, ttl)
        return added

    def is_member(self, key: str, value: str) -> bool:
        return bool(self._client.sismember(key, value))

    def members(self, key: str) -> set[str]:
        return cast(set[str], self._client.smembers(key))

    def remove_from_set(self, key: str, value: str) -> None:
        self._client.srem(key, value)


redis_client = RedisClient()
