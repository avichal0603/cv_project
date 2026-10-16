# Reproducible Experiment Guide — Screen Moiré Removal

This guide provides step-by-step instructions for reproducing all benchmarks, tests, dataset generations, and evaluation experiments on your local computer.

---

## 1. Environment Verification

Ensure Python 3.8+ and Node.js 18+ are available:

```bash
python3 --version
node --version
npm --version
```

Verify backend dependencies are installed:
```bash
cd /Users/avichalyadav/Desktop/SystemsEngg/csm043/moire_removal/backend
python3 -c "import cv2, numpy, scipy, pywt, skimage, fastapi, uvicorn; print('All core libraries verified!')"
```

---

## 2. Unit & Integration Test Suite

Execute the test suite (44 automated test cases covering algorithm stability, dimension preservation, range constraints, edge cases, metric calculation, and API endpoints):

```bash
cd /Users/avichalyadav/Desktop/SystemsEngg/csm043/moire_removal/backend
python3 -m pytest tests/ -v
```

Expected result:
```
============================== 44 passed in 1.17s ==============================
```

---

## 3. Dataset Generation & Regeneration

To regenerate the 5 pairs of high-resolution screen-like synthetic samples ($800 \times 600$ pixels) with beating moiré patterns and chromatic fringing:

```bash
cd /Users/avichalyadav/Desktop/SystemsEngg/csm043/moire_removal/backend
python3 -c "
from datasets.synthetic import generate_all_synthetic_samples
import cv2, os

samples = generate_all_synthetic_samples('datasets/generated')
print(f'Successfully generated {len(samples)} clean/moiré image pairs in datasets/generated/')
"
```

Generated sample categories:
1. `01_small_text_clean.png` & `01_small_text_moire.png` (Code snippets, paragraphs, small typography)
2. `02_spreadsheet_clean.png` & `02_spreadsheet_moire.png` (Thin cell borders, accounting numbers)
3. `03_ui_elements_clean.png` & `03_ui_elements_moire.png` (Toolbar icons, toggle switches, buttons)
4. `04_code_editor_clean.png` & `04_code_editor_moire.png` (Dark IDE theme, syntax coloring, line numbers)
5. `05_geometric_shapes_clean.png` & `05_geometric_shapes_moire.png` (High-contrast circles, polygons, diagonals)

---

## 4. Running the Benchmark Suite

To execute the batch evaluation across all dataset pairs and output aggregate metrics (PSNR, SSIM, Edge Preservation F1, and runtime latency):

```bash
cd /Users/avichalyadav/Desktop/SystemsEngg/csm043/moire_removal/backend
python3 evaluation/benchmark.py
```

Expected terminal output:
```
=================================================================
Algorithm       | Avg Time (s) | PSNR (dB)  | SSIM     | Edge F1 
-----------------------------------------------------------------
gaussian        | 0.0028       | 21.16      | 0.4359   | 0.8288  
fft             | 0.0422       | 23.83      | 0.5133   | 0.9212  
wavelet         | 0.0115       | 24.08      | 0.4976   | 0.8646  
edge_aware      | 0.0353       | 26.24      | 0.6153   | 0.8782  
=================================================================
```

---

## 5. Running the Ablation Study

To evaluate the contribution of the Edge Retention Mask in the proposed Edge-Aware filter:

```bash
cd /Users/avichalyadav/Desktop/SystemsEngg/csm043/moire_removal/backend
python3 -c "
import json, cv2, numpy as np
from datasets.prepare import load_dataset_pairs
from evaluation.metrics import evaluate_all
from processing.edge_aware import edge_aware_filter, guided_filter_manual

pairs = load_dataset_pairs('datasets/generated')
results = {'full': [], 'bilat_only': [], 'guided_only': []}

for p in pairs:
    clean, moire = p['clean'], p['moire']
    # Full proposed
    f = edge_aware_filter(moire, filter_strength=50, edge_threshold=80)
    results['full'].append(evaluate_all(clean, f))
    # Bilateral without mask
    b = cv2.bilateralFilter(moire, 9, 75, 75)
    results['bilat_only'].append(evaluate_all(clean, b))
    # Guided without mask
    gray = cv2.cvtColor(moire, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    g = np.zeros_like(moire)
    for c in range(3):
        gf = guided_filter_manual(gray, moire[:,:,c].astype(np.float32)/255.0, 8, 0.04)
        g[:,:,c] = np.clip(gf * 255.0, 0, 255).astype(np.uint8)
    results['guided_only'].append(evaluate_all(clean, g))

print(f'Proposed Full:       PSNR={np.mean([x[\"psnr\"] for x in results[\"full\"]]):.2f} dB, Edge-F1={np.mean([x[\"edge_preservation_score\"] for x in results[\"full\"]]):.4f}')
print(f'Ablation (Bilat):    PSNR={np.mean([x[\"psnr\"] for x in results[\"bilat_only\"]]):.2f} dB, Edge-F1={np.mean([x[\"edge_preservation_score\"] for x in results[\"bilat_only\"]]):.4f}')
print(f'Ablation (Guided):   PSNR={np.mean([x[\"psnr\"] for x in results[\"guided_only\"]]):.2f} dB, Edge-F1={np.mean([x[\"edge_preservation_score\"] for x in results[\"guided_only\"]]):.4f}')
"
```

---

## 6. End-to-End Web App Verification

1. **Verify Backend Service**:
   ```bash
   curl -s http://localhost:8000/api/health
   # Response: {"status":"ok","service":"screen-moire-removal-api"}
   ```

2. **Verify Frontend Dev Server**:
   ```bash
   curl -I http://localhost:5173
   # Response: HTTP/1.1 200 OK
   ```

3. **Verify API Proxy**:
   ```bash
   curl -s http://localhost:5173/api/algorithms
   # Returns list of 4 algorithms with parameter schemas
   ```

4. **Interactive Browser Steps**:
   - Open `http://localhost:5173` in Google Chrome or Mozilla Firefox.
   - Drag and drop `moire_removal/backend/datasets/generated/01_small_text_moire.png` into the upload box.
   - Click **"Load Ground Truth Reference"** in the right panel and upload `01_small_text_clean.png`.
   - Click **"Process Image"** to execute the default Edge-Aware filter. Notice PSNR, SSIM, and Edge F1 populate in real time.
   - Switch to **"FFT Notch Filter"** and click **"Process Image"**. Observe the frequency spectrum preview display periodic peaks.
   - Click **"Compare All Methods"** to trigger multi-algorithm batch processing and view all results side-by-side.
   - Drag the center divider on the comparison slider, or use the mouse wheel to zoom up to $6\times$ and inspect character edges.
