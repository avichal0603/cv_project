import React from 'react';

export default function ParameterControls({
  algorithm,
  params,
  onParamChange,
  onResetDefaults
}) {
  if (!algorithm) return null;

  const parameterDefs = algorithm.parameters || [];

  return (
    <div className="sidebar-section">
      <div className="section-title">
        <span>Parameters</span>
        <button
          className="btn btn-sm"
          onClick={onResetDefaults}
          title="Reset parameters to recommended defaults"
          style={{ padding: '2px 8px', fontSize: '10px' }}
        >
          Reset Defaults
        </button>
      </div>

      {parameterDefs.length === 0 ? (
        <div style={{ color: 'var(--text-muted)', fontSize: '11px', padding: '6px 0' }}>
          This algorithm operates without tunable hyperparameters.
        </div>
      ) : (
        <div className="parameters-wrapper">
          {parameterDefs.map((p) => {
            const val = params[p.name] !== undefined ? params[p.name] : (p.default !== undefined ? p.default : '');
            const label = p.label || p.name.replace(/_/g, ' ');
            const description = p.description || `Parameter: ${p.name}`;

            const isEnum = p.type === 'enum' || p.type === 'select' || (Array.isArray(p.options) && p.options.length > 0);
            const isBool = p.type === 'boolean' || p.type === 'bool';

            if (isBool) {
              return (
                <div key={p.name} className="param-group">
                  <div className="param-toggle-row">
                    <div className="param-label-group">
                      <label htmlFor={`param-${p.name}`} className="param-label" style={{ textTransform: 'capitalize' }}>
                        {label}
                      </label>
                      <span className="param-tooltip-icon" title={description}>ⓘ</span>
                    </div>
                    <label className="param-toggle">
                      <input
                        type="checkbox"
                        id={`param-${p.name}`}
                        checked={Boolean(val)}
                        onChange={(e) => onParamChange(p.name, e.target.checked)}
                      />
                      <span className="param-toggle-slider"></span>
                    </label>
                  </div>
                </div>
              );
            }

            if (isEnum) {
              const options = p.options || [];
              return (
                <div key={p.name} className="param-group">
                  <div className="param-header">
                    <div className="param-label-group">
                      <label htmlFor={`param-${p.name}`} className="param-label" style={{ textTransform: 'capitalize' }}>
                        {label}
                      </label>
                      <span className="param-tooltip-icon" title={description}>ⓘ</span>
                    </div>
                  </div>
                  <select
                    id={`param-${p.name}`}
                    className="param-select"
                    value={val}
                    onChange={(e) => onParamChange(p.name, e.target.value)}
                  >
                    {options.map((opt) => {
                      const optVal = typeof opt === 'object' ? opt.value : opt;
                      const optLabel = typeof opt === 'object' ? opt.label : opt;
                      return (
                        <option key={optVal} value={optVal}>
                          {optLabel}
                        </option>
                      );
                    })}
                  </select>
                </div>
              );
            }

            // Numeric parameter
            const min = p.min !== undefined ? p.min : 0;
            const max = p.max !== undefined ? p.max : 100;
            const step = p.step !== undefined ? p.step : (Number.isInteger(min) && Number.isInteger(max) ? 1 : 0.05);

            return (
              <div key={p.name} className="param-group">
                <div className="param-header">
                  <div className="param-label-group">
                    <label htmlFor={`param-${p.name}`} className="param-label" style={{ textTransform: 'capitalize' }}>
                      {label}
                    </label>
                    <span className="param-tooltip-icon" title={description}>ⓘ</span>
                  </div>
                  <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                    {val}
                  </span>
                </div>
                <div className="param-input-row">
                  <input
                    type="range"
                    id={`slider-${p.name}`}
                    className="param-slider"
                    min={min}
                    max={max}
                    step={step}
                    value={val}
                    onChange={(e) => {
                      const num = parseFloat(e.target.value);
                      onParamChange(p.name, isNaN(num) ? min : num);
                    }}
                  />
                  <input
                    type="number"
                    id={`param-${p.name}`}
                    className="param-number-input"
                    min={min}
                    max={max}
                    step={step}
                    value={val}
                    onChange={(e) => {
                      const num = parseFloat(e.target.value);
                      onParamChange(p.name, isNaN(num) ? 0 : num);
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
