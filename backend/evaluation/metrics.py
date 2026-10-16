"""Evaluation Metrics for Screen Moiré Pattern Removal.

Computes standard image quality metrics:
- PSNR (Peak Signal-to-Noise Ratio)
- SSIM (Structural Similarity Index)
- Edge Preservation Score (Canny Edge Overlap F1 Score)
"""

from typing import Dict, Tuple, Union
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim_fn

try:
    from processing.gaussian import _ensure_bgr_uint8
except ImportError:
    from backend.processing.gaussian import _ensure_bgr_uint8


def compute_psnr(
    ref: np.ndarray,
    target: np.ndarray,
    max_val: float = 255.0,
) -> float:
    """Compute Peak Signal-to-Noise Ratio (PSNR) in decibels (dB).

    Args:
        ref: Ground-truth reference image (uint8).
        target: Processed target image (uint8).
        max_val: Maximum possible pixel intensity.

    Returns:
        PSNR value in dB (capped at 100.0 for identical images).
    """
    ref_u8 = _ensure_bgr_uint8(ref)
    target_u8 = _ensure_bgr_uint8(target)

    if ref_u8.shape != target_u8.shape:
        target_u8 = cv2.resize(target_u8, (ref_u8.shape[1], ref_u8.shape[0]), interpolation=cv2.INTER_LINEAR)

    diff = ref_u8.astype(np.float64) - target_u8.astype(np.float64)
    mse = np.mean(diff ** 2)

    if mse <= 1e-10:
        return 100.0

    psnr = 10.0 * np.log10((max_val ** 2) / mse)
    return float(round(psnr, 4))


def compute_ssim(
    ref: np.ndarray,
    target: np.ndarray,
) -> float:
    """Compute Structural Similarity Index (SSIM) between two images.

    Args:
        ref: Ground-truth reference image (uint8).
        target: Processed target image (uint8).

    Returns:
        SSIM value in range [-1.0, 1.0] (1.0 = identical).
    """
    ref_u8 = _ensure_bgr_uint8(ref)
    target_u8 = _ensure_bgr_uint8(target)

    if ref_u8.shape != target_u8.shape:
        target_u8 = cv2.resize(target_u8, (ref_u8.shape[1], ref_u8.shape[0]), interpolation=cv2.INTER_LINEAR)

    h, w = ref_u8.shape[:2]
    win_size = min(7, h if h % 2 == 1 else h - 1, w if w % 2 == 1 else w - 1)
    if win_size < 3:
        win_size = 3

    score = ssim_fn(
        ref_u8,
        target_u8,
        win_size=win_size,
        channel_axis=2,
        data_range=255,
    )
    return float(round(score, 4))


def compute_edge_preservation(
    ref: np.ndarray,
    target: np.ndarray,
    low_thresh: int = 50,
    high_thresh: int = 150,
    tolerance: int = 1,
) -> float:
    """Compute Edge Preservation Score as F1-score of Canny edge pixels.

    Args:
        ref: Ground-truth reference image.
        target: Processed target image.
        low_thresh: Lower hysteresis threshold for Canny.
        high_thresh: Upper hysteresis threshold for Canny.
        tolerance: Pixel dilation radius to allow slight 1px positional shifts.

    Returns:
        F1 score in range [0.0, 1.0].
    """
    ref_u8 = _ensure_bgr_uint8(ref)
    target_u8 = _ensure_bgr_uint8(target)

    if ref_u8.shape != target_u8.shape:
        target_u8 = cv2.resize(target_u8, (ref_u8.shape[1], ref_u8.shape[0]), interpolation=cv2.INTER_LINEAR)

    gray_ref = cv2.cvtColor(ref_u8, cv2.COLOR_BGR2GRAY)
    gray_target = cv2.cvtColor(target_u8, cv2.COLOR_BGR2GRAY)

    edges_ref = cv2.Canny(gray_ref, low_thresh, high_thresh) > 0
    edges_target = cv2.Canny(gray_target, low_thresh, high_thresh) > 0

    ref_count = int(np.count_nonzero(edges_ref))
    target_count = int(np.count_nonzero(edges_target))

    if ref_count == 0 and target_count == 0:
        return 1.0
    if ref_count == 0 or target_count == 0:
        return 0.0

    if tolerance > 0:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2 * tolerance + 1, 2 * tolerance + 1))
        dilated_ref = cv2.dilate(edges_ref.astype(np.uint8), kernel) > 0
        dilated_target = cv2.dilate(edges_target.astype(np.uint8), kernel) > 0

        # True Positives from target edge pixels that match dilated ref edges
        tp_target = np.count_nonzero(edges_target & dilated_ref)
        # True Positives from ref edge pixels that match dilated target edges
        tp_ref = np.count_nonzero(edges_ref & dilated_target)

        precision = tp_target / target_count
        recall = tp_ref / ref_count
    else:
        tp = np.count_nonzero(edges_ref & edges_target)
        precision = tp / target_count
        recall = tp / ref_count

    if precision + recall < 1e-10:
        return 0.0

    f1 = 2.0 * (precision * recall) / (precision + recall)
    return float(round(f1, 4))


def evaluate_all(
    ref: np.ndarray,
    target: np.ndarray,
) -> Dict[str, float]:
    """Calculate all standard metrics between reference and processed images.

    Returns:
        Dictionary with keys 'psnr', 'ssim', and 'edge_preservation_score'.
    """
    psnr = compute_psnr(ref, target)
    ssim = compute_ssim(ref, target)
    edge_f1 = compute_edge_preservation(ref, target)

    return {
        "psnr": psnr,
        "ssim": ssim,
        "edge_preservation_score": edge_f1,
    }
