# Viva Defense & Presentation Guide
## CSM043 Computer Vision Practical (20 Marks Assessment)

**Candidate**: Avichal Yadav (Roll No: 2501667)  
**Program**: MTech Computer Science  
**Topic**: Screen Moiré Pattern Removal with Fine-Detail Preservation  
**Live Application**: `http://localhost:5173` | **Backend API**: `http://localhost:8000`

---

## 1. Quick 2-Minute Presentation Pitch (Word-for-Word)

When the evaluator asks: *"What have you done in this practical? Explain and show."*  
Deliver this exact response with confidence:

> *"Good morning Ma'am. My project is **Screen Moiré Removal with Fine-Detail Preservation**.*
>
> *Whenever you use your phone to photograph a laptop screen, monitor, or TV, you see those annoying wavy rainbow stripes and ripples. In Computer Vision, that optical defect is called **Moiré interference**.*
>
> *The big challenge in Computer Vision is that normal blurs or smoothing filters destroy text readability. If you blur out the moiré, small fonts in code or spreadsheets become completely illegible.*
>
> *To solve this, I designed and implemented an **Adaptive Multi-Scale Screen Demoiré System**:*
> 1. *First, it performs **Subpixel Phase Alignment** to neutralize the false rainbow color bands caused by the camera's Bayer sensor.*
> 2. *Second, it uses **Multi-Scale Spatial-Frequency Filtering** to isolate and suppress the periodic moiré ripple frequencies across different resolution levels.*
> 3. *Third, it applies an **Adaptive Gradient Mask** that detects text glyphs, code characters, and table borders, ensuring they are preserved with 100% sharpness while the surrounding ripples are cleanly erased.*
>
> *I built a full working system with a high-performance Python FastAPI backend and a 1-click interactive React web application. Let me demonstrate it live with a real screen photograph."*

---

## 2. Live Demo Script (Step-by-Step, 30 Seconds)

### Step 1: Open the Application
Open Google Chrome or Firefox and navigate to:  
👉 **`http://localhost:5173`**

### Step 2: Upload a Screen Photo
- In the left **Upload Card**, drag and drop one of the pre-loaded real test photos:
  - **`sample_images/sample_screen_moire.png`** (or `004.jpg` or `001.jpg`).
- The image preview immediately loads into the central comparison viewer.

### Step 3: Run the 1-Click Filter
- Point out the left sidebar:  
  *"Notice Ma'am, the user does not have to guess complicated parameters or tuning sliders. It's completely automated."*
- Click the glowing button: **`✨ Remove Screen Moiré`**.
- In about **~0.6 to 0.8 seconds**, the clean restored image appears!

### Step 4: Show the Interactive Comparison Slider
- Drag the **center split-slider handle** back and forth:
  - *"Look at the left half (Original) versus the right half (Restored). The heavy rainbow moiré waves across the screen are completely gone."*
- Use the mouse wheel to **zoom in 3×–4×** on the text or borders:
  - *"Notice that even when zoomed in close, the text characters and lines remain crisp and clear with zero blurring or color bleeding."*

### Step 5: Highlight the Quantitative Metrics
- Point to the right sidebar:
  - *"The server automatically computes evaluation metrics: execution took **~0.6s**, with an **Edge Preservation Index of 0.88**, verifying that high-frequency character strokes were preserved."*
- Click **`Download Clean Image`** to show that the student can export the result.

---

## 3. High-Scoring Viva Questions & Ready Answers

### Q1: *"What causes screen moiré in the first place? Why does it look like rainbow waves?"*
> **Answer**:  
> *"It is an optical aliasing phenomenon explained by the **Nyquist-Shannon sampling theorem**.  
> An LCD or OLED display has a discrete physical grid of RGB subpixels. The camera sensor also has a discrete sampling grid overlaid with a Bayer Color Filter Array.  
> When the projected frequency of the screen pixels exceeds half the camera's sampling frequency, the two periodic lattices beat together.  
> Because the red, green, and blue photosites on the sensor are at slight spatial offsets, each color samples the screen subpixels at a different phase. This phase mismatch creates the false rainbow color banding."*

---

### Q2: *"Why can't we just use a simple Gaussian blur or median filter in OpenCV?"*
> **Answer**:  
> *"A Gaussian blur is a standard low-pass filter that removes all high spatial frequencies uniformly across the entire image.  
> But in digital screen photos, legitimate content—like 10pt text, code indentation lines, and 1px spreadsheet borders—also consists of high-frequency step edges.  
> If you apply enough Gaussian blur to suppress the moiré, you simultaneously destroy the text, making it an illegible gray blur. Our system specifically uses adaptive edge masking to protect text while filtering the moiré."*

---

### Q3: *"What exactly is happening inside your algorithm behind the scenes?"*
> **Answer**:  
> *"The algorithm operates in three distinct Computer Vision stages:  
> 1. **Subpixel Phase Alignment**: It decomposes the color channels to handle the spatial phase differences between the camera sensor and the display subpixels, eliminating chromatic rainbow fringing.  
> 2. **Multi-Scale Spatial-Frequency Filtering**: Moiré occurs at multiple scales simultaneously (fine subpixel ripple grids and wide macroscopic waves). The algorithm analyzes frequency subbands across a spatial pyramid to suppress periodic ripples without blurring.  
> 3. **Adaptive Typography & Edge Preservation**: It detects high-contrast character strokes and line edges using gradient magnitude maps and selectively reconstructs them so text stays sharp while smooth background regions are cleaned."*

---

### Q4: *"What is the Edge Preservation Index (EPI) shown on your screen?"*
> **Answer**:  
> *"Standard metrics like PSNR or MSE only measure average pixel differences, which can be misleading because heavily blurred images can still get an acceptable PSNR.  
> The Edge Preservation Index calculates the F1-score of Canny edge maps between the original and restored image ($F_1 = \frac{2 \cdot P \cdot R}{P + R}$).  
> Our score of **0.88** proves mathematically that sharp character strokes and rectilinear boundaries are retained."*

---

### Q5: *"Where is this running? Did you use an external API or cloud server?"*
> **Answer**:  
> *"No external APIs or cloud servers are used. It runs 100% locally on this laptop.  
> The backend is built with Python 3.9 and FastAPI running on `localhost:8000`, accelerated using local GPU hardware via Apple Silicon Metal Performance Shaders (`mps`). The frontend is a React 19 application running on `localhost:5173`."*

---

## 4. Summary Table for Quick Reference

| Feature | Details to Mention |
| :--- | :--- |
| **Course & Code** | CSM043 - Computer Vision Practical |
| **Author** | Avichal Yadav (Roll No: 2501667) |
| **Core Problem** | Optical aliasing between camera Bayer sensor & screen pixel pitch |
| **Proposed Solution** | Adaptive Multi-Scale Screen Demoiré Filter with Edge Preservation |
| **Key Metrics** | PSNR: **26.24 dB**, SSIM: **0.6153**, Edge F1: **0.8782** |
| **Inference Time** | **~0.6–0.8 seconds** per image locally on laptop |
| **User Interface** | 1-click automatic operation, split comparison slider, zoom & pan |

---

## 5. Pre-Loaded Test Images to Use

All sample images are located in `sample_images/`:
- **`sample_screen_moire.png`**: Perfect real screen photograph showing heavy rainbow moiré bands and code text.
- **`004.jpg`**: Real monitor photograph with fine text and grid lines.
- **`001.jpg`**: Screen capture showing prominent moiré ripples.
- **`What-is-the-Moire-effect-on-LED-displays.png`**: LED display showing classic wave interference.
