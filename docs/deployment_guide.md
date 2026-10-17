# Deployment Guide: Vercel Frontend & Cloud Backend
## Screen Moiré Removal System (CSM043 Computer Vision Practical)

**Author**: Avichal Yadav (Roll No: 2501667)  
**Repository**: `https://github.com/avichal0603/cv_project`

---

## 1. Overview of Architecture

This project is decoupled into:
1. **Frontend (React 19 + Vite)**: Deployed to **Vercel** for fast global CDN distribution.
2. **Backend (FastAPI + PyTorch + OpenCV)**: Deployed to a container host (**Render**, **Railway**, **Hugging Face Spaces**, or run locally with a secure tunnel).

> [!NOTE]
> **Why is the backend hosted separately from Vercel?**  
> Vercel's serverless functions have a hard uncompressed bundle limit of **250 MB**. PyTorch (`torch` + `torchvision`) requires **~800 MB+** of shared libraries. Hosting the heavy computer-vision backend on a dedicated container platform (like Render or Railway) while hosting the UI on Vercel is standard production architecture.

---

## 2. Deploy Frontend to Vercel (Step-by-Step)

### Method A: Deploy via Vercel Web Dashboard (Recommended)

1. Go to **[vercel.com](https://vercel.com)** and log in with your GitHub account.
2. Click **Add New...** $\rightarrow$ **Project**.
3. Select your repository: **`avichal0603/cv_project`** and click **Import**.
4. Configure Project Settings:
   - **Framework Preset**: `Vite` (automatically detected).
   - **Root Directory**: Leave as `./` (or select `frontend`).
     *(Both root `vercel.json` and `frontend/vercel.json` are pre-configured to build automatically).*
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. *(Optional)* Under **Environment Variables**, add:
   - **Name**: `VITE_API_BASE_URL`
   - **Value**: Your backend URL (e.g., `https://moire-removal-api.onrender.com` or your ngrok tunnel).
     *(If omitted, it defaults to relative `/api`, which works when using a reverse proxy or local dev).*
6. Click **Deploy**. In ~45 seconds, your app will be live at `https://your-project.vercel.app`!

---

## 3. Deploy Backend (4 Free Options)

### Option 1: Render.com (100% Free Cloud Web Service)
1. Go to **[render.com](https://render.com)** and sign in with GitHub.
2. Click **New +** $\rightarrow$ **Web Service**.
3. Select your repository: **`avichal0603/cv_project`**.
4. Choose **Docker** as the environment (our optimized [`Dockerfile`](file:///Users/avichalyadav/Desktop/SystemsEngg/csm043/moire_removal/Dockerfile) is pre-configured with CPU-optimized PyTorch).
5. Select the **Free** instance type.
6. Click **Create Web Service**.
7. Once deployed, Render gives you a public URL like:
   `https://moire-removal-api.onrender.com`
8. In your Vercel Project Settings $\rightarrow$ Environment Variables, set:
   `VITE_API_BASE_URL` = `https://moire-removal-api.onrender.com`
   Redeploy Vercel. Done!

---

### Option 2: Live Viva Demo via Local Tunnel / Ngrok (Fastest for Evaluator)
If you want to demonstrate the live Vercel site while using your laptop's fast Apple Silicon GPU acceleration during the viva:

1. Start your local backend on your laptop:
   ```bash
   cd backend
   python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
   ```
2. In a second terminal, open a free public tunnel:
   ```bash
   npx localtunnel --port 8000
   # OR:
   ngrok http 8000
   ```
3. Copy the generated URL (e.g., `https://smooth-terms-point.loca.lt`).
4. In your Vercel project settings, set `VITE_API_BASE_URL` to this tunnel URL, or test directly from your browser!

---

### Option 3: Railway.app
1. Go to **[railway.app](https://railway.app)**.
2. Click **New Project** $\rightarrow$ **Deploy from GitHub repo**.
3. Select `cv_project`. Railway automatically builds using the `Dockerfile`.
4. Generate a public domain under service settings.

---

### Option 4: Hugging Face Spaces (Free CPU & GPU)
1. Go to **[huggingface.co/spaces](https://huggingface.co/spaces)**.
2. Create a new Space with SDK: **Docker**.
3. Push the backend code. Hugging Face runs FastAPI Docker containers for free with no timeout restrictions.

---

## 4. Local Testing Before Cloud Deployment

To verify both frontend and backend locally before or during demonstration:

```bash
# Terminal 1: Backend
cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

Open **`http://localhost:5173`** in your browser.
