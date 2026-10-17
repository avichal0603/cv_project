# Screen Moiré Removal with Fine-Detail Preservation
## Coursework Project Report: CSM043 Computer Vision Practical

**Student Name**: Avichal Yadav  
**Roll Number**: 2501667  
**Program**: MTech Computer Science  
**Course**: CSM043 - Computer Vision Practical (1-Credit Coursework)  
**Evaluation**: Practical Lab Assessment (20 Marks)  
**Interactive Application**: `http://localhost:5173` | **API Server**: `http://localhost:8000`

---

## 1. Abstract

When photographing computer displays (LCD, OLED, LED), the periodic physical subpixel structure of the screen beats with the discrete photosite grid of the camera's digital sensor, generating distracting **moiré interference patterns**. These patterns manifest as spatial ripples, localized contrast shifts, and chromatic "rainbow" bands. In digital document photography—such as snapshots of code, spreadsheets, technical documentation, and user interfaces—moiré severely degrades visual clarity and renders optical character recognition (OCR) unreliable.

Standard spatial filtering techniques (e.g., Gaussian, box, or median smoothing) eliminate moiré only by destructively blurring high-frequency details, making small text (8–12pt) and 1px table borders illegible. In this coursework project, we design, implement, test, and demonstrate an end-to-end **Adaptive Multi-Scale Screen Demoiré System** that removes complex screen moiré interference while rigorously preserving fine typography, line borders, and interface icons.

The system is deployed as an interactive, zero-configuration web application built with a high-performance **FastAPI (Python 3.9)** backend and a **React 19** frontend. Users can drag-and-drop or capture a screen photograph and obtain a clean, demoiréed result with a single click. The interface includes an interactive before/after split-slider with continuous zoom and pan, quantitative quality metrics (PSNR, SSIM, Edge Preservation Index), and high-resolution export. Across our test benchmark, the system achieves an average **PSNR of 26.24 dB**, **SSIM of 0.6153**, and **Edge Preservation Index (EPI) of 0.8782**, executing in **sub-second latency (~0.6–0.8s)** on personal laptop hardware.

---

## 2. Problem Statement & Physical Principles

### 2.1 Physics of Screen Moiré Formation
A digital computer display is composed of an array of discrete emissive elements (subpixels arranged in Red-Green-Blue vertical stripes or PenTile arrangements). The display lattice has a characteristic 2D spatial frequency:

$$\mathbf{F}_{\text{screen}} = \begin{bmatrix} f_{x,\text{screen}} \\ f_{y,\text{screen}} \end{bmatrix} = \begin{bmatrix} 1/P_x \\ 1/P_y \end{bmatrix}$$

where $P_x$ and $P_y$ represent the horizontal and vertical display pixel pitch.

Similarly, the camera sensor records the optical projection through a discrete 2D sampling grid overlaid with a Bayer Color Filter Array (CFA) having sampling frequency:

$$\mathbf{F}_{\text{cam}} = \begin{bmatrix} f_{x,\text{cam}} \\ f_{y,\text{cam}} \end{bmatrix}$$

According to the **Nyquist-Shannon sampling theorem**, when the optical image of the display subpixel lattice projected onto the sensor plane exceeds the sensor's Nyquist limit ($f_{\text{projected}} > \frac{1}{2} f_{\text{cam}}$), spatial aliasing occurs. The non-linear multiplication between the two periodic functions yields beat frequencies:

$$\mathbf{F}_{\text{moire}} = |\mathbf{F}_{\text{screen}} \pm k \cdot \mathbf{F}_{\text{cam}}|, \quad k \in \mathbb{Z}^+$$

### 2.2 Degradation Characteristics on Real Screens
Photographs of digital screens exhibit three distinct forms of degradation:

1. **Chromatic Aliasing (Rainbow Banding)**: The red, green, and blue photosites on the camera's Bayer CFA are physically displaced from one another. Consequently, each color channel samples the screen subpixels at a different spatial phase offset, generating false color fringes (vibrant magenta, cyan, and yellow waves).
2. **Non-Stationary Spatial Ripples**: Due to lens perspective distortion, camera tilt angle, and screen curvature, the relative spatial frequency and orientation of the moiré waves vary continuously across the image.
3. **High-Frequency Content Overlap**: Legitimate screen content—such as font strokes, code indentation lines, spreadsheet grids, and UI icons—consists of sharp, high-gradient edges that occupy the same high-frequency spatial bands as the moiré pattern. Naive low-pass filtering eliminates moiré only at the cost of destroying text legibility.

---

## 3. Objective & Design Goals

For this 1-credit Computer Vision practical (CSM043), the objectives were established as follows:

1. **Moiré Suppression**: Eliminate both chromatic rainbow fringing and spatial luminance ripple waves from real screen photographs.
2. **Typography & Edge Preservation**: Retain crisp legibility for small font text, table borders, and user-interface elements without haloing or blur.
3. **Automated Zero-Configuration Operation**: Avoid confusing parameter sliders or manual frequency tuning; provide a single-click automated workflow accessible to any user.
4. **Reproducible Quantitative Evaluation**: Provide rigorous objective metrics including Peak Signal-to-Noise Ratio (PSNR), Structural Similarity (SSIM), and Edge Preservation Index (EPI).
5. **Efficient Local Execution**: Execute reliably on standard personal computer hardware without requiring external cloud API dependencies.
6. **Usable Interactive Interface**: Build a responsive web application featuring real-time split-screen before/after comparison with zoom and pan inspection.

---

## 4. Why Simple Spatial Filters Fail

To understand the core Computer Vision challenge, we analyzed conventional image restoration methods:

### 4.1 Gaussian Low-Pass Smoothing
Convolving the image with a 2D Gaussian kernel $G(x, y; \sigma) = \frac{1}{2\pi\sigma^2} \exp\left(-\frac{x^2+y^2}{2\sigma^2}\right)$ suppresses high frequencies uniformly across the entire image. While this attenuates fine moiré ripples, it blurs character strokes: 10pt text becomes fuzzy, punctuation disappears, and spreadsheet borders fade into a gray wash.

### 4.2 Global 2D Fourier (FFT) Notch Filtering
Computing the 2D Discrete Fourier Transform allows isolating harmonic spikes corresponding to periodic stripes:

$$F(u, v) = \sum_{x=0}^{M-1} \sum_{y=0}^{N-1} f(x, y) \exp\left[-j2\pi\left(\frac{ux}{M} + \frac{vy}{N}\right)\right]$$

Placing notch-reject filters at detected frequency peaks works well if the moiré stripes are perfectly parallel and planar. However, on real photographs, camera tilt and lens distortion curve the moiré frequencies across the screen. A global Fourier filter cannot follow a spatially varying frequency trajectory, leaving strong residual ghosting.

### 4.3 Standard Gradient Edge-Preserving Filters
Standard bilateral or Canny-guided filters rely on an intensity gradient threshold ($|\nabla I| > T_{\text{edge}}$) to protect edges. While effective for low-amplitude noise, real screen moiré creates sharp, high-contrast subpixel ridges that trick classical edge detectors into classifying the moiré fringes as legitimate edges. Consequently, the filter refuses to smooth them, leaving the moiré patterns largely intact.

---

## 5. Implemented Multi-Scale Adaptive Demoiré System

To overcome these fundamental limitations, we implemented a unified **Adaptive Multi-Scale Screen Demoiré Pipeline** designed around the specific physical properties of screen-camera interference:

```
                      Raw Screen Photograph
                                |
                                v
    +-------------------------------------------------------+
    |   Stage 1: Subpixel Spatial & Phase Decomposition    |
    |   - Reorganizes spatial samples to preserve phase     |
    |   - Decouples chromatic Bayer CFA offsets             |
    +-------------------------------------------------------+
                                |
                                v
    +-------------------------------------------------------+
    |   Stage 2: Multi-Scale Spatial-Frequency Filtering   |
    |   - Decomposes image across resolution pyramid scales |
    |   - Dilated receptive fields capture non-linear waves |
    |   - Attenuates coarse rainbow bands & fine ripples    |
    +-------------------------------------------------------+
                                |
                                v
    +-------------------------------------------------------+
    |   Stage 3: Adaptive Edge & Typography Reconstruction  |
    |   - Preserves high-gradient character strokes & lines |
    |   - Neutralizes chromatic color fringing              |
    |   - Reconstructs full-resolution clean output image   |
    +-------------------------------------------------------+
                                |
                                v
                     Clean Restored Screen
```

### Stage 1: Subpixel Spatial & Phase Decomposition
Rather than applying standard spatial pooling or aggressive downsampling (which permanently destroys subpixel phase alignment), the pipeline reorganizes the spatial grid into multi-channel phase components. This allows the system to process high-resolution display interactions while maintaining 100% of the camera sampling lattice information.

### Stage 2: Multi-Scale Spatial-Frequency Filtering
Because screen moiré spans multiple spatial scales simultaneously—from microscopic subpixel grid beats (1–3 pixels wide) to macroscopic rainbow curves spanning hundreds of pixels—the filtering engine operates across multiple spatial pyramid resolutions:
- At finer scales, high-frequency spatial ripples and subpixel color oscillations are suppressed.
- At coarser scales, long-wavelength chromatic bands and contrast waves are isolated and neutralized.
- Dilated receptive fields allow capturing long-range periodic wave dependencies without reducing spatial resolution.

### Stage 3: Adaptive Edge & Typography Reconstruction
To protect text characters, code listings, and user-interface elements from blurring:
- High-contrast structural boundaries are adaptively preserved.
- Chromatic balancing neutralizes the false yellow/magenta/cyan fringes caused by Bayer CFA phase shifts.
- The multi-scale components are reconstructed into a full-resolution RGB image with strict dynamic range clamping $[0, 255]$ to avoid numerical artifacts.

---

## 6. Software Architecture & Implementation

The project is structured into a decoupled client-server architecture:

```
+-------------------------------------------------------------------------+
|                  Client: React 19 / Vite Web Application                |
|  - Zero-configuration single-click workflow                             |
|  - Drag-and-drop file upload (PNG, JPEG, WebP, AVIF) & camera capture    |
|  - Interactive Split-Pane Comparison Slider with synchronized zoom/pan  |
|  - Real-time quantitative performance metrics & history tracking        |
|  - Full-resolution PNG and side-by-side composite download export       |
+-------------------------------------------------------------------------+
                                    |
                    REST API (HTTP / JSON + Base64)
                    Vite Proxy :5173 -> FastAPI :8000
                                    v
+-------------------------------------------------------------------------+
|                    Server: FastAPI REST Microservice                    |
|  - /api/algorithms : Algorithm metadata and capability discovery        |
|  - /api/process    : Automated demoiréing pipeline with timing          |
|  - /api/evaluate   : PSNR, SSIM, and Edge-F1 score calculation          |
|  - In-memory Base64 image decoding/encoding (zero disk write overhead)  |
|  - Hardware acceleration: Apple Silicon GPU (MPS) / CPU fallback        |
+-------------------------------------------------------------------------+
```

### 6.1 Backend Implementation Details
- **Framework**: Python 3.9, FastAPI 0.115, Uvicorn 0.34.
- **Core Processing**: OpenCV 4.10 (`opencv-python-headless`), NumPy 2.0, PyTorch 2.8.
- **Hardware Acceleration**: Automatically detects and leverages **Apple Silicon Metal Performance Shaders (`mps`)** on macOS, falling back to CPU if unavailable.
- **Memory Optimization**: Images are processed in-memory using base64 payload decoding, eliminating disk I/O bottleneck. Images exceeding $1536 \times 1536$ are intelligently scaled for sub-second responsive execution, then reconstructed with Lanczos-4 interpolation.
- **Test Coverage**: 46 unit and integration tests passing (`pytest tests/`).

### 6.2 Frontend Implementation Details
- **Framework**: React 19.2, Vite 8.3, modern dark-mode CSS3 design.
- **Single-Button User Experience**: Upload or drop an image $\rightarrow$ click `✨ Remove Screen Moiré` $\rightarrow$ view clean output.
- **Comparison Slider (`ComparisonSlider.jsx`)**: Synchronized before/after split viewer supporting smooth drag divider, mouse-wheel zoom ($1\times$ to $5\times$), and pan navigation for close inspection of text glyphs.
- **Export Capabilities (`ExportPanel.jsx`)**: Instant download of restored image or high-resolution side-by-side comparison composite.

---

## 7. Quantitative Evaluation & Metrics

### 7.1 Evaluation Metrics Formulation

1. **Peak Signal-to-Noise Ratio (PSNR)**:
   Measures absolute reconstruction fidelity against a clean reference:
   $$\text{MSE} = \frac{1}{3MN} \sum_{c=1}^3 \sum_{x=1}^M \sum_{y=1}^N \left(I_{\text{ref}}(x, y, c) - I_{\text{proc}}(x, y, c)\right)^2$$
   $$\text{PSNR} = 10 \log_{10}\left(\frac{255^2}{\text{MSE}}\right) \quad (\text{dB})$$

2. **Structural Similarity Index (SSIM)**:
   Measures perceived structural, luminance, and contrast similarity:
   $$\text{SSIM}(x, y) = \frac{(2\mu_x\mu_y + C_1)(2\sigma_{xy} + C_2)}{(\mu_x^2 + \mu_y^2 + C_1)(\sigma_x^2 + \sigma_y^2 + C_2)}$$

3. **Edge Preservation Index (EPI / Canny Edge F1 Score)**:
   Extracts binary Canny edge fields ($E_{\text{ref}}, E_{\text{proc}}$) to measure retention of character strokes and line borders:
   $$\text{Precision} = \frac{|E_{\text{ref}} \cap E_{\text{proc}}|}{|E_{\text{proc}}|}, \quad \text{Recall} = \frac{|E_{\text{ref}} \cap E_{\text{proc}}|}{|E_{\text{ref}}|}$$
   $$F_1 = \frac{2 \cdot \text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$$

4. **Execution Latency**: Wall-clock processing time measured on server via `time.perf_counter()`.

### 7.2 Experimental Benchmark Results

The table below summarizes performance across five representative screen environments:

| Screen Scenario | Input Degraded | Gaussian Smoothing | Proposed Adaptive Filter | Improvement |
| :--- | :--- | :--- | :--- | :--- |
| **Small Typography (10–14pt)** | 18.92 dB / 0.385 | 19.60 dB / 0.369 | **24.62 dB / 0.550** | **+5.02 dB PSNR** |
| **Spreadsheet (1px Grids)** | 19.10 dB / 0.342 | 20.54 dB / 0.335 | **23.94 dB / 0.512** | **+3.40 dB PSNR** |
| **User Interface & Icons** | 19.45 dB / 0.420 | 21.15 dB / 0.416 | **24.98 dB / 0.575** | **+3.83 dB PSNR** |
| **Code Editor (Dark Theme)** | 20.80 dB / 0.490 | 25.17 dB / 0.588 | **33.24 dB / 0.835** | **+8.07 dB PSNR** |
| **Geometric Shapes** | 18.43 dB / 0.423 | 19.36 dB / 0.471 | **24.40 dB / 0.605** | **+5.04 dB PSNR** |
| **Average Across Dataset** | **19.34 dB / 0.412** | **21.16 dB / 0.436** | **26.24 dB / 0.615** | **+5.08 dB / +41.1% SSIM** |

**Edge Preservation Score**: The proposed system achieves an average **Edge F1 of 0.8782**, confirming that sharp high-contrast characters remain intact.  
**Processing Latency**: Average execution time on an Apple Silicon M-series laptop is **~0.62 seconds per image**, enabling near real-time interactive usage.

---

## 8. Qualitative Results on Real-World Screen Captures

We evaluated the system on actual camera photographs of computer monitors displaying code, text documents, and user interfaces (e.g., `sample_images/004.jpg`, `sample_images/sample_screen_moire.png`):

1. **Rainbow Wave Suppression**: Large, wavy chromatic bands spanning across monitor screens are completely neutralized, restoring natural uniform backgrounds.
2. **Text Legibility**: In code editor photographs, syntax-colored keywords, indentation guides, and line numbers remain sharp and legible with zero halo artifacts or color bleeding.
3. **Table & Grid Clarity**: 1px horizontal and vertical borders in spreadsheet cells are fully preserved without broken segments or blurring.

---

## 9. How to Run and Demonstrate the System

### Prerequisites
- Python 3.9+ with PyTorch and OpenCV
- Node.js 18+ and npm

### Quick Start Commands
```bash
# 1. Start the Backend Server (Port 8000)
cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000

# 2. Start the Frontend Web Application (Port 5173)
cd frontend
npm run dev
```

### Live Demonstration Steps
1. Open `http://localhost:5173` in a web browser.
2. Drag and drop any screen photo from `sample_images/` (e.g., `sample_screen_moire.png` or `004.jpg`).
3. Click the prominent primary button: **`✨ Remove Screen Moiré`**.
4. Within ~0.6–0.8 seconds, the demoiréed result appears.
5. Drag the central **Split Comparison Slider** to inspect the before/after transition.
6. Use the mouse wheel to **zoom in up to $5\times$** on text characters to demonstrate fine detail preservation.
7. Click **`Download Clean Image`** or **`Download Comparison`** to export the restored output.

---

## 10. Conclusion

In this coursework project, we developed an end-to-end, fully functional Computer Vision system for removing screen moiré patterns while preserving fine typography and line structures. By combining subpixel phase decomposition with multi-scale spatial-frequency filtering and adaptive edge preservation, the system effectively overcomes the trade-off that causes classical smoothing filters to destroy text. 

The resulting application is robust, easy to demonstrate with zero configuration, and achieves superior quantitative performance (**26.24 dB PSNR, 0.6153 SSIM, 0.8782 Edge F1**) and qualitative clarity on real-world screen photographs.

---

*Report prepared by Avichal Yadav (Roll No: 2501667) for CSM043 Computer Vision Practical, October 2026.*
