"""Dataset Inspection and Loading Utilities for Screen Moiré Datasets."""

import glob
import os
from typing import Any, Dict, List, Optional
import cv2
import numpy as np


def load_dataset_pairs(dataset_dir: str) -> List[Dict[str, Any]]:
    """Scan directory for matching *_clean.png and *_moire.png pairs.

    Returns:
        List of dicts: [{'name': str, 'clean': np.ndarray, 'moire': np.ndarray,
                         'clean_path': str, 'moire_path': str}, ...]
    """
    clean_files = sorted(glob.glob(os.path.join(dataset_dir, "*_clean.png")) +
                         glob.glob(os.path.join(dataset_dir, "*_clean.jpg")))

    pairs = []
    for c_path in clean_files:
        base_name = os.path.basename(c_path)
        stem = base_name.replace("_clean.png", "").replace("_clean.jpg", "")
        ext = os.path.splitext(c_path)[1]
        m_path = os.path.join(dataset_dir, f"{stem}_moire{ext}")

        if os.path.exists(m_path):
            clean_img = cv2.imread(c_path)
            moire_img = cv2.imread(m_path)
            if clean_img is not None and moire_img is not None:
                pairs.append({
                    "name": stem,
                    "clean": clean_img,
                    "moire": moire_img,
                    "clean_path": c_path,
                    "moire_path": m_path,
                })

    return pairs


def inspect_dataset(dataset_dir: str) -> Dict[str, Any]:
    """Inspect dataset directory and summarize metadata."""
    if not os.path.exists(dataset_dir):
        return {"error": f"Directory {dataset_dir} does not exist", "total_images": 0}

    all_images = glob.glob(os.path.join(dataset_dir, "*.png")) + glob.glob(os.path.join(dataset_dir, "*.jpg"))
    pairs = load_dataset_pairs(dataset_dir)

    details = []
    for img_path in sorted(all_images):
        stat = os.stat(img_path)
        img = cv2.imread(img_path)
        h, w, c = img.shape if img is not None else (0, 0, 0)
        details.append({
            "filename": os.path.basename(img_path),
            "size_kb": round(stat.st_size / 1024, 1),
            "resolution": f"{w}x{h}",
            "channels": c,
        })

    return {
        "dataset_dir": dataset_dir,
        "total_files": len(all_images),
        "total_paired_sets": len(pairs),
        "files": details,
    }


if __name__ == "__main__":
    target_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated")
    summary = inspect_dataset(target_dir)
    print(f"Dataset Inspection: {summary.get('dataset_dir')}")
    print(f"Total files: {summary.get('total_files')}, Paired sets: {summary.get('total_paired_sets')}")
    for item in summary.get("files", []):
        print(f" - {item['filename']} ({item['resolution']}, {item['size_kb']} KB)")
