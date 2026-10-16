"""Integration tests for Screen Moiré Removal FastAPI API endpoints."""

import base64
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from main import app
from api.routes import encode_image_to_base64


@pytest.fixture
def client():
    """Create FastAPI TestClient."""
    return TestClient(app)


@pytest.fixture
def sample_image_base64():
    """Generate a simple test image encoded in base64."""
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.rectangle(img, (20, 20), (80, 80), (100, 180, 255), -1)
    cv2.circle(img, (50, 50), 20, (50, 200, 50), -1)
    return encode_image_to_base64(img)


@pytest.fixture
def sample_moire_base64():
    """Generate a test image with moire ripple in base64."""
    img = np.full((100, 100, 3), 200, dtype=np.uint8)
    y, x = np.mgrid[0:100, 0:100]
    ripple = (np.sin(x * 0.3) * 40.0).astype(np.int16)
    noisy = np.clip(img.astype(np.int16) + ripple[:, :, np.newaxis], 0, 255).astype(np.uint8)
    return encode_image_to_base64(noisy)


class TestRootAndHealthEndpoints:
    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert "api_endpoints" in data

    def test_health_endpoint(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestAlgorithmEndpoints:
    def test_get_algorithms(self, client):
        response = client.get("/api/algorithms")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 4
        ids = [item["id"] for item in data]
        assert "gaussian" in ids
        assert "fft" in ids
        assert "wavelet" in ids
        assert "edge_aware" in ids


class TestProcessEndpoint:
    @pytest.mark.parametrize("algo", ["gaussian", "fft", "wavelet", "edge_aware"])
    def test_process_success(self, client, sample_image_base64, algo):
        payload = {
            "image": sample_image_base64,
            "algorithm": algo,
            "params": {}
        }
        response = client.post("/api/process", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["algorithm"] == algo
        assert data["processed_image"].startswith("data:image/png;base64,")
        assert data["processing_time"] >= 0.0

        if algo == "fft":
            assert data["spectrum"] is not None
            assert data["spectrum"].startswith("data:image/png;base64,")

    def test_process_invalid_algorithm(self, client, sample_image_base64):
        payload = {
            "image": sample_image_base64,
            "algorithm": "magic_quantum_filter",
        }
        response = client.post("/api/process", json=payload)
        assert response.status_code == 400

    def test_process_invalid_base64(self, client):
        payload = {
            "image": "not-valid-base64-data@@@!!!",
            "algorithm": "gaussian",
        }
        response = client.post("/api/process", json=payload)
        assert response.status_code == 400


class TestEvaluateEndpoint:
    def test_evaluate_images(self, client, sample_image_base64, sample_moire_base64):
        payload = {
            "reference_image": sample_image_base64,
            "processed_image": sample_moire_base64,
        }
        response = client.post("/api/evaluate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "psnr" in data
        assert "ssim" in data
        assert "edge_preservation_score" in data
        assert isinstance(data["psnr"], float)
        assert isinstance(data["ssim"], float)
        assert isinstance(data["edge_preservation_score"], float)


class TestSpectrumEndpoint:
    def test_compute_spectrum(self, client, sample_image_base64):
        payload = {
            "image": sample_image_base64,
            "min_frequency": 15,
            "auto_detect_peaks": True,
        }
        response = client.post("/api/spectrum", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["spectrum"].startswith("data:image/png;base64,")
        assert data["width"] == 100
        assert data["height"] == 100
        assert isinstance(data["detected_peaks"], list)


class TestCompareEndpoint:
    def test_compare_without_reference(self, client, sample_moire_base64):
        payload = {
            "image": sample_moire_base64,
            "algorithms": ["gaussian", "edge_aware"],
        }
        response = client.post("/api/compare", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 2
        assert data["results"][0]["algorithm"] == "gaussian"
        assert data["results"][1]["algorithm"] == "edge_aware"
        assert data["results"][0]["processed_image"].startswith("data:image/png;base64,")

    def test_compare_with_reference(self, client, sample_moire_base64, sample_image_base64):
        payload = {
            "image": sample_moire_base64,
            "reference_image": sample_image_base64,
            "algorithms": ["fft", "wavelet"],
        }
        response = client.post("/api/compare", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 2
        for item in data["results"]:
            assert item["metrics"] is not None
            assert "psnr" in item["metrics"]
            assert "ssim" in item["metrics"]
