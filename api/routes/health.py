"""
Health check routes – no AI processing, no heavy imports.
"""
import sys
from fastapi import APIRouter
from api.schemas import HealthResponse, ComponentStatus, ModelsHealthResponse

router = APIRouter()

from pathlib import Path

_curr = Path(__file__).resolve()
_backend_dir = next((str(_p) for _p in [_curr] + list(_curr.parents) if _p.name == "backend" and _p.is_dir()), None)
if _backend_dir and _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

M3_PATH = next((str(_p / "Equilearn3" / "nlp") for _p in [_curr] + list(_curr.parents) if (_p / "Equilearn3" / "nlp").is_dir()), str((_curr.parents[3] / "Equilearn3" / "nlp").resolve()))
M1_PATH = next((str(_p / "Equilearn2" / "EquiLearn-member-1") for _p in [_curr] + list(_curr.parents) if (_p / "Equilearn2" / "EquiLearn-member-1").is_dir()), None)
if M1_PATH and M1_PATH not in sys.path:
    sys.path.insert(0, M1_PATH)

M2_PATH = next((str(_p / "Equilearn1" / "EquiLearn-member-2") for _p in [_curr] + list(_curr.parents) if (_p / "Equilearn1" / "EquiLearn-member-2").is_dir()), None)
if M2_PATH and M2_PATH not in sys.path:
    sys.path.insert(0, M2_PATH)

# --------------------------------------------------------------------------- #
# GET /api/v1/health
# --------------------------------------------------------------------------- #
@router.get("/health", response_model=HealthResponse, tags=["Health"])
def service_health():
    """Returns the overall service status. Lightweight – no inference."""
    return HealthResponse(
        status="ok",
        service="EquiLearn Backend",
        version="1.0.0",
    )


# --------------------------------------------------------------------------- #
# GET /api/v1/models/health
# --------------------------------------------------------------------------- #
@router.get("/models/health", response_model=ModelsHealthResponse, tags=["Health"])
def models_health():
    """
    Reports availability of M1, M2 and M3 components.
    Checks by importing the relevant modules – does NOT run inference.
    """
    components: list[ComponentStatus] = []

    # --- M3 check: import core M3 modules from the nlp directory ---
    if M3_PATH not in sys.path:
        sys.path.insert(0, M3_PATH)

    for name, module_path in [
        ("M3 (NLP/Accessibility)", "main_pipeline"),
        ("M3 – LLM Processor",    "llm_processing"),
        ("M3 – Text Analysis",    "text_analysis"),
        ("M3 – Accessibility Rules", "accessibility_rules"),
    ]:
        try:
            __import__(module_path)
            components.append(ComponentStatus(name=name, status="available"))
        except Exception as exc:
            components.append(ComponentStatus(name=name, status="unavailable", detail=str(exc)))

    # --- Integration layer checks ---
    for name, module in [
        ("Integration Adapter", "integration_adapter"),
        ("Orchestrator",        "orchestrator"),
        ("Package Builder",     "package_builder"),
    ]:
        try:
            __import__(module)
            components.append(ComponentStatus(name=name, status="available"))
        except Exception as exc:
            components.append(ComponentStatus(name=name, status="unavailable", detail=str(exc)))

    # --- M1 / M2 real pipeline connector checks ---
    for name, module in [
        ("M1 (Computer Vision / OCR)", "equilearn.vision.pipeline"),
        ("M2 (Speech-to-Text)",        "audio_speech.src.audio_extractor"),
    ]:
        try:
            __import__(module)
            components.append(ComponentStatus(name=name, status="available"))
        except Exception as exc:
            components.append(ComponentStatus(name=name, status="unavailable", detail=str(exc)))

    any_unavailable = any(c.status == "unavailable" for c in components)
    overall = "degraded" if any_unavailable else "healthy"

    return ModelsHealthResponse(overall=overall, components=components)
