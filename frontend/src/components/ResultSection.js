import React, { useState } from 'react';
import './ResultSection.css';

function ResultSection({ result }) {
  const isValid = result.valid;
  const [showOcr, setShowOcr] = useState(false);
  const recipient = result.gemini_data?.recipient;

  return (
    <div className="results">

      {/* ---- Postmark Status ---- */}
      <div className={`postmark-card ${isValid ? 'valid' : 'invalid'}`}>
        <div className="postmark-left">
          {/* Circular postmark stamp */}
          <div className={`stamp ${isValid ? 'stamp-valid' : 'stamp-invalid'}`}>
            <div className="stamp-ring">
              <span className="stamp-text">{isValid ? 'VERIFIED' : 'MISMATCH'}</span>
              <span className="stamp-pin">{result.pincode || result.extracted_pin}</span>
            </div>
          </div>
        </div>
        <div className="postmark-right">
          <h2 className="postmark-title">
            {isValid ? 'PIN Code Valid' : 'PIN Code Mismatch'}
          </h2>
          <p className="postmark-msg">{result.message}</p>
        </div>
      </div>

      {/* ---- Recipient Details ---- */}
      {recipient && (
        <div className="card">
          <div className="card-header">
            <div className="card-icon">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <circle cx="8" cy="5" r="3" stroke="currentColor" strokeWidth="1.5" fill="none"/>
                <path d="M2 14c0-3.3 2.7-6 6-6s6 2.7 6 6" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round"/>
              </svg>
            </div>
            <h3 className="card-label">Recipient Details</h3>
          </div>
          <div className="detail-rows">
            {recipient.name && (
              <div className="detail-row">
                <span className="detail-key">Name</span>
                <span className="detail-val">{recipient.name}</span>
              </div>
            )}
            {recipient.address && (
              <div className="detail-row">
                <span className="detail-key">Address</span>
                <span className="detail-val">{recipient.address}</span>
              </div>
            )}
            {recipient.city && (
              <div className="detail-row">
                <span className="detail-key">City</span>
                <span className="detail-val">{recipient.city}</span>
              </div>
            )}
            {recipient.district && (
              <div className="detail-row">
                <span className="detail-key">District</span>
                <span className="detail-val">{recipient.district}</span>
              </div>
            )}
            {recipient.state && (
              <div className="detail-row">
                <span className="detail-key">State</span>
                <span className="detail-val">{recipient.state}</span>
              </div>
            )}
            {recipient.pincode && (
              <div className="detail-row">
                <span className="detail-key">PIN Code</span>
                <span className="detail-val mono">{recipient.pincode}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ---- Postal Info Grid ---- */}
      {isValid && (
        <div className="card">
          <div className="card-header">
            <div className="card-icon">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M8 1L8 9M8 9L5 6M8 9L11 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M2 11v2a2 2 0 002 2h8a2 2 0 002-2v-2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
            </div>
            <h3 className="card-label">Postal Information</h3>
          </div>
          <div className="info-grid">
            {[
              ['District', result.district],
              ['State', result.state],
              ['Circle', result.circle],
              ['Region', result.region],
              ['Division', result.division],
              result.latitude && result.latitude !== 'NA'
                ? ['Coordinates', `${result.latitude}, ${result.longitude}`]
                : null,
            ].filter(Boolean).map(([label, value], i) => (
              <div key={i} className="info-cell">
                <span className="cell-label">{label}</span>
                <span className="cell-value">{value}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ---- Post Offices ---- */}
      {isValid && result.post_offices?.length > 0 && (
        <div className="card">
          <div className="card-header">
            <div className="card-icon">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <rect x="2" y="3" width="12" height="10" rx="2" stroke="currentColor" strokeWidth="1.5" fill="none"/>
                <path d="M2 6h12" stroke="currentColor" strokeWidth="1.5"/>
              </svg>
            </div>
            <h3 className="card-label">Post Offices</h3>
            <span className="pill">{result.post_offices.length}</span>
          </div>
          <div className="office-list">
            {result.post_offices.map((o, i) => (
              <div key={i} className="office-item">
                <span className="office-name">{o.officename}</span>
                <span className={`badge ${o.delivery === 'Delivery' ? 'badge-green' : 'badge-gray'}`}>
                  {o.delivery}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ---- Suggestion (invalid) ---- */}
      {!isValid && result.suggestion && (
        <div className="card card-suggestion">
          <div className="card-header">
            <div className="card-icon suggestion-icon">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <circle cx="8" cy="8" r="6.5" stroke="currentColor" strokeWidth="1.5" fill="none"/>
                <path d="M8 5v3M8 10v1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
            </div>
            <h3 className="card-label">Suggested Correction</h3>
          </div>
          <div className="suggestion-body">
            <div className="suggestion-pin-wrap">
              <span className="suggestion-label">Correct PIN</span>
              <span className="suggestion-pin">{result.suggestion.suggested_pin}</span>
            </div>
            <div className="suggestion-details">
              {result.suggestion.district && (
                <div className="detail-row compact">
                  <span className="detail-key">District</span>
                  <span className="detail-val">{result.suggestion.district}</span>
                </div>
              )}
              {result.suggestion.state && (
                <div className="detail-row compact">
                  <span className="detail-key">State</span>
                  <span className="detail-val">{result.suggestion.state}</span>
                </div>
              )}
              {result.suggestion.circle && (
                <div className="detail-row compact">
                  <span className="detail-key">Circle</span>
                  <span className="detail-val">{result.suggestion.circle}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ---- Actual location (invalid) ---- */}
      {!isValid && result.actual_location && (
        <div className="card">
          <div className="card-header">
            <div className="card-icon">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M8 1C5.2 1 3 3.2 3 6c0 4 5 9 5 9s5-5 5-9c0-2.8-2.2-5-5-5z" stroke="currentColor" strokeWidth="1.5" fill="none"/>
                <circle cx="8" cy="6" r="2" stroke="currentColor" strokeWidth="1.5" fill="none"/>
              </svg>
            </div>
            <h3 className="card-label">PIN {result.pincode} Actually Belongs To</h3>
          </div>
          <div className="info-grid">
            <div className="info-cell">
              <span className="cell-label">District</span>
              <span className="cell-value">{result.actual_location.district}</span>
            </div>
            <div className="info-cell">
              <span className="cell-label">State</span>
              <span className="cell-value">{result.actual_location.state}</span>
            </div>
          </div>
        </div>
      )}

      {/* ---- ML Validation ---- */}
      {result.ml_validation?.ml_valid !== null && result.ml_validation?.ml_valid !== undefined && (
        <div className="card">
          <div className="card-header">
            <div className="card-icon">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <rect x="1" y="8" width="3" height="6" rx="1" stroke="currentColor" strokeWidth="1.5" fill="none"/>
                <rect x="6.5" y="4" width="3" height="10" rx="1" stroke="currentColor" strokeWidth="1.5" fill="none"/>
                <rect x="12" y="1" width="3" height="13" rx="1" stroke="currentColor" strokeWidth="1.5" fill="none"/>
              </svg>
            </div>
            <h3 className="card-label">ML Validation</h3>
            <span className={`badge ${result.ml_validation.ml_valid ? 'badge-green' : 'badge-red'}`}>
              {result.ml_validation.ml_valid ? 'PASS' : 'FAIL'}
            </span>
          </div>
          <p className="ml-text">{result.ml_validation.message}</p>
          {result.ml_validation.hint && <p className="ml-hint">{result.ml_validation.hint}</p>}
        </div>
      )}

      {/* ---- OCR Text (collapsible) ---- */}
      {result.extracted_text && (
        <div className="card">
          <div className="card-header clickable" onClick={() => setShowOcr(!showOcr)}>
            <div className="card-icon">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <rect x="2" y="2" width="12" height="12" rx="2" stroke="currentColor" strokeWidth="1.5" fill="none"/>
                <path d="M5 6h6M5 8.5h4M5 11h5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
            </div>
            <h3 className="card-label">Extracted Text</h3>
            <svg
              width="16" height="16" viewBox="0 0 16 16" fill="none"
              className={`chevron ${showOcr ? 'open' : ''}`}
            >
              <path d="M4 6l4 4 4-4" stroke="#a8a29e" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          {showOcr && (
            <pre className="ocr-text">{result.extracted_text}</pre>
          )}
        </div>
      )}
    </div>
  );
}

export default ResultSection;
