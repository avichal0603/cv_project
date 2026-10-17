"""API Route Handlers for Screen Moiré Removal."""

import base64
import logging
from typing import Any, Dict, List, Optional
import cv2
from fastapi import APIRouter, HTTPException, status
import numpy as np

try:
    from api.models import (
        AlgorithmInfo,
        CompareItem,
        CompareRequest,
        CompareResponse,
        EvaluateRequest,
        EvaluateResponse,
        ProcessRequest,
        ProcessResponse,
        SpectrumRequest,
        SpectrumResponse,
    )
    from processing.pipeline import get_available_algorithms, process_image
    from processing.fft_filter import detect_periodic_peaks, create_spectrum_visualization
    from evaluation.metrics import evaluate_all
except ImportError:
    from backend.api.models import (
        AlgorithmInfo,
        CompareItem,
        CompareRequest,
        CompareResponse,
        EvaluateRequest,
        EvaluateResponse,
        ProcessRequest,
        ProcessResponse,
        SpectrumRequest,
        SpectrumResponse,
    )
    from backend.processing.pipeline import get_available_algorithms, process_image
    from backend.processing.fft_filter import detect_periodic_peaks, create_spectrum_visualization
    from backend.evaluation.metrics import evaluate_all

logger = logging.getLogger("moire_api")
router = APIRouter()


def decode_base64_image(b64_string: str) -> np.ndarray:
    """Decode a base64 string (raw or data URI) into a BGR uint8 numpy array.

    Raises:
        HTTPException: if decoding fails or image is invalid.
    """
    if not b64_string or not isinstance(b64_string, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image data must be a non-empty base64 string",
        )

    # Strip data URI header if present (e.g. data:image/png;base64,...)
    if "," in b64_string:
        header, b64_data = b64_string.split(",", 1)
    else:
        b64_data = b64_string

    # Strip whitespaces and fix base64 padding
    b64_data = b64_data.strip()
    missing_padding = len(b64_data) % 4
    if missing_padding != 0:
        b64_data += "=" * (4 - missing_padding)

    try:
        raw_bytes = base64.b64decode(b64_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid base64 payload: {str(e)}",
        )

    if not raw_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Decoded image payload is empty",
        )

    np_arr = np.frombuffer(raw_bytes, dtype=np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if image is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to decode image from provided base64 data",
        )

    return image


def encode_image_to_base64(
    image: np.ndarray,
    img_format: str = "png",
    include_data_uri: bool = True,
) -> str:
    """Encode an OpenCV BGR image into a base64 string."""
    success, buffer = cv2.imencode(f".{img_format}", image)
    if not success:
        raise RuntimeError("Failed to encode image to buffer")

    b64_str = base64.b64encode(buffer).decode("utf-8")
    if include_data_uri:
        return f"data:image/{img_format};base64,{b64_str}"
    return b64_str


@router.get("/health", summary="Health Check")
async def health_check():
    """Service health probe."""
    return {"status": "ok", "service": "screen-moire-removal-api"}


@router.get("/algorithms", response_model=List[AlgorithmInfo], summary="Get Available Algorithms")
async def list_algorithms():
    """Return all available moiré reduction algorithms and parameter specifications."""
    return get_available_algorithms()


@router.post("/process", response_model=ProcessResponse, summary="Process Moiré Image")
async def process_moire_image(req: ProcessRequest):
    """Process an image using a selected algorithm with custom parameters."""
    img = decode_base64_image(req.image)

    try:
        result = process_image(img, req.algorithm, req.params or {})
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("Error executing algorithm: %s", str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Processing error: {str(e)}")

    processed_b64 = encode_image_to_base64(result["image"])
    spectrum_b64 = None
    if result.get("spectrum") is not None:
        spectrum_b64 = encode_image_to_base64(result["spectrum"])

    return ProcessResponse(
        success=True,
        algorithm=req.algorithm,
        processed_image=processed_b64,
        processing_time=round(result["processing_time"], 4),
        spectrum=spectrum_b64,
        metadata=result.get("metadata", {}),
    )


@router.post("/evaluate", response_model=EvaluateResponse, summary="Evaluate Image Quality")
async def evaluate_images(req: EvaluateRequest):
    """Compute PSNR, SSIM, and Edge Preservation Score between reference and processed images."""
    ref_img = decode_base64_image(req.reference_image)
    proc_img = decode_base64_image(req.processed_image)

    try:
        metrics = evaluate_all(ref_img, proc_img)
    except Exception as e:
        logger.exception("Metric calculation failed: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation calculation error: {str(e)}",
        )

    return EvaluateResponse(**metrics)


@router.post("/spectrum", response_model=SpectrumResponse, summary="Compute 2D FFT Spectrum")
async def compute_spectrum(req: SpectrumRequest):
    """Compute 2D FFT magnitude spectrum and identify periodic peaks."""
    img = decode_base64_image(req.image)
    h, w = img.shape[:2]

    # Convert to grayscale / luminance float32
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    f_shift = np.fft.fftshift(np.fft.fft2(gray))
    log_mag = np.log1p(np.abs(f_shift))

    detected_peaks = []
    if req.auto_detect_peaks:
        min_freq = req.min_frequency or 20
        detected_peaks = detect_periodic_peaks(log_mag, min_frequency=min_freq)

    spectrum_img = create_spectrum_visualization(
        f_shift,
        peaks=detected_peaks,
        min_frequency=req.min_frequency or 20,
    )

    spectrum_b64 = encode_image_to_base64(spectrum_img)
    return SpectrumResponse(
        spectrum=spectrum_b64,
        detected_peaks=detected_peaks,
        width=w,
        height=h,
    )


@router.post("/compare", response_model=CompareResponse, summary="Compare Multiple Algorithms")
async def compare_algorithms(req: CompareRequest):
    """Execute multiple algorithms concurrently on the same image and return side-by-side results."""
    input_img = decode_base64_image(req.image)
    ref_img = decode_base64_image(req.reference_image) if req.reference_image else None

    available_keys = [algo["id"] for algo in get_available_algorithms()]
    algos_to_run = req.algorithms if req.algorithms else available_keys
    param_map = req.params or {}

    algorithm_registry = {algo["id"]: algo["name"] for algo in get_available_algorithms()}
    results = []

    for algo_id in algos_to_run:
        algo_id_clean = algo_id.lower().strip()
        if algo_id_clean not in available_keys:
            continue

        params = param_map.get(algo_id_clean, {})
        try:
            res = process_image(input_img, algo_id_clean, params)
            processed_b64 = encode_image_to_base64(res["image"])
            spectrum_b64 = encode_image_to_base64(res["spectrum"]) if res.get("spectrum") is not None else None

            metrics = None
            if ref_img is not None:
                metrics = evaluate_all(ref_img, res["image"])

            results.append(CompareItem(
                algorithm=algo_id_clean,
                name=algorithm_registry.get(algo_id_clean, algo_id_clean),
                processed_image=processed_b64,
                processing_time=round(res["processing_time"], 4),
                spectrum=spectrum_b64,
                metrics=metrics,
            ))
        except Exception as e:
            logger.error(f"Error comparing algorithm {algo_id_clean}: {e}")

    return CompareResponse(results=results)
