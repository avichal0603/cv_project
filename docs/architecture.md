# Screen Moiré Removal — System Architecture Documentation

## 1. System Overview

The **Screen Moiré Demoireing Studio** is a decoupled client-server application engineered for high-fidelity restoration of photographed screens. It removes high-frequency aliasing and chromatic interference while preserving crucial structural details (monospaced code, spreadsheet cell borders, small typography, and UI glyphs).

```
                      +-------------------------------------------------+
                      |              Web Browser Client                 |
                      |  React 19 + Vite (Port 5173 / Localhost)        |
                      +-------------------------------------------------+
                                      |                    ^
               HTTP POST JSON Payload |                    | JSON Responses
              (Base64 Image + Params) |                    | (Base64 Result +
                                      v                    |  Metrics + Time)
                      +-------------------------------------------------+
                      |            FastAPI API Gateway                  |
                      |          Python 3.9+ (Port 8000)                |
                      +-------------------------------------------------+
                                      |
                      +---------------+---------------+
                      |                               |
                      v                               v
         +--------------------------+    +--------------------------+
         |   Processing Pipeline    |    |    Evaluation Engine     |
         | (NumPy / SciPy / OpenCV) |    |  (Scikit-Image / NumPy)  |
         +--------------------------+    +--------------------------+
           |       |        |      |       |          |         |
           v       v        v      v       v          v         v
        Gaussian  FFT    Wavelet  Edge    PSNR      SSIM      Edge
        Baseline Notch   Shrink  Adaptive                     F1
```

---

## 2. Component Specifications

### 2.1 Frontend Architecture (`frontend/`)

- **Framework**: React 19 running on Vite 8, transpiled with pure ES modules.
- **Styling Architecture**: Native modular CSS (`app.css`) implementing a GitHub dark-mode design system (`#0d1117` canvas, `#161b22` surfaces, `#30363d` structural dividers, `#58a6ff` interactive accents).
- **Core State Machine (`useImageProcessor.js`)**:
  - Manages original image, processed output, reference ground-truth, and live FFT spectrum previews.
  - Asynchronous dispatch via `AbortController` enabling user cancellation during heavy processing.
  - Real-time parameter schema synchronization with the backend `/api/algorithms` endpoint.
  - Client-side history cache (up to 10 snapshots) allowing immediate one-click comparison of previous parameter runs.
- **Interactive Workspace Components**:
  - `ComparisonSlider.jsx`: Pointer-driven interactive split-pane with coordinate-locked synchronized zoom ($0.5\times$ to $6.0\times$) and pan translation.
  - `CameraCapture.jsx`: Direct access to system webcams via `navigator.mediaDevices.getUserMedia` with video frame freeze-and-crop canvas capture.
  - `ParameterControls.jsx`: Dynamically rendered controls adapted to algorithm parameter types (`int`, `float`, `bool`, `select`).
  - `CompareGrid.jsx`: Multi-algorithm concurrent benchmark grid for rapid comparative evaluation.
  - `SpectrumView.jsx`: Visual inspection of 2D FFT magnitude spectrum to spot harmonic peaks.

### 2.2 Backend Architecture (`backend/`)

- **Server**: FastAPI with Uvicorn ASGI server running on `0.0.0.0:8000`.
- **CORS Configuration**: Open local origin handling (`http://localhost:5173` and `*`).
- **Data Serialization**:
  - Pydantic models for request validation and schema definition (`api/models.py`).
  - Safe Base64 payload decoding with padding normalization and direct memory-buffer decoding via `cv2.imdecode`.
  - Zero filesystem I/O for processing requests; all intermediate buffers exist in memory.

---

## 3. Algorithm Pipeline Design (`processing/`)

```
Input Image (H x W x 3 uint8)
     |
     +--> [gaussian.py]   --> YCrCb / RGB Gaussian kernel convolution
     |
     +--> [fft_filter.py] --> 2D FFT -> Log Magnitude -> Peak Detection -> Gaussian Notch Reject -> IFFT
     |
     +--> [wavelet.py]    --> 2D DWT -> Multi-level Pyramidal Subbands -> Detail Thresholding -> 2D IDWT
     |
     +--> [edge_aware.py] --> Sobel/Canny Edge Retention Mask -> Bilateral Filter -> Guided Filter -> Alpha Blend
```

### 3.1 Gaussian Smoothing Baseline (`gaussian.py`)
- Provides the lower-bound reference for naive spatial low-pass filtering.
- Implements luminance-isolated filtering in $Y\text{CrCb}$ color space ($Y$ channel blurred, chromatic channels untouched) to prevent color bleed across sharp text boundaries.

### 3.2 2D FFT Notch Reject Filter (`fft_filter.py`)
- Performs 2D Fast Fourier Transform on floating-point luminance.
- Centered magnitude spectrum: $S(u, v) = \log(1 + |\mathcal{F}\{I\}|)$.
- Automated peak discovery excludes low frequencies ($r < r_{\text{min}}$) to prevent wiping out legitimate structural content.
- Generates Gaussian notch reject attenuation masks at detected coordinates $(u_k, v_k)$ and their conjugate mirrors $(-u_k, -v_k)$.
- Inverse 2D FFT reconstructs the space-domain signal with strict $[0, 255]$ dynamic range clamping.

### 3.3 Multi-Scale Wavelet Denoising (`wavelet.py`)
- Employs 2D Discrete Wavelet Transform (`pywt.wavedec2`) supporting Daubechies (`db1`–`db4`), Symlets (`sym4`), Coiflets (`coif1`), and Biorthogonal (`bior1.3`) wavelets.
- Decomposes into multiresolution approximation $LL_J$ and directional detail subbands $(LH_j, HL_j, HH_j)$ for scales $j = 1, \dots, J$.
- Applies soft or hard thresholding to directional detail coefficients containing high-frequency beating patterns while preserving low-frequency coarse structures.

### 3.4 Hybrid Edge-Aware Filter (`edge_aware.py`)
- Computes Sobel gradient magnitude: $G(x, y) = \sqrt{G_x^2 + G_y^2}$.
- Computes multi-scale Canny edge map smoothed by a Gaussian kernel.
- Generates a soft edge-retention mask: $M(x, y) \in [0, 1]$.
- Applies Bilateral Filtering for edge-respecting tone smoothing:
  $$I_{\text{bilat}}(p) = \frac{1}{W_p} \sum_{q \in \Omega} I(q) f_r(\|I(p) - I(q)\|) g_s(\|p - q\|)$$
- Applies $O(N)$ Guided Filtering (`guided_filter_manual`) using the grayscale luminance as the structural guide image.
- Blends filtered regions with original inputs using the edge mask:
  $$I_{\text{out}} = M \odot I_{\text{orig}} + (1 - M) \odot I_{\text{filtered}}$$
- High-contrast characters and thin grid lines maintain $M \approx 1$ (zero blur), while flat screen areas with moiré ripple receive full smoothing ($M \approx 0$).

---

## 4. Evaluation Suite (`evaluation/`)

1. **PSNR (Peak Signal-to-Noise Ratio)**:
   $$\text{PSNR} = 10 \log_{10}\left(\frac{255^2}{\text{MSE}}\right)$$
2. **SSIM (Structural Similarity Index)**:
   Calculated across windowed luminance patches with stability constants $C_1 = (0.01 \times 255)^2$ and $C_2 = (0.03 \times 255)^2$.
3. **Edge Preservation Score (EPI / Edge F1)**:
   Extracts binary Canny edge fields $E_{\text{ref}}$ and $E_{\text{proc}}$:
   $$\text{Precision} = \frac{|E_{\text{ref}} \cap E_{\text{proc}}|}{|E_{\text{proc}}|}, \quad \text{Recall} = \frac{|E_{\text{ref}} \cap E_{\text{proc}}|}{|E_{\text{ref}}|}, \quad F_1 = \frac{2 \cdot P \cdot R}{P + R}$$

---

## 5. Security & Deployment

- **Port Isolation**: Backend defaults to port `8000`, frontend to port `5173`.
- **Zero Cloud Leakage**: All computation occurs on localhost; no telemetry or external network calls are made.
- **Hardware Agnostic**: Fully optimized for CPU execution without requiring discrete CUDA hardware.
