"""Unit tests for Evaluation Metrics."""

import cv2
import numpy as np
import pytest

from evaluation.metrics import (
    compute_psnr,
    compute_ssim,
    compute_edge_preservation,
    evaluate_all,
)


@pytest.fixture
def clean_image():
    """Create a structured test image with sharp edges and gradients."""
    img = np.full((120, 120, 3), 200, dtype=np.uint8)
    cv2.rectangle(img, (20, 20), (100, 100), (30, 40, 50), -1)
    cv2.circle(img, (60, 60), 25, (220, 180, 40), -1)
    cv2.putText(img, "TEST", (30, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    return img


@pytest.fixture
def noisy_image(clean_image):
    """Create a degraded version with Gaussian noise and blur."""
    noise = np.random.normal(0, 15, clean_image.shape).astype(np.int16)
    noisy = np.clip(clean_image.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return noisy


class TestPSNR:
    def test_psnr_identical(self, clean_image):
        score = compute_psnr(clean_image, clean_image)
        assert score == 100.0

    def test_psnr_noisy(self, clean_image, noisy_image):
        score = compute_psnr(clean_image, noisy_image)
        assert 15.0 <= score <= 35.0

    def test_psnr_different_resolution(self, clean_image):
        resized = cv2.resize(clean_image, (60, 60))
        score = compute_psnr(clean_image, resized)
        assert isinstance(score, float)
        assert score > 0.0


class TestSSIM:
    def test_ssim_identical(self, clean_image):
        score = compute_ssim(clean_image, clean_image)
        assert pytest.approx(1.0, abs=1e-3) == score

    def test_ssim_noisy(self, clean_image, noisy_image):
        score = compute_ssim(clean_image, noisy_image)
        assert 0.0 <= score < 1.0


class TestEdgePreservation:
    def test_edge_preservation_identical(self, clean_image):
        score = compute_edge_preservation(clean_image, clean_image)
        assert pytest.approx(1.0, abs=1e-3) == score

    def test_edge_preservation_blurred(self, clean_image):
        blurred = cv2.GaussianBlur(clean_image, (15, 15), 5.0)
        score = compute_edge_preservation(clean_image, blurred)
        assert 0.0 <= score < 1.0

    def test_edge_preservation_blank(self):
        blank1 = np.zeros((100, 100, 3), dtype=np.uint8)
        blank2 = np.zeros((100, 100, 3), dtype=np.uint8)
        score = compute_edge_preservation(blank1, blank2)
        assert score == 1.0


class TestEvaluateAll:
    def test_evaluate_all_bundle(self, clean_image, noisy_image):
        metrics = evaluate_all(clean_image, noisy_image)
        assert "psnr" in metrics
        assert "ssim" in metrics
        assert "edge_preservation_score" in metrics
        assert isinstance(metrics["psnr"], float)
        assert isinstance(metrics["ssim"], float)
        assert isinstance(metrics["edge_preservation_score"], float)
