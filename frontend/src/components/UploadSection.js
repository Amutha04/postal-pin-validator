import React, { useState, useRef, useEffect, useCallback } from 'react';
import './UploadSection.css';
import axios from 'axios';
import { toast } from 'react-toastify';
import BulkResults from './BulkResults';
import Dashboard from './Dashboard';
import ResultSection from './ResultSection';
import API_BASE_URL from '../apiConfig';

const HISTORY_STORAGE_KEY = 'pincheck_validation_history';

const getDisplayTime = () => new Date().toLocaleString([], {
  month: 'short',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
});

const getHistoryDate = () => new Date().toISOString().slice(0, 10);

function UploadSection({ authToken, user }) {
  const [mode, setMode] = useState('scan');
  const [loading, setLoading] = useState(false);
  const [showSlowOcrHint, setShowSlowOcrHint] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const [lookupResult, setLookupResult] = useState(null);
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [pinInput, setPinInput] = useState('');
  const [bulkFiles, setBulkFiles] = useState([]);
  const [bulkResults, setBulkResults] = useState([]);
  const [history, setHistory] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(HISTORY_STORAGE_KEY)) || [];
    } catch (error) {
      return [];
    }
  });
  const [bulkProgress, setBulkProgress] = useState({ current: 0, total: 0, running: false });

  // Live scanner state
  const [cameraActive, setCameraActive] = useState(false);
  const [liveProcessing, setLiveProcessing] = useState(false);
  const [liveOverlay, setLiveOverlay] = useState(null);
  const [liveCount, setLiveCount] = useState(0);
  const [liveResults, setLiveResults] = useState([]);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);
  const bulkInputRef = useRef(null);
  const slowHintTimerRef = useRef(null);
  const isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);

  const normalizeResult = useCallback((source, data, filename = '-') => {
    const recipient = data.groq_data?.recipient;
    return {
      id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      date: getHistoryDate(),
      time: getDisplayTime(),
      source,
      filename,
      status: data.valid ? 'Valid' : 'Mismatch',
      pincode: data.pincode || data.extracted_pin || '-',
      district: data.district || recipient?.district || data.suggestion?.district || data.actual_location?.district || '-',
      state: data.state || recipient?.state || data.suggestion?.state || data.actual_location?.state || '-',
      suggestion: data.suggestion?.suggested_pin || '-',
      message: data.message || '',
      ocr_engine: data.ocr_engine || (data.lookup ? 'Manual lookup' : '-'),
    };
  }, []);

  const normalizeError = useCallback((source, filename, message) => ({
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    date: getHistoryDate(),
    time: getDisplayTime(),
    source,
    filename,
    status: 'Error',
    pincode: '-',
    district: '-',
    state: '-',
    suggestion: '-',
    message: message || 'Failed',
    ocr_engine: '-',
  }), []);

  const appendHistory = useCallback((items) => {
    const rows = Array.isArray(items) ? items : [items];
    setHistory(prev => [...rows, ...prev].slice(0, 250));
    if (authToken) {
      axios.post(`${API_BASE_URL}/api/history`, { rows }, {
        headers: { Authorization: `Bearer ${authToken}` },
      }).catch(() => {
        toast.error('Could not save dashboard history');
      });
    }
  }, [authToken]);

  const clearHistory = () => {
    setHistory([]);
    if (authToken) {
      axios.delete(`${API_BASE_URL}/api/history`, {
        headers: { Authorization: `Bearer ${authToken}` },
      }).catch(() => {
        toast.error('Could not clear saved history');
      });
    }
    toast.success('Dashboard history cleared');
  };

  useEffect(() => {
    if (!authToken) {
      localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(history));
    }
  }, [authToken, history]);

  useEffect(() => {
    if (!authToken) {
      try {
        setHistory(JSON.parse(localStorage.getItem(HISTORY_STORAGE_KEY)) || []);
      } catch (error) {
        setHistory([]);
      }
      return;
    }

    axios.get(`${API_BASE_URL}/api/history`, {
      headers: { Authorization: `Bearer ${authToken}` },
    }).then((response) => {
      setHistory(response.data.history || []);
    }).catch(() => {
      toast.error('Could not load saved dashboard history');
    });
  }, [authToken]);

  const startSlowOcrHint = useCallback(() => {
    if (slowHintTimerRef.current) {
      clearTimeout(slowHintTimerRef.current);
    }
    setShowSlowOcrHint(false);
    slowHintTimerRef.current = setTimeout(() => {
      setShowSlowOcrHint(true);
    }, 1200);
  }, []);

  const stopSlowOcrHint = useCallback(() => {
    if (slowHintTimerRef.current) {
      clearTimeout(slowHintTimerRef.current);
      slowHintTimerRef.current = null;
    }
    setShowSlowOcrHint(false);
  }, []);

  useEffect(() => () => stopSlowOcrHint(), [stopSlowOcrHint]);

  // ---- Single scan handlers ----
  const handleFile = (file) => {
    if (file && file.type.startsWith('image/')) {
      setImage(file);
      setPreview(URL.createObjectURL(file));
      setScanResult(null);
    }
  };

  const handleSubmit = async () => {
    if (!image) return;
    const formData = new FormData();
    formData.append('image', image);
    try {
      setLoading(true);
      startSlowOcrHint();
      const response = await axios.post(
        `${API_BASE_URL}/api/validate`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      setScanResult(response.data);
      appendHistory(normalizeResult('Scan', response.data, image.name));
      toast.success('Validation complete');
    } catch (error) {
      const msg = error.response?.data?.error || 'Something went wrong';
      appendHistory(normalizeError('Scan', image.name, msg));
      toast.error(msg);
    } finally {
      stopSlowOcrHint();
      setLoading(false);
    }
  };

  // FIX 6: Clear pinInput after successful lookup so placeholder reappears
  const handleLookup = async () => {
    const pin = pinInput.trim();
    if (pin.length !== 6 || !/^\d{6}$/.test(pin)) {
      toast.error('Enter a valid 6-digit PIN code');
      return;
    }
    try {
      setLoading(true);
      const response = await axios.post(
        `${API_BASE_URL}/api/lookup`,
        { pincode: pin },
        { headers: { 'Content-Type': 'application/json' } }
      );
      setLookupResult(response.data);
      appendHistory(normalizeResult('Lookup', response.data, pin));
      if (response.data.valid) {
        toast.success('PIN code found');
        setPinInput(''); // FIX 6: clear input so placeholder reappears
      } else {
        toast.error('PIN code not found');
        setPinInput(''); // FIX 6: clear on not found too
      }
    } catch (error) {
      const msg = error.response?.data?.error || 'Something went wrong';
      appendHistory(normalizeError('Lookup', pin, msg));
      toast.error(msg);
    } finally {
      setLoading(false);
      setPinInput('');
    }
  };

  const handleClear = () => {
    setImage(null);
    setPreview(null);
    setScanResult(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handlePinKeyDown = (e) => {
    if (e.key === 'Enter') handleLookup();
  };

  // ---- Bulk handlers ----
  // FIX 3: handleBulkFiles for NEW files (replaces all)
  const handleBulkFiles = (files) => {
    const images = Array.from(files).filter(f => f.type.startsWith('image/'));
    if (images.length === 0) { toast.error('No valid image files selected'); return; }
    setBulkFiles(images);
    setBulkResults([]); // reset results only when starting fresh
    setBulkProgress({ current: 0, total: 0, running: false });
  };

  // FIX 3: handleAddMore — appends files, keeps existing results
  const handleAddMore = (files) => {
    const images = Array.from(files).filter(f => f.type.startsWith('image/'));
    if (images.length === 0) { toast.error('No valid image files selected'); return; }
    setBulkFiles(images); // new batch to validate
    // DO NOT reset bulkResults — keep previous results intact
    setBulkProgress({ current: 0, total: 0, running: false });
  };

  // FIX 3: Validate appends to existing results instead of replacing
  const handleBulkValidate = async () => {
    if (bulkFiles.length === 0) return;
    setBulkProgress({ current: 0, total: bulkFiles.length, running: true });
    for (let i = 0; i < bulkFiles.length; i++) {
      const file = bulkFiles[i];
      const formData = new FormData();
      formData.append('image', file);
      setBulkProgress(prev => ({ ...prev, current: i + 1 }));
      try {
        startSlowOcrHint();
        const response = await axios.post(
          `${API_BASE_URL}/api/validate`, formData,
          { headers: { 'Content-Type': 'multipart/form-data' } }
        );
        const resultRow = normalizeResult('Bulk', response.data, file.name);
        setBulkResults(prev => [...prev, resultRow]);
        appendHistory(resultRow);
      } catch (error) {
        const msg = error.response?.data?.error || 'Failed';
        const errorRow = normalizeError('Bulk', file.name, msg);
        setBulkResults(prev => [...prev, errorRow]);
        appendHistory(errorRow);
      }
      stopSlowOcrHint();
    }
    const processedCount = bulkFiles.length;
    setBulkFiles([]);
    setBulkProgress(prev => ({ ...prev, running: false }));
    toast.success(`Bulk validation complete: ${processedCount} images processed`);
  };

  const handleBulkClear = () => {
    setBulkFiles([]);
    setBulkResults([]);
    setBulkProgress({ current: 0, total: 0, running: false });
    if (bulkInputRef.current) bulkInputRef.current.value = '';
  };

  // ---- Live Scanner ----
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } }
      });
      streamRef.current = stream;
      setCameraActive(true);
      setLiveCount(0);
      setLiveResults([]);
    } catch (err) {
      toast.error('Could not access camera. Check permissions.');
    }
  };

  useEffect(() => {
    if (cameraActive && videoRef.current && streamRef.current) {
      videoRef.current.srcObject = streamRef.current;
    }
  }, [cameraActive]);

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop());
      streamRef.current = null;
    }
    setCameraActive(false);
    setLiveProcessing(false);
    setLiveOverlay(null);
  }, []);

  const captureAndValidate = useCallback(async () => {
    if (liveProcessing || !videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);
    canvas.toBlob(async (blob) => {
      if (!blob) return;
      setLiveProcessing(true);
      setLiveOverlay(null);
      startSlowOcrHint();
      const formData = new FormData();
      formData.append('image', blob, `capture-${Date.now()}.jpg`);
      try {
        const response = await axios.post(
          `${API_BASE_URL}/api/validate`, formData,
          { headers: { 'Content-Type': 'multipart/form-data' } }
        );
        const data = response.data;
        const resultRow = normalizeResult('Live', data, `Capture #${liveResults.length + 1}`);
        setLiveOverlay(data.valid ? 'valid' : 'invalid');
        setLiveResults(prev => [...prev, resultRow]);
        appendHistory(resultRow);
        setLiveCount(prev => prev + 1);
      } catch (error) {
        const msg = error.response?.data?.error || 'Failed';
        const errorRow = normalizeError('Live', `Capture #${liveResults.length + 1}`, msg);
        setLiveOverlay('error');
        setLiveResults(prev => [...prev, errorRow]);
        appendHistory(errorRow);
        setLiveCount(prev => prev + 1);
      } finally {
        stopSlowOcrHint();
        setLiveProcessing(false);
        setTimeout(() => setLiveOverlay(null), 1500);
      }
    }, 'image/jpeg', 0.9);
  }, [appendHistory, liveProcessing, liveResults.length, normalizeError, normalizeResult, startSlowOcrHint, stopSlowOcrHint]);

  useEffect(() => {
    if (mode !== 'live' || !cameraActive) return;
    const handler = (e) => {
      if (e.code === 'Space' && !liveProcessing) {
        e.preventDefault();
        captureAndValidate();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [mode, cameraActive, liveProcessing, captureAndValidate]);

  useEffect(() => {
    if (mode !== 'live') stopCamera();
  }, [mode, stopCamera]);

  return (
    <div className="upload-section">
      <div className="hero-text">
        <h1 className="hero-title">
          Validate your <span className="highlight">PIN Code</span>
        </h1>
        <p className="hero-sub">
          Scan an envelope or type a PIN to verify against 157,000+ Indian postal records.
        </p>
      </div>

      {/* Mode toggle */}
      <div className="mode-toggle">
        <button className={`mode-btn ${mode === 'scan' ? 'active' : ''}`}
          onClick={() => setMode('scan')}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <rect x="1" y="3" width="14" height="10" rx="2" stroke="currentColor" strokeWidth="1.5" fill="none"/>
            <circle cx="8" cy="8" r="2.5" stroke="currentColor" strokeWidth="1.5" fill="none"/>
          </svg>
          Scan
        </button>
        <button className={`mode-btn ${mode === 'lookup' ? 'active' : ''}`}
          onClick={() => setMode('lookup')}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="7" cy="7" r="4.5" stroke="currentColor" strokeWidth="1.5" fill="none"/>
            <path d="M10.5 10.5L14 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
          Lookup
        </button>
        <button className={`mode-btn ${mode === 'bulk' ? 'active' : ''}`}
          onClick={() => setMode('bulk')}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <rect x="2" y="1" width="12" height="4" rx="1" stroke="currentColor" strokeWidth="1.3" fill="none"/>
            <rect x="2" y="6" width="12" height="4" rx="1" stroke="currentColor" strokeWidth="1.3" fill="none"/>
            <rect x="2" y="11" width="12" height="4" rx="1" stroke="currentColor" strokeWidth="1.3" fill="none"/>
          </svg>
          Bulk
        </button>
        <button className={`mode-btn ${mode === 'live' ? 'active' : ''}`}
          onClick={() => setMode('live')}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="3" fill="currentColor"/>
            <circle cx="8" cy="8" r="6.5" stroke="currentColor" strokeWidth="1.5" fill="none"/>
          </svg>
          Live
        </button>
        <button className={`mode-btn ${mode === 'dashboard' ? 'active' : ''}`}
          onClick={() => setMode('dashboard')}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <rect x="2" y="8" width="2.5" height="5" rx="1" fill="currentColor"/>
            <rect x="6.75" y="4" width="2.5" height="9" rx="1" fill="currentColor"/>
            <rect x="11.5" y="6" width="2.5" height="7" rx="1" fill="currentColor"/>
          </svg>
          Dashboard
        </button>
      </div>

      {/* ---- SCAN MODE ---- */}
      {mode === 'scan' && (
        <>
          <div
            className={`envelope ${dragActive ? 'drag-over' : ''} ${preview ? 'has-preview' : ''}`}
            onClick={() => !preview && fileInputRef.current.click()}
            onDrop={(e) => { e.preventDefault(); setDragActive(false); handleFile(e.dataTransfer.files[0]); }}
            onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
            onDragLeave={() => setDragActive(false)}
          >
            <div className="airmail-stripe top-stripe">
              {[...Array(20)].map((_, i) => (
                <div key={i} className={`stripe-block ${i % 2 === 0 ? 'red' : 'blue'}`} />
              ))}
            </div>
            <div className="envelope-content">
              {preview ? (
                <div className="preview-area">
                  <img src={preview} alt="Envelope" className="preview-img" />
                  <button className="clear-btn" onClick={(e) => { e.stopPropagation(); handleClear(); }}>
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                      <path d="M1 1L13 13M1 13L13 1" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                    </svg>
                  </button>
                </div>
              ) : (
                <div className="drop-content">
                  <div className="drop-icon">
                    <svg width="56" height="56" viewBox="0 0 56 56" fill="none">
                      <rect x="4" y="14" width="48" height="32" rx="3" stroke="#d6d3d1" strokeWidth="2" fill="#fafaf9"/>
                      <path d="M4 17L28 34L52 17" stroke="#d6d3d1" strokeWidth="2" fill="none"/>
                      <rect x="32" y="6" width="14" height="14" rx="2" fill="#fef2f2" stroke="#fca5a5" strokeWidth="1.5"/>
                      <path d="M36 10L39 15L42 10" stroke="#dc2626" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
                    </svg>
                  </div>
                  <p className="drop-text">Drop your envelope image here</p>
                  <p className="drop-hint">or click to browse — JPG, PNG supported</p>
                </div>
              )}
            </div>
            <div className="airmail-stripe bottom-stripe">
              {[...Array(20)].map((_, i) => (
                <div key={i} className={`stripe-block ${i % 2 === 0 ? 'blue' : 'red'}`} />
              ))}
            </div>
          </div>
          <input type="file" accept="image/*" ref={fileInputRef}
            onChange={(e) => handleFile(e.target.files[0])} style={{ display: 'none' }} />
          <input type="file" accept="image/*" capture="environment" ref={cameraInputRef}
            onChange={(e) => handleFile(e.target.files[0])} style={{ display: 'none' }} />
          <div className="actions">
            <button className="btn-ghost" onClick={() => fileInputRef.current.click()}>
              {preview ? 'Change Image' : 'Browse Files'}
            </button>
            {isMobile && (
              <button className="btn-ghost" onClick={() => cameraInputRef.current.click()}>
                Camera
              </button>
            )}
            {preview && (
              <button className="btn-primary" onClick={handleSubmit} disabled={loading}>
                {loading ? (
                  <span className="btn-loading"><span className="spinner"></span>Analyzing...</span>
                ) : 'Validate PIN'}
              </button>
            )}
          </div>
          {loading && showSlowOcrHint && (
            <p className="slow-ocr-hint">Reading envelope... this may take a few seconds.</p>
          )}
          {scanResult && <ResultSection result={scanResult} />}
        </>
      )}

      {/* ---- LOOKUP MODE ---- */}
      {mode === 'lookup' && (
        <div className="lookup-section">
          <div className="lookup-input-wrap">
            <input
              type="text"
              className="lookup-input"
              placeholder="Enter 6-digit PIN code"
              value={pinInput}
              onChange={(e) => setPinInput(e.target.value.replace(/\D/g, '').slice(0, 6))}
              onKeyDown={handlePinKeyDown}
              maxLength={6}
              autoFocus
            />
            <button className="btn-primary lookup-btn" onClick={handleLookup}
              disabled={loading || pinInput.length !== 6}>
              {loading ? (
                <span className="btn-loading"><span className="spinner"></span>Looking up...</span>
              ) : 'Lookup'}
            </button>
          </div>
          <p className="lookup-hint">Type a PIN and press Enter or click Lookup</p>
          {lookupResult && <ResultSection result={lookupResult} />}
        </div>
      )}

      {/* ---- BULK MODE ---- */}
      {/* FIX 2: BulkResults rendered INSIDE bulk mode section only */}
      {mode === 'bulk' && (
        <div className="bulk-section">
          <div className={`envelope ${dragActive ? 'drag-over' : ''}`}
            onClick={() => !bulkProgress.running && bulkInputRef.current.click()}
            onDrop={(e) => { e.preventDefault(); setDragActive(false); handleBulkFiles(e.dataTransfer.files); }}
            onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
            onDragLeave={() => setDragActive(false)}>
            <div className="airmail-stripe top-stripe">
              {[...Array(20)].map((_, i) => (
                <div key={i} className={`stripe-block ${i % 2 === 0 ? 'red' : 'blue'}`} />
              ))}
            </div>
            <div className="envelope-content">
              <div className="drop-content">
                {bulkFiles.length > 0 ? (
                  <>
                    <div className="bulk-file-count">{bulkFiles.length}</div>
                    <p className="drop-text">{bulkFiles.length} envelope{bulkFiles.length > 1 ? 's' : ''} selected</p>
                    <p className="drop-hint">{bulkFiles.map(f => f.name).slice(0, 3).join(', ')}{bulkFiles.length > 3 ? ` +${bulkFiles.length - 3} more` : ''}</p>
                  </>
                ) : (
                  <>
                    <div className="drop-icon">
                      <svg width="56" height="56" viewBox="0 0 56 56" fill="none">
                        <rect x="8" y="10" width="40" height="28" rx="3" stroke="#d6d3d1" strokeWidth="2" fill="#fafaf9"/>
                        <rect x="4" y="14" width="40" height="28" rx="3" stroke="#d6d3d1" strokeWidth="2" fill="#fff"/>
                        <path d="M4 17L24 30L44 17" stroke="#d6d3d1" strokeWidth="2" fill="none"/>
                      </svg>
                    </div>
                    <p className="drop-text">Drop multiple envelope images</p>
                    <p className="drop-hint">or click to browse — select multiple files</p>
                  </>
                )}
              </div>
            </div>
            <div className="airmail-stripe bottom-stripe">
              {[...Array(20)].map((_, i) => (
                <div key={i} className={`stripe-block ${i % 2 === 0 ? 'blue' : 'red'}`} />
              ))}
            </div>
          </div>

          {/* FIX 3: separate file input for "Add More" */}
          <input type="file" accept="image/*" multiple ref={bulkInputRef}
            onChange={(e) => handleBulkFiles(e.target.files)} style={{ display: 'none' }} />
          <input type="file" accept="image/*" multiple
            id="bulk-add-more-input"
            onChange={(e) => handleAddMore(e.target.files)} style={{ display: 'none' }} />

          {bulkProgress.running && (
            <div className="bulk-progress">
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${(bulkProgress.current / bulkProgress.total) * 100}%` }} />
              </div>
              <span className="progress-text">Processing {bulkProgress.current} of {bulkProgress.total}...</span>
            </div>
          )}
          {bulkProgress.running && showSlowOcrHint && (
            <p className="slow-ocr-hint">Reading envelope... this may take a few seconds.</p>
          )}
          <div className="actions">
            {(bulkFiles.length > 0 || bulkResults?.length > 0) && (
              <button className="btn-ghost" onClick={handleBulkClear} disabled={bulkProgress.running}>Clear All</button>
            )}
            {/* FIX 3: Add More uses separate handler that preserves results */}
            <button className="btn-ghost"
              onClick={() => {
                if (bulkResults?.length > 0) {
                  document.getElementById('bulk-add-more-input').click();
                } else {
                  bulkInputRef.current.click();
                }
              }}
              disabled={bulkProgress.running}>
              {bulkFiles.length > 0 || bulkResults?.length > 0 ? 'Add More' : 'Browse Files'}
            </button>
            {bulkFiles.length > 0 && (
              <button className="btn-primary" onClick={handleBulkValidate} disabled={bulkProgress.running}>
                {bulkProgress.running ? (
                  <span className="btn-loading"><span className="spinner"></span>Processing...</span>
                ) : `Validate ${bulkFiles.length} Image${bulkFiles.length > 1 ? 's' : ''}`}
              </button>
            )}
          </div>

          {/* FIX 2: BulkResults ONLY shown inside bulk mode */}
          {bulkResults && bulkResults.length > 0 && (
            <BulkResults results={bulkResults} />
          )}
        </div>
      )}

      {/* ---- LIVE SCANNER MODE ---- */}
      {mode === 'live' && (
        <div className="live-section">
          <div className="live-feed-wrap">
            <div className="airmail-stripe top-stripe">
              {[...Array(20)].map((_, i) => (
                <div key={i} className={`stripe-block ${i % 2 === 0 ? 'red' : 'blue'}`} />
              ))}
            </div>
            <div className="live-feed-container">
              {!cameraActive ? (
                <div className="live-placeholder" onClick={startCamera}>
                  <div className="drop-icon">
                    <svg width="56" height="56" viewBox="0 0 56 56" fill="none">
                      <rect x="4" y="12" width="48" height="34" rx="4" stroke="#d6d3d1" strokeWidth="2" fill="#fafaf9"/>
                      <circle cx="28" cy="29" r="8" stroke="#d6d3d1" strokeWidth="2" fill="none"/>
                      <circle cx="28" cy="29" r="3" fill="#d6d3d1"/>
                      <path d="M18 12l2-5h16l2 5" stroke="#d6d3d1" strokeWidth="2" fill="none"/>
                      <circle cx="42" cy="18" r="2" fill="#dc2626"/>
                    </svg>
                  </div>
                  <p className="drop-text">Click to start camera</p>
                  <p className="drop-hint">Hold envelopes up to scan them one by one</p>
                </div>
              ) : (
                <div className="live-video-wrap">
                  <video ref={videoRef} autoPlay playsInline muted className="live-video" />
                  <div className="scan-corners">
                    <div className="corner tl"></div>
                    <div className="corner tr"></div>
                    <div className="corner bl"></div>
                    <div className="corner br"></div>
                  </div>
                  {liveProcessing && (
                    <div className="live-overlay processing">
                      <div className="live-spinner"></div>
                      <span>Analyzing...</span>
                    </div>
                  )}
                  {liveOverlay === 'valid' && (
                    <div className="live-overlay result-valid">
                      <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                        <circle cx="32" cy="32" r="30" fill="#22c55e"/>
                        <path d="M20 32l8 8 16-16" stroke="#fff" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    </div>
                  )}
                  {liveOverlay === 'invalid' && (
                    <div className="live-overlay result-invalid">
                      <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                        <circle cx="32" cy="32" r="30" fill="#ef4444"/>
                        <path d="M22 22l20 20M42 22L22 42" stroke="#fff" strokeWidth="4" strokeLinecap="round"/>
                      </svg>
                    </div>
                  )}
                  {liveOverlay === 'error' && (
                    <div className="live-overlay result-error">
                      <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                        <circle cx="32" cy="32" r="30" fill="#f59e0b"/>
                        <path d="M32 20v16M32 42v2" stroke="#fff" strokeWidth="4" strokeLinecap="round"/>
                      </svg>
                    </div>
                  )}
                  {liveCount > 0 && <div className="live-counter">{liveCount} scanned</div>}
                  <div className="rec-indicator">
                    <span className="rec-dot"></span>
                    LIVE
                  </div>
                </div>
              )}
            </div>
            <div className="airmail-stripe bottom-stripe">
              {[...Array(20)].map((_, i) => (
                <div key={i} className={`stripe-block ${i % 2 === 0 ? 'blue' : 'red'}`} />
              ))}
            </div>
          </div>
          <canvas ref={canvasRef} style={{ display: 'none' }} />
          <div className="actions">
            {!cameraActive ? (
              <button className="btn-primary" onClick={startCamera}>
                Start Camera
              </button>
            ) : (
              <>
                <button className="btn-capture" onClick={captureAndValidate} disabled={liveProcessing}>
                  <div className="capture-ring"><div className="capture-dot"></div></div>
                  Capture
                </button>
                <span className="spacebar-hint">or press Spacebar</span>
                <button className="btn-ghost" onClick={stopCamera} style={{ marginLeft: 'auto' }}>Stop Camera</button>
              </>
            )}
          </div>
          {liveProcessing && showSlowOcrHint && (
            <p className="slow-ocr-hint">Reading envelope... this may take a few seconds.</p>
          )}
          {liveResults.length > 0 && <BulkResults results={liveResults} />}
        </div>
      )}

      {mode === 'dashboard' && (
        <Dashboard history={history} onClear={clearHistory} user={user} />
      )}
    </div>
  );
}

export default UploadSection;
