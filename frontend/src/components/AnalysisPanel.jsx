import React, { useRef } from 'react';

export default function AnalysisPanel({
  dimensions,
  processedImage,
  referenceImage,
  onReferenceSelect,
  onReferenceRemove,
  onReevaluate,
  metrics,
  history,
  onSelectHistory
}) {
  const refInputRef = useRef(null);

  const handleRefFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      onReferenceSelect(e.target.files[0]);
    }
  };

  const formatParamSummary = (params) => {
    if (!params || Object.keys(params).length === 0) return 'Default settings';
    return Object.entries(params)
      .slice(0, 4)
      .map(([k, v]) => `${k}: ${v}`)
      .join(', ');
  };

  const psnrVal = metrics && metrics.psnr !== undefined ? `${Number(metrics.psnr).toFixed(2)} dB` : null;
  const ssimVal = metrics && metrics.ssim !== undefined ? Number(metrics.ssim).toFixed(4) : null;
  const epiVal = metrics && metrics.edge_preservation_score !== undefined
    ? Number(metrics.edge_preservation_score).toFixed(4)
    : null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      {/* Metrics Section */}
      <div className="sidebar-section">
        <div className="section-title">
          <span>Performance & Metrics</span>
          {processedImage && (
            <span style={{ fontSize: '10px', color: 'var(--success-color)' }}>
              Completed
            </span>
          )}
        </div>

        <div className="metric-grid">
          <div className="metric-card">
            <span className="metric-title">Latency</span>
            <span className="metric-value highlight">
              {processedImage ? `${processedImage.processingTime}s` : '—'}
            </span>
            <span className="metric-hint">Server execution</span>
          </div>

          <div className="metric-card">
            <span className="metric-title">Resolution</span>
            <span className="metric-value">
              {dimensions ? `${dimensions.width}×${dimensions.height}` : '—'}
            </span>
            <span className="metric-hint">Pixel dimensions</span>
          </div>

          <div className="metric-card">
            <span className="metric-title">PSNR</span>
            <span className="metric-value success">
              {psnrVal || '—'}
            </span>
            <span className="metric-hint">Peak SNR</span>
          </div>

          <div className="metric-card">
            <span className="metric-title">SSIM</span>
            <span className="metric-value success">
              {ssimVal || '—'}
            </span>
            <span className="metric-hint">Structural match</span>
          </div>

          <div className="metric-card full-width">
            <span className="metric-title">Edge Preservation Index</span>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
              <span className="metric-value">
                {epiVal || '—'}
              </span>
              <span className="metric-hint">High frequency gradient retention</span>
            </div>
          </div>
        </div>

        {/* Algorithm details */}
        {processedImage && (
          <div style={{ marginTop: '4px', fontSize: '11px', color: 'var(--text-secondary)' }}>
            <div><strong style={{ color: 'var(--text-primary)' }}>Algorithm:</strong> {processedImage.algorithmName || processedImage.algorithm}</div>
            <div style={{ marginTop: '2px', wordBreak: 'break-all' }}>
              <strong style={{ color: 'var(--text-primary)' }}>Config:</strong> {formatParamSummary(processedImage.params)}
            </div>
          </div>
        )}
      </div>

      {/* Ground Truth Reference Image for Evaluation */}
      <div className="sidebar-section">
        <div className="section-title">
          <span>Ground Truth Reference</span>
        </div>

        <input
          type="file"
          ref={refInputRef}
          onChange={handleRefFileChange}
          accept="image/png, image/jpeg, image/webp"
          style={{ display: 'none' }}
        />

        {referenceImage ? (
          <div className="upload-preview-box">
            <img
              src={referenceImage.preview}
              alt="Reference ground truth"
              className="upload-thumbnail"
            />
            <div className="upload-meta">
              <div className="upload-filename" title={referenceImage.name}>
                {referenceImage.name}
              </div>
              <div className="upload-details">
                {referenceImage.width} × {referenceImage.height} px
              </div>
              <div style={{ display: 'flex', gap: '6px', marginTop: '4px' }}>
                <button
                  className="btn btn-sm btn-primary"
                  onClick={onReevaluate}
                  disabled={!processedImage}
                  title="Compute PSNR, SSIM, and Edge Preservation"
                >
                  Evaluate
                </button>
                <button
                  className="btn btn-sm"
                  onClick={() => refInputRef.current && refInputRef.current.click()}
                >
                  Change
                </button>
              </div>
            </div>
            <button
              className="upload-remove-btn"
              onClick={onReferenceRemove}
              title="Remove reference image"
            >
              ✕
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div className="warning-callout">
              <span style={{ fontSize: '13px' }}>⚠️</span>
              <div>
                No ground truth reference loaded. Objective quality metrics (PSNR, SSIM, Edge Score) require an un-corrupted reference image.
              </div>
            </div>
            <button
              className="btn btn-sm"
              onClick={() => refInputRef.current && refInputRef.current.click()}
            >
              📂 Load Reference Image
            </button>
          </div>
        )}
      </div>

      {/* History Log */}
      <div className="sidebar-section">
        <div className="section-title">
          <span>Session History</span>
          <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
            {history.length} runs
          </span>
        </div>

        {history.length === 0 ? (
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', textAlign: 'center', padding: '10px 0' }}>
            Run results will appear here for comparison.
          </div>
        ) : (
          <div className="history-list">
            {history.map((item) => (
              <div
                key={item.id}
                className="history-item"
                onClick={() => onSelectHistory(item)}
                title="Click to restore this output to workspace"
              >
                <div>
                  <div className="history-name">{item.algorithmName || item.algorithm}</div>
                  <div className="history-time">{item.timestamp} • {item.processingTime}s</div>
                </div>
                {item.metrics && item.metrics.psnr !== undefined ? (
                  <span style={{ color: 'var(--success-color)', fontSize: '10px', fontFamily: 'var(--font-mono)' }}>
                    {Number(item.metrics.psnr).toFixed(1)} dB
                  </span>
                ) : (
                  <span style={{ color: 'var(--text-muted)', fontSize: '10px' }}>
                    View →
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
