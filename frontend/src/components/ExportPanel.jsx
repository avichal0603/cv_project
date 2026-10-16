import React, { useState } from 'react';

export default function ExportPanel({
  originalSrc,
  processedImage,
  _originalName
}) {
  const [exporting, setExporting] = useState(false);

  // Helper to trigger browser download
  const triggerDownload = (url, filename) => {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const getTimestamp = () => {
    const now = new Date();
    return now.toISOString().replace(/[:.]/g, '-').slice(0, 19);
  };

  // Download individual processed PNG
  const handleDownloadProcessed = () => {
    if (!processedImage || !processedImage.dataUrl) return;

    const algo = (processedImage.algorithm || 'demoire').replace(/[^a-z0-9]/gi, '_').toLowerCase();
    const filename = `moire_removed_${algo}_${getTimestamp()}.png`;
    triggerDownload(processedImage.dataUrl, filename);
  };

  // Render composite side-by-side comparison image onto canvas and download
  const handleDownloadComparison = async () => {
    if (!originalSrc || !processedImage || !processedImage.dataUrl) return;

    setExporting(true);

    try {
      const loadImg = (src) => new Promise((resolve, reject) => {
        const img = new Image();
        img.crossOrigin = 'anonymous';
        img.onload = () => resolve(img);
        img.onerror = (e) => reject(e);
        img.src = src;
      });

      const [imgOriginal, imgProcessed] = await Promise.all([
        loadImg(originalSrc),
        loadImg(processedImage.dataUrl)
      ]);

      const canvas = document.createElement('canvas');
      const targetHeight = Math.max(imgOriginal.height, imgProcessed.height);
      const aspectOrig = imgOriginal.width / imgOriginal.height;
      const aspectProc = imgProcessed.width / imgProcessed.height;

      const origW = Math.round(targetHeight * aspectOrig);
      const procW = Math.round(targetHeight * aspectProc);

      const headerHeight = 60;
      canvas.width = origW + procW;
      canvas.height = targetHeight + headerHeight;

      const ctx = canvas.getContext('2d');

      // Dark background
      ctx.fillStyle = '#0d1117';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Header labels
      ctx.fillStyle = '#e6edf3';
      ctx.font = 'bold 24px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
      ctx.fillText('Original (Moiré)', 24, 40);

      const algoLabel = `Processed (${processedImage.algorithmName || processedImage.algorithm || 'Demoiré'})`;
      ctx.fillText(algoLabel, origW + 24, 40);

      // Draw original image
      ctx.drawImage(imgOriginal, 0, headerHeight, origW, targetHeight);

      // Draw processed image
      ctx.drawImage(imgProcessed, origW, headerHeight, procW, targetHeight);

      // Dividing line
      ctx.strokeStyle = '#30363d';
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.moveTo(origW, 0);
      ctx.lineTo(origW, canvas.height);
      ctx.stroke();

      canvas.toBlob((blob) => {
        if (!blob) return;
        const blobUrl = URL.createObjectURL(blob);
        const algo = (processedImage.algorithm || 'demoire').replace(/[^a-z0-9]/gi, '_').toLowerCase();
        const filename = `moire_comparison_${algo}_${getTimestamp()}.png`;
        triggerDownload(blobUrl, filename);
        setTimeout(() => URL.revokeObjectURL(blobUrl), 1000);
      }, 'image/png');
    } catch (err) {
      console.error('Export comparison failed:', err);
      alert('Could not render comparison composite: ' + err.message);
    } finally {
      setExporting(false);
    }
  };

  const isReady = Boolean(processedImage && processedImage.dataUrl);

  return (
    <div className="sidebar-section">
      <div className="section-title">
        <span>Export & Download</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <button
          className="btn btn-primary"
          disabled={!isReady}
          onClick={handleDownloadProcessed}
          title="Save the processed demoiré image to disk (PNG format)"
        >
          <span>📥</span> Download Processed Image
        </button>

        <button
          className="btn btn-sm"
          disabled={!isReady || !originalSrc || exporting}
          onClick={handleDownloadComparison}
          title="Export a high-res side-by-side composite comparing Original vs Processed"
        >
          <span>🖼️</span> {exporting ? 'Rendering Composite...' : 'Download Side-by-Side'}
        </button>

        {!isReady && (
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', textAlign: 'center' }}>
            Process an image to enable export options.
          </div>
        )}
      </div>
    </div>
  );
}
