"""
M1-STAGE 5 — Alt-Text & Diagram Understanding Implementation
Combines OCR text labels with VLM visual relationships to generate accessible, screen-reader-friendly descriptions.
Pipeline Flow: OCR + VLM + Context → Alt-Text & Diagram Explanation
"""

from typing import Dict, Any, List, Optional, Union
from equilearn.core.schemas import OCRResult, VLMResult, OCRWord


class AltTextGenerator:
    """Class for generating structured accessibility alt-text and diagram explanations."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}

    def _extract_key_ocr_labels(self, ocr_result: Optional[OCRResult], max_labels: int = 8) -> List[str]:
        """Extracts unique, clean text labels from OCR blocks avoiding raw text dumps."""
        if not ocr_result or not ocr_result.text.strip():
            return []

        labels: List[str] = []
        seen = set()

        if ocr_result.blocks:
            for block in ocr_result.blocks:
                txt = block.text.strip()
                if txt and len(txt) > 1 and txt.lower() not in seen:
                    labels.append(txt)
                    seen.add(txt.lower())
                    if len(labels) >= max_labels:
                        break

        if not labels and ocr_result.text.strip():
            # Fallback to splitting raw text if blocks are not itemized
            words = [w.strip() for w in ocr_result.text.split() if len(w.strip()) > 1]
            for w in words:
                if w.lower() not in seen:
                    labels.append(w)
                    seen.add(w.lower())
                    if len(labels) >= max_labels:
                        break

        return labels

    def generate_alt_text(
        self,
        vlm_result: Optional[VLMResult] = None,
        ocr_result: Optional[OCRResult] = None,
        context: Optional[Union[Dict[str, Any], str]] = None,
    ) -> str:
        """
        Generates clear, concise, accessibility-focused alt-text for screen readers.
        Fuses VLM visual semantics with OCR text labels without inventing information.
        """
        vlm_valid = vlm_result is not None and bool(vlm_result.description.strip())
        ocr_valid = ocr_result is not None and bool(ocr_result.text.strip())

        ctx_title = ""
        if isinstance(context, str):
            ctx_title = context.strip()
        elif isinstance(context, dict):
            ctx_title = context.get("title", "").strip() or context.get("heading", "").strip()

        # Extract OCR labels
        ocr_labels = self._extract_key_ocr_labels(ocr_result)

        # Case 1: Both VLM and OCR available
        if vlm_valid and ocr_valid:
            parts = []
            if ctx_title:
                parts.append(f"[{ctx_title}]")

            parts.append(vlm_result.description.strip())

            if vlm_result.visual_elements:
                elements_str = ", ".join(vlm_result.visual_elements[:5])
                parts.append(f"Visual elements: {elements_str}.")

            if vlm_result.relationships:
                rel_str = "; ".join(vlm_result.relationships[:3])
                parts.append(f"Relationships: {rel_str}.")

            if ocr_labels:
                labels_str = ", ".join(ocr_labels)
                parts.append(f"Text labels: {labels_str}.")

            return " ".join(parts)

        # Case 2: VLM-only fallback
        if vlm_valid and not ocr_valid:
            parts = []
            if ctx_title:
                parts.append(f"[{ctx_title}]")

            parts.append(vlm_result.description.strip())

            if vlm_result.visual_elements:
                elements_str = ", ".join(vlm_result.visual_elements[:5])
                parts.append(f"Visual elements: {elements_str}.")

            if vlm_result.relationships:
                rel_str = "; ".join(vlm_result.relationships[:3])
                parts.append(f"Relationships: {rel_str}.")

            return " ".join(parts)

        # Case 3: OCR-only fallback
        if ocr_valid and not vlm_valid:
            parts = []
            if ctx_title:
                parts.append(f"[{ctx_title}]")

            if ocr_labels:
                labels_str = ", ".join(ocr_labels)
                parts.append(f"Image containing text labels: {labels_str}.")
            else:
                parts.append(f"Image containing text: {ocr_result.text.strip()}.")

            return " ".join(parts)

        # Case 4: Neither available / Both failed
        if ctx_title:
            return f"[{ctx_title}] Image content unavailable."
        return ""

    def generate_diagram_explanation(
        self,
        vlm_result: Optional[VLMResult] = None,
        ocr_result: Optional[OCRResult] = None,
        context: Optional[Union[Dict[str, Any], str]] = None,
    ) -> Dict[str, Any]:
        """
        Extracts structured diagram information: title, labels, components, connections,
        spatial relationships, overall description, and combined alt-text.
        """
        warnings: List[str] = []
        errors: List[str] = []

        if vlm_result and vlm_result.warnings:
            warnings.extend(vlm_result.warnings)
        if vlm_result and vlm_result.errors:
            errors.extend(vlm_result.errors)
        if ocr_result and ocr_result.warnings:
            warnings.extend(ocr_result.warnings)
        if ocr_result and ocr_result.errors:
            errors.extend(ocr_result.errors)

        title = ""
        if isinstance(context, str):
            title = context.strip()
        elif isinstance(context, dict):
            title = context.get("title", "").strip() or context.get("heading", "").strip()

        ocr_labels = self._extract_key_ocr_labels(ocr_result, max_labels=15)
        components = list(vlm_result.visual_elements) if vlm_result else []
        relationships = list(vlm_result.relationships) if vlm_result else []
        description = vlm_result.description if vlm_result else ""

        # Connections can be derived from relationships containing "connects", "points", "arrow", or "linked"
        connections = [r for r in relationships if any(k in r.lower() for k in ["connect", "point", "arrow", "link", "to"])]

        alt_text = self.generate_alt_text(vlm_result=vlm_result, ocr_result=ocr_result, context=context)

        return {
            "title": title,
            "labels": ocr_labels,
            "components": components,
            "connections": connections,
            "spatial_relationships": relationships,
            "overall_description": description,
            "alt_text": alt_text,
            "warnings": list(set(warnings)),
            "errors": list(set(errors)),
        }
