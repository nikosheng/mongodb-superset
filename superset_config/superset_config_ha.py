import os

from cachelib.redis import RedisCache


def env(name: str, default: str) -> str:
    return os.getenv(name, default)


SUPERSET_SECRET_KEY = env("SUPERSET_SECRET_KEY", "change_this_secret_for_enterprise")
SQLALCHEMY_DATABASE_URI = env(
    "SUPERSET_DATABASE_URI",
    "postgresql+psycopg2://superset:superset@postgres:5432/superset",
)
SQLALCHEMY_TRACK_MODIFICATIONS = False

REDIS_HOST = env("REDIS_HOST", "redis")
REDIS_PORT = int(env("REDIS_PORT", "6379"))
REDIS_CELERY_DB = int(env("REDIS_CELERY_DB", "0"))
REDIS_RESULTS_DB = int(env("REDIS_RESULTS_DB", "1"))
REDIS_CACHE_DB = int(env("REDIS_CACHE_DB", "2"))


class CeleryConfig:
    broker_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_CELERY_DB}"
    result_backend = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_RESULTS_DB}"
    imports = (
        "superset.sql_lab",
        "superset.tasks.scheduler",
        "superset.tasks.thumbnails",
        "superset.tasks.cache",
    )
    worker_prefetch_multiplier = 1
    task_acks_late = False
    beat_schedule = {
        "reports.scheduler": {
            "task": "reports.scheduler",
            "schedule": 60.0,
        },
        "reports.prune_log": {
            "task": "reports.prune_log",
            "schedule": 3600.0,
        },
    }


CELERY_CONFIG = CeleryConfig

RESULTS_BACKEND = RedisCache(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_RESULTS_DB,
    key_prefix="superset_results",
)

CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
    "CACHE_KEY_PREFIX": "superset_cache_",
    "CACHE_REDIS_HOST": REDIS_HOST,
    "CACHE_REDIS_PORT": REDIS_PORT,
    "CACHE_REDIS_DB": REDIS_CACHE_DB,
}

DATA_CACHE_CONFIG = CACHE_CONFIG

FEATURE_FLAGS = {
    "ALERT_REPORTS": True,
}

ENABLE_PROXY_FIX = True
PROXY_FIX_CONFIG = {
    "x_for": 1,
    "x_proto": 1,
    "x_host": 1,
    "x_port": 1,
    "x_prefix": 1,
}
