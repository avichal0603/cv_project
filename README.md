# Screen Moiré Removal — Fine-Detail Preservation System

A complete local system for removing moiré patterns from photographs of computer screens while preserving meaningful visual information such as small text, thin lines, UI elements, and edges.

Built as a Computer Vision academic assignment with 4 restoration algorithms, quantitative evaluation, and an interactive web dashboard.

![Architecture](docs/architecture-overview.png)

---

## Quick Start

### Prerequisites
- **Python 3.8+** (tested with 3.9.6)
- **Node.js 18+** (tested with 24.21.0)
- **npm 9+**

### 1. Install Python Dependencies

```bash
cd moire_removal/backend
pip3 install -r requirements.txt
```

### 2. Install Frontend Dependencies

```bash
cd moire_removal/frontend
npm install
```

### 3. Start the Application

**Terminal 1 — Backend (FastAPI on port 8000):**
```bash
cd moire_removal/backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 — Frontend (Vite dev server on port 5173):**
```bash
cd moire_removal/frontend
npm run dev
```

### 4. Open in Browser

Navigate to **http://localhost:5173**

---

## Features

### Image Processing Algorithms

| Algorithm | Type | Key Strength | Typical Speed |
|-----------|------|-------------|---------------|
| **Gaussian Smoothing** | Spatial baseline | Simple, fast | ~5ms |
| **FFT Notch Filter** | Frequency domain | Targets periodic interference | ~80ms |
| **Wavelet Denoising** | Multi-scale | Preserves structure | ~15ms |
| **Edge-Aware Adaptive** | Hybrid bilateral+guided | Best detail preservation | ~40ms |

### Interactive Dashboard
- 🖱️ **Drag-and-drop** image upload (PNG, JPEG, WebP, max 20MB)
- 📸 **Camera capture** with live preview
- 🔀 **Before/after comparison slider** with synchronized zoom and pan
- ⚙️ **Dynamic parameter controls** with sliders, toggles, and dropdowns
- 📊 **Evaluation metrics** (PSNR, SSIM, Edge Preservation) with reference image
- 📈 **FFT spectrum visualization** for frequency analysis
- 🔄 **Compare All** mode — runs all algorithms side-by-side
- 📥 **Export** processed images and side-by-side comparisons
- 📋 **Session history** of processing results

### Evaluation System
- **PSNR** (Peak Signal-to-Noise Ratio)
- **SSIM** (Structural Similarity Index)
- **Edge Preservation Score** (Canny edge F1 score)
- Batch benchmark runner for dataset evaluation

---

## Project Structure

```
moire_removal/
├── backend/                        # Python FastAPI backend
│   ├── main.py                     # FastAPI entry point
│   ├── requirements.txt            # Python dependencies
│   ├── api/
│   │   ├── routes.py               # REST API endpoints
│   │   └── models.py               # Pydantic schemas
│   ├── processing/
│   │   ├── gaussian.py             # Gaussian smoothing baseline
│   │   ├── fft_filter.py           # FFT notch filtering + spectrum viz
│   │   ├── wavelet.py              # Wavelet multi-scale denoising
│   │   ├── edge_aware.py           # Edge-aware bilateral + guided filter
│   │   └── pipeline.py             # Algorithm dispatch & registry
│   ├── evaluation/
│   │   ├── metrics.py              # PSNR, SSIM, edge preservation
│   │   └── benchmark.py            # Batch evaluation runner
│   ├── datasets/
│   │   ├── synthetic.py            # Synthetic test image generator
│   │   ├── prepare.py              # Dataset utilities
│   │   └── generated/              # 10 synthetic test images (5 pairs)
│   └── tests/                      # 44 unit & integration tests
├── frontend/                       # React + Vite frontend
│   ├── src/
│   │   ├── App.jsx                 # Main dashboard layout
│   │   ├── components/             # UI components
│   │   │   ├── ImageUpload.jsx     # Drag-and-drop upload
│   │   │   ├── CameraCapture.jsx   # Webcam capture
│   │   │   ├── ComparisonSlider.jsx # Before/after slider
│   │   │   ├── AlgorithmPanel.jsx  # Algorithm selection
│   │   │   ├── ParameterControls.jsx # Dynamic params
│   │   │   ├── ProcessingControls.jsx # Process/compare buttons
│   │   │   ├── CompareGrid.jsx     # Multi-algorithm grid
│   │   │   ├── AnalysisPanel.jsx   # Metrics & history
│   │   │   ├── SpectrumView.jsx    # FFT spectrum display
│   │   │   └── ExportPanel.jsx     # Download functions
│   │   ├── hooks/
│   │   │   └── useImageProcessor.js # State management & API
│   │   └── styles/
│   │       └── app.css             # Dark theme stylesheet
│   └── vite.config.js              # Dev proxy config
├── docs/
│   ├── report.md                   # Research report
│   ├── architecture.md             # Architecture document
│   └── experiment-guide.md         # Reproducible experiments
└── README.md                       # This file
```

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/algorithms` | GET | List available algorithms with parameter specs |
| `/api/process` | POST | Process image with selected algorithm |
| `/api/evaluate` | POST | Compute PSNR/SSIM/EPS between processed and reference |
| `/api/spectrum` | POST | Generate FFT magnitude spectrum visualization |
| `/api/compare` | POST | Run multiple algorithms on same image |

---

## Running Tests

```bash
cd moire_removal/backend
python3 -m pytest tests/ -v
```

**44 tests** covering:
- Algorithm output validity (shape, dtype, range)
- Metric computation correctness
- API endpoint integration

---

## Benchmark Results (Synthetic Dataset)

| Algorithm | Avg Time | Avg PSNR (dB) | Avg SSIM | Avg Edge F1 |
|-----------|---------|---------------|----------|-------------|
| Gaussian | 3ms | 21.16 | 0.436 | 0.829 |
| FFT Notch | 43ms | 23.83 | 0.513 | **0.921** |
| Wavelet | 12ms | 24.08 | 0.498 | 0.865 |
| **Edge-Aware** | 33ms | **26.24** | **0.615** | 0.878 |

> [!NOTE]
> Results on synthetic moiré. Real camera-screen photographs may differ significantly.

---

## Limitations

1. Synthetic moiré differs from real camera-screen interaction (no lens blur, perspective, exposure variation)
2. No deep learning model included (classical methods only) — could be added as future work
3. OCR-based text preservation metric not implemented (would require Tesseract)
4. Very large images (>4000px) may be slow on CPU
5. Camera capture requires HTTPS in production (works on localhost)

---

## Academic References

1. Sun, Y. et al. "Moiré Photo Restoration Using Multiresolution Convolutional Neural Networks." *IEEE TIP*, 2018.
2. He, K. et al. "Guided Image Filtering." *IEEE TPAMI*, 2013.
3. Tomasi, C. & Manduchi, R. "Bilateral Filtering for Gray and Color Images." *ICCV*, 1998.
4. Donoho, D. L. "De-Noising by Soft-Thresholding." *IEEE TIT*, 1995.
5. Gonzalez, R. & Woods, R. *Digital Image Processing*, 4th Ed., Pearson, 2018.

---

## License

Academic use. No proprietary datasets or models are included.
