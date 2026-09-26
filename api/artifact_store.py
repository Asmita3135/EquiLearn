import os
import socket
from pathlib import Path
from urllib.parse import urlparse

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────
S3_ENDPOINT  = os.getenv("S3_ENDPOINT",  "http://localhost:9000")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minioadmin")
S3_BUCKET    = os.getenv("S3_BUCKET",    "equilearn-artifacts")

# Explicit in-memory mock for unit tests
MOCK_S3 = os.getenv("MOCK_S3", "0") == "1"

# Local filesystem fallback directory (used when S3/MinIO is unreachable)
_DEFAULT_LOCAL_DIR = Path(__file__).resolve().parents[1] / ".artifacts"
LOCAL_ARTIFACT_DIR = Path(os.getenv("LOCAL_ARTIFACT_DIR", str(_DEFAULT_LOCAL_DIR)))


# ──────────────────────────────────────────────────────────────────────────────
# Broker / endpoint reachability probe
# ──────────────────────────────────────────────────────────────────────────────
def _is_s3_available(endpoint: str, timeout: float = 0.5) -> bool:
    """Return True only if the S3/MinIO TCP port is reachable."""
    try:
        parsed = urlparse(endpoint)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 9000
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


# Decide backend once at import time.
#   1. MOCK_S3=1          → in-memory dict   (tests)
#   2. S3 reachable       → real boto3/MinIO
#   3. Otherwise          → local filesystem  (local dev without MinIO)
_S3_AVAILABLE = (not MOCK_S3) and _is_s3_available(S3_ENDPOINT)
_USE_LOCAL    = (not MOCK_S3) and (not _S3_AVAILABLE)

if _USE_LOCAL:
    LOCAL_ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


# ──────────────────────────────────────────────────────────────────────────────
# In-memory store (MOCK_S3 mode)
# ──────────────────────────────────────────────────────────────────────────────
_mock_store: dict = {}


def clear_mock_store() -> None:
    global _mock_store
    _mock_store = {}


# ──────────────────────────────────────────────────────────────────────────────
# S3 / MinIO helpers
# ──────────────────────────────────────────────────────────────────────────────
def get_s3_client():
    import boto3
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        region_name="us-east-1",
    )


def init_bucket() -> None:
    if MOCK_S3 or _USE_LOCAL:
        return
    from botocore.exceptions import ClientError
    client = get_s3_client()
    try:
        client.head_bucket(Bucket=S3_BUCKET)
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            client.create_bucket(Bucket=S3_BUCKET)


# ──────────────────────────────────────────────────────────────────────────────
# Public API – save / get artifacts
# ──────────────────────────────────────────────────────────────────────────────
def save_artifact(
    job_id: str,
    artifact_type: str,
    content: bytes,
    content_type: str = "application/octet-stream",
) -> None:
    key = f"{job_id}/{artifact_type}"

    if MOCK_S3:
        _mock_store[key] = (content, content_type)
        return

    if _USE_LOCAL:
        dest = LOCAL_ARTIFACT_DIR / job_id
        dest.mkdir(parents=True, exist_ok=True)
        (dest / artifact_type).write_bytes(content)
        # Store content-type alongside
        (dest / f"{artifact_type}.ct").write_text(content_type, encoding="utf-8")
        return

    # Real S3/MinIO
    client = get_s3_client()
    client.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=content,
        ContentType=content_type,
    )


def get_artifact(job_id: str, artifact_type: str) -> tuple:
    """Returns (content_bytes, content_type). Returns (None, None) if not found."""
    key = f"{job_id}/{artifact_type}"

    if MOCK_S3:
        return _mock_store.get(key, (None, None))

    if _USE_LOCAL:
        artifact_file = LOCAL_ARTIFACT_DIR / job_id / artifact_type
        ct_file       = LOCAL_ARTIFACT_DIR / job_id / f"{artifact_type}.ct"
        if not artifact_file.exists():
            return None, None
        content      = artifact_file.read_bytes()
        content_type = ct_file.read_text(encoding="utf-8") if ct_file.exists() else "application/octet-stream"
        return content, content_type

    # Real S3/MinIO
    from botocore.exceptions import ClientError
    client = get_s3_client()
    try:
        response = client.get_object(Bucket=S3_BUCKET, Key=key)
        return response["Body"].read(), response["ContentType"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            return None, None
        raise
