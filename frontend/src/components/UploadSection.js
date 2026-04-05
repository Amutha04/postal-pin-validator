import React, { useState, useRef } from 'react';
import './UploadSection.css';
import axios from 'axios';
import { toast } from 'react-toastify';

function UploadSection({ setResult, setLoading, loading }) {
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const handleFile = (file) => {
    if (file && file.type.startsWith('image/')) {
      setImage(file);
      setPreview(URL.createObjectURL(file));
      setResult(null);
    }
  };

  const handleSubmit = async () => {
    if (!image) return;
    const formData = new FormData();
    formData.append('image', image);
    try {
      setLoading(true);
      const response = await axios.post(
        'http://127.0.0.1:5000/api/validate',
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      setResult(response.data);
      toast.success('Validation complete');
    } catch (error) {
      const msg = error.response?.data?.error || 'Something went wrong';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setImage(null);
    setPreview(null);
    setResult(null);
    fileInputRef.current.value = '';
  };

  return (
    <div className="upload-section">
      {/* Title area */}
      <div className="hero-text">
        <h1 className="hero-title">
          Validate your <span className="highlight">PIN Code</span>
        </h1>
        <p className="hero-sub">
          Upload an envelope photo and we'll extract & verify the postal code against 157,000+ Indian postal records.
        </p>
      </div>

      {/* Envelope upload zone */}
      <div
        className={`envelope ${dragActive ? 'drag-over' : ''} ${preview ? 'has-preview' : ''}`}
        onClick={() => !preview && fileInputRef.current.click()}
        onDrop={(e) => { e.preventDefault(); setDragActive(false); handleFile(e.dataTransfer.files[0]); }}
        onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
        onDragLeave={() => setDragActive(false)}
      >
        {/* Airmail stripe top */}
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
              {/* Envelope SVG illustration */}
              <div className="drop-icon">
                <svg width="56" height="56" viewBox="0 0 56 56" fill="none">
                  <rect x="4" y="14" width="48" height="32" rx="3" stroke="#d6d3d1" strokeWidth="2" fill="#fafaf9"/>
                  <path d="M4 17L28 34L52 17" stroke="#d6d3d1" strokeWidth="2" fill="none"/>
                  <rect x="32" y="6" width="14" height="14" rx="2" fill="#fef2f2" stroke="#fca5a5" strokeWidth="1.5"/>
                  <path d="M36 10L39 15L42 10" stroke="#dc2626" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
                </svg>
              </div>
              <p className="drop-text">Drop your envelope image here</p>
              <p className="drop-hint">or click to browse &mdash; JPG, PNG supported</p>
            </div>
          )}
        </div>

        {/* Airmail stripe bottom */}
        <div className="airmail-stripe bottom-stripe">
          {[...Array(20)].map((_, i) => (
            <div key={i} className={`stripe-block ${i % 2 === 0 ? 'blue' : 'red'}`} />
          ))}
        </div>
      </div>

      <input
        type="file"
        accept="image/*"
        ref={fileInputRef}
        onChange={(e) => handleFile(e.target.files[0])}
        style={{ display: 'none' }}
      />

      {/* Action buttons */}
      <div className="actions">
        <button className="btn-ghost" onClick={() => fileInputRef.current.click()}>
          {preview ? 'Change Image' : 'Browse Files'}
        </button>
        {preview && (
          <button className="btn-primary" onClick={handleSubmit} disabled={loading}>
            {loading ? (
              <span className="btn-loading">
                <span className="spinner"></span>
                Analyzing...
              </span>
            ) : (
              'Validate PIN'
            )}
          </button>
        )}
      </div>
    </div>
  );
}

export default UploadSection;
