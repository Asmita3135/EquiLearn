import sys
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

# Add M3 path to import existing dataclasses
_curr = Path(__file__).resolve()
_backend_dir = next((str(_p) for _p in [_curr] + list(_curr.parents) if _p.name == "backend" and _p.is_dir()), None)
if _backend_dir and _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

M3_PATH = next((str(_p / "Equilearn3" / "nlp") for _p in [_curr] + list(_curr.parents) if (_p / "Equilearn3" / "nlp").is_dir()), str((_curr.parent.parent / "Equilearn3" / "nlp").resolve()))
if M3_PATH not in sys.path:
    sys.path.insert(0, M3_PATH)

from input_integration import Member1Input, Member2Input, TimestampedSegment

@dataclass
class IntegrationContract:
    """
    Shared integration contract for EquiLearn.
    Acts as the main payload structure for the Integration Adapter.
    """
    job_id: str
    input_type: str
    raw_text: Optional[str] = None
    
    # Existing M1/M2 structures preserved
    m1_data: Optional[Member1Input] = None
    m2_data: Optional[Member2Input] = None
    
    # Additional extended fields required by the contract
    ocr_metadata_confidence: Optional[Dict[str, Any]] = None
    alt_text: Optional[str] = None
    vtt: Optional[str] = None
    source_metadata: Optional[Dict[str, Any]] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    # ---------------------------------------------------------
    # Helper Properties to directly access fields required by spec
    # ---------------------------------------------------------
    @property
    def ocr_text(self) -> Optional[str]:
        return self.m1_data.ocr_text if self.m1_data else None

    @property
    def visual_description(self) -> Optional[str]:
        return self.m1_data.visual_description if self.m1_data else None

    @property
    def transcript(self) -> Optional[str]:
        return self.m2_data.transcript if self.m2_data else None

    @property
    def timestamps(self) -> Optional[List[TimestampedSegment]]:
        return self.m2_data.segments if self.m2_data else None
