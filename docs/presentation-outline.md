# Academic Presentation Outline: Screen Moiré Removal with Fine-Detail Preservation

*Designed for a 20-Mark Computer Vision Practical / Viva Presentation (10-15 Minutes)*

---

## Slide & Viva Roadmap (Mark Distribution Matrix)

| Section | Target Duration | Content & Focus Area | Marks (Approx.) |
| :--- | :--- | :--- | :--- |
| **1. Problem & Motivation** | 2 min | Physical origin of screen moiré, aliasing, why naive smoothing fails | 3 Marks |
| **2. Mathematical Formulation** | 3 min | Spatial vs. frequency domain, DWT subbands, guided filtering | 4 Marks |
| **3. Proposed Architecture** | 2 min | Decoupled client-server design, FastAPI engine, React 19 UI | 3 Marks |
| **4. Live Interactive Demo** | 4 min | Real-time demo: upload, before/after slider, zoom, FFT spectrum, compare grid | 5 Marks |
| **5. Quantitative Evaluation & Ablation** | 3 min | PSNR/SSIM/Edge-F1 benchmarks across 5 screen types, ablation proof | 3 Marks |
| **6. Limitations & Viva Q&A** | 2 min | Deep learning vs classical trade-offs, failure modes, future work | 2 Marks |

---

## Detailed Speaking Points per Slide

### Slide 1: Title & Introduction
- **Project Title**: Screen Moiré Removal with Fine-Detail Preservation.
- **Presenter**: Avichalyadav (Systems Engineering / CSM043).
- **Core Thesis**: When photographing computer screens, optical aliasing causes severe wavy interference patterns. Standard spatial filters eliminate moiré only at the cost of smearing fine text and grid borders. We propose an edge-adaptive multi-scale restoration system that selectively dampens moiré oscillations while maintaining near-perfect typography sharpness.

### Slide 2: Physics of Screen Moiré
- **Cause**: Superposition of two periodic structures: the discrete LCD/OLED RGB subpixel pitch ($f_{\text{screen}}$) and the digital camera sensor's Bayer filter sampling grid ($f_{\text{camera}}$).
- **Spatial Aliasing**: When $f_{\text{screen}} > \frac{1}{2} f_{\text{sampling}}$, high frequencies alias down into visible low-frequency beat waves:
  $$f_{\text{moire}} = |f_{\text{screen}} - f_{\text{camera}}|$$
- **The Core Dilemma**: Legitimate screen elements (small 10pt fonts, 1px table borders) occupy the identical spatial frequency bandwidth as the moiré pattern.

### Slide 3: Algorithms & Mathematical Formulation
- **Baseline 1 — Gaussian Smoothing**:
  $G(x, y) = \frac{1}{2\pi\sigma^2} \exp\left(-\frac{x^2+y^2}{2\sigma^2}\right)$. Baseline showing that standard low-pass blurring eliminates moiré only by destroying text readability (PSNR 21.16 dB, SSIM 0.4359).
- **Baseline 2 — 2D FFT Notch Filtering**:
  Converts luminance to 2D Fourier domain $\mathcal{F}\{I\}(u, v)$. Detects localized interference peaks outside the central DC band ($r > r_{\text{min}}$) and applies conjugate symmetric Gaussian notch reject filters.
- **Method 3 — Multiresolution Wavelet Shrinkage**:
  Applies 2D Discrete Wavelet Transform ($LL_J, LH_j, HL_j, HH_j$). Suppresses high-frequency diagonal and directional detail coefficients while keeping approximation structures intact.
- **Proposed Method 4 — Hybrid Edge-Aware Adaptive Filter**:
  1. Computes Sobel gradient magnitude + Canny edge maps to create a continuous edge retention mask $M(x, y) \in [0, 1]$.
  2. Applies Bilateral Filtering for edge-preserving photometric smoothing.
  3. Applies $O(N)$ box-filtered Guided Filter using grayscale luminance as structural guide.
  4. Blends via $I_{\text{out}} = M \odot I_{\text{orig}} + (1 - M) \odot I_{\text{filtered}}$.

### Slide 4: Quantitative Evaluation & Benchmarking
- **Test Dataset**: 5 synthetic screen types ($800 \times 600$): small text, spreadsheets, UI icons, code editor, geometric shapes.
- **Benchmark Summary Table**:
  - Gaussian: PSNR 21.16 dB, SSIM 0.4359, Edge-F1 0.8288, 2.8ms
  - FFT Notch: PSNR 23.83 dB, SSIM 0.5133, Edge-F1 0.9212, 42.2ms
  - Wavelet: PSNR 24.08 dB, SSIM 0.4976, Edge-F1 0.8646, 11.5ms
  - **Proposed Edge-Aware**: **PSNR 26.24 dB**, **SSIM 0.6153**, **Edge-F1 0.8782**, 35.3ms
- **Ablation Study**:
  - Full Proposed with Edge Mask: PSNR 26.22 dB, Edge-F1 0.8919
  - Bilateral without Edge Mask: PSNR 27.70 dB, Edge-F1 0.8910 (oversmoothed text)
  - Guided Filter only: PSNR 24.68 dB, Edge-F1 0.8432

### Slide 5: Live Software Demonstration
1. Show the interactive web dashboard at `http://localhost:5173`.
2. Upload `01_small_text_moire.png` and ground-truth `01_small_text_clean.png`.
3. Demonstrate the **Comparison Slider** with $4\times$ zoom on character strokes.
4. Switch to **FFT Notch Filter**: highlight the 2D FFT magnitude spectrum window and the detected harmonic peaks.
5. Click **"Compare All Methods"**: show the side-by-side comparative inspection cards and latencies.
6. Trigger **Webcam Capture** modal to show live hardware camera integration.

### Slide 6: Common Viva Questions & Defense Answers
- **Q1: Why not just train a deep U-Net / CNN?**
  *Answer*: Classical edge-adaptive algorithms run instantaneously on commodity CPU hardware (<40ms per image), require zero GPU memory or heavy 500MB weight downloads, have completely explainable mathematical parameter bounds, and avoid hallucinating false text characters.
- **Q2: Why did FFT notch filter achieve the highest Edge F1 score (0.9212) on code editors?**
  *Answer*: FFT notch rejection removes only narrow harmonic spectral spikes without performing spatial spatial convolution, leaving rectilinear horizontal and vertical syntax lines untouched. However, for non-periodic rainbow moiré, spatial edge-aware filtering yields superior structural similarity (SSIM 0.6153 vs 0.5133).
- **Q3: How does the Guided Filter avoid boundary halo artifacts?**
  *Answer*: The guided filter assumes a local linear model $I_{\text{out}} = a_k I_{\text{guide}} + b_k$ within local patch $\omega_k$. Because $I_{\text{guide}}$ is the input luminance itself, the output gradient is mathematically bounded by the guide gradient, avoiding false ringing or edge overshoot.
