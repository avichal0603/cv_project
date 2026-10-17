import React from 'react';
import { useImageProcessor } from './hooks/useImageProcessor';
import ImageUpload from './components/ImageUpload';
import ComparisonSlider from './components/ComparisonSlider';
import AnalysisPanel from './components/AnalysisPanel';
import ExportPanel from './components/ExportPanel';
import './styles/app.css';

export default function App() {
  const {
    originalImage,
    processedImage,
    referenceImage,
    loading,
    loadingStatus,
    error,
    backendStatus,
    metrics,
    history,
    setOriginalImage,
    setReferenceImage,
    processImage,
    evaluateImage,
    cancelProcessing,
    selectHistoricalResult
  } = useImageProcessor();

  const handleProcessClick = () => {
    processImage('auto_demoire', {});
  };

  const handleReevaluate = () => {
    if (processedImage && referenceImage) {
      evaluateImage(processedImage.dataUrl, referenceImage.file);
    }
  };

  return (
    <div className="app-container">
      {/* Top Header */}
      <header className="app-header">
        <div className="header-brand">
          <div className="header-icon">M</div>
          <div className="header-title-group">
            <h1>
              Screen Moiré Removal System
              <span className="header-version">CV LAB</span>
            </h1>
            <div className="header-subtitle">
              Automated Screen Photograph Enhancement & Artifact Removal
            </div>
          </div>
        </div>

        <div className="header-actions">
          <div
            className={`status-badge ${backendStatus}`}
            title={backendStatus === 'online' ? 'System backend connected and active' : 'Connecting to backend... (If sleeping, may take ~30s)'}
          >
            <span className="status-dot"></span>
            <span>System: {backendStatus.toUpperCase()}</span>
          </div>
        </div>
      </header>

      {/* Main Workspace Layout */}
      <div className="dashboard-layout">
        {/* Left Sidebar: Upload & 1-Click Action */}
        <aside className="sidebar left-sidebar">
          {/* Upload Dropzone */}
          <ImageUpload
            imageInfo={originalImage}
            onImageSelect={setOriginalImage}
            onImageRemove={() => setOriginalImage(null)}
          />

          {/* Action Card */}
          <div className="sidebar-section auto-card" style={{
            background: 'linear-gradient(180deg, rgba(31, 111, 235, 0.12) 0%, rgba(22, 27, 34, 0.8) 100%)',
            border: '1px solid rgba(88, 166, 255, 0.35)',
            borderRadius: 'var(--radius-lg)',
            padding: '16px',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--accent-color)', fontWeight: 700 }}>
                Automated Processing
              </span>
              <span style={{
                background: 'rgba(63, 185, 80, 0.18)',
                color: 'var(--success-color)',
                fontSize: '10px',
                padding: '2px 8px',
                borderRadius: '10px',
                fontWeight: 600
              }}>
                Ready
              </span>
            </div>

            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
              Automatically detects and eliminates screen moiré patterns while preserving text legibility and fine borders.
            </div>

            <button
              className="btn btn-primary"
              disabled={!originalImage || loading}
              onClick={handleProcessClick}
              style={{
                padding: '13px',
                fontSize: '14px',
                fontWeight: 600,
                background: 'linear-gradient(135deg, #1f6feb 0%, #238636 100%)',
                borderColor: '#388bfd',
                boxShadow: originalImage ? '0 0 16px rgba(31, 111, 235, 0.4)' : 'none',
                cursor: originalImage ? 'pointer' : 'not-allowed'
              }}
            >
              {loading ? '⏳ Removing Moiré...' : '✨ Remove Screen Moiré'}
            </button>

            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
              paddingTop: '8px',
              borderTop: '1px solid var(--border-color)',
              fontSize: '11px',
              color: 'var(--text-muted)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Algorithm:</span>
                <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>Adaptive Moiré Filter</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Parameters:</span>
                <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>Auto-Calibrated</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Text Preservation:</span>
                <span style={{ color: 'var(--success-color)', fontWeight: 500 }}>Active</span>
              </div>
            </div>
          </div>

          {/* Loading status */}
          {loading && (
            <div className="processing-status-box" style={{ marginTop: 'auto' }}>
              <div className="processing-spinner"></div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '12px' }}>Processing Image</div>
                <div style={{ fontSize: '11px', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                  {loadingStatus || 'Removing moiré interference...'}
                </div>
              </div>
              <button
                className="btn btn-sm btn-danger"
                onClick={cancelProcessing}
                title="Cancel processing"
              >
                Cancel
              </button>
            </div>
          )}

          {error && (
            <div className="error-banner" style={{ marginTop: 'auto' }}>
              <div style={{ fontWeight: 600, fontSize: '12px' }}>Processing Notice</div>
              <div style={{ fontSize: '11px' }}>{error}</div>
            </div>
          )}
        </aside>

        {/* Center Workspace: Split-screen comparison */}
        <main className="workspace-main">
          <div className="workspace-toolbar">
            <div className="toolbar-left">
              <span style={{ fontWeight: 600, fontSize: '13px' }}>
                Interactive Split Comparison
              </span>
              {originalImage && (
                <span style={{ fontSize: '11px', color: 'var(--text-secondary)', marginLeft: '10px' }}>
                  {originalImage.width} × {originalImage.height} px
                </span>
              )}
            </div>

            <div className="toolbar-right">
              {processedImage && (
                <span style={{ fontSize: '11px', color: 'var(--success-color)' }}>
                  ✓ Demoiréing Complete ({processedImage.processingTime}s)
                </span>
              )}
            </div>
          </div>

          <ComparisonSlider
            originalSrc={originalImage ? originalImage.preview : null}
            processedSrc={processedImage ? processedImage.dataUrl : null}
            algorithmName="Adaptive Demoiré Filter"
            dimensions={originalImage ? { width: originalImage.width, height: originalImage.height } : null}
          />
        </main>

        {/* Right Sidebar: Analysis & Export */}
        <aside className="sidebar right-sidebar">
          {/* Download & Export Buttons */}
          <ExportPanel
            originalSrc={originalImage ? originalImage.preview : null}
            processedImage={processedImage}
            originalName={originalImage ? originalImage.name : null}
          />

          {/* Performance & Quality Metrics */}
          <AnalysisPanel
            dimensions={originalImage ? { width: originalImage.width, height: originalImage.height } : null}
            processedImage={processedImage}
            referenceImage={referenceImage}
            onReferenceSelect={setReferenceImage}
            onReferenceRemove={() => setReferenceImage(null)}
            onReevaluate={handleReevaluate}
            metrics={metrics}
            history={history}
            onSelectHistory={selectHistoricalResult}
          />
        </aside>
      </div>

      {/* Bottom Footer */}
      <footer className="app-footer">
        <div className="footer-left">
          <span className="footer-credit">
            Computer Vision Practical • Made by <strong>Avichal Yadav</strong> (2501667, MTech CS)
          </span>
        </div>
        <div className="footer-right">
          <span className="footer-tag">CSM043 Coursework</span>
        </div>
      </footer>
    </div>
  );
}
