# Sample Moiré Dataset & Test Images

A curated benchmark collection of real-world and synthetic screen moiré test photographs, downloaded and cataloged for the **Screen Moiré Removal System** (CSM043 Computer Vision Assignment).

---

## Directory Structure

```
sample_images/
├── uhdm_*_moire.jpg               # Real-world 4K screen moiré photos from ECCV 2022 UHDM dataset
├── screen_photo_*.png             # Real monitor/display photos captured with dual-lens cameras
├── screen_moire_macro.jpg         # High-magnification macro photograph of screen subpixel moiré
├── bentham_screen_moire.png       # Screen-displayed portrait exhibit with color moiré fringes
├── effet_moire_display.jpg        # High-resolution photographic screen moiré pattern
├── 001.jpg                        # Original 4032×3024 smartphone photo of laptop display
├── ground_truth/                  # Ground truth clean reference images (for PSNR/SSIM evaluation)
│   ├── uhdm_0002_clean_ref.jpg
│   ├── uhdm_0016_clean_ref.jpg
│   ├── uhdm_0025_clean_ref.jpg
│   └── ...
└── synthetic/                     # 10 paired synthetic benchmark images (clean vs moiré)
    ├── 01_small_text_clean.png / 01_small_text_moire.png
    ├── 02_spreadsheet_clean.png / 02_spreadsheet_moire.png
    ├── 03_ui_elements_clean.png / 03_ui_elements_moire.png
    ├── 04_code_editor_clean.png / 04_code_editor_moire.png
    └── 05_geometric_shapes_clean.png / 05_geometric_shapes_moire.png
```

---

## Dataset Breakdown

### 1. ECCV 2022 UHDM Benchmark Images (`uhdm_*_moire.jpg`)
- **Source**: *Towards Efficient and Scale-Robust Ultra-High-Definition Image Demoireing* (ECCV 2022).
- **Description**: Real camera-captured screen photos exhibiting complex multi-frequency ripple patterns, color fringing, and curved interference fringes.
- **Pairs**: Matching clean reference images are stored in `ground_truth/uhdm_*_clean_ref.jpg` to enable quantitative metrics (PSNR, SSIM, and Canny Edge Preservation).

### 2. Dual-Lens Screen Photos (`screen_photo_*.png`)
- **Source**: *Dual-lens Image Demoireing* (GitHub: `circle11111/dual_lens_demoireing`).
- **Description**: Full 1080p real monitor and laptop displays captured under ambient lighting. Includes real text documents, IDE code, and web pages with screen moiré.

### 3. Wikimedia Commons Photographic Screen Moiré
- `screen_moire_macro.jpg`: Macro close-up showing RGB subpixel grid interference with digital camera sensor.
- `bentham_screen_moire.png`: Screen display showing fine detail and distinct chromatic moiré fringes.
- `effet_moire_display.jpg`: High-resolution photograph of physical screen interference.

### 4. Synthetic Paired Benchmark (`synthetic/`)
- Designed specifically to measure fine-detail preservation:
  - Small font typography (8pt–14pt text)
  - Dense spreadsheets and financial tables
  - IDE syntax highlighting and code editor lines
  - UI navigation buttons and borders
  - Geometric vectors and concentric rings

---

## Testing in the Web Application

1. **1-Click Quick Samples**:
   Open [http://localhost:5173](http://localhost:5173). Under the **Input Image** panel on the left sidebar, click any preset card under **⚡ Sample Moiré Images** to load it immediately.
2. **File Browser**:
   Click **📁 Browse Files** in the dashboard and select any image from `sample_images/`.
3. **Reference Comparison & Metrics**:
   Upload the matching file from `sample_images/ground_truth/` into the **Reference Image (Optional)** panel to evaluate PSNR (dB), SSIM, and Edge Preservation Score automatically.
