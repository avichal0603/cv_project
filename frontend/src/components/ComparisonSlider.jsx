import React, { useState, useRef, useEffect, useCallback } from 'react';

export default function ComparisonSlider({
  originalSrc,
  processedSrc,
  algorithmName,
  dimensions
}) {
  const [sliderPos, setSliderPos] = useState(50); // percentage 0 to 100
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDraggingSlider, setIsDraggingSlider] = useState(false);
  const [isPanning, setIsPanning] = useState(false);
  
  const containerRef = useRef(null);
  const imageWrapperRef = useRef(null);
  const panStartRef = useRef({ x: 0, y: 0, panX: 0, panY: 0 });

  // Reset zoom & pan when image changes
  useEffect(() => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setSliderPos(50);
  }, [originalSrc, processedSrc]);

  // Handle Zoom via Wheel
  const handleWheel = useCallback((e) => {
    e.preventDefault();
    const zoomFactor = 0.1;
    const direction = e.deltaY < 0 ? 1 : -1;
    setZoom((prevZoom) => {
      const nextZoom = prevZoom + direction * zoomFactor * prevZoom;
      const clamped = Math.min(Math.max(nextZoom, 0.5), 6.0);
      return parseFloat(clamped.toFixed(2));
    });
  }, []);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    el.addEventListener('wheel', handleWheel, { passive: false });
    return () => {
      el.removeEventListener('wheel', handleWheel);
    };
  }, [handleWheel]);

  // Slider dragging calculation
  const updateSliderPosition = useCallback((clientX) => {
    if (!imageWrapperRef.current) return;
    const rect = imageWrapperRef.current.getBoundingClientRect();
    const x = clientX - rect.left;
    const percentage = Math.min(Math.max((x / rect.width) * 100, 0), 100);
    setSliderPos(percentage);
  }, []);

  // Pointer Down handling
  const handlePointerDown = (e) => {
    // If clicking on or near the divider line/handle
    const isDividerTarget = e.target.closest('.slider-divider') || e.target.closest('.slider-handle');

    if (isDividerTarget) {
      setIsDraggingSlider(true);
      e.target.setPointerCapture?.(e.pointerId);
      return;
    }

    // Otherwise, initiate panning (especially useful when zoomed in)
    setIsPanning(true);
    panStartRef.current = {
      x: e.clientX,
      y: e.clientY,
      panX: pan.x,
      panY: pan.y
    };
    e.currentTarget.setPointerCapture?.(e.pointerId);
  };

  const handlePointerMove = (e) => {
    if (isDraggingSlider) {
      updateSliderPosition(e.clientX);
    } else if (isPanning) {
      const dx = e.clientX - panStartRef.current.x;
      const dy = e.clientY - panStartRef.current.y;
      setPan({
        x: panStartRef.current.panX + dx,
        y: panStartRef.current.panY + dy
      });
    }
  };

  const handlePointerUp = (e) => {
    if (isDraggingSlider) {
      setIsDraggingSlider(false);
      try {
        e.target.releasePointerCapture?.(e.pointerId);
      } catch {
        // ignore
      }
    }
    if (isPanning) {
      setIsPanning(false);
      try {
        e.currentTarget.releasePointerCapture?.(e.pointerId);
      } catch {
        // ignore
      }
    }
  };

  // Keyboard navigation for slider
  const handleKeyDown = (e) => {
    let step = 2;
    if (e.shiftKey) step = 10;

    switch (e.key) {
      case 'ArrowLeft':
      case 'ArrowDown':
        e.preventDefault();
        setSliderPos(p => Math.max(0, p - step));
        break;
      case 'ArrowRight':
      case 'ArrowUp':
        e.preventDefault();
        setSliderPos(p => Math.min(100, p + step));
        break;
      case 'Home':
        e.preventDefault();
        setSliderPos(0);
        break;
      case 'End':
        e.preventDefault();
        setSliderPos(100);
        break;
      default:
        break;
    }
  };

  const handleZoomIn = () => {
    setZoom(z => Math.min(6.0, parseFloat((z + 0.25).toFixed(2))));
  };

  const handleZoomOut = () => {
    setZoom(z => Math.max(0.5, parseFloat((z - 0.25).toFixed(2))));
  };

  const handleResetZoom = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setSliderPos(50);
  };

  if (!originalSrc) {
    return (
      <div className="workspace-empty">
        <div className="workspace-empty-icon">
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
            <circle cx="8.5" cy="8.5" r="1.5"></circle>
            <polyline points="21 15 16 10 5 21"></polyline>
          </svg>
        </div>
        <div style={{ maxWidth: '380px' }}>
          <h2 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '6px' }}>
            No Image Uploaded
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            Upload a screen photo containing moiré fringe patterns or capture directly via webcam to begin demodulation.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="slider-container" ref={containerRef}>
      {/* Zoom / Pan Floating Control Bar */}
      <div
        style={{
          position: 'absolute',
          bottom: '16px',
          right: '16px',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          zIndex: 30,
          backgroundColor: 'rgba(22, 27, 34, 0.85)',
          backdropFilter: 'blur(8px)',
          padding: '4px 8px',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-color)',
          boxShadow: 'var(--shadow-md)'
        }}
      >
        <span className="zoom-indicator">
          {Math.round(zoom * 100)}%
        </span>
        <button
          className="btn btn-sm btn-icon"
          onClick={handleZoomOut}
          title="Zoom out"
          disabled={zoom <= 0.5}
        >
          –
        </button>
        <button
          className="btn btn-sm btn-icon"
          onClick={handleZoomIn}
          title="Zoom in"
          disabled={zoom >= 6.0}
        >
          +
        </button>
        <button
          className="btn btn-sm"
          onClick={handleResetZoom}
          title="Reset zoom & pan to default fit"
          style={{ fontSize: '11px', padding: '4px 8px' }}
        >
          Fit
        </button>
      </div>

      {/* Main Viewport */}
      <div
        className={`slider-viewport ${isPanning ? 'panning' : ''}`}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
      >
        <div
          className="slider-transform-wrapper"
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            transition: isPanning ? 'none' : 'transform 0.08s ease-out'
          }}
        >
          <div className="slider-inner" ref={imageWrapperRef}>
            {/* If no processed image yet, show original image with prompt */}
            {!processedSrc ? (
              <div style={{ position: 'relative' }}>
                <img
                  src={originalSrc}
                  alt="Original source"
                  className="slider-img"
                  draggable={false}
                />
                <div className="slider-badge badge-original">Original (Moiré)</div>
                <div
                  style={{
                    position: 'absolute',
                    bottom: '12px',
                    left: '50%',
                    transform: 'translateX(-50%)',
                    backgroundColor: 'rgba(13, 17, 23, 0.88)',
                    backdropFilter: 'blur(6px)',
                    border: '1px solid var(--border-color)',
                    padding: '6px 14px',
                    borderRadius: 'var(--radius-md)',
                    color: 'var(--text-secondary)',
                    fontSize: '12px',
                    pointerEvents: 'none',
                    whiteSpace: 'nowrap'
                  }}
                >
                  Click <strong>⚡ Process Image</strong> in sidebar to generate demoiré result
                </div>
              </div>
            ) : (
              <>
                {/* Background Layer: Processed Result */}
                <img
                  src={processedSrc}
                  alt="Processed demoiré output"
                  className="slider-img"
                  draggable={false}
                />

                {/* Foreground Layer: Original Input (Clipped to slider position) */}
                <div
                  className="slider-processed-layer"
                  style={{
                    clipPath: `inset(0 ${100 - sliderPos}% 0 0)`
                  }}
                >
                  <img
                    src={originalSrc}
                    alt="Original moiré pattern"
                    className="slider-img"
                    draggable={false}
                  />
                </div>

                {/* Badges */}
                <div className="slider-badge badge-original">
                  Original {dimensions ? `(${dimensions.width}×${dimensions.height})` : ''}
                </div>
                <div className="slider-badge badge-processed">
                  {algorithmName || 'Processed'}
                </div>

                {/* Draggable Divider Bar */}
                <div
                  className="slider-divider"
                  style={{ left: `${sliderPos}%` }}
                >
                  <div
                    className="slider-handle"
                    tabIndex={0}
                    role="slider"
                    aria-label="Image comparison divider"
                    aria-valuenow={Math.round(sliderPos)}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    onKeyDown={handleKeyDown}
                    title="Drag left/right or use arrow keys to inspect moiré removal"
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <polyline points="15 18 9 12 15 6"></polyline>
                    </svg>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ marginLeft: '-4px' }}>
                      <polyline points="9 18 15 12 9 6"></polyline>
                    </svg>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
