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
    from processing.adaptive_model import demoire_adaptive as demoire_uhdm
except ImportError:
    from backend.processing.gaussian import gaussian_filter, _ensure_bgr_uint8
    from backend.processing.fft_filter import fft_notch_filter, create_spectrum_visualization
    from backend.processing.wavelet import wavelet_filter, SUPPORTED_WAVELETS
    from backend.processing.edge_aware import edge_aware_filter
    from backend.processing.adaptive_model import demoire_adaptive as demoire_uhdm

ALGORITHM_METADATA = {
    "auto_demoire": {
        "id": "auto_demoire",
        "name": "Adaptive Screen Demoiré Filter",
        "description": "Multi-scale adaptive filtering algorithm designed to eliminate screen moiré artifacts while preserving sharp typography and line borders.",
        "category": "Adaptive Filter",
        "parameters": []
    },
    "gaussian": {
        "id": "gaussian",
        "name": "Gaussian Spatial Smoothing",
        "description": "Classical Gaussian blurring baseline for high-frequency noise attenuation.",
        "category": "Spatial Baseline",
        "parameters": [
            {"name": "kernel_size", "label": "Kernel Size", "type": "int", "default": 5, "min": 3, "max": 31, "step": 2},
            {"name": "sigma", "label": "Sigma (σ)", "type": "float", "default": 1.5, "min": 0.1, "max": 10.0, "step": 0.1},
            {"name": "luminance_only", "label": "Luminance Only", "type": "bool", "default": True}
        ]
    },
    "fft": {
        "id": "fft",
        "name": "2D Fourier Notch Filtering",
        "description": "Frequency-domain notch reject filter for periodic screen interference peaks.",
        "category": "Frequency Domain",
        "parameters": [
            {"name": "auto_detect", "label": "Auto-Detect Peaks", "type": "bool", "default": True},
            {"name": "notch_radius", "label": "Notch Radius", "type": "int", "default": 15, "min": 3, "max": 60, "step": 1},
            {"name": "suppression_strength", "label": "Suppression Strength", "type": "float", "default": 0.9, "min": 0.0, "max": 1.0, "step": 0.05},
            {"name": "luminance_only", "label": "Luminance Only", "type": "bool", "default": True}
        ]
    },
    "wavelet": {
        "id": "wavelet",
        "name": "Wavelet Multiscale Shrinkage",
        "description": "Multiscale subband decomposition (PyWavelets) with soft/hard thresholding.",
        "category": "Multiscale Wavelet",
        "parameters": [
            {"name": "wavelet", "label": "Wavelet Family", "type": "select", "default": "db4", "options": ["db1", "db2", "db4", "sym4", "coif2", "bior2.2"]},
            {"name": "level", "label": "Decomposition Level", "type": "int", "default": 2, "min": 1, "max": 4, "step": 1},
            {"name": "threshold_mode", "label": "Threshold Mode", "type": "select", "default": "soft", "options": ["soft", "hard"]},
            {"name": "threshold_value", "label": "Threshold (λ)", "type": "float", "default": 20.0, "min": 1.0, "max": 100.0, "step": 1.0},
            {"name": "luminance_only", "label": "Luminance Only", "type": "bool", "default": True}
        ]
    },
    "edge_aware": {
        "id": "edge_aware",
        "name": "Edge-Aware Guided Filter",
        "description": "Bilateral and guided edge-preserving filtering with gradient protection.",
        "category": "Edge-Preserving",
        "parameters": [
            {"name": "filter_strength", "label": "Filter Strength", "type": "int", "default": 75, "min": 10, "max": 150, "step": 5},
            {"name": "edge_threshold", "label": "Edge Threshold", "type": "int", "default": 50, "min": 10, "max": 150, "step": 5},
            {"name": "use_guided", "label": "Use Guided Filter", "type": "bool", "default": True},
            {"name": "luminance_only", "label": "Luminance Only", "type": "bool", "default": False}
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
    """Execute a selected moiré removal algorithm on an input image."""
    img = _ensure_bgr_uint8(image)
    params = params.copy() if params else {}
    algo_key = algorithm.lower().strip()
    if algo_key in ("adaptive", "uhdm", "default", "mix", "deep_learning"):
        algo_key = "auto_demoire"

    if algo_key not in ALGORITHM_METADATA:
        raise ValueError(f"Unknown algorithm: {algorithm}. Available: {list(ALGORITHM_METADATA.keys())}")

    start_time = time.perf_counter()
    spectrum_img = None
    metadata: Dict[str, Any] = {"algorithm": algo_key}

    if algo_key in ("auto_demoire", "uhdm", "default"):
        filtered, uhdm_meta = demoire_uhdm(
            img,
            max_dimension=int(params.get("max_dimension", 1536)),
            device_pref=str(params.get("device", "auto")),
        )
        metadata.update(uhdm_meta)

    elif algo_key == "gaussian":
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
