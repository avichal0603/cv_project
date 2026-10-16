import React from 'react';

export default function AlgorithmPanel({
  algorithms,
  selectedAlgorithm,
  onSelectAlgorithm,
  backendStatus,
  onRefresh
}) {
  return (
    <div className="sidebar-section">
      <div className="section-title">
        <span>Removal Algorithm</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          {backendStatus === 'checking' && (
            <span style={{ fontSize: '10px', color: 'var(--warning-color)' }}>Syncing...</span>
          )}
          <button
            className="btn btn-sm"
            onClick={onRefresh}
            title="Refresh algorithm list from backend"
            style={{ padding: '2px 6px', height: '20px', fontSize: '10px' }}
          >
            ↻
          </button>
        </div>
      </div>

      <div className="algorithm-list">
        {algorithms && algorithms.length > 0 ? (
          algorithms.map((algo) => {
            const isSelected = algo.id === selectedAlgorithm;
            return (
              <div
                key={algo.id}
                className={`algorithm-card ${isSelected ? 'active' : ''}`}
                onClick={() => onSelectAlgorithm(algo.id)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onSelectAlgorithm(algo.id);
                  }
                }}
              >
                <input
                  type="radio"
                  id={`algo-${algo.id}`}
                  name="algorithm-selection"
                  checked={isSelected}
                  onChange={() => onSelectAlgorithm(algo.id)}
                  className="algorithm-radio"
                  aria-label={algo.name}
                />
                <div className="algorithm-info">
                  <div className="algorithm-name">{algo.name}</div>
                  <div className="algorithm-desc">{algo.description}</div>
                </div>
              </div>
            );
          })
        ) : (
          <div style={{ padding: '12px', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '12px' }}>
            No algorithms available.
          </div>
        )}
      </div>
    </div>
  );
}
