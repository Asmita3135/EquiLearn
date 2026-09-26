import os
import socket
from urllib.parse import urlparse
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# For testing, we can inject CELERY_ALWAYS_EAGER=1 via env variables.
CELERY_ALWAYS_EAGER = os.getenv("CELERY_ALWAYS_EAGER", "0") == "1"


def _is_broker_available(broker_url: str, timeout: float = 0.5) -> bool:
    """
    Probe whether the Celery broker is reachable within `timeout` seconds.
    Returns False on any error (connection refused, timeout, parse error).
    """
    try:
        parsed = urlparse(broker_url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 6379
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


# Auto-detect: if the env flag isn't set AND the broker is unreachable,
# fall back to eager (synchronous inline) execution so POST /api/v1/jobs
# never hangs waiting for a broker that isn't running.
if not CELERY_ALWAYS_EAGER:
    CELERY_ALWAYS_EAGER = not _is_broker_available(REDIS_URL)

celery_app = Celery(
    "equilearn_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["worker.tasks"],
)

celery_app.conf.update(
    task_always_eager=CELERY_ALWAYS_EAGER,
    task_eager_propagates=CELERY_ALWAYS_EAGER,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
