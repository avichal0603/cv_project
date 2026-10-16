import React from 'react';

export default function CompareGrid({
  results,
  selectedAlgorithm,
  onSelectResult,
  onBackToSlider
}) {
  if (!results || results.length === 0) {
    return (
      <div className="workspace-empty">
        <div className="workspace-empty-icon">
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <rect x="3" y="3" width="7" height="7"></rect>
            <rect x="14" y="3" width="7" height="7"></rect>
            <rect x="14" y="14" width="7" height="7"></rect>
            <rect x="3" y="14" width="7" height="7"></rect>
          </svg>
        </div>
        <div style={{ maxWidth: '380px', textAlign: 'center' }}>
          <h2 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '6px' }}>
            No Multi-Method Comparison Data
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            Click &quot;Compare All Methods&quot; in the left sidebar to execute and benchmark all algorithms side by side.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: 'calc(100% - 44px)', overflow: 'hidden' }}>
      <div style={{ padding: '12px 20px', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-surface)' }}>
        <div>
          <span style={{ fontWeight: 600, fontSize: '13px' }}>Multi-Algorithm Benchmark ({results.length} methods)</span>
          <span style={{ fontSize: '11px', color: 'var(--text-secondary)', marginLeft: '10px' }}>
            Click any card to inspect it in high-resolution interactive comparison slider
          </span>
        </div>
        <button className="btn btn-sm" onClick={onBackToSlider}>
          ← Back to Slider
        </button>
      </div>

      <div className="compare-grid-container">
        {results.map((res) => {
          const isSelected = res.algorithm === selectedAlgorithm;
          const time = typeof res.processing_time === 'number'
            ? `${res.processing_time.toFixed(3)}s`
            : (res.processing_time || 'N/A');

          return (
            <div
              key={res.algorithm}
              className={`compare-card ${isSelected ? 'selected' : ''}`}
              onClick={() => onSelectResult(res)}
            >
              <div className="compare-card-image-wrapper">
                <img
                  src={res.output_image}
                  alt={res.name || res.algorithm}
                  className="compare-card-image"
                />
              </div>
              <div className="compare-card-body">
                <div className="compare-card-title">{res.name || res.algorithm}</div>
                <div className="compare-card-meta">
                  <span>Latency: <strong style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>{time}</strong></span>
                  <span style={{ color: isSelected ? 'var(--accent-color)' : 'var(--text-muted)' }}>
                    {isSelected ? '✓ Active' : 'Select →'}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
