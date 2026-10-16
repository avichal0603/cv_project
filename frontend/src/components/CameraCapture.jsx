import React, { useState, useRef, useEffect, useCallback } from 'react';

export default function CameraCapture({ isOpen, onClose, onCapture }) {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  
  const [snapshot, setSnapshot] = useState(null);
  const [error, setError] = useState(null);
  const [isReady, setIsReady] = useState(false);

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => {
        try {
          track.stop();
        } catch (e) {
          console.error('Error stopping track:', e);
        }
      });
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  }, []);

  // Initialize camera stream when modal opens
  useEffect(() => {
    let active = true;

    if (isOpen) {
      (async () => {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          setError('Webcam access is not supported by your browser or environment (requires HTTPS or localhost).');
          return;
        }

        try {
          const constraints = {
            video: {
              width: { ideal: 1920 },
              height: { ideal: 1080 },
              facingMode: 'user'
            },
            audio: false
          };

          const stream = await navigator.mediaDevices.getUserMedia(constraints);
          if (!active) {
            stream.getTracks().forEach(t => t.stop());
            return;
          }

          streamRef.current = stream;
          if (videoRef.current) {
            videoRef.current.srcObject = stream;
            videoRef.current.onloadedmetadata = () => {
              if (active) setIsReady(true);
            };
            await videoRef.current.play();
          }
        } catch (err) {
          if (!active) return;
          console.error('Camera error:', err);
          if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
            setError('Camera permission was denied. Please allow camera permissions in your browser bar and try again.');
          } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
            setError('No camera device was detected on your system.');
          } else {
            setError(`Unable to access webcam: ${err.message || 'Unknown error'}`);
          }
        }
      })();
    } else {
      stopCamera();
    }

    return () => {
      active = false;
      stopCamera();
    };
  }, [isOpen, stopCamera]);

  const loading = isOpen && !isReady && !snapshot && !error;

  // Capture frame to canvas and create File
  const handleCapture = () => {
    if (!videoRef.current) return;

    const video = videoRef.current;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 720;

    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const dataUrl = canvas.toDataURL('image/png');
    setSnapshot(dataUrl);

    // Convert to File object
    canvas.toBlob(blob => {
      if (blob) {
        const file = new File([blob], `camera-capture-${Date.now()}.png`, { type: 'image/png' });
        // Stash file on snapshot state or store temporarily
        canvas._capturedFile = file;
      }
    }, 'image/png');
  };

  const handleRetake = () => {
    setSnapshot(null);
  };

  const handleAccept = () => {
    if (!snapshot) return;

    // Convert dataUrl to File
    fetch(snapshot)
      .then(res => res.blob())
      .then(blob => {
        const file = new File([blob], `screen-moire-${Date.now()}.png`, { type: 'image/png' });
        onCapture(file);
        handleClose();
      })
      .catch(err => {
        setError(`Failed to save captured photo: ${err.message}`);
      });
  };

  const handleClose = () => {
    stopCamera();
    setSnapshot(null);
    setError(null);
    setIsReady(false);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">Live Camera Capture</div>
          <button className="modal-close-btn" onClick={handleClose} title="Close">✕</button>
        </div>

        <div className="modal-body">
          <div className="camera-preview-container">
            {error ? (
              <div className="error-banner" style={{ margin: '20px' }}>
                <div className="error-banner-content">
                  <strong>Camera Notice:</strong> {error}
                </div>
              </div>
            ) : loading ? (
              <div className="processing-status-box" style={{ background: 'transparent', border: 'none' }}>
                <div className="processing-spinner"></div>
                <span>Initializing camera sensor...</span>
              </div>
            ) : snapshot ? (
              <img src={snapshot} alt="Captured frame" className="camera-snapshot-preview" />
            ) : (
              <video
                ref={videoRef}
                playsInline
                autoPlay
                muted
                className="camera-video"
              />
            )}
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
              {snapshot ? 'Review photo before using for moiré removal' : 'Aim camera at screen moiré pattern and snap a frame'}
            </span>

            <div style={{ display: 'flex', gap: '8px' }}>
              {snapshot ? (
                <>
                  <button className="btn" onClick={handleRetake}>
                    ↺ Retake
                  </button>
                  <button className="btn btn-primary" onClick={handleAccept}>
                    ✓ Use This Image
                  </button>
                </>
              ) : (
                <>
                  <button className="btn" onClick={handleClose}>
                    Cancel
                  </button>
                  <button
                    className="btn btn-accent"
                    onClick={handleCapture}
                    disabled={loading || !!error}
                  >
                    📸 Capture Frame
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
