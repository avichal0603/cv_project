"""Pydantic Models and Data Schemas for the Moiré Removal API."""

from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, Field


class ParameterSchema(BaseModel):
    """Specification of an algorithm parameter."""
    name: str
    label: str
    type: str  # 'int', 'float', 'bool', 'select'
    default: Any
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    options: Optional[List[str]] = None
    description: Optional[str] = None


class AlgorithmInfo(BaseModel):
    """Metadata describing a removal algorithm."""
    id: str
    name: str
    description: str
    category: str
    parameters: List[ParameterSchema]


class ProcessRequest(BaseModel):
    """Request payload for /api/process endpoint."""
    image: str = Field(..., description="Base64 encoded input image (raw or data URI)")
    algorithm: str = Field(..., description="Algorithm ID ('gaussian', 'fft', 'wavelet', 'edge_aware')")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Algorithm specific parameters")


class ProcessResponse(BaseModel):
    """Response payload for /api/process endpoint."""
    success: bool = True
    algorithm: str
    processed_image: str = Field(..., description="Base64 encoded processed PNG image")
    processing_time: float = Field(..., description="Execution time in seconds")
    spectrum: Optional[str] = Field(None, description="Base64 FFT magnitude spectrum if applicable")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class EvaluateRequest(BaseModel):
    """Request payload for /api/evaluate endpoint."""
    reference_image: str = Field(..., description="Base64 clean ground truth reference image")
    processed_image: str = Field(..., description="Base64 processed candidate image")


class EvaluateResponse(BaseModel):
    """Response payload for /api/evaluate endpoint."""
    psnr: float = Field(..., description="Peak Signal-to-Noise Ratio in dB")
    ssim: float = Field(..., description="Structural Similarity Index [-1, 1]")
    edge_preservation_score: float = Field(..., description="Canny edge F1 score [0, 1]")


class SpectrumRequest(BaseModel):
    """Request payload for /api/spectrum endpoint."""
    image: str = Field(..., description="Base64 encoded input image")
    min_frequency: Optional[int] = Field(20, description="Exclusion radius for DC")
    auto_detect_peaks: Optional[bool] = Field(True, description="Mark detected harmonic peaks")


class SpectrumResponse(BaseModel):
    """Response payload for /api/spectrum endpoint."""
    spectrum: str = Field(..., description="Base64 encoded spectrum visualization PNG")
    detected_peaks: List[Tuple[int, int]] = Field(default_factory=list)
    width: int
    height: int


class CompareItem(BaseModel):
    """Individual algorithm result within comparison response."""
    algorithm: str
    name: str
    processed_image: str
    processing_time: float
    spectrum: Optional[str] = None
    metrics: Optional[Dict[str, float]] = None


class CompareRequest(BaseModel):
    """Request payload for /api/compare endpoint."""
    image: str = Field(..., description="Base64 encoded moiré image")
    reference_image: Optional[str] = Field(None, description="Optional clean reference image for metric calculation")
    algorithms: Optional[List[str]] = Field(
        default=None,
        description="List of algorithm IDs to compare. Defaults to all 4 algorithms."
    )
    params: Optional[Dict[str, Dict[str, Any]]] = Field(
        default_factory=dict,
        description="Optional per-algorithm parameter overrides"
    )


class CompareResponse(BaseModel):
    """Response payload for /api/compare endpoint."""
    results: List[CompareItem]
