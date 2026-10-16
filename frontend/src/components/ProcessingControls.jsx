import React from 'react';

export default function ProcessingControls({
  hasImage,
  loading,
  loadingStatus,
  error,
  onProcess,
  onCompareAll,
  onCancel,
  onRetry
}) {
  return (
    <div className="processing-actions">
      {error && (
        <div className="error-banner">
          <div className="error-banner-content">
            <div style={{ fontWeight: 600, marginBottom: '2px' }}>Processing Error</div>
            <div>{error}</div>
            {onRetry && (
              <button
                className="btn btn-sm btn-danger"
                onClick={onRetry}
                style={{ marginTop: '6px' }}
              >
                ↺ Retry Operation
              </button>
            )}
          </div>
        </div>
      )}

      {loading && (
        <div className="processing-status-box">
          <div className="processing-spinner"></div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Processing in Progress</div>
            <div style={{ fontSize: '11px', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
              {loadingStatus || 'Applying frequency filtering...'}
            </div>
          </div>
          <button
            className="btn btn-sm"
            onClick={onCancel}
            title="Abort operation"
            style={{ borderColor: 'var(--error-color)', color: 'var(--error-color)' }}
          >
            Cancel
          </button>
        </div>
      )}

      {!loading ? (
        <>
          <button
            className="btn btn-primary processing-btn-large"
            disabled={!hasImage}
            onClick={() => onProcess()}
          >
            <span style={{ fontSize: '15px' }}>⚡</span> Process Image
          </button>

          <button
            className="btn btn-accent"
            disabled={!hasImage}
            onClick={() => onCompareAll()}
            title="Process image across all algorithms concurrently to benchmark results"
          >
            <span>▦</span> Compare All Methods
          </button>
        </>
      ) : (
        <button
          className="btn btn-danger processing-btn-large"
          onClick={onCancel}
        >
          ✕ Cancel Processing
        </button>
      )}
    </div>
  );
}
