"""Batch Evaluation Runner and Benchmarking Suite.

Runs all implemented algorithms across a dataset of test images,
recording processing times and quality metrics (PSNR, SSIM, Edge Preservation).
"""

import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is in sys.path
backend_root = str(Path(__file__).resolve().parent.parent)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)
import cv2
import numpy as np

try:
    from processing.pipeline import process_image, get_available_algorithms
    from evaluation.metrics import evaluate_all
except ImportError:
    from backend.processing.pipeline import process_image, get_available_algorithms
    from backend.evaluation.metrics import evaluate_all


def run_benchmark_on_pairs(
    image_pairs: List[Dict[str, Any]],
    algorithms: Optional[List[str]] = None,
    algo_params: Optional[Dict[str, Dict]] = None,
) -> Dict[str, Dict[str, float]]:
    """Benchmark algorithms on pairs of {'name': str, 'clean': np.ndarray, 'moire': np.ndarray}.

    Args:
        image_pairs: List of dicts with 'name', 'clean', 'moire'.
        algorithms: List of algorithm names to run. Defaults to all available.
        algo_params: Optional dictionary of algorithm parameters.

    Returns:
        Dictionary mapping algorithm name to average metrics and per-image results.
    """
    if algorithms is None:
        algorithms = ["gaussian", "fft", "wavelet", "edge_aware"]

    algo_params = algo_params or {}
    results = {}

    for algo in algorithms:
        params = algo_params.get(algo, {})
        times = []
        psnrs = []
        ssims = []
        edges = []
        detail = []

        for pair in image_pairs:
            name = pair.get("name", "unnamed")
            clean = pair["clean"]
            moire = pair["moire"]

            res = process_image(moire, algo, params)
            processed = res["image"]
            proc_time = res["processing_time"]

            metrics = evaluate_all(clean, processed)

            times.append(proc_time)
            psnrs.append(metrics["psnr"])
            ssims.append(metrics["ssim"])
            edges.append(metrics["edge_preservation_score"])

            detail.append({
                "image_name": name,
                "time_sec": round(proc_time, 4),
                **metrics,
            })

        results[algo] = {
            "avg_time_sec": round(float(np.mean(times)), 4) if times else 0.0,
            "avg_psnr": round(float(np.mean(psnrs)), 2) if psnrs else 0.0,
            "avg_ssim": round(float(np.mean(ssims)), 4) if ssims else 0.0,
            "avg_edge_preservation": round(float(np.mean(edges)), 4) if edges else 0.0,
            "samples_count": len(image_pairs),
            "per_image": detail,
        }

    return results


def run_benchmark_directory(
    dataset_dir: str,
    algorithms: Optional[List[str]] = None,
) -> Dict[str, Dict[str, float]]:
    """Load clean and moiré image pairs from a directory and run benchmarks."""
    try:
        from datasets.prepare import load_dataset_pairs
    except ImportError:
        from backend.datasets.prepare import load_dataset_pairs
    pairs = load_dataset_pairs(dataset_dir)
    if not pairs:
        print(f"No image pairs found in {dataset_dir}")
        return {}

    return run_benchmark_on_pairs(pairs, algorithms=algorithms)


if __name__ == "__main__":
    try:
        from datasets.synthetic import generate_all_synthetic_samples
    except ImportError:
        from backend.datasets.synthetic import generate_all_synthetic_samples
    print("Generating temporary test images for benchmark...")
    samples = generate_all_synthetic_samples()
    print(f"Benchmarking across {len(samples)} synthetic images...")
    bench_results = run_benchmark_on_pairs(samples)

    print("\n" + "=" * 65)
    print(f"{'Algorithm':<15} | {'Avg Time (s)':<12} | {'PSNR (dB)':<10} | {'SSIM':<8} | {'Edge F1':<8}")
    print("-" * 65)
    for algo, stats in bench_results.items():
        print(
            f"{algo:<15} | {stats['avg_time_sec']:<12.4f} | {stats['avg_psnr']:<10.2f} | "
            f"{stats['avg_ssim']:<8.4f} | {stats['avg_edge_preservation']:<8.4f}"
        )
    print("=" * 65)
