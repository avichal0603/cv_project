"""Unit tests for Screen Moiré Removal algorithms."""

import numpy as np
import pytest

from processing.gaussian import gaussian_filter, _ensure_bgr_uint8
from processing.fft_filter import (
    fft_notch_filter,
    detect_periodic_peaks,
    create_notch_filter,
    create_spectrum_visualization,
)
from processing.wavelet import wavelet_filter, _denoise_single_channel_wavelet
from processing.edge_aware import edge_aware_filter, guided_filter_manual, compute_edge_mask
from processing.pipeline import process_image, get_available_algorithms


@pytest.fixture
def sample_bgr_image():
    """Create a test synthetic pattern image (200x200 BGR)."""
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    img[50:150, 50:150] = (200, 100, 50)
    # Add high frequency moire-like ripple
    y, x = np.mgrid[0:200, 0:200]
    ripple = (np.sin(x * 0.4) * 30.0).astype(np.int16)
    img = np.clip(img.astype(np.int16) + ripple[:, :, np.newaxis], 0, 255).astype(np.uint8)
    return img


@pytest.fixture
def sample_small_image():
    """Create a very small test image (7x7 BGR)."""
    return np.random.randint(0, 255, (7, 7, 3), dtype=np.uint8)


class TestInputSanitization:
    def test_ensure_bgr_from_grayscale_2d(self):
        gray = np.full((50, 50), 128, dtype=np.uint8)
        bgr = _ensure_bgr_uint8(gray)
        assert bgr.shape == (50, 50, 3)
        assert bgr.dtype == np.uint8

    def test_ensure_bgr_from_float(self):
        f_img = np.full((50, 50, 3), 0.5, dtype=np.float32)
        bgr = _ensure_bgr_uint8(f_img)
        assert bgr.shape == (50, 50, 3)
        assert bgr.dtype == np.uint8
        assert 126 <= bgr[0, 0, 0] <= 128

    def test_invalid_input(self):
        with pytest.raises(TypeError):
            _ensure_bgr_uint8("not-an-image")
        with pytest.raises(ValueError):
            _ensure_bgr_uint8(np.array([]))


class TestGaussianSmoothing:
    def test_gaussian_basic(self, sample_bgr_image):
        out = gaussian_filter(sample_bgr_image, kernel_size=5, sigma=1.5, luminance_only=True)
        assert out.shape == sample_bgr_image.shape
        assert out.dtype == np.uint8
        assert not np.array_equal(out, sample_bgr_image)

    def test_gaussian_rgb_mode(self, sample_bgr_image):
        out = gaussian_filter(sample_bgr_image, kernel_size=7, sigma=2.0, luminance_only=False)
        assert out.shape == sample_bgr_image.shape
        assert out.dtype == np.uint8

    def test_gaussian_even_kernel(self, sample_bgr_image):
        # Even kernel (e.g. 6) should automatically be converted to odd (7)
        out = gaussian_filter(sample_bgr_image, kernel_size=6, sigma=1.0)
        assert out.shape == sample_bgr_image.shape

    def test_gaussian_small_image(self, sample_small_image):
        out = gaussian_filter(sample_small_image, kernel_size=15, sigma=1.0)
        assert out.shape == sample_small_image.shape
        assert out.dtype == np.uint8


class TestFFTNotchFiltering:
    def test_fft_notch_filter_basic(self, sample_bgr_image):
        filtered, spectrum, notches = fft_notch_filter(
            sample_bgr_image,
            auto_detect=True,
            notch_radius=10,
            suppression_strength=0.9,
            min_frequency=15,
            luminance_only=True,
        )
        assert filtered.shape == sample_bgr_image.shape
        assert filtered.dtype == np.uint8
        assert spectrum.shape == sample_bgr_image.shape
        assert spectrum.dtype == np.uint8
        assert isinstance(notches, list)

    def test_fft_notch_manual(self, sample_bgr_image):
        manual_notches = [(90, 90), (110, 110)]
        filtered, spectrum, notches = fft_notch_filter(
            sample_bgr_image,
            auto_detect=False,
            manual_notches=manual_notches,
        )
        assert filtered.shape == sample_bgr_image.shape
        assert len(notches) == 2

    def test_fft_spectrum_visualization(self, sample_bgr_image):
        f = np.fft.fftshift(np.fft.fft2(sample_bgr_image[:, :, 0].astype(float)))
        viz = create_spectrum_visualization(f, peaks=[(80, 80)], min_frequency=20)
        assert viz.ndim == 3 and viz.shape[2] == 3
        assert viz.dtype == np.uint8


class TestWaveletDenoising:
    def test_wavelet_basic(self, sample_bgr_image):
        out = wavelet_filter(
            sample_bgr_image,
            wavelet="db4",
            level=2,
            threshold_mode="soft",
            threshold_value=25.0,
            luminance_only=True,
        )
        assert out.shape == sample_bgr_image.shape
        assert out.dtype == np.uint8

    def test_wavelet_hard_threshold_rgb(self, sample_bgr_image):
        out = wavelet_filter(
            sample_bgr_image,
            wavelet="sym4",
            level=2,
            threshold_mode="hard",
            threshold_value=30.0,
            luminance_only=False,
        )
        assert out.shape == sample_bgr_image.shape
        assert out.dtype == np.uint8

    def test_wavelet_odd_dimensions(self):
        # 101x103 odd sized image
        odd_img = np.random.randint(0, 255, (101, 103, 3), dtype=np.uint8)
        out = wavelet_filter(odd_img, level=3)
        assert out.shape == odd_img.shape


class TestEdgeAwareFiltering:
    def test_edge_aware_basic(self, sample_bgr_image):
        out = edge_aware_filter(
            sample_bgr_image,
            filter_strength=75,
            edge_threshold=50,
            use_guided=True,
            multi_scale=False,
        )
        assert out.shape == sample_bgr_image.shape
        assert out.dtype == np.uint8

    def test_manual_guided_filter(self):
        guide = np.random.rand(80, 80).astype(np.float32)
        src = np.random.rand(80, 80).astype(np.float32)
        filtered = guided_filter_manual(guide, src, radius=4, eps=0.04)
        assert filtered.shape == (80, 80)
        assert 0.0 <= filtered.min() and filtered.max() <= 1.0

    def test_edge_mask_bounds(self, sample_bgr_image):
        mask = compute_edge_mask(sample_bgr_image, edge_threshold=50)
        assert mask.shape == sample_bgr_image.shape[:2]
        assert 0.0 <= mask.min() and mask.max() <= 1.0


class TestPipelineDispatch:
    @pytest.mark.parametrize("algo", ["gaussian", "fft", "wavelet", "edge_aware"])
    def test_pipeline_dispatch(self, sample_bgr_image, algo):
        res = process_image(sample_bgr_image, algo)
        assert "image" in res
        assert res["image"].shape == sample_bgr_image.shape
        assert res["processing_time"] >= 0.0
        assert "metadata" in res

        if algo == "fft":
            assert res["spectrum"] is not None

    def test_unknown_algorithm(self, sample_bgr_image):
        with pytest.raises(ValueError, match="Unknown algorithm"):
            process_image(sample_bgr_image, "non_existent_algo")

    def test_algorithm_registry(self):
        algos = get_available_algorithms()
        assert len(algos) == 4
        ids = {a["id"] for a in algos}
        assert ids == {"gaussian", "fft", "wavelet", "edge_aware"}
