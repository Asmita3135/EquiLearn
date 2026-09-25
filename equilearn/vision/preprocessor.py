"""
M1-STAGE 2 — Image Preprocessing Foundation
Resizes, denoises, deskews, and normalizes image quality for downstream OCR/VLM.
Pipeline Flow: extraction → preprocessing (resize → denoise → deskew → normalize)
"""

from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union
import cv2
import numpy as np
from PIL import Image


class ImagePreprocessor:
    """Class for document image cleanup and optimization preserving original data."""

    def __init__(
        self,
        max_dim: int = 2000,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.max_dim = max_dim
        self.config = config or {}

    def _to_numpy(self, image: Any) -> Tuple[np.ndarray, bool]:
        """
        Converts input image (path, PIL Image, or numpy array) to a numpy ndarray copy.
        Returns tuple of (numpy_array_copy, is_pil_input).
        Raises ValueError or FileNotFoundError if invalid.
        """
        if image is None:
            raise ValueError("Image input cannot be None.")

        is_pil = False
        if isinstance(image, (str, Path)):
            path = Path(image)
            if not path.is_file():
                raise FileNotFoundError(f"Image file not found: {image}")
            arr = cv2.imread(str(path))
            if arr is None:
                raise ValueError(f"Could not read image file: {image}")
            arr = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
        elif isinstance(image, Image.Image):
            is_pil = True
            arr = np.array(image.convert("RGB"))
        elif isinstance(image, np.ndarray):
            if image.size == 0:
                raise ValueError("Input image array is empty.")
            arr = image.copy()
        else:
            raise ValueError(f"Unsupported image type: {type(image)}")

        return arr, is_pil

    def _to_original_format(self, arr: np.ndarray, is_pil: bool) -> Any:
        """Converts numpy array back to PIL.Image if input was PIL Image."""
        if is_pil:
            return Image.fromarray(arr)
        return arr

    def resize(
        self,
        image: Any,
        max_dim: Optional[int] = None,
        target_size: Optional[Tuple[int, int]] = None,
    ) -> Any:
        """
        Resizes image while preserving aspect ratio if max_dim is set, or to target_size (width, height).
        Preserves original image input.
        """
        arr, is_pil = self._to_numpy(image)
        h, w = arr.shape[:2]

        if target_size:
            tw, th = target_size
            resized = cv2.resize(arr, (tw, th), interpolation=cv2.INTER_AREA)
            return self._to_original_format(resized, is_pil)

        limit = max_dim or self.max_dim
        if max(h, w) > limit:
            scale = limit / float(max(h, w))
            new_w = max(1, int(w * scale))
            new_h = max(1, int(h * scale))
            resized = cv2.resize(arr, (new_w, new_h), interpolation=cv2.INTER_AREA)
            return self._to_original_format(resized, is_pil)

        return self._to_original_format(arr, is_pil)

    def denoise(self, image: Any) -> Any:
        """Removes background noise and scan artifacts from image copy."""
        arr, is_pil = self._to_numpy(image)

        if len(arr.shape) == 3 and arr.shape[2] == 3:
            # Color RGB image
            denoised = cv2.fastNlMeansDenoisingColored(arr, None, 7, 7, 7, 21)
        elif len(arr.shape) == 2 or (len(arr.shape) == 3 and arr.shape[2] == 1):
            # Grayscale image
            denoised = cv2.fastNlMeansDenoising(arr, None, 7, 7, 21)
        else:
            denoised = arr

        return self._to_original_format(denoised, is_pil)

    def deskew(self, image: Any) -> Any:
        """Detects text skew angle and rotates image copy to align text horizontally."""
        arr, is_pil = self._to_numpy(image)
        h, w = arr.shape[:2]

        # Convert to grayscale for skew detection
        if len(arr.shape) == 3 and arr.shape[2] == 3:
            gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        else:
            gray = arr.copy()

        # Invert and threshold to find text pixels
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        coords = np.column_stack(np.where(thresh > 0))

        if coords.shape[0] < 10:
            return self._to_original_format(arr, is_pil)

        rect = cv2.minAreaRect(coords)
        angle = rect[-1]

        # OpenCV minAreaRect angle adjustment logic
        if angle < -45:
            angle = -(90 + angle)
        elif angle > 45:
            angle = 90 - angle
        else:
            angle = -angle

        # Rotate only if skew is noticeable
        if 0.2 < abs(angle) < 45.0:
            center = (w // 2, h // 2)
            rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)
            border_val = (255, 255, 255) if len(arr.shape) == 3 else 255
            straightened = cv2.warpAffine(
                arr,
                rot_mat,
                (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=border_val,
            )
            return self._to_original_format(straightened, is_pil)

        return self._to_original_format(arr, is_pil)

    def normalize(self, image: Any) -> Any:
        """Normalizes contrast, brightness, and color space for optimal OCR/VLM input."""
        arr, is_pil = self._to_numpy(image)

        if len(arr.shape) == 3 and arr.shape[2] == 3:
            # Convert RGB to LAB, apply CLAHE on L channel
            lab = cv2.cvtColor(arr, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            cl = clahe.apply(l)
            limg = cv2.merge((cl, a, b))
            normalized = cv2.cvtColor(limg, cv2.COLOR_LAB2RGB)
        elif len(arr.shape) == 2:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            normalized = clahe.apply(arr)
        else:
            normalized = arr

        return self._to_original_format(normalized, is_pil)

    def preprocess_pipeline(self, image: Any) -> Any:
        """Applies complete preprocessing chain: resize -> denoise -> deskew -> normalize."""
        resized = self.resize(image)
        denoised = self.denoise(resized)
        deskewed = self.deskew(denoised)
        return self.normalize(deskewed)
