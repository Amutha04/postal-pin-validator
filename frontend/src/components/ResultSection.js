import React from 'react';
import './ResultSection.css';
import { MdCheckCircle, MdCancel, MdLocationOn, MdInfo } from 'react-icons/md';

function ResultSection({ result }) {
  const isValid = result.valid;

  return (
    <div className="result-section">

      {/* ── Status Banner ── */}
      <div className={`status-banner ${isValid ? 'valid' : 'invalid'}`}>
        {isValid
          ? <MdCheckCircle size={32} />
          : <MdCancel size={32} />
        }
        <div>
          <h3>{result.message}</h3>
          <p>PIN Code: <strong>{result.pincode || result.extracted_pin}</strong></p>
        </div>
      </div>

      {/* ── OCR Extracted Text ── */}
      {result.extracted_text && (
        <div className="info-card">
          <h4><MdInfo size={18} /> Extracted Text from Image</h4>
          <pre className="ocr-text">{result.extracted_text}</pre>
        </div>
      )}

      {/* ── Valid PIN Details ── */}
      {isValid && (
        <div className="info-card">
          <h4><MdLocationOn size={18} /> Location Details</h4>
          <div className="details-grid">
            <div className="detail-item">
              <span className="label">District</span>
              <span className="value">{result.district}</span>
            </div>
            <div className="detail-item">
              <span className="label">State</span>
              <span className="value">{result.state}</span>
            </div>
            <div className="detail-item">
              <span className="label">Circle</span>
              <span className="value">{result.circle}</span>
            </div>
            <div className="detail-item">
              <span className="label">Region</span>
              <span className="value">{result.region}</span>
            </div>
            <div className="detail-item">
              <span className="label">Division</span>
              <span className="value">{result.division}</span>
            </div>
            {result.latitude && result.latitude !== 'NA' && (
              <div className="detail-item">
                <span className="label">Coordinates</span>
                <span className="value">
                  {result.latitude}, {result.longitude}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Post Offices ── */}
      {isValid && result.post_offices && result.post_offices.length > 0 && (
        <div className="info-card">
          <h4>📮 Post Offices in this PIN</h4>
          <div className="post-offices-list">
            {result.post_offices.map((office, index) => (
              <div key={index} className="post-office-item">
                <span className="office-name">
                  {office.officename}
                </span>
                <span className={`office-type ${
                  office.delivery === 'Delivery' ? 'delivery' : 'non-delivery'
                }`}>
                  {office.delivery}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Invalid PIN — Suggestion ── */}
      {!isValid && result.suggestion && (
        <div className="info-card suggestion-card">
          <h4>💡 Suggested Correct PIN</h4>
          <div className="suggestion-content">
            <div className="suggested-pin">
              {result.suggestion.suggested_pin}
            </div>
            <div className="suggestion-details">
              <p>District: <strong>{result.suggestion.district}</strong></p>
              <p>State: <strong>{result.suggestion.state}</strong></p>
              {result.suggestion.circle && (
                <p>Circle: <strong>{result.suggestion.circle}</strong></p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── ML Validation ── */}
      {result.ml_validation && result.ml_validation.ml_valid !== null && (
        <div className="info-card ml-card">
          <h4>🤖 ML Model Validation</h4>
          <p>{result.ml_validation.message}</p>
          {result.ml_validation.hint && (
            <p className="hint">{result.ml_validation.hint}</p>
          )}
        </div>
      )}

      {/* ── Actual Location for Invalid PIN ── */}
      {!isValid && result.actual_location && (
        <div className="info-card">
          <h4>📍 PIN {result.pincode} actually belongs to</h4>
          <div className="details-grid">
            <div className="detail-item">
              <span className="label">District</span>
              <span className="value">{result.actual_location.district}</span>
            </div>
            <div className="detail-item">
              <span className="label">State</span>
              <span className="value">{result.actual_location.state}</span>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

export default ResultSection;