"""Synthetic Dataset Generator for Screen Moiré Removal Evaluation.

Generates realistic screen content test patterns:
1. Small text & typography
2. Spreadsheet gridlines and table cells
3. UI elements, buttons, checkboxes, and sliders
4. Code editor with monospace syntax highlighting
5. Geometric calibration shapes and test patterns

Also applies realistic synthetic moiré interference:
- Periodic 2D spatial beating frequencies
- Chromatic Bayer subpixel phase shifts
- Radial / curved perspective wave distortion
"""

import os
from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np


def add_moire_pattern(
    image: np.ndarray,
    pattern_type: str = "composite",
    strength: float = 0.35,
    freq1: float = 0.08,
    angle1: float = 23.0,
    freq2: float = 0.12,
    angle2: float = -38.0,
    color_shift: bool = True,
) -> np.ndarray:
    """Add synthetic periodic screen moiré patterns to a clean image.

    Args:
        image: Clean input image (BGR, uint8).
        pattern_type: 'grid_beating', 'radial', 'chromatic', or 'composite'.
        strength: Amplitude of moiré interference [0.0 - 1.0].
        freq1: Spatial frequency 1 (cycles/pixel).
        angle1: Orientation angle in degrees for wave 1.
        freq2: Spatial frequency 2 (cycles/pixel).
        angle2: Orientation angle in degrees for wave 2.
        color_shift: Enable RGB chromatic phase interference.

    Returns:
        Moiréd image (BGR, uint8).
    """
    h, w = image.shape[:2]
    y_coords, x_coords = np.mgrid[0:h, 0:w].astype(np.float32)

    # Convert angles to radians
    rad1 = np.deg2rad(angle1)
    rad2 = np.deg2rad(angle2)

    # Projected coordinates along wave vectors
    u1 = x_coords * np.cos(rad1) + y_coords * np.sin(rad1)
    u2 = x_coords * np.cos(rad2) + y_coords * np.sin(rad2)

    # Primary 2D periodic sinusoidal interference
    wave1 = np.sin(2.0 * np.pi * freq1 * u1)
    wave2 = np.cos(2.0 * np.pi * freq2 * u2)

    # Secondary beating / cross-modulation
    beating = wave1 * wave2

    # Radial curved lens/screen distortion moiré
    cy, cx = h * 0.45, w * 0.55
    r_sq = ((x_coords - cx) / w) ** 2 + ((y_coords - cy) / h) ** 2
    radial_wave = np.sin(180.0 * r_sq + 2.0 * np.pi * freq1 * u1)

    if pattern_type == "grid_beating":
        base_pattern = 0.6 * wave1 + 0.4 * wave2
    elif pattern_type == "radial":
        base_pattern = 0.7 * radial_wave + 0.3 * wave1
    elif pattern_type == "chromatic":
        base_pattern = wave1
    else:  # composite
        base_pattern = 0.45 * beating + 0.35 * radial_wave + 0.20 * wave1

    img_f = image.astype(np.float32)

    if color_shift:
        # Chromatic subpixel phase shifts simulate Bayer sensor vs display RGB stripe beating
        phase_r = 0.0
        phase_g = 2.0 * np.pi / 3.0
        phase_b = 4.0 * np.pi / 3.0

        shift_r = np.sin(2.0 * np.pi * freq1 * u1 + phase_r) * 0.5 + base_pattern * 0.5
        shift_g = np.sin(2.0 * np.pi * freq1 * u1 + phase_g) * 0.5 + base_pattern * 0.5
        shift_b = np.sin(2.0 * np.pi * freq1 * u1 + phase_b) * 0.5 + base_pattern * 0.5

        # BGR ordering in OpenCV
        moire_layers = [shift_b, shift_g, shift_r]
        out_channels = []
        for ch_idx, pattern_layer in enumerate(moire_layers):
            channel = img_f[:, :, ch_idx]
            # Multiplicative + additive modulation
            modulated = channel * (1.0 + strength * 0.5 * pattern_layer) + (strength * 40.0 * pattern_layer)
            out_channels.append(np.clip(modulated, 0, 255))
        result = np.stack(out_channels, axis=2).astype(np.uint8)
    else:
        # Monochrome intensity ripple
        moire_2d = base_pattern[:, :, np.newaxis]
        modulated = img_f * (1.0 + strength * 0.5 * moire_2d) + (strength * 40.0 * moire_2d)
        result = np.clip(modulated, 0, 255).astype(np.uint8)

    return result


def generate_text_document_image(width: int = 800, height: int = 600) -> np.ndarray:
    """Generate a synthetic text document simulating a clean webpage or reader."""
    img = np.full((height, width, 3), 250, dtype=np.uint8)

    # Document Header
    cv2.rectangle(img, (40, 30), (width - 40, 80), (240, 240, 240), -1)
    cv2.putText(img, "Research Brief: Screen Moiré Pattern Removal", (55, 65),
                cv2.FONT_HERSHEY_DUPLEX, 0.75, (40, 40, 40), 2, cv2.LINE_AA)

    # Subheading
    cv2.putText(img, "1. Executive Summary & Problem Formulation", (50, 120),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (20, 90, 170), 2, cv2.LINE_AA)

    # Body paragraphs
    body_lines = [
        "Digital photography of LCD/OLED screens frequently introduces severe moire artifacts.",
        "These patterns arise from the high-frequency beating between the screen subpixel pitch",
        "and the digital camera Bayer color filter array (CFA). The resulting spatial alias waves",
        "severely degrade text legibility, fine typography, and edge definition.",
        "",
        "Key challenges in screen moire removal include preserving sharp high-frequency text edges",
        "while simultaneously suppressing chromatic fringes and non-linear periodic bands.",
        "Baseline spatial filtering often blurs essential strokes, whereas frequency-domain notch",
        "filtering provides targeted attenuation of periodic Fourier harmonics.",
    ]

    y_pos = 155
    for line in body_lines:
        if line:
            cv2.putText(img, line, (50, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (60, 60, 60), 1, cv2.LINE_AA)
        y_pos += 26

    # Section 2
    cv2.putText(img, "2. Comparative Algorithm Benchmarks", (50, y_pos + 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (20, 90, 170), 2, cv2.LINE_AA)
    y_pos += 55

    bullet_points = [
        "A. Spatial Gaussian Blur (YCrCb luminance decoupling)",
        "B. 2D Discrete Fast Fourier Transform (FFT) Gaussian Notch Reject",
        "C. Multiresolution Wavelet Detail Coefficient Soft Thresholding",
        "D. Edge-Aware Adaptive Guided Bilateral Blending",
    ]

    for pt in bullet_points:
        cv2.circle(img, (60, y_pos - 4), 3, (20, 90, 170), -1, cv2.LINE_AA)
        cv2.putText(img, pt, (75, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.43, (50, 50, 50), 1, cv2.LINE_AA)
        y_pos += 28

    # Small footnote
    cv2.line(img, (40, height - 50), (width - 40, height - 50), (210, 210, 210), 1)
    cv2.putText(img, "Confidential - Screen Optical Diagnostics Suite - Page 1 of 4",
                (50, height - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (140, 140, 140), 1, cv2.LINE_AA)

    return img


def generate_spreadsheet_image(width: int = 800, height: int = 600) -> np.ndarray:
    """Generate a synthetic spreadsheet with rows, columns, and data."""
    img = np.full((height, width, 3), 255, dtype=np.uint8)

    # Title Bar
    cv2.rectangle(img, (0, 0), (width, 40), (45, 120, 65), -1)
    cv2.putText(img, "Financial_Projection_Q4.xlsx - Sheets", (15, 26),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

    # Formula bar
    cv2.rectangle(img, (0, 40), (width, 70), (245, 245, 245), -1)
    cv2.line(img, (0, 70), (width, 70), (200, 200, 200), 1)
    cv2.putText(img, "fx  =SUM(D4:D18) * 1.15", (15, 62),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, (90, 90, 90), 1, cv2.LINE_AA)

    # Grid parameters
    col_widths = [50, 150, 110, 110, 120, 120, 140]
    row_height = 28
    start_y = 70
    headers = ["#", "Quarterly Dept", "Budget ($)", "Actual ($)", "Variance", "Growth (%)", "Audit Status"]

    # Header row
    cv2.rectangle(img, (0, start_y), (width, start_y + row_height), (225, 235, 225), -1)
    x = 0
    for idx, (cw, h_title) in enumerate(zip(col_widths, headers)):
        cv2.line(img, (x + cw, start_y), (x + cw, height), (215, 215, 215), 1)
        cv2.putText(img, h_title, (x + 8, start_y + 19),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (30, 70, 40), 1, cv2.LINE_AA)
        x += cw
    cv2.line(img, (0, start_y + row_height), (width, start_y + row_height), (180, 180, 180), 2)

    departments = [
        ("Engineering", "450,000", "438,200", "+11,800", "+8.4%", "Verified"),
        ("Product R&D", "320,000", "329,500", "-9,500", "+12.1%", "Under Review"),
        ("Infrastructure", "210,000", "198,400", "+11,600", "+4.2%", "Verified"),
        ("QA & Testing", "140,000", "137,800", "+2,200", "+3.1%", "Verified"),
        ("Customer Success", "180,000", "185,100", "-5,100", "+6.7%", "Flagged"),
        ("Sales Enterprise", "550,000", "592,400", "-42,400", "+24.8%", "Verified"),
        ("Marketing Brand", "280,000", "275,000", "+5,000", "+15.3%", "Verified"),
        ("Legal Compliance", "95,000", "91,200", "+3,800", "+1.0%", "Verified"),
        ("Human Resources", "125,000", "122,800", "+2,200", "+5.5%", "Verified"),
        ("Executive Admin", "160,000", "158,900", "+1,100", "+2.9%", "Verified"),
        ("Design Systems", "110,000", "108,300", "+1,700", "+9.4%", "Verified"),
        ("Security Ops", "190,000", "184,700", "+5,300", "+14.0%", "Verified"),
    ]

    curr_y = start_y + row_height
    for row_idx, row_vals in enumerate(departments):
        # Alternate row fill
        if row_idx % 2 == 1:
            cv2.rectangle(img, (0, curr_y), (width, curr_y + row_height), (248, 250, 248), -1)

        # Row number
        cv2.putText(img, str(row_idx + 1), (15, curr_y + 19),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (120, 120, 120), 1, cv2.LINE_AA)

        # Values
        curr_x = col_widths[0]
        for val_idx, val in enumerate(row_vals):
            color = (40, 40, 40)
            if "-" in val and "$" in val:
                color = (40, 40, 200)  # Red for negative variance
            elif "Verified" in val:
                color = (30, 120, 40)
            elif "Flagged" in val:
                color = (30, 80, 210)

            cv2.putText(img, val, (curr_x + 8, curr_y + 19),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, color, 1, cv2.LINE_AA)
            curr_x += col_widths[val_idx + 1]

        cv2.line(img, (0, curr_y + row_height), (width, curr_y + row_height), (220, 220, 220), 1)
        curr_y += row_height

    return img


def generate_ui_elements_image(width: int = 800, height: int = 600) -> np.ndarray:
    """Generate a clean software user interface with buttons, toggles, and panels."""
    img = np.full((height, width, 3), 242, dtype=np.uint8)

    # Window Top Bar (macOS style)
    cv2.rectangle(img, (0, 0), (width, 42), (228, 228, 228), -1)
    cv2.line(img, (0, 42), (width, 42), (200, 200, 200), 1)
    cv2.circle(img, (20, 21), 6, (75, 75, 235), -1, cv2.LINE_AA)   # Close
    cv2.circle(img, (40, 21), 6, (80, 190, 240), -1, cv2.LINE_AA)  # Min
    cv2.circle(img, (60, 21), 6, (80, 200, 100), -1, cv2.LINE_AA)  # Max
    cv2.putText(img, "Image Processor Preferences - v2.4", (width // 2 - 130, 26),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (60, 60, 60), 1, cv2.LINE_AA)

    # Sidebar
    cv2.rectangle(img, (0, 43), (180, height), (235, 235, 238), -1)
    cv2.line(img, (180, 43), (180, height), (210, 210, 215), 1)

    sidebar_items = ["Dashboard", "Algorithms", "Frequency FFT", "Wavelet DWT", "Edge Filtering", "Diagnostics", "Settings"]
    sy = 80
    for idx, item in enumerate(sidebar_items):
        if idx == 1:
            cv2.rectangle(img, (8, sy - 18), (172, sy + 10), (220, 225, 245), -1)
            cv2.putText(img, f"> {item}", (20, sy), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 60, 20), 1, cv2.LINE_AA)
        else:
            cv2.putText(img, f"  {item}", (20, sy), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (70, 70, 70), 1, cv2.LINE_AA)
        sy += 36

    # Main Card
    cv2.rectangle(img, (210, 65), (width - 30, height - 30), (255, 255, 255), -1)
    cv2.rectangle(img, (210, 65), (width - 30, height - 30), (215, 215, 220), 1)

    # Card Title
    cv2.putText(img, "Adaptive Moiré Suppression Configuration", (235, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 0.62, (30, 30, 30), 2, cv2.LINE_AA)

    # Checkboxes
    cb_items = [
        ("Enable 2D FFT periodic harmonic notch filtering", True),
        ("Preserve high-contrast typography edges via Canny mask", True),
        ("Apply multi-scale bilateral luminance smoothing", False),
        ("Decouple chroma channels (YCrCb color space)", True),
    ]

    cby = 140
    for label, checked in cb_items:
        cv2.rectangle(img, (235, cby - 12), (251, cby + 4), (160, 160, 160), 1)
        if checked:
            cv2.rectangle(img, (238, cby - 9), (248, cby + 1), (190, 80, 20), -1)
            cv2.putText(img, "x", (240, cby), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)
        cv2.putText(img, label, (265, cby), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (50, 50, 50), 1, cv2.LINE_AA)
        cby += 34

    # Slider Controls
    slider_labels = ["Filter Strength (75%)", "Edge Retention Threshold (50)", "Wavelet Shrinkage (20.0)"]
    slider_vals = [0.75, 0.50, 0.40]
    for sl_label, val in zip(slider_labels, slider_vals):
        cv2.putText(img, sl_label, (235, cby), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (70, 70, 70), 1, cv2.LINE_AA)
        cby += 12
        # Track
        cv2.rectangle(img, (235, cby), (width - 60, cby + 6), (220, 220, 225), -1)
        active_w = int((width - 60 - 235) * val)
        cv2.rectangle(img, (235, cby), (235 + active_w, cby + 6), (190, 80, 20), -1)
        cv2.circle(img, (235 + active_w, cby + 3), 7, (245, 245, 245), -1, cv2.LINE_AA)
        cv2.circle(img, (235 + active_w, cby + 3), 7, (180, 70, 15), 1, cv2.LINE_AA)
        cby += 32

    # Action Buttons
    btn_y = height - 75
    # Primary Button (Save Changes)
    cv2.rectangle(img, (width - 170, btn_y), (width - 50, btn_y + 32), (195, 85, 25), -1)
    cv2.putText(img, "Apply Filters", (width - 152, btn_y + 21),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA)
    # Secondary Button
    cv2.rectangle(img, (width - 290, btn_y), (width - 185, btn_y + 32), (240, 240, 245), -1)
    cv2.rectangle(img, (width - 290, btn_y), (width - 185, btn_y + 32), (190, 190, 195), 1)
    cv2.putText(img, "Reset Defaults", (width - 280, btn_y + 21),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (80, 80, 80), 1, cv2.LINE_AA)

    return img


def generate_code_editor_image(width: int = 800, height: int = 600) -> np.ndarray:
    """Generate a synthetic dark-theme IDE code editor with syntax highlighting."""
    img = np.full((height, width, 3), 32, dtype=np.uint8)  # Dark background (BGR 32,32,32)

    # Top Tabs Bar
    cv2.rectangle(img, (0, 0), (width, 36), (24, 24, 24), -1)
    # Active Tab
    cv2.rectangle(img, (45, 0), (220, 36), (32, 32, 32), -1)
    cv2.line(img, (45, 0), (220, 0), (220, 130, 40), 2)  # Active tab indicator
    cv2.putText(img, "moire_filter.py", (65, 23),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, (220, 220, 220), 1, cv2.LINE_AA)

    # Inactive Tab
    cv2.putText(img, "metrics.py", (245, 23),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, (130, 130, 130), 1, cv2.LINE_AA)

    # Sidebar gutter
    cv2.rectangle(img, (0, 36), (45, height - 25), (28, 28, 28), -1)
    cv2.line(img, (45, 36), (45, height - 25), (50, 50, 50), 1)

    code_lines = [
        [("import ", (200, 120, 200)), ("numpy ", (120, 190, 240)), ("as ", (200, 120, 200)), ("np", (210, 210, 210))],
        [("from ", (200, 120, 200)), ("scipy.fft ", (120, 190, 240)), ("import ", (200, 120, 200)), ("fft2, ifft2", (210, 210, 210))],
        [("", (0, 0, 0))],
        [("def ", (210, 140, 80)), ("suppress_moire_harmonics", (100, 220, 255)), ("(image, radius=15):", (210, 210, 210))],
        [("    # Compute 2D Fourier transform", (100, 150, 100))],
        [("    f_transform = ", (210, 210, 210)), ("np.fft.fft2", (100, 220, 255)), ("(image)", (210, 210, 210))],
        [("    f_shifted = ", (210, 210, 210)), ("np.fft.fftshift", (100, 220, 255)), ("(f_transform)", (210, 210, 210))],
        [("    h, w = image.shape[:2]", (210, 210, 210))],
        [("    cy, cx = h // 2, w // 2", (210, 210, 210))],
        [("", (0, 0, 0))],
        [("    # Construct Gaussian notch reject mask", (100, 150, 100))],
        [("    y, x = ", (210, 210, 210)), ("np.ogrid", (100, 220, 255)), ("[:h, :w]", (210, 210, 210))],
        [("    dist_sq = (y - cy)**2 + (x - cx)**2", (210, 210, 210))],
        [("    mask = ", (210, 210, 210)), ("1.0 - np.exp", (100, 220, 255)), ("(-dist_sq / (2 * radius**2))", (210, 210, 210))],
        [("", (0, 0, 0))],
        [("    # Filter and reconstruct", (100, 150, 100))],
        [("    filtered = f_shifted * mask", (210, 210, 210))],
        [("    recon = ", (210, 210, 210)), ("np.fft.ifft2", (100, 220, 255)), ("(np.fft.ifftshift(filtered)).real", (210, 210, 210))],
        [("    ", (0, 0, 0)), ("return ", (200, 120, 200)), ("np.clip(recon, 0, 255).astype(np.uint8)", (210, 210, 210))],
    ]

    line_y = 65
    for idx, tokens in enumerate(code_lines):
        # Line number
        cv2.putText(img, f"{idx+1:>2}", (12, line_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (90, 90, 90), 1, cv2.LINE_AA)

        # Syntax highlighted tokens
        token_x = 60
        for text, color in tokens:
            if text:
                cv2.putText(img, text, (token_x, line_y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.42, color, 1, cv2.LINE_AA)
                token_x += int(len(text) * 8.5)
        line_y += 24

    # Bottom status bar
    cv2.rectangle(img, (0, height - 24), (width, height), (0, 122, 204), -1)
    cv2.putText(img, "UTF-8   Python 3.9.6   Spaces: 4   LF   Main Branch", (15, height - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1, cv2.LINE_AA)

    return img


def generate_geometric_shapes_image(width: int = 800, height: int = 600) -> np.ndarray:
    """Generate high-contrast geometric calibration patterns and radial lines."""
    img = np.full((height, width, 3), 245, dtype=np.uint8)

    # Title
    cv2.putText(img, "Resolution & Spatial Frequency Calibration Chart", (40, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (30, 30, 30), 2, cv2.LINE_AA)

    # Concentric rings (Left side)
    center1 = (200, 220)
    for r in range(15, 160, 12):
        color = (30, 30, 30) if (r // 12) % 2 == 0 else (220, 220, 220)
        cv2.circle(img, center1, r, color, 2, cv2.LINE_AA)

    # Siemens star / radial spokes (Right side)
    center2 = (580, 220)
    for ang in range(0, 360, 10):
        rad = np.deg2rad(ang)
        x2 = int(center2[0] + 140 * np.cos(rad))
        y2 = int(center2[1] + 140 * np.sin(rad))
        cv2.line(img, center2, (x2, y2), (40, 40, 40), 1, cv2.LINE_AA)

    # Fine checkerboard patch (Center bottom)
    cb_x, cb_y = 60, 410
    tile_size = 14
    for r in range(8):
        for c in range(16):
            if (r + c) % 2 == 0:
                cv2.rectangle(img,
                              (cb_x + c * tile_size, cb_y + r * tile_size),
                              (cb_x + (c + 1) * tile_size, cb_y + (r + 1) * tile_size),
                              (20, 20, 20), -1)

    # Calibration gradient ramp (Right bottom)
    ramp_x, ramp_y, ramp_w, ramp_h = 360, 410, 380, 40
    for i in range(ramp_w):
        val = int(255.0 * i / ramp_w)
        cv2.line(img, (ramp_x + i, ramp_y), (ramp_x + i, ramp_y + ramp_h), (val, val, val), 1)
    cv2.rectangle(img, (ramp_x, ramp_y), (ramp_x + ramp_w, ramp_y + ramp_h), (40, 40, 40), 1)

    # Step wedges
    wedge_y = 470
    step_w = ramp_w // 8
    for i in range(8):
        val = int(255 * i / 7)
        cv2.rectangle(img, (ramp_x + i * step_w, wedge_y), (ramp_x + (i + 1) * step_w, wedge_y + 30), (val, val, val), -1)
        cv2.rectangle(img, (ramp_x + i * step_w, wedge_y), (ramp_x + (i + 1) * step_w, wedge_y + 30), (100, 100, 100), 1)

    return img


def generate_all_synthetic_samples(
    width: int = 800,
    height: int = 600,
) -> List[Dict[str, np.ndarray]]:
    """Generate all 5 synthetic test patterns with clean and moiréd versions.

    Returns:
        List of dicts: [{'name': ..., 'clean': ndarray, 'moire': ndarray}, ...]
    """
    generators = [
        ("01_small_text", generate_text_document_image, {"freq1": 0.08, "angle1": 25.0, "strength": 0.35}),
        ("02_spreadsheet", generate_spreadsheet_image, {"freq1": 0.10, "angle1": -18.0, "strength": 0.38}),
        ("03_ui_elements", generate_ui_elements_image, {"freq1": 0.07, "angle1": 33.0, "strength": 0.32}),
        ("04_code_editor", generate_code_editor_image, {"freq1": 0.09, "angle1": -42.0, "strength": 0.34}),
        ("05_geometric_shapes", generate_geometric_shapes_image, {"freq1": 0.06, "angle1": 15.0, "strength": 0.36}),
    ]

    samples = []
    for name, gen_fn, moire_params in generators:
        clean = gen_fn(width=width, height=height)
        moire = add_moire_pattern(clean, pattern_type="composite", **moire_params)
        samples.append({
            "name": name,
            "clean": clean,
            "moire": moire,
        })

    return samples


def save_synthetic_dataset(output_dir: str, width: int = 800, height: int = 600) -> List[str]:
    """Generate and write synthetic test images to disk."""
    os.makedirs(output_dir, exist_ok=True)
    samples = generate_all_synthetic_samples(width=width, height=height)
    saved_files = []

    for item in samples:
        name = item["name"]
        clean_path = os.path.join(output_dir, f"{name}_clean.png")
        moire_path = os.path.join(output_dir, f"{name}_moire.png")

        cv2.imwrite(clean_path, item["clean"])
        cv2.imwrite(moire_path, item["moire"])

        saved_files.append(clean_path)
        saved_files.append(moire_path)

    return saved_files


if __name__ == "__main__":
    target_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated")
    print(f"Generating synthetic images in {target_dir}...")
    files = save_synthetic_dataset(target_dir)
    print(f"Successfully generated {len(files)} files:")
    for f in files:
        print(f" - {os.path.basename(f)}")
