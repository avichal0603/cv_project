import React, { useRef, useState } from 'react';
import CameraCapture from './CameraCapture';

const SAMPLE_PRESETS = [
  { id: 'uhdm_curved', label: 'Curved Moiré', desc: 'UHDM Real', src: '/samples/uhdm_0002_moire.jpg' },
  { id: 'uhdm_text', label: 'Screen Text', desc: 'Typography', src: '/samples/uhdm_0025_moire.jpg' },
  { id: 'macro', label: 'Monitor Macro', desc: 'Subpixel', src: '/samples/screen_moire_macro.jpg' },
  { id: 'small_text', label: 'Small Text', desc: 'Fine Detail', src: '/samples/01_small_text_moire.png' },
  { id: 'code', label: 'Code Editor', desc: 'IDE Lines', src: '/samples/04_code_editor_moire.png' },
  { id: 'portrait', label: 'Portrait', desc: 'Screen Photo', src: '/samples/bentham_screen_moire.png' },
];

export default function ImageUpload({ imageInfo, onImageSelect, onImageRemove }) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [cameraModalOpen, setCameraModalOpen] = useState(false);
  const fileInputRef = useRef(null);

  const handleSelectSample = async (sample) => {
    try {
      const res = await fetch(sample.src);
      const blob = await res.blob();
      const ext = sample.src.endsWith('.png') ? '.png' : '.jpg';
      const file = new File([blob], `${sample.id}${ext}`, { type: blob.type });
      onImageSelect(file);
    } catch (e) {
      console.error('Failed to load sample image:', e);
    }
  };

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isDragOver) setIsDragOver(true);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      onImageSelect(file);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      onImageSelect(file);
    }
  };

  const handleBrowseClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
      fileInputRef.current.click();
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes && bytes !== 0) return '';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="sidebar-section">
      <div className="section-title">
        <span>Input Image</span>
        {imageInfo && (
          <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
            {imageInfo.width}×{imageInfo.height}
          </span>
        )}
      </div>

      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept="image/png, image/jpeg, image/webp, image/avif, .avif"
        style={{ display: 'none' }}
      />

      {imageInfo ? (
        <div className="upload-preview-box">
          <img
            src={imageInfo.preview}
            alt="Source thumbnail"
            className="upload-thumbnail"
          />
          <div className="upload-meta">
            <div className="upload-filename" title={imageInfo.name}>
              {imageInfo.name}
            </div>
            <div className="upload-details">
              {imageInfo.width} × {imageInfo.height} px • {formatFileSize(imageInfo.size)}
            </div>
            <div style={{ display: 'flex', gap: '6px', marginTop: '4px' }}>
              <button
                className="btn btn-sm"
                onClick={handleBrowseClick}
                title="Replace with another image"
              >
                Replace
              </button>
              <button
                className="btn btn-sm"
                onClick={() => setCameraModalOpen(true)}
                title="Capture new from camera"
              >
                Camera
              </button>
            </div>
          </div>
          <button
            className="upload-remove-btn"
            onClick={onImageRemove}
            title="Remove image"
            aria-label="Remove image"
          >
            ✕
          </button>
        </div>
      ) : (
        <div
          className={`upload-dropzone ${isDragOver ? 'drag-over' : ''}`}
          onDragEnter={handleDragEnter}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={handleBrowseClick}
        >
          <div className="upload-icon-wrapper">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
          </div>
          <div className="upload-text-main">Drop screen moiré photo here</div>
          <div className="upload-text-sub">Supports PNG, JPEG, WebP, AVIF (up to 20MB)</div>
          
          <div className="upload-actions-row" onClick={e => e.stopPropagation()}>
            <button className="btn btn-sm" onClick={handleBrowseClick}>
              📁 Browse Files
            </button>
            <button
              className="btn btn-sm btn-accent"
              onClick={() => setCameraModalOpen(true)}
            >
              📷 Camera
            </button>
          </div>
        </div>
      )}

      <div className="sample-presets-container">
        <div className="sample-presets-header">
          <span>⚡ Sample Moiré Images</span>
          <span className="sample-presets-hint">Click to test instantly</span>
        </div>
        <div className="sample-presets-grid">
          {SAMPLE_PRESETS.map((sample) => (
            <button
              key={sample.id}
              type="button"
              className="sample-preset-card"
              onClick={() => handleSelectSample(sample)}
              title={`${sample.label} (${sample.desc})`}
            >
              <img src={sample.src} alt={sample.label} className="sample-preset-thumb" />
              <div className="sample-preset-info">
                <span className="sample-preset-title">{sample.label}</span>
                <span className="sample-preset-tag">{sample.desc}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      <CameraCapture
        isOpen={cameraModalOpen}
        onClose={() => setCameraModalOpen(false)}
        onCapture={(file) => onImageSelect(file)}
      />
    </div>
  );
}
