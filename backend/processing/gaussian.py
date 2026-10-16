"""Gaussian Smoothing Filter for Moiré Pattern Reduction.

This module provides Gaussian smoothing baseline with support for:
- Full RGB / channel-independent processing
- Luminance-only processing in YCrCb color space
- Edge-case handling (small images, even kernel sizes, grayscale input)
"""

from typing import Union
import cv2
import numpy as np


def _ensure_bgr_uint8(image: np.ndarray) -> np.ndarray:
    """Ensure the image is a 3-channel BGR uint8 numpy array."""
    if not isinstance(image, np.ndarray):
        raise TypeError(f"Expected numpy.ndarray, got {type(image)}")
    if image.size == 0:
        raise ValueError("Image is empty")

    # Handle float / non-uint8 images
    if image.dtype != np.uint8:
        if np.issubdtype(image.dtype, np.floating):
            if image.max() <= 1.0:
                img_u8 = (image * 255.0).clip(0, 255).astype(np.uint8)
            else:
                img_u8 = image.clip(0, 255).astype(np.uint8)
        else:
            img_u8 = image.clip(0, 255).astype(np.uint8)
    else:
        img_u8 = image.copy()

    # Handle grayscale (2D or 3D with 1 channel)
    if img_u8.ndim == 2:
        img_u8 = cv2.cvtColor(img_u8, cv2.COLOR_GRAY2BGR)
    elif img_u8.ndim == 3 and img_u8.shape[2] == 1:
        img_u8 = cv2.cvtColor(img_u8, cv2.COLOR_GRAY2BGR)
    elif img_u8.ndim == 3 and img_u8.shape[2] == 4:
        # RGBA to BGR
        img_u8 = cv2.cvtColor(img_u8, cv2.COLOR_BGRA2BGR)
    elif img_u8.ndim != 3 or img_u8.shape[2] != 3:
        raise ValueError(f"Unsupported image shape: {image.shape}")

    return img_u8


def gaussian_filter(
    image: np.ndarray,
    kernel_size: int = 5,
    sigma: float = 1.5,
    luminance_only: bool = True,
) -> np.ndarray:
    """Apply Gaussian smoothing to an image.

    Args:
        image: Input image (BGR, uint8, HxWx3 or grayscale).
        kernel_size: Size of Gaussian kernel (must be odd, 3-31).
        sigma: Standard deviation of Gaussian kernel (0.5 - 10.0).
        luminance_only: If True, only the Y (luminance) channel in YCrCb is blurred,
                        preserving chroma details and reducing color bleed.

    Returns:
        Filtered BGR image as uint8 numpy array.
    """
    img = _ensure_bgr_uint8(image)
    h, w = img.shape[:2]

    # Validate and constrain kernel_size
    kernel_size = int(kernel_size)
    if kernel_size < 3:
        kernel_size = 3
    if kernel_size > 31:
        kernel_size = 31
    # Ensure kernel is odd
    if kernel_size % 2 == 0:
        kernel_size += 1

    # Ensure kernel does not exceed image dimensions
    max_dim = min(h, w)
    if kernel_size > max_dim:
        kernel_size = max_dim if max_dim % 2 == 1 else max_dim - 1
        if kernel_size < 1:
            kernel_size = 1

    if kernel_size <= 1:
        return img.copy()

    # Constrain sigma
    sigma = float(np.clip(sigma, 0.1, 20.0))

    if luminance_only:
        # Convert BGR to YCrCb
        ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
        y, cr, cb = cv2.split(ycrcb)

        # Apply Gaussian blur only to luminance (Y)
        y_blurred = cv2.GaussianBlur(y, (kernel_size, kernel_size), sigmaX=sigma, sigmaY=sigma)

        # Merge back and convert to BGR
        merged = cv2.merge([y_blurred, cr, cb])
        result = cv2.cvtColor(merged, cv2.COLOR_YCrCb2BGR)
    else:
        # Apply Gaussian blur across all channels
        result = cv2.GaussianBlur(img, (kernel_size, kernel_size), sigmaX=sigma, sigmaY=sigma)

    return np.clip(result, 0, 255).astype(np.uint8)
