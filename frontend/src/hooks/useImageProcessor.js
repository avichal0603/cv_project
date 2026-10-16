import { useState, useEffect, useRef, useCallback } from 'react';

export const DEFAULT_ALGORITHMS = [
  {
    id: 'gaussian',
    name: 'Gaussian Smoothing',
    description: 'Baseline spatial low-pass filter. Establishes how much moiré is removed by simple blurring and how much detail is lost.',
    parameters: [
      { name: 'kernel_size', label: 'Kernel Size', type: 'int', min: 3, max: 31, default: 5, step: 2, description: 'Size of the Gaussian blur kernel (odd integer).' },
      { name: 'sigma', label: 'Sigma', type: 'float', min: 0.5, max: 10.0, default: 1.5, step: 0.1, description: 'Standard deviation of the Gaussian filter.' },
      { name: 'luminance_only', label: 'Luminance Only', type: 'bool', default: true, description: 'Blur only the luminance channel (Y in YCrCb) to preserve color sharpness.' }
    ]
  },
  {
    id: 'fft',
    name: 'FFT Notch Filter',
    description: 'Detects periodic interference peaks in the 2D frequency domain and suppresses them with Gaussian notch reject filters.',
    parameters: [
      { name: 'notch_radius', label: 'Notch Radius', type: 'int', min: 5, max: 50, default: 15, step: 1, description: 'Radius of the notch filter applied to each detected peak.' },
      { name: 'suppression_strength', label: 'Suppression Strength', type: 'float', min: 0.0, max: 1.0, default: 0.95, step: 0.05, description: 'How strongly detected peaks are attenuated (1.0 = full removal).' },
      { name: 'min_frequency', label: 'Min Frequency', type: 'int', min: 10, max: 100, default: 20, step: 5, description: 'Minimum distance from DC center to consider as interference.' },
      { name: 'auto_detect', label: 'Auto-Detect Peaks', type: 'bool', default: true, description: 'Automatically detect periodic frequency peaks.' }
    ]
  },
  {
    id: 'wavelet',
    name: 'Wavelet Denoising',
    description: 'Multi-level discrete wavelet decomposition with coefficient thresholding to remove interference while preserving structure.',
    parameters: [
      { name: 'wavelet', label: 'Wavelet Type', type: 'select', options: ['db1', 'db2', 'db4', 'sym4', 'coif1', 'bior1.3'], default: 'db4', description: 'Mother wavelet filter bank to use.' },
      { name: 'level', label: 'Decomposition Level', type: 'int', min: 1, max: 5, default: 3, step: 1, description: 'Number of wavelet decomposition levels.' },
      { name: 'threshold_mode', label: 'Threshold Mode', type: 'select', options: ['soft', 'hard'], default: 'soft', description: 'Soft thresholding shrinks coefficients; hard sets them to zero.' },
      { name: 'threshold_value', label: 'Threshold Value', type: 'float', min: 5.0, max: 100.0, default: 30.0, step: 1.0, description: 'Threshold magnitude for wavelet coefficient suppression.' },
      { name: 'luminance_only', label: 'Luminance Only', type: 'bool', default: true, description: 'Apply wavelet denoising only to the luminance channel.' }
    ]
  },
  {
    id: 'edge_aware',
    name: 'Edge-Aware Adaptive',
    description: 'Bilateral + guided filtering with edge-aware blending. Aggressive filtering in flat regions, gentle near edges and text.',
    parameters: [
      { name: 'filter_strength', label: 'Filter Strength', type: 'int', min: 1, max: 100, default: 50, step: 1, description: 'Overall filtering intensity (scales bilateral and guided filter parameters).' },
      { name: 'edge_threshold', label: 'Edge Threshold', type: 'int', min: 10, max: 200, default: 80, step: 5, description: 'Gradient magnitude threshold for edge detection.' },
      { name: 'bilateral_d', label: 'Bilateral Diameter', type: 'int', min: 5, max: 15, default: 9, step: 2, description: 'Pixel neighborhood diameter for bilateral filter.' },
      { name: 'bilateral_sigma_color', label: 'Bilateral Color Sigma', type: 'float', min: 25, max: 150, default: 75, step: 5, description: 'Filter sigma in color space.' },
      { name: 'bilateral_sigma_space', label: 'Bilateral Space Sigma', type: 'float', min: 25, max: 150, default: 75, step: 5, description: 'Filter sigma in coordinate space.' },
      { name: 'guided_radius', label: 'Guided Filter Radius', type: 'int', min: 2, max: 16, default: 8, step: 1, description: 'Radius of the guided filter window.' },
      { name: 'guided_eps', label: 'Guided Filter Eps', type: 'float', min: 0.001, max: 1.0, default: 0.04, step: 0.005, description: 'Regularization parameter for edge preservation.' }
    ]
  }
];

/** Convert a File to a base64 data-URI string */
const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = (e) => reject(new Error('Failed to read file: ' + e));
    reader.readAsDataURL(file);
  });
};

export const formatImageSrc = (src) => {
  if (!src) return null;
  if (src.startsWith('data:image/') || src.startsWith('blob:') || src.startsWith('http')) {
    return src;
  }
  return `data:image/png;base64,${src}`;
};

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export function useImageProcessor() {
  const [originalImage, setOriginalImageState] = useState(null);
  const [processedImage, setProcessedImage] = useState(null);
  const [referenceImage, setReferenceImageState] = useState(null);
  const [spectrumImage, setSpectrumImage] = useState(null);
  const [comparisonResults, setComparisonResults] = useState([]);

  const [algorithms, setAlgorithms] = useState(DEFAULT_ALGORITHMS);
  const [selectedAlgorithm, setSelectedAlgorithm] = useState(DEFAULT_ALGORITHMS[0].id);

  const getDefaultParams = useCallback((algoId, algoList = algorithms) => {
    const algo = algoList.find(a => a.id === algoId);
    if (!algo || !algo.parameters) return {};
    const defaultObj = {};
    algo.parameters.forEach(p => {
      defaultObj[p.name] = p.default !== undefined ? p.default : (p.type === 'number' || p.type === 'int' || p.type === 'float' ? 0 : '');
    });
    return defaultObj;
  }, [algorithms]);

  const [params, setParams] = useState(() => {
    const firstAlgo = DEFAULT_ALGORITHMS[0];
    const defaultObj = {};
    if (firstAlgo && firstAlgo.parameters) {
      firstAlgo.parameters.forEach(p => {
        defaultObj[p.name] = p.default !== undefined ? p.default : 0;
      });
    }
    return defaultObj;
  });

  const [loading, setLoading] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState('');
  const [error, setError] = useState(null);
  const [backendStatus, setBackendStatus] = useState('checking');

  const [metrics, setMetrics] = useState(null);
  const [history, setHistory] = useState([]);

  const abortControllerRef = useRef(null);

  // Fetch algorithm definitions from backend
  const fetchAlgorithms = useCallback(async () => {
    try {
      setBackendStatus('checking');
      const response = await fetch(`${API_BASE}/api/algorithms`, {
        headers: { Accept: 'application/json' }
      });
      if (!response.ok) throw new Error(`${response.status}`);
      const data = await response.json();
      if (Array.isArray(data) && data.length > 0) {
        setAlgorithms(data);
        setBackendStatus('online');
        if (!data.some(a => a.id === selectedAlgorithm)) {
          setSelectedAlgorithm(data[0].id);
          setParams(getDefaultParams(data[0].id, data));
        }
      } else {
        setBackendStatus('online');
      }
    } catch {
      setBackendStatus('offline');
    }
  }, [selectedAlgorithm, getDefaultParams]);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const response = await fetch(`${API_BASE}/api/algorithms`);
        if (!response.ok) throw new Error();
        const data = await response.json();
        if (active && Array.isArray(data) && data.length > 0) {
          setAlgorithms(data);
          setBackendStatus('online');
          // Select the first backend algorithm and load its defaults
          setSelectedAlgorithm(data[0].id);
          const defaultObj = {};
          if (data[0].parameters) {
            data[0].parameters.forEach(p => {
              defaultObj[p.name] = p.default !== undefined ? p.default : 0;
            });
          }
          setParams(defaultObj);
        } else if (active) {
          setBackendStatus('online');
        }
      } catch {
        if (active) setBackendStatus('offline');
      }
    })();
    return () => { active = false; };
  }, []);

  // Set original image
  const setOriginalImage = useCallback((file) => {
    if (!file) {
      setOriginalImageState(null);
      setProcessedImage(null);
      setSpectrumImage(null);
      setComparisonResults([]);
      setMetrics(null);
      return;
    }

    const allowedTypes = ['image/png', 'image/jpeg', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      setError(`Invalid file type (${file.type || 'unknown'}). Please upload PNG, JPEG, or WebP.`);
      return;
    }

    const maxSize = 20 * 1024 * 1024;
    if (file.size > maxSize) {
      setError(`File too large (${(file.size / (1024 * 1024)).toFixed(1)} MB). Max 20MB.`);
      return;
    }

    setError(null);
    const previewUrl = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      setOriginalImageState({
        file,
        preview: previewUrl,
        name: file.name,
        size: file.size,
        width: img.naturalWidth,
        height: img.naturalHeight
      });
      setProcessedImage(null);
      setSpectrumImage(null);
      setComparisonResults([]);
      setMetrics(null);
    };
    img.onerror = () => {
      setError('Failed to read the uploaded image.');
      URL.revokeObjectURL(previewUrl);
    };
    img.src = previewUrl;
  }, []);

  // Set reference image
  const setReferenceImage = useCallback((file) => {
    if (!file) {
      setReferenceImageState(null);
      setMetrics(null);
      return;
    }

    const allowedTypes = ['image/png', 'image/jpeg', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      setError('Reference image: Invalid type. Only PNG, JPEG, and WebP supported.');
      return;
    }

    const previewUrl = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      setReferenceImageState({
        file,
        preview: previewUrl,
        name: file.name,
        width: img.naturalWidth,
        height: img.naturalHeight
      });
      setError(null);
    };
    img.onerror = () => {
      setError('Failed to read reference image.');
      URL.revokeObjectURL(previewUrl);
    };
    img.src = previewUrl;
  }, []);

  const selectAlgorithm = useCallback((algoId) => {
    setSelectedAlgorithm(algoId);
    setParams(getDefaultParams(algoId));
  }, [getDefaultParams]);

  const updateParam = useCallback((name, value) => {
    setParams(prev => ({ ...prev, [name]: value }));
  }, []);

  const resetParams = useCallback(() => {
    setParams(getDefaultParams(selectedAlgorithm));
  }, [selectedAlgorithm, getDefaultParams]);

  const cancelProcessing = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setLoading(false);
      setLoadingStatus('');
      setError('Processing cancelled.');
    }
  }, []);

  // Evaluate processed image against reference
  const evaluateImage = useCallback(async (processedB64, refFile) => {
    if (!processedB64 || !refFile) return null;
    try {
      const refB64 = await fileToBase64(refFile);

      const res = await fetch(`${API_BASE}/api/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          processed_image: processedB64,
          reference_image: refB64
        })
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Evaluation failed (${res.status}): ${text}`);
      }

      const evalData = await res.json();
      setMetrics(evalData);
      return evalData;
    } catch (err) {
      console.warn('Evaluation error:', err.message);
      return null;
    }
  }, []);

  // Fetch FFT spectrum
  const fetchSpectrum = useCallback(async (fileToUse) => {
    const file = fileToUse || (originalImage ? originalImage.file : null);
    if (!file) return;

    try {
      const b64 = await fileToBase64(file);
      const res = await fetch(`${API_BASE}/api/spectrum`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: b64 })
      });

      if (!res.ok) throw new Error(`Spectrum fetch failed: ${res.statusText}`);

      const data = await res.json();
      if (data.spectrum) {
        setSpectrumImage(formatImageSrc(data.spectrum));
      }
    } catch (err) {
      console.warn('Could not fetch spectrum:', err.message);
    }
  }, [originalImage]);

  // Process image with selected algorithm & parameters — sends JSON with base64
  const processImage = useCallback(async (customAlgo = null, customParams = null) => {
    if (!originalImage || !originalImage.file) {
      setError('Please upload an image first.');
      return;
    }

    const algoId = customAlgo || selectedAlgorithm;
    const currentAlgoMeta = algorithms.find(a => a.id === algoId) || { name: algoId };
    const effectiveParams = customParams || params;

    abortControllerRef.current = new AbortController();
    const { signal } = abortControllerRef.current;

    setLoading(true);
    setLoadingStatus(`Processing with ${currentAlgoMeta.name}...`);
    setError(null);

    const startTime = performance.now();

    try {
      const imageB64 = await fileToBase64(originalImage.file);

      const response = await fetch(`${API_BASE}/api/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image: imageB64,
          algorithm: algoId,
          params: effectiveParams
        }),
        signal
      });

      if (!response.ok) {
        let errorMsg = `Server error ${response.status}`;
        try {
          const errorJson = await response.json();
          if (errorJson.detail) errorMsg = errorJson.detail;
        } catch {
          const raw = await response.text();
          if (raw) errorMsg = raw;
        }
        throw new Error(errorMsg);
      }

      const data = await response.json();
      const clientDuration = ((performance.now() - startTime) / 1000).toFixed(3);
      const processingTime = data.processing_time !== undefined ? data.processing_time : parseFloat(clientDuration);

      // Backend returns "processed_image" field
      const outputSrc = formatImageSrc(data.processed_image);

      if (!outputSrc) {
        throw new Error('API returned an empty or invalid output image.');
      }

      const processedObj = {
        dataUrl: outputSrc,
        algorithm: algoId,
        algorithmName: currentAlgoMeta.name,
        params: effectiveParams,
        processingTime: typeof processingTime === 'number' ? processingTime.toFixed(3) : processingTime
      };

      setProcessedImage(processedObj);

      // Backend returns "spectrum" field for FFT
      if (data.spectrum) {
        setSpectrumImage(formatImageSrc(data.spectrum));
      }

      // If reference image exists, run evaluation automatically
      let currentMetrics = null;
      if (referenceImage && referenceImage.file) {
        setLoadingStatus('Computing evaluation metrics (PSNR, SSIM, EPI)...');
        currentMetrics = await evaluateImage(data.processed_image, referenceImage.file);
      }

      // Add to history
      setHistory(prev => {
        const newItem = {
          id: Date.now(),
          timestamp: new Date().toLocaleTimeString(),
          algorithm: algoId,
          algorithmName: currentAlgoMeta.name,
          params: effectiveParams,
          dataUrl: outputSrc,
          processingTime: processedObj.processingTime,
          metrics: currentMetrics
        };
        return [newItem, ...prev.slice(0, 9)];
      });

      setBackendStatus('online');
    } catch (err) {
      if (err.name === 'AbortError') {
        setError('Processing was cancelled.');
      } else {
        const isNetworkErr = err.message.includes('Failed to fetch') || err.message.includes('NetworkError');
        if (isNetworkErr) {
          setBackendStatus('offline');
          setError('Cannot connect to backend at http://localhost:8000. Please ensure the FastAPI server is running.');
        } else {
          setError(`Processing failed: ${err.message}`);
        }
      }
    } finally {
      setLoading(false);
      setLoadingStatus('');
      abortControllerRef.current = null;
    }
  }, [originalImage, selectedAlgorithm, algorithms, params, referenceImage, evaluateImage]);

  // Run all algorithms for comparison — sends JSON with base64
  const compareAll = useCallback(async () => {
    if (!originalImage || !originalImage.file) {
      setError('Please upload an image before comparing all methods.');
      return;
    }

    abortControllerRef.current = new AbortController();
    const { signal } = abortControllerRef.current;

    setLoading(true);
    setLoadingStatus('Running all algorithms for comparison...');
    setError(null);
    setComparisonResults([]);

    const algoIds = algorithms.map(a => a.id);

    try {
      const imageB64 = await fileToBase64(originalImage.file);
      let refB64 = null;
      if (referenceImage && referenceImage.file) {
        refB64 = await fileToBase64(referenceImage.file);
      }

      const response = await fetch(`${API_BASE}/api/compare`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image: imageB64,
          algorithms: algoIds,
          reference_image: refB64
        }),
        signal
      });

      if (!response.ok) {
        throw new Error(`Compare failed (${response.status}): ${response.statusText}`);
      }

      const data = await response.json();
      if (data && Array.isArray(data.results)) {
        // Backend returns "processed_image" per result
        const formatted = data.results.map(r => ({
          ...r,
          output_image: formatImageSrc(r.processed_image)
        }));
        setComparisonResults(formatted);
        if (formatted.length > 0 && !processedImage) {
          const first = formatted[0];
          setProcessedImage({
            dataUrl: first.output_image,
            algorithm: first.algorithm,
            algorithmName: first.name || first.algorithm,
            params: {},
            processingTime: first.processing_time
          });
        }
      } else {
        throw new Error('Comparison response did not contain results array.');
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        setError('Comparison was cancelled.');
      } else {
        const isNetworkErr = err.message.includes('Failed to fetch') || err.message.includes('NetworkError');
        if (isNetworkErr) {
          setBackendStatus('offline');
          setError('Backend unavailable. Cannot run comparison.');
        } else {
          setError(`Comparison error: ${err.message}`);
        }
      }
    } finally {
      setLoading(false);
      setLoadingStatus('');
      abortControllerRef.current = null;
    }
  }, [originalImage, referenceImage, algorithms, processedImage]);

  const selectHistoricalResult = useCallback((item) => {
    if (!item) return;
    setProcessedImage({
      dataUrl: item.dataUrl,
      algorithm: item.algorithm,
      algorithmName: item.algorithmName,
      params: item.params,
      processingTime: item.processingTime
    });
    setSelectedAlgorithm(item.algorithm);
    if (item.params) setParams(item.params);
    if (item.metrics) setMetrics(item.metrics);
  }, []);

  return {
    originalImage,
    processedImage,
    referenceImage,
    spectrumImage,
    comparisonResults,
    algorithms,
    selectedAlgorithm,
    params,
    loading,
    loadingStatus,
    error,
    backendStatus,
    metrics,
    history,
    setOriginalImage,
    setReferenceImage,
    selectAlgorithm,
    updateParam,
    resetParams,
    processImage,
    evaluateImage,
    compareAll,
    fetchSpectrum,
    cancelProcessing,
    selectHistoricalResult,
    setProcessedImage,
    setError,
    fetchAlgorithms
  };
}
