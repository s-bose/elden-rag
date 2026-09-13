from enum import Enum


class RedisKey(Enum):
    SEEN = "run:{run_id}:seen:{category}"
    DONE = "run:{run_id}:done"
    FAILED = "run:{run_id}:failed"

    def __call__(self, **kwargs: object) -> str:
        return self.value.format(**kwargs)
