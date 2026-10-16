"""Edge-Aware Adaptive Filtering for Screen Moiré Pattern Removal.

This module implements an adaptive edge-preserving filter combining:
- Gradient/edge map extraction (Sobel & Canny)
- Bilateral filtering for non-linear local tone smoothing
- Guided filtering (with cv2.ximgproc support and pure-NumPy/OpenCV fallback)
- Soft edge-weight blending to protect sharp text, gridlines, and UI icons
- Optional multi-scale processing
"""

from typing import Optional, Tuple
import cv2
import numpy as np

try:
    from processing.gaussian import _ensure_bgr_uint8
except ImportError:
    from backend.processing.gaussian import _ensure_bgr_uint8


def guided_filter_manual(
    guide: np.ndarray,
    src: np.ndarray,
    radius: int = 4,
    eps: float = 0.04,
) -> np.ndarray:
    """Fast O(N) Guided Filter using box filters.

    Args:
        guide: Guidance image in float32 [0, 1] (H, W) or (H, W, C).
        src: Input image in float32 [0, 1] (H, W) or (H, W, C).
        radius: Filter kernel radius.
        eps: Regularization parameter.

    Returns:
        Filtered image in float32 [0, 1] with same shape as src.
    """
    ksize = (2 * radius + 1, 2 * radius + 1)

    if src.ndim == 2:
        g = guide if guide.ndim == 2 else cv2.cvtColor(guide, cv2.COLOR_BGR2GRAY)
        p = src

        mean_I = cv2.boxFilter(g, cv2.CV_32F, ksize)
        mean_p = cv2.boxFilter(p, cv2.CV_32F, ksize)
        mean_Ip = cv2.boxFilter(g * p, cv2.CV_32F, ksize)
        cov_Ip = mean_Ip - mean_I * mean_p

        mean_II = cv2.boxFilter(g * g, cv2.CV_32F, ksize)
        var_I = mean_II - mean_I * mean_I

        a = cov_Ip / (var_I + eps)
        b = mean_p - a * mean_I

        mean_a = cv2.boxFilter(a, cv2.CV_32F, ksize)
        mean_b = cv2.boxFilter(b, cv2.CV_32F, ksize)

        q = mean_a * g + mean_b
        return np.clip(q, 0.0, 1.0)
    else:
        # Multi-channel
        h, w, c = src.shape
        if guide.ndim == 2:
            g = guide
        else:
            g = cv2.cvtColor(guide, cv2.COLOR_BGR2GRAY)

        mean_I = cv2.boxFilter(g, cv2.CV_32F, ksize)
        mean_II = cv2.boxFilter(g * g, cv2.CV_32F, ksize)
        var_I = mean_II - mean_I * mean_I

        filtered_channels = []
        for ch in range(c):
            p = src[:, :, ch]
            mean_p = cv2.boxFilter(p, cv2.CV_32F, ksize)
            mean_Ip = cv2.boxFilter(g * p, cv2.CV_32F, ksize)
            cov_Ip = mean_Ip - mean_I * mean_p

            a = cov_Ip / (var_I + eps)
            b = mean_p - a * mean_I

            mean_a = cv2.boxFilter(a, cv2.CV_32F, ksize)
            mean_b = cv2.boxFilter(b, cv2.CV_32F, ksize)

            q = mean_a * g + mean_b
            filtered_channels.append(q)

        return np.clip(np.stack(filtered_channels, axis=2), 0.0, 1.0)


def apply_guided_filter(
    guide: np.ndarray,
    src: np.ndarray,
    radius: int = 4,
    eps: float = 0.04,
) -> np.ndarray:
    """Wrapper that utilizes cv2.ximgproc.guidedFilter if available, otherwise manual fallback."""
    if hasattr(cv2, 'ximgproc') and hasattr(cv2.ximgproc, 'guidedFilter'):
        try:
            return cv2.ximgproc.guidedFilter(guide, src, radius, eps)
        except Exception:
            pass

    # Normalize to float32 [0, 1] if uint8
    guide_f = guide.astype(np.float32) / 255.0 if guide.dtype == np.uint8 else guide.astype(np.float32)
    src_f = src.astype(np.float32) / 255.0 if src.dtype == np.uint8 else src.astype(np.float32)

    res = guided_filter_manual(guide_f, src_f, radius=radius, eps=eps)
    return (res * 255.0).clip(0, 255).astype(np.uint8)


def compute_edge_mask(image: np.ndarray, edge_threshold: float = 50.0) -> np.ndarray:
    """Compute normalized edge retention mask [0, 1] where 1.0 means strong edge to retain.

    Args:
        image: BGR uint8 image.
        edge_threshold: Gradient threshold (10 - 200).

    Returns:
        Float32 mask of shape (H, W) in range [0, 1].
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Compute Sobel gradients
    sobel_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    grad_mag = np.sqrt(sobel_x ** 2 + sobel_y ** 2)

    # Compute Canny binary edge map for fine lines
    canny = cv2.Canny(gray, int(edge_threshold * 0.7), int(edge_threshold * 1.5))
    canny_soft = cv2.GaussianBlur(canny.astype(np.float32) / 255.0, (3, 3), 1.0)

    # Normalize gradient magnitude
    norm_grad = np.clip(grad_mag / max(1.0, float(edge_threshold)), 0.0, 1.0)

    # Combine Sobel and soft Canny
    combined_mask = np.maximum(norm_grad, canny_soft)
    # Smooth mask slightly to prevent harsh edge seams
    smooth_mask = cv2.GaussianBlur(combined_mask, (3, 3), 0.8)
    return np.clip(smooth_mask, 0.0, 1.0).astype(np.float32)


def edge_aware_filter(
    image: np.ndarray,
    filter_strength: int = 75,
    edge_threshold: int = 50,
    bilateral_d: int = 9,
    bilateral_sigma_color: float = 75.0,
    bilateral_sigma_space: float = 75.0,
    guided_radius: int = 4,
    guided_eps: float = 0.04,
    use_guided: bool = True,
    multi_scale: bool = False,
    luminance_only: bool = False,
) -> np.ndarray:
    """Apply edge-aware adaptive filtering to suppress moiré while preserving sharp edges.

    Args:
        image: Input image (BGR uint8).
        filter_strength: Blending strength in [1, 100].
        edge_threshold: Threshold for edge preservation sensitivity in [10, 200].
        bilateral_d: Diameter of each pixel neighborhood for bilateral filter (5-15).
        bilateral_sigma_color: Filter sigma in the color space (25-150).
        bilateral_sigma_space: Filter sigma in the coordinate space (25-150).
        guided_radius: Radius of guided filter (2-16).
        guided_eps: Regularization parameter for guided filter (0.001-1.0).
        use_guided: Whether to include guided filtering stage.
        multi_scale: If True, applies multi-scale guided filtering.
        luminance_only: If True, applies edge-aware smoothing primarily to luminance.

    Returns:
        Filtered BGR image as uint8 numpy array.
    """
    img = _ensure_bgr_uint8(image)
    h, w = img.shape[:2]

    # Constrain parameters
    filter_strength = int(np.clip(filter_strength, 1, 100))
    edge_threshold = int(np.clip(edge_threshold, 10, 200))
    bilateral_d = int(np.clip(bilateral_d, 3, 15))
    guided_radius = int(np.clip(guided_radius, 2, 16))
    guided_eps = float(np.clip(guided_eps, 0.0001, 1.0))

    # Compute edge retention mask: 1.0 = sharp edge (preserve), 0.0 = flat/moiré region (smooth)
    edge_mask_2d = compute_edge_mask(img, edge_threshold=edge_threshold)
    edge_mask = np.repeat(edge_mask_2d[:, :, np.newaxis], 3, axis=2)

    # Step 1: Bilateral smoothing
    if luminance_only:
        ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
        y = ycrcb[:, :, 0]
        y_bilateral = cv2.bilateralFilter(
            y,
            d=bilateral_d,
            sigmaColor=bilateral_sigma_color,
            sigmaSpace=bilateral_sigma_space,
        )
        ycrcb_bilat = ycrcb.copy()
        ycrcb_bilat[:, :, 0] = y_bilateral
        smoothed = cv2.cvtColor(ycrcb_bilat, cv2.COLOR_YCrCb2BGR)
    else:
        smoothed = cv2.bilateralFilter(
            img,
            d=bilateral_d,
            sigmaColor=bilateral_sigma_color,
            sigmaSpace=bilateral_sigma_space,
        )

    # Step 2: Guided filtering (optional refinement)
    if use_guided:
        gray_guide = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        smoothed = apply_guided_filter(
            gray_guide,
            smoothed,
            radius=guided_radius,
            eps=guided_eps,
        )

        if multi_scale:
            # Second stage with larger radius to capture broader moiré waves
            smoothed = apply_guided_filter(
                gray_guide,
                smoothed,
                radius=min(16, guided_radius * 2),
                eps=guided_eps * 2.0,
            )

    # Step 3: Adaptive Edge-Aware Blending
    # High edge region -> retains original image; Low edge region -> smoothed image
    filtered_blend = (edge_mask * img.astype(np.float32) +
                      (1.0 - edge_mask) * smoothed.astype(np.float32))

    # Step 4: Master Filter Strength blending
    alpha = filter_strength / 100.0
    final_output = alpha * filtered_blend + (1.0 - alpha) * img.astype(np.float32)

    return np.clip(final_output, 0, 255).astype(np.uint8)
