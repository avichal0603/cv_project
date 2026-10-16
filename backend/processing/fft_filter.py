"""FFT Notch Filtering for Periodic Moiré Pattern Removal.

This module implements 2D Fast Fourier Transform (FFT) notch filtering:
- Forward 2D FFT per channel or luminance
- Automated detection of periodic moiré peaks in frequency domain
- Gaussian notch reject filter synthesis with conjugate symmetry and DC protection
- Manual notch specification support
- Inverse 2D FFT reconstruction
- Generation of high-contrast magnitude spectrum visualizations with notch markers
"""

from typing import List, Optional, Tuple, Union
import cv2
import numpy as np
from scipy.ndimage import maximum_filter

try:
    from processing.gaussian import _ensure_bgr_uint8
except ImportError:
    from backend.processing.gaussian import _ensure_bgr_uint8


def detect_periodic_peaks(
    log_magnitude: np.ndarray,
    min_frequency: int = 20,
    peak_threshold: float = 0.85,
    max_peaks: int = 12,
    neighborhood_size: int = 15,
) -> List[Tuple[int, int]]:
    """Detect prominent periodic peaks in the centered log-magnitude spectrum.

    Args:
        log_magnitude: Centered 2D log magnitude spectrum (H, W).
        min_frequency: Radius around center DC to exclude.
        peak_threshold: Relative threshold in [0.5, 0.99] determining peak sensitivity.
        max_peaks: Maximum number of peak pairs to return.
        neighborhood_size: Window size for local maximum detection.

    Returns:
        List of (y, x) peak coordinates in the shifted spectrum.
    """
    h, w = log_magnitude.shape
    cy, cx = h // 2, w // 2

    # Create coordinate grid distance from center
    y_coords, x_coords = np.ogrid[:h, :w]
    dist_from_center = np.sqrt((y_coords - cy) ** 2 + (x_coords - cx) ** 2)

    # Exclude DC region and border margins
    margin = 8
    valid_mask = (dist_from_center >= min_frequency)
    valid_mask[:margin, :] = False
    valid_mask[-margin:, :] = False
    valid_mask[:, :margin] = False
    valid_mask[:, -margin:] = False

    # Also avoid detecting raw horizontal/vertical window sinc axes (within 2px of crosshair)
    # as those represent rectangular windowing and text lines, not moiré interference
    axis_guard = 2
    valid_mask[cy - axis_guard : cy + axis_guard + 1, :] = False
    valid_mask[:, cx - axis_guard : cx + axis_guard + 1] = False

    if not np.any(valid_mask):
        return []

    # Find local maxima using maximum filter
    footprint = np.ones((neighborhood_size, neighborhood_size), dtype=bool)
    local_max = maximum_filter(log_magnitude, footprint=footprint, mode='constant', cval=-np.inf)
    is_peak = (log_magnitude == local_max) & valid_mask

    # Get values of valid candidates
    valid_values = log_magnitude[valid_mask]
    min_v = float(valid_values.min())
    max_v = float(valid_values.max())

    if max_v - min_v < 1e-6:
        return []

    # Cutoff scales between 50th percentile (or min) and max
    percentile_base = float(np.percentile(valid_values, 75))
    cutoff = percentile_base + float(peak_threshold) * (max_v - percentile_base)
    peak_indices = np.argwhere(is_peak & (log_magnitude >= cutoff))

    if len(peak_indices) == 0:
        # Fallback to top peaks if cutoff was too strict
        peak_indices = np.argwhere(is_peak)
        if len(peak_indices) == 0:
            return []

    # Sort peaks by descending magnitude
    peak_magnitudes = [log_magnitude[py, px] for py, px in peak_indices]
    sorted_order = np.argsort(peak_magnitudes)[::-1]
    sorted_peaks = [tuple(peak_indices[i]) for i in sorted_order]

    # Select distinct peaks with conjugate symmetry awareness
    selected_peaks = []
    selected_set = set()

    for py, px in sorted_peaks:
        if (py, px) in selected_set:
            continue
        sym_y = 2 * cy - py
        sym_x = 2 * cx - px

        selected_peaks.append((int(py), int(px)))
        selected_set.add((py, px))
        selected_set.add((sym_y, sym_x))

        if len(selected_peaks) >= max_peaks:
            break

    return selected_peaks


def create_notch_filter(
    shape: Tuple[int, int],
    peaks: List[Tuple[int, int]],
    notch_radius: int = 15,
    suppression_strength: float = 0.9,
    min_frequency: int = 20,
) -> np.ndarray:
    """Create a 2D Gaussian notch reject filter centered at DC with strict DC protection.

    Args:
        shape: (H, W) shape of the frequency grid.
        peaks: List of (py, px) notch center locations.
        notch_radius: Radius (sigma) of the Gaussian notch.
        suppression_strength: Attenuation factor at notch center (0.0 = none, 1.0 = total).
        min_frequency: DC exclusion radius to protect from any attenuation.

    Returns:
        2D float32 transfer function H(u, v) in range [0, 1].
    """
    h, w = shape
    cy, cx = h // 2, w // 2
    y_coords, x_coords = np.ogrid[:h, :w]
    dist_from_dc = np.sqrt((y_coords - cy) ** 2 + (x_coords - cx) ** 2)

    # Start with all-pass filter
    filter_mask = np.ones((h, w), dtype=np.float32)
    strength = np.clip(float(suppression_strength), 0.0, 1.0)

    for py, px in peaks:
        # Distance from peak to DC
        peak_dist = np.sqrt((py - cy) ** 2 + (px - cx) ** 2)
        # Adapt notch radius so Gaussian tail does not leak into DC
        eff_radius = max(2.0, min(float(notch_radius), (peak_dist - min_frequency * 0.5) / 1.8))
        radius_sq = 2.0 * (eff_radius ** 2)

        # Distance squared from primary peak
        d1_sq = (y_coords - py) ** 2 + (x_coords - px) ** 2
        notch1 = 1.0 - strength * np.exp(-d1_sq / radius_sq)

        # Distance squared from conjugate symmetric peak
        sym_y = 2 * cy - py
        sym_x = 2 * cx - px
        d2_sq = (y_coords - sym_y) ** 2 + (x_coords - sym_x) ** 2
        notch2 = 1.0 - strength * np.exp(-d2_sq / radius_sq)

        filter_mask *= (notch1 * notch2).astype(np.float32)

    # Strict smooth DC protection: guaranteed 1.0 within min_frequency
    taper_width = 8.0
    taper = np.clip((dist_from_dc - (min_frequency - 2)) / taper_width, 0.0, 1.0).astype(np.float32)
    filter_mask = 1.0 - (1.0 - filter_mask) * taper

    return np.clip(filter_mask, 0.0, 1.0)


def create_spectrum_visualization(
    f_shift: np.ndarray,
    peaks: Optional[List[Tuple[int, int]]] = None,
    min_frequency: int = 20,
    colormap: int = cv2.COLORMAP_VIRIDIS,
) -> np.ndarray:
    """Generate an informative, color-mapped visualization of the FFT magnitude spectrum."""
    if f_shift.ndim == 3:
        mag = np.mean(np.abs(f_shift), axis=2)
    else:
        mag = np.abs(f_shift)

    log_mag = np.log1p(mag)
    min_val, max_val = log_mag.min(), log_mag.max()
    if max_val - min_val > 1e-6:
        norm_mag = ((log_mag - min_val) / (max_val - min_val) * 255.0).astype(np.uint8)
    else:
        norm_mag = np.zeros_like(log_mag, dtype=np.uint8)

    # Colorize spectrum
    spectrum_bgr = cv2.applyColorMap(norm_mag, colormap)

    h, w = norm_mag.shape
    cy, cx = h // 2, w // 2

    # Draw DC center circle (min_frequency boundary)
    if min_frequency > 0:
        cv2.circle(spectrum_bgr, (cx, cy), min_frequency, (120, 120, 120), 1, cv2.LINE_AA)
    # Mark DC center
    cv2.drawMarker(spectrum_bgr, (cx, cy), (0, 0, 255), cv2.MARKER_CROSS, 8, 1, cv2.LINE_AA)

    # Mark detected / specified notches
    if peaks:
        for py, px in peaks:
            sym_y = 2 * cy - py
            sym_x = 2 * cx - px

            cv2.circle(spectrum_bgr, (px, py), 10, (0, 255, 255), 2, cv2.LINE_AA)
            cv2.drawMarker(spectrum_bgr, (px, py), (0, 255, 255), cv2.MARKER_TILTED_CROSS, 6, 1)

            cv2.circle(spectrum_bgr, (sym_x, sym_y), 10, (0, 200, 200), 1, cv2.LINE_AA)

    return spectrum_bgr


def fft_notch_filter(
    image: np.ndarray,
    auto_detect: bool = True,
    notch_radius: int = 15,
    suppression_strength: float = 0.9,
    min_frequency: int = 20,
    peak_threshold: float = 0.85,
    manual_notches: Optional[List[Union[List[int], Tuple[int, int]]]] = None,
    luminance_only: bool = True,
) -> Tuple[np.ndarray, np.ndarray, List[Tuple[int, int]]]:
    """Filter periodic moiré patterns using 2D FFT notch reject filtering."""
    img = _ensure_bgr_uint8(image)
    h, w = img.shape[:2]

    # Constrain parameters
    notch_radius = int(np.clip(notch_radius, 2, min(h, w) // 2))
    suppression_strength = float(np.clip(suppression_strength, 0.0, 1.0))
    min_frequency = int(np.clip(min_frequency, 5, min(h, w) // 2))
    peak_threshold = float(np.clip(peak_threshold, 0.5, 0.99))

    # Determine processing channels
    if luminance_only:
        ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
        target_channel = ycrcb[:, :, 0].astype(np.float32)
    else:
        target_channel = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)

    # Compute 2D FFT of representative channel for peak detection & visualization
    f = np.fft.fft2(target_channel)
    f_shift = np.fft.fftshift(f)
    log_mag = np.log1p(np.abs(f_shift))

    # Detect or collect notches
    all_notches: List[Tuple[int, int]] = []
    if auto_detect:
        detected = detect_periodic_peaks(
            log_mag,
            min_frequency=min_frequency,
            peak_threshold=peak_threshold,
        )
        all_notches.extend(detected)

    if manual_notches:
        for notch in manual_notches:
            ny, nx = int(notch[0]), int(notch[1])
            if 0 <= ny < h and 0 <= nx < w:
                all_notches.append((ny, nx))

    # Deduplicate notches
    unique_notches = []
    seen = set()
    for py, px in all_notches:
        if (py, px) not in seen:
            seen.add((py, px))
            unique_notches.append((py, px))

    # Generate filter transfer function H(u, v)
    if unique_notches:
        filter_h = create_notch_filter(
            (h, w),
            peaks=unique_notches,
            notch_radius=notch_radius,
            suppression_strength=suppression_strength,
            min_frequency=min_frequency,
        )
    else:
        filter_h = np.ones((h, w), dtype=np.float32)

    # Apply filter
    if luminance_only:
        f_filtered_shift = f_shift * filter_h
        f_filtered = np.fft.ifftshift(f_filtered_shift)
        y_recon = np.fft.ifft2(f_filtered).real
        y_recon = np.clip(y_recon, 0, 255).astype(np.uint8)

        ycrcb[:, :, 0] = y_recon
        result = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)
    else:
        result_channels = []
        for ch in range(3):
            c_f = np.fft.fft2(img[:, :, ch].astype(np.float32))
            c_f_shift = np.fft.fftshift(c_f)
            c_f_filtered_shift = c_f_shift * filter_h
            c_recon = np.fft.ifft2(np.fft.ifftshift(c_f_filtered_shift)).real
            result_channels.append(np.clip(c_recon, 0, 255).astype(np.uint8))
        result = cv2.merge(result_channels)

    # Generate magnitude spectrum visualization
    spectrum_viz = create_spectrum_visualization(
        f_shift,
        peaks=unique_notches,
        min_frequency=min_frequency,
    )

    return result, spectrum_viz, unique_notches
