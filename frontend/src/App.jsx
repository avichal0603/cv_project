import React, { useState } from 'react';
import { useImageProcessor } from './hooks/useImageProcessor';
import ImageUpload from './components/ImageUpload';
import AlgorithmPanel from './components/AlgorithmPanel';
import ParameterControls from './components/ParameterControls';
import ProcessingControls from './components/ProcessingControls';
import ComparisonSlider from './components/ComparisonSlider';
import CompareGrid from './components/CompareGrid';
import AnalysisPanel from './components/AnalysisPanel';
import SpectrumView from './components/SpectrumView';
import ExportPanel from './components/ExportPanel';
import './styles/app.css';

export default function App() {
  const {
    originalImage,
    processedImage,
    referenceImage,
    spectrumImage,
    comparisonResults,
    algorithms,
    selectedAlgorithm,
    params,
    loading,
    loadingStatus,
    error,
    backendStatus,
    metrics,
    history,
    setOriginalImage,
    setReferenceImage,
    selectAlgorithm,
    updateParam,
    resetParams,
    processImage,
    evaluateImage,
    compareAll,
    fetchSpectrum,
    cancelProcessing,
    selectHistoricalResult,
    setProcessedImage,
    fetchAlgorithms
  } = useImageProcessor();

  const [viewMode, setViewMode] = useState('slider'); // 'slider' | 'compare'

  const currentAlgoDef = algorithms.find(a => a.id === selectedAlgorithm) || algorithms[0];

  const handleCompareAllClick = async () => {
    setViewMode('compare');
    await compareAll();
  };

  const handleSelectCompareResult = (result) => {
    setProcessedImage({
      dataUrl: result.output_image,
      algorithm: result.algorithm,
      algorithmName: result.name || result.algorithm,
      params: {},
      processingTime: result.processing_time
    });
    selectAlgorithm(result.algorithm);
    setViewMode('slider');
  };

  const handleSelectHistoryItem = (item) => {
    selectHistoricalResult(item);
    setViewMode('slider');
  };

  const handleReevaluate = () => {
    if (processedImage && referenceImage) {
      evaluateImage(processedImage.dataUrl, referenceImage.file);
    }
  };

  return (
    <div className="app-container">
      {/* Top Navigation Bar */}
      <header className="app-header">
        <div className="header-brand">
          <div className="header-icon">M</div>
          <div className="header-title-group">
            <h1>
              Screen Moiré Demoireing Studio
              <span className="header-version">CV LAB</span>
            </h1>
            <div className="header-subtitle">
              High-Fidelity Artifact Elimination & Frequency Notch Filtering
            </div>
          </div>
        </div>

        <div className="header-actions">
          <div
            className={`status-badge ${backendStatus}`}
            title={
              backendStatus === 'online'
                ? 'Connected to FastAPI backend at http://localhost:8000'
                : backendStatus === 'offline'
                ? 'Backend offline (using built-in algorithms). Run FastAPI server on port 8000.'
                : 'Verifying backend connection...'
            }
          >
            <span className="status-dot"></span>
            <span>Backend: {backendStatus.toUpperCase()}</span>
          </div>
        </div>
      </header>

      {/* Main Layout Grid */}
      <div className="dashboard-layout">
        {/* Left Sidebar: Controls & Inputs */}
        <aside className="sidebar left-sidebar">
          {/* File / Camera Upload */}
          <ImageUpload
            imageInfo={originalImage}
            onImageSelect={setOriginalImage}
            onImageRemove={() => setOriginalImage(null)}
          />

          {/* Algorithm Selection */}
          <AlgorithmPanel
            algorithms={algorithms}
            selectedAlgorithm={selectedAlgorithm}
            onSelectAlgorithm={selectAlgorithm}
            backendStatus={backendStatus}
            onRefresh={fetchAlgorithms}
          />

          {/* Dynamic Hyperparameters */}
          <ParameterControls
            algorithm={currentAlgoDef}
            params={params}
            onParamChange={updateParam}
            onResetDefaults={resetParams}
          />

          {/* Primary Action Buttons */}
          <ProcessingControls
            hasImage={Boolean(originalImage)}
            loading={loading}
            loadingStatus={loadingStatus}
            error={error}
            onProcess={() => {
              setViewMode('slider');
              processImage();
            }}
            onCompareAll={handleCompareAllClick}
            onCancel={cancelProcessing}
            onRetry={() => processImage()}
          />
        </aside>

        {/* Center Workspace: Comparison Slider / Grid */}
        <main className="workspace-main">
          {/* Toolbar */}
          <div className="workspace-toolbar">
            <div className="toolbar-left">
              <div className="view-tabs">
                <button
                  className={`view-tab ${viewMode === 'slider' ? 'active' : ''}`}
                  onClick={() => setViewMode('slider')}
                >
                  Comparison Slider
                </button>
                <button
                  className={`view-tab ${viewMode === 'compare' ? 'active' : ''}`}
                  onClick={() => setViewMode('compare')}
                >
                  Benchmark Grid {comparisonResults.length > 0 ? `(${comparisonResults.length})` : ''}
                </button>
              </div>

              {originalImage && (
                <span style={{ fontSize: '11px', color: 'var(--text-secondary)', marginLeft: '8px' }}>
                  {originalImage.width} × {originalImage.height} px
                </span>
              )}
            </div>

            <div className="toolbar-right">
              {originalImage && (
                <button
                  className="btn btn-sm"
                  onClick={() => fetchSpectrum()}
                  title="Compute 2D FFT Magnitude Spectrum"
                  style={{ fontSize: '11px' }}
                >
                  Analyze 2D FFT Spectrum
                </button>
              )}
            </div>
          </div>

          {/* Center Viewport */}
          {viewMode === 'slider' ? (
            <ComparisonSlider
              originalSrc={originalImage ? originalImage.preview : null}
              processedSrc={processedImage ? processedImage.dataUrl : null}
              algorithmName={processedImage ? processedImage.algorithmName : (currentAlgoDef ? currentAlgoDef.name : '')}
              dimensions={originalImage ? { width: originalImage.width, height: originalImage.height } : null}
            />
          ) : (
            <CompareGrid
              results={comparisonResults}
              selectedAlgorithm={selectedAlgorithm}
              onSelectResult={handleSelectCompareResult}
              onBackToSlider={() => setViewMode('slider')}
            />
          )}
        </main>

        {/* Right Sidebar: Analysis & Export */}
        <aside className="sidebar right-sidebar">
          {/* Export & Download */}
          <ExportPanel
            originalSrc={originalImage ? originalImage.preview : null}
            processedImage={processedImage}
            originalName={originalImage ? originalImage.name : null}
          />

          {/* FFT Spectrum Display */}
          <SpectrumView
            spectrumImage={spectrumImage}
            onRequestSpectrum={() => fetchSpectrum()}
            hasImage={Boolean(originalImage)}
            algorithm={selectedAlgorithm}
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
            onSelectHistory={handleSelectHistoryItem}
          />
        </aside>
      </div>
    </div>
  );
}
