"""Unified Processing Pipeline and Dispatcher for Moiré Removal Algorithms.

This module provides a unified interface to execute, benchmark, and parameterize
all available screen moiré reduction algorithms.
"""

import time
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

try:
    from processing.gaussian import gaussian_filter, _ensure_bgr_uint8
    from processing.fft_filter import fft_notch_filter, create_spectrum_visualization
    from processing.wavelet import wavelet_filter, SUPPORTED_WAVELETS
    from processing.edge_aware import edge_aware_filter
except ImportError:
    from backend.processing.gaussian import gaussian_filter, _ensure_bgr_uint8
    from backend.processing.fft_filter import fft_notch_filter, create_spectrum_visualization
    from backend.processing.wavelet import wavelet_filter, SUPPORTED_WAVELETS
    from backend.processing.edge_aware import edge_aware_filter

ALGORITHM_METADATA = {
    "gaussian": {
        "id": "gaussian",
        "name": "Gaussian Smoothing",
        "description": "Baseline smoothing filter with luminance-only or multi-channel blurring.",
        "category": "Spatial Baseline",
        "parameters": [
            {
                "name": "kernel_size",
                "label": "Kernel Size",
                "type": "int",
                "default": 5,
                "min": 3,
                "max": 31,
                "step": 2,
                "description": "Size of the Gaussian blur kernel (odd integer)."
            },
            {
                "name": "sigma",
                "label": "Sigma",
                "type": "float",
                "default": 1.5,
                "min": 0.5,
                "max": 10.0,
                "step": 0.1,
                "description": "Standard deviation of the Gaussian filter."
            },
            {
                "name": "luminance_only",
                "label": "Luminance Only",
                "type": "bool",
                "default": True,
                "description": "Blur only the luminance channel (Y in YCrCb) to preserve color sharpness."
            }
        ]
    },
    "fft": {
        "id": "fft",
        "name": "FFT Notch Filtering",
        "description": "Frequency-domain notch reject filtering targeting periodic moiré peaks.",
        "category": "Frequency Domain",
        "parameters": [
            {
                "name": "auto_detect",
                "label": "Auto-Detect Peaks",
                "type": "bool",
                "default": True,
                "description": "Automatically detect periodic moiré frequencies in the 2D FFT spectrum."
            },
            {
                "name": "notch_radius",
                "label": "Notch Radius",
                "type": "int",
                "default": 15,
                "min": 5,
                "max": 50,
                "step": 1,
                "description": "Gaussian notch width in frequency space."
            },
            {
                "name": "suppression_strength",
                "label": "Suppression Strength",
                "type": "float",
                "default": 0.9,
                "min": 0.0,
                "max": 1.0,
                "step": 0.05,
                "description": "Notch attenuation strength (1.0 = full suppression)."
            },
            {
                "name": "min_frequency",
                "label": "DC Protection Radius",
                "type": "int",
                "default": 20,
                "min": 10,
                "max": 100,
                "step": 5,
                "description": "Low-frequency boundary around DC to preserve base image structures."
            },
            {
                "name": "peak_threshold",
                "label": "Peak Sensitivity",
                "type": "float",
                "default": 0.85,
                "min": 0.5,
                "max": 0.99,
                "step": 0.01,
                "description": "Relative threshold for automated peak detection."
            },
            {
                "name": "luminance_only",
                "label": "Luminance Only",
                "type": "bool",
                "default": True,
                "description": "Apply notch filter only in luminance space."
            }
        ]
    },
    "wavelet": {
        "id": "wavelet",
        "name": "Wavelet Denoising",
        "description": "Multi-level 2D Discrete Wavelet Transform detail coefficient thresholding.",
        "category": "Multiresolution",
        "parameters": [
            {
                "name": "wavelet",
                "label": "Wavelet Family",
                "type": "select",
                "options": ["db1", "db2", "db4", "sym4", "coif1", "bior1.3"],
                "default": "db4",
                "description": "Mother wavelet function."
            },
            {
                "name": "level",
                "label": "Decomposition Level",
                "type": "int",
                "default": 2,
                "min": 1,
                "max": 5,
                "step": 1,
                "description": "Number of multiresolution decomposition levels."
            },
            {
                "name": "threshold_mode",
                "label": "Threshold Mode",
                "type": "select",
                "options": ["soft", "hard"],
                "default": "soft",
                "description": "Thresholding nonlinearity (soft or hard shrink)."
            },
            {
                "name": "threshold_value",
                "label": "Threshold Value",
                "type": "float",
                "default": 20.0,
                "min": 5.0,
                "max": 100.0,
                "step": 1.0,
                "description": "Detail coefficient noise threshold."
            },
            {
                "name": "luminance_only",
                "label": "Luminance Only",
                "type": "bool",
                "default": True,
                "description": "Apply wavelet thresholding to luminance channel only."
            }
        ]
    },
    "edge_aware": {
        "id": "edge_aware",
        "name": "Edge-Aware Adaptive Filtering",
        "description": "Hybrid bilateral and guided filter with soft edge-gradient blending.",
        "category": "Edge-Preserving Spatial",
        "parameters": [
            {
                "name": "filter_strength",
                "label": "Filter Strength",
                "type": "int",
                "default": 75,
                "min": 1,
                "max": 100,
                "step": 1,
                "description": "Overall smoothing strength blend factor."
            },
            {
                "name": "edge_threshold",
                "label": "Edge Threshold",
                "type": "int",
                "default": 50,
                "min": 10,
                "max": 200,
                "step": 5,
                "description": "Gradient sensitivity threshold for edge retention."
            },
            {
                "name": "bilateral_d",
                "label": "Bilateral Diameter",
                "type": "int",
                "default": 9,
                "min": 5,
                "max": 15,
                "step": 2,
                "description": "Diameter of bilateral filter pixel neighborhood."
            },
            {
                "name": "bilateral_sigma_color",
                "label": "Bilateral Color Sigma",
                "type": "float",
                "default": 75.0,
                "min": 25.0,
                "max": 150.0,
                "step": 5.0,
                "description": "Bilateral filter range sigma."
            },
            {
                "name": "bilateral_sigma_space",
                "label": "Bilateral Space Sigma",
                "type": "float",
                "default": 75.0,
                "min": 25.0,
                "max": 150.0,
                "step": 5.0,
                "description": "Bilateral filter spatial domain sigma."
            },
            {
                "name": "guided_radius",
                "label": "Guided Radius",
                "type": "int",
                "default": 4,
                "min": 2,
                "max": 16,
                "step": 1,
                "description": "Guided filter window radius."
            },
            {
                "name": "guided_eps",
                "label": "Guided Regularization (eps)",
                "type": "float",
                "default": 0.04,
                "min": 0.001,
                "max": 1.0,
                "step": 0.005,
                "description": "Guided filter smoothness regularization factor."
            },
            {
                "name": "use_guided",
                "label": "Enable Guided Filter",
                "type": "bool",
                "default": True,
                "description": "Apply secondary guided filtering stage."
            },
            {
                "name": "luminance_only",
                "label": "Luminance Only",
                "type": "bool",
                "default": False,
                "description": "Apply smoothing primarily to luminance channel."
            }
        ]
    }
}


def get_available_algorithms() -> List[Dict[str, Any]]:
    """Return list of supported algorithms and their parameter specifications."""
    return list(ALGORITHM_METADATA.values())


def process_image(
    image: np.ndarray,
    algorithm: str,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Execute a selected moiré removal algorithm on an input image.

    Args:
        image: Input image (BGR uint8).
        algorithm: Identifier ('gaussian', 'fft', 'wavelet', 'edge_aware').
        params: Optional dictionary of algorithm hyperparameters.

    Returns:
        Dictionary containing:
        - 'image': Filtered image (BGR uint8)
        - 'spectrum': Magnitude spectrum visualization (BGR uint8, or None)
        - 'processing_time': Execution time in seconds
        - 'metadata': Dictionary with algorithm-specific execution details
    """
    img = _ensure_bgr_uint8(image)
    params = params.copy() if params else {}
    algo_key = algorithm.lower().strip()

    if algo_key not in ALGORITHM_METADATA:
        raise ValueError(f"Unknown algorithm '{algorithm}'. Available: {list(ALGORITHM_METADATA.keys())}")

    start_time = time.perf_counter()
    spectrum_img = None
    metadata: Dict[str, Any] = {"algorithm": algo_key}

    if algo_key == "gaussian":
        filtered = gaussian_filter(
            img,
            kernel_size=int(params.get("kernel_size", 5)),
            sigma=float(params.get("sigma", 1.5)),
            luminance_only=bool(params.get("luminance_only", True)),
        )

    elif algo_key == "fft":
        filtered, spectrum_img, notches = fft_notch_filter(
            img,
            auto_detect=bool(params.get("auto_detect", True)),
            notch_radius=int(params.get("notch_radius", 15)),
            suppression_strength=float(params.get("suppression_strength", 0.9)),
            min_frequency=int(params.get("min_frequency", 20)),
            peak_threshold=float(params.get("peak_threshold", 0.85)),
            manual_notches=params.get("manual_notches", None),
            luminance_only=bool(params.get("luminance_only", True)),
        )
        metadata["detected_peaks_count"] = len(notches)
        metadata["notches"] = notches

    elif algo_key == "wavelet":
        filtered = wavelet_filter(
            img,
            wavelet=str(params.get("wavelet", "db4")),
            level=int(params.get("level", 2)),
            threshold_mode=str(params.get("threshold_mode", "soft")),
            threshold_value=float(params.get("threshold_value", 20.0)),
            luminance_only=bool(params.get("luminance_only", True)),
            per_level_thresholds=params.get("per_level_thresholds", None),
        )

    elif algo_key == "edge_aware":
        filtered = edge_aware_filter(
            img,
            filter_strength=int(params.get("filter_strength", 75)),
            edge_threshold=int(params.get("edge_threshold", 50)),
            bilateral_d=int(params.get("bilateral_d", 9)),
            bilateral_sigma_color=float(params.get("bilateral_sigma_color", 75.0)),
            bilateral_sigma_space=float(params.get("bilateral_sigma_space", 75.0)),
            guided_radius=int(params.get("guided_radius", 4)),
            guided_eps=float(params.get("guided_eps", 0.04)),
            use_guided=bool(params.get("use_guided", True)),
            multi_scale=bool(params.get("multi_scale", False)),
            luminance_only=bool(params.get("luminance_only", False)),
        )

    elapsed = time.perf_counter() - start_time
    metadata["processing_time"] = round(elapsed, 4)

    return {
        "image": filtered,
        "spectrum": spectrum_img,
        "processing_time": elapsed,
        "metadata": metadata,
    }
