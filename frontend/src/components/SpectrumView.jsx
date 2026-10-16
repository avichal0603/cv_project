import React, { useState } from 'react';

export default function SpectrumView({
  spectrumImage,
  onRequestSpectrum,
  hasImage,
  algorithm
}) {
  const [isOpen, setIsOpen] = useState(true);

  // If algorithm is FFT notch or spectrum image already present, default to showing
  const isFFTRelated = algorithm === 'fft_notch' || Boolean(spectrumImage);

  return (
    <div className="sidebar-section">
      <div className="section-title">
        <span>2D Fourier Spectrum</span>
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          <button
            className="btn btn-sm"
            onClick={() => setIsOpen(!isOpen)}
            style={{ padding: '2px 6px', fontSize: '10px' }}
          >
            {isOpen ? 'Collapse' : 'Expand'}
          </button>
        </div>
      </div>

      {isOpen && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {spectrumImage ? (
            <div className="spectrum-box">
              <img
                src={spectrumImage}
                alt="2D FFT Magnitude Spectrum"
                title="Frequency spectrum showing periodic moiré spikes and filter notches"
              />
            </div>
          ) : (
            <div
              style={{
                padding: '16px 12px',
                textAlign: 'center',
                backgroundColor: 'var(--bg-primary)',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--text-secondary)',
                fontSize: '11px'
              }}
            >
              <p style={{ marginBottom: '8px' }}>
                {isFFTRelated
                  ? 'Run processing or compute spectrum to inspect frequency domain moiré spikes.'
                  : 'Fourier magnitude spectrum is available for frequency-domain analysis.'}
              </p>
              <button
                className="btn btn-sm"
                disabled={!hasImage}
                onClick={onRequestSpectrum}
                style={{ margin: '0 auto' }}
              >
                🔍 Analyze FFT Spectrum
              </button>
            </div>
          )}

          {spectrumImage && (
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '10px', color: 'var(--text-muted)' }}>
              <span>Log-magnitude | Shifted DC</span>
              <button
                className="btn btn-sm"
                onClick={onRequestSpectrum}
                title="Re-compute spectrum"
                style={{ fontSize: '10px', padding: '2px 6px' }}
              >
                Re-analyze
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
