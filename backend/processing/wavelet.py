"""Wavelet-based Denoising for Screen Moiré Pattern Attenuation.

This module implements multi-level 2D Discrete Wavelet Transform (DWT) thresholding:
- Multi-level 2D decomposition using PyWavelets (pywt)
- Flexible wavelet families (db1-db4, sym4, coif1, bior1.3, etc.)
- Hard and Soft thresholding of detail sub-bands (LH, HL, HH)
- Universal and per-level thresholding options
- Luminance-only (YCrCb) and multi-channel processing
- Output dimension alignment and uint8 clamping
"""

from typing import Dict, List, Optional, Union
import cv2
import numpy as np
import pywt

try:
    from processing.gaussian import _ensure_bgr_uint8
except ImportError:
    from backend.processing.gaussian import _ensure_bgr_uint8

SUPPORTED_WAVELETS = ['db1', 'db2', 'db4', 'sym4', 'coif1', 'bior1.3', 'haar', 'sym2']


def _denoise_single_channel_wavelet(
    channel: np.ndarray,
    wavelet_name: str = 'db4',
    level: int = 2,
    threshold_mode: str = 'soft',
    threshold_value: float = 20.0,
    per_level_thresholds: Optional[Dict[int, float]] = None,
) -> np.ndarray:
    """Apply 2D DWT detail thresholding to a single float32 channel."""
    h, w = channel.shape
    wavelet = pywt.Wavelet(wavelet_name)

    # Determine maximum valid decomposition level for this channel size
    max_level = pywt.dwt_max_level(min(h, w), wavelet.dec_len)
    actual_level = max(1, min(int(level), max_level))

    # Decompose into approximation and detail coefficients:
    # coeffs = [cAn, (cHn, cVn, cDn), ..., (cH1, cV1, cD1)]
    coeffs = pywt.wavedec2(channel, wavelet=wavelet, level=actual_level)
    cA = coeffs[0]
    details = coeffs[1:]

    new_details = []
    # pywt orders details from coarsest (highest level index) down to level 1
    # details[0] is level actual_level, details[-1] is level 1
    for i, detail_tuple in enumerate(details):
        current_lvl = actual_level - i
        # Determine threshold for this level
        if per_level_thresholds and current_lvl in per_level_thresholds:
            lvl_thresh = float(per_level_thresholds[current_lvl])
        else:
            # Scale threshold slightly for higher frequencies (level 1 has highest noise)
            # Universal threshold scaling factor: details closer to level 1 get slightly higher threshold
            lvl_thresh = float(threshold_value) * (1.0 + 0.1 * (actual_level - current_lvl))

        cH, cV, cD = detail_tuple
        if threshold_mode == 'hard':
            cH_t = pywt.threshold(cH, lvl_thresh, mode='hard')
            cV_t = pywt.threshold(cV, lvl_thresh, mode='hard')
            cD_t = pywt.threshold(cD, lvl_thresh, mode='hard')
        else:  # soft
            cH_t = pywt.threshold(cH, lvl_thresh, mode='soft')
            cV_t = pywt.threshold(cV, lvl_thresh, mode='soft')
            cD_t = pywt.threshold(cD, lvl_thresh, mode='soft')

        new_details.append((cH_t, cV_t, cD_t))

    new_coeffs = [cA] + new_details
    reconstructed = pywt.waverec2(new_coeffs, wavelet=wavelet)

    # Ensure reconstructed array matches original dimensions exactly
    reconstructed = reconstructed[:h, :w]
    return reconstructed


def wavelet_filter(
    image: np.ndarray,
    wavelet: str = 'db4',
    level: int = 2,
    threshold_mode: str = 'soft',
    threshold_value: float = 20.0,
    luminance_only: bool = True,
    per_level_thresholds: Optional[Dict[int, float]] = None,
) -> np.ndarray:
    """Remove moiré artifacts via multi-level 2D Wavelet detail thresholding.

    Args:
        image: Input image (BGR uint8).
        wavelet: Wavelet name ('db1','db2','db4','sym4','coif1','bior1.3').
        level: Decomposition depth (1 - 5).
        threshold_mode: 'soft' or 'hard' thresholding.
        threshold_value: Baseline threshold value (5.0 - 100.0).
        luminance_only: If True, only filter luminance in YCrCb color space.
        per_level_thresholds: Optional mapping of {level: threshold_value}.

    Returns:
        Filtered BGR image as uint8 numpy array.
    """
    img = _ensure_bgr_uint8(image)
    h, w = img.shape[:2]

    # Validate wavelet name
    if wavelet not in pywt.wavelist(kind='discrete'):
        wavelet = 'db4'

    # Validate mode
    if threshold_mode not in ('soft', 'hard'):
        threshold_mode = 'soft'

    # Clamp parameters
    threshold_value = float(np.clip(threshold_value, 1.0, 150.0))
    level = int(np.clip(level, 1, 5))

    if luminance_only:
        ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
        y = ycrcb[:, :, 0].astype(np.float32)

        y_denoised = _denoise_single_channel_wavelet(
            y,
            wavelet_name=wavelet,
            level=level,
            threshold_mode=threshold_mode,
            threshold_value=threshold_value,
            per_level_thresholds=per_level_thresholds,
        )

        ycrcb[:, :, 0] = np.clip(y_denoised, 0, 255).astype(np.uint8)
        result = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)
    else:
        channels = cv2.split(img.astype(np.float32))
        denoised_channels = []
        for ch in channels:
            d_ch = _denoise_single_channel_wavelet(
                ch,
                wavelet_name=wavelet,
                level=level,
                threshold_mode=threshold_mode,
                threshold_value=threshold_value,
                per_level_thresholds=per_level_thresholds,
            )
            denoised_channels.append(np.clip(d_ch, 0, 255).astype(np.uint8))
        result = cv2.merge(denoised_channels)

    return np.clip(result, 0, 255).astype(np.uint8)
