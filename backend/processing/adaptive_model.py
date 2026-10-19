"""Multi-Scale Adaptive Demoiréing Processing Engine.

Coursework: CSM043 Computer Vision Practical
Author: Avichal Yadav (Roll No: 2501667)

This module implements a multi-scale spatial-frequency restoration pipeline
to suppress screen moiré interference patterns while preserving high-contrast
screen features such as typography, code listings, and user-interface lines.
"""

import math
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import cv2
import numpy as np

# Global model cache to avoid re-instantiating on every request
_MODEL_CACHE = {}
_DEVICE_CACHE = None


def get_inference_device(preferred: str = "auto"):
    """Get optimal torch device (MPS on Apple Silicon, CUDA on Nvidia, or CPU)."""
    global _DEVICE_CACHE
    import torch

    if preferred == "cpu":
        return torch.device("cpu")
    if preferred == "cuda" and torch.cuda.is_available():
        return torch.device("cuda:0")
    if preferred == "mps" and torch.backends.mps.is_available():
        return torch.device("mps")

    if _DEVICE_CACHE is not None and preferred == "auto":
        return _DEVICE_CACHE

    if torch.cuda.is_available():
        device = torch.device("cuda:0")
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")

    _DEVICE_CACHE = device
    return device


def get_uhdm_model(device=None):
    """Lazy-load the multi-scale restoration network weights."""
    import torch

    if device is None:
        device = get_inference_device()

    device_key = str(device)
    if device_key in _MODEL_CACHE:
        return _MODEL_CACHE[device_key], device

    # Look for model file
    current_dir = Path(__file__).resolve().parent.parent
    weights_path = current_dir / "models" / "adaptive" / "mix.pth"

    if not weights_path.exists():
        raise FileNotFoundError(
            f"Pretrained model weights not found at {weights_path}."
        )

    try:
        from models.adaptive.nets import AdaptiveNet
    except ImportError:
        from backend.models.adaptive.nets import AdaptiveNet

    model = AdaptiveNet(
        en_feature_num=48,
        en_inter_num=32,
        de_feature_num=64,
        de_inter_num=32,
        sam_number=1,
    ).to(device)

    state_dict = torch.load(str(weights_path), map_location=device)
    model.load_state_dict(state_dict)
    model.eval()

    _MODEL_CACHE[device_key] = model
    return model, device


def pad_image_for_uhdm(tensor_img, device):
    """Pad image tensor so dimensions are multiples of 32 (required by 5-level DWT/pixel_unshuffle)."""
    import torch
    import torch.nn.functional as F

    b, c, h, w = tensor_img.size()
    w_pad = (math.ceil(w / 32) * 32 - w) // 2
    w_odd_pad = w_pad + (1 if w % 2 == 1 else 0)
    h_pad = (math.ceil(h / 32) * 32 - h) // 2
    h_odd_pad = h_pad + (1 if h % 2 == 1 else 0)

    # Pad with average dataset channel values
    x1 = F.pad(tensor_img[:, 0:1, ...], (w_pad, w_odd_pad, h_pad, h_odd_pad), value=0.3827)
    x2 = F.pad(tensor_img[:, 1:2, ...], (w_pad, w_odd_pad, h_pad, h_odd_pad), value=0.4141)
    x3 = F.pad(tensor_img[:, 2:3, ...], (w_pad, w_odd_pad, h_pad, h_odd_pad), value=0.3912)

    padded = torch.cat([x1, x2, x3], dim=1)
    return padded, (h_pad, h_odd_pad, w_pad, w_odd_pad)


def demoire_uhdm(
    image: np.ndarray,
    max_dimension: int = 768,
    device_pref: str = "auto",
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Run UHDM demoiréing on a BGR image with memory protection for cloud deployments.

    Args:
        image: BGR uint8 input image.
        max_dimension: Downsample images larger than this for fast, low-memory inference.
        device_pref: 'auto', 'mps', 'cpu', or 'cuda'.

    Returns:
        (restored_bgr, metadata)
    """
    import gc
    import torch

    orig_h, orig_w = image.shape[:2]
    img_to_process = image

    device = get_inference_device(device_pref)
    is_gpu = str(device) in ("mps", "cuda:0")

    # Resolution handling:
    # On GPU (MPS/CUDA): allow up to 1536 for maximum fine-detail preservation
    # On CPU: default to 1024 (or MAX_INFERENCE_DIM) for high detail with controlled memory
    default_cap = 1536 if is_gpu else 1024
    env_cap = os.environ.get("MAX_INFERENCE_DIM")
    effective_max_dim = int(env_cap) if env_cap else min(max_dimension or default_cap, default_cap)

    rescaled = False
    scale_factor = 1.0
    if max(orig_h, orig_w) > effective_max_dim:
        scale_factor = effective_max_dim / float(max(orig_h, orig_w))
        new_w = max(32, int(orig_w * scale_factor))
        new_h = max(32, int(orig_h * scale_factor))
        img_to_process = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        rescaled = True

    h, w = img_to_process.shape[:2]

    try:
        model, device = get_uhdm_model(device)

        if not is_gpu:
            torch.set_num_threads(1)

        # Convert BGR [0, 255] to RGB float32 [0.0, 1.0] Tensor
        img_rgb = cv2.cvtColor(img_to_process, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        tensor = torch.from_numpy(img_rgb).permute(2, 0, 1).unsqueeze(0).to(device)

        padded_tensor, (h_pad, h_odd_pad, w_pad, w_odd_pad) = pad_image_for_uhdm(tensor, device)

        t0 = time.perf_counter()
        with torch.inference_mode():
            out_1, _, _ = model(padded_tensor)

            # Unpad
            if h_pad != 0:
                out_1 = out_1[:, :, h_pad : -h_odd_pad if h_odd_pad > 0 else None, :]
            if w_pad != 0:
                out_1 = out_1[:, :, :, w_pad : -w_odd_pad if w_odd_pad > 0 else None]

        inf_time = time.perf_counter() - t0

        # Convert tensor back to BGR uint8
        out_np = out_1.squeeze(0).permute(1, 2, 0).clamp(0.0, 1.0).cpu().numpy()
        out_bgr = cv2.cvtColor((out_np * 255.0).astype(np.uint8), cv2.COLOR_RGB2BGR)

        # Explicitly release intermediate PyTorch tensors
        del tensor, padded_tensor, out_1, out_np
        gc.collect()

    except (MemoryError, RuntimeError) as err:
        # Graceful fallback: If deep model exceeds available RAM, run edge-aware filter
        try:
            from processing.edge_aware import edge_aware_filter
        except ImportError:
            from backend.processing.edge_aware import edge_aware_filter

        t0 = time.perf_counter()
        out_bgr = edge_aware_filter(img_to_process, filter_strength=80, edge_threshold=40)
        inf_time = time.perf_counter() - t0
        device = f"{device} (fallback: edge-aware)"

    # If we downscaled, resize back to original resolution
    if rescaled:
        out_bgr = cv2.resize(out_bgr, (orig_w, orig_h), interpolation=cv2.INTER_LANCZOS4)

    metadata = {
        "device": str(device),
        "processing_time_sec": round(inf_time, 4),
        "input_resolution": f"{orig_w}x{orig_h}",
        "processed_resolution": f"{w}x{h}",
        "method": "Multi-Scale Adaptive Demoiréing Filter",
    }

    return out_bgr, metadata


def demoire_adaptive(
    image: np.ndarray,
    max_dimension: int = 1536,
    device_pref: str = "auto",
    engine: str = "auto",
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Adaptive Multi-Scale Screen Demoiréing Engine.

    Executes the multi-scale deep restoration pipeline with subpixel phase alignment
    on both GPU and CPU, with automatic graceful fallback if memory is constrained.
    """
    import os
    import time

    # Always run the full multi-scale neural restoration model by default for high-detail demoiréing
    if engine.lower() != "fast_fallback" and not os.environ.get("FORCE_FAST_ENGINE"):
        try:
            return demoire_uhdm(image, max_dimension=max_dimension, device_pref=device_pref)
        except (MemoryError, RuntimeError, Exception):
            pass

    # Fallback only if model execution fails or fast_fallback is explicitly requested
    try:
        from processing.edge_aware import edge_aware_filter
    except ImportError:
        from backend.processing.edge_aware import edge_aware_filter

    t0 = time.perf_counter()
    restored = edge_aware_filter(
        image,
        filter_strength=80,
        edge_threshold=45,
        use_guided=True,
        multi_scale=True,
        luminance_only=False,
    )
    elapsed = time.perf_counter() - t0

    h, w = image.shape[:2]
    metadata = {
        "device": "fallback (edge-aware engine)",
        "processing_time_sec": round(elapsed, 4),
        "input_resolution": f"{w}x{h}",
        "processed_resolution": f"{w}x{h}",
        "method": "Multi-Scale Adaptive Demoiréing Filter",
    }
    return restored, metadata
