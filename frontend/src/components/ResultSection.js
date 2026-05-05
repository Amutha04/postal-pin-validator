import React, { useState, useEffect } from 'react';
import './ResultSection.css';
import { toast } from 'react-toastify';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import axios from 'axios';
import 'leaflet/dist/leaflet.css';

function ResultSection({ result }) {
  const isValid = result.valid;
  const [showOcr, setShowOcr] = useState(false);
  const [nearbyPins, setNearbyPins] = useState([]);
  const recipient = result.gemini_data?.recipient;

  const hasCoords = result.latitude && result.longitude &&
    result.latitude !== 'NA' && result.longitude !== 'NA' &&
    !isNaN(parseFloat(result.latitude)) && !isNaN(parseFloat(result.longitude));

  // Fetch nearby PINs when we have coordinates
  useEffect(() => {
    if (hasCoords) {
      axios.post('http://127.0.0.1:5000/api/nearby', {
        lat: parseFloat(result.latitude),
        lng: parseFloat(result.longitude),
        exclude: result.pincode,
      }).then(res => setNearbyPins(res.data))
        .catch(() => setNearbyPins([]));
    }
  }, [hasCoords, result.latitude, result.longitude, result.pincode]);

  // Custom red marker for main PIN
  const mainIcon = hasCoords ? new L.DivIcon({
    className: 'map-pin-icon',
    html: `<svg width="28" height="40" viewBox="0 0 28 40" fill="none">
      <path d="M14 0C6.3 0 0 6.3 0 14c0 10.5 14 26 14 26s14-15.5 14-26C28 6.3 21.7 0 14 0z" fill="#dc2626"/>
      <circle cx="14" cy="14" r="6" fill="#fff"/>
    </svg>`,
    iconSize: [28, 40],
    iconAnchor: [14, 40],
    popupAnchor: [0, -40],
  }) : null;

  // Smaller gray marker for nearby PINs
  const nearbyIcon = new L.DivIcon({
    className: 'map-pin-icon',
    html: `<svg width="20" height="28" viewBox="0 0 20 28" fill="none">
      <path d="M10 0C4.5 0 0 4.5 0 10c0 7.5 10 18 10 18s10-10.5 10-18C20 4.5 15.5 0 10 0z" fill="#6b7280"/>
      <circle cx="10" cy="10" r="4" fill="#fff"/>
    </svg>`,
    iconSize: [20, 28],
    iconAnchor: [10, 28],
    popupAnchor: [0, -28],
  });

  const copyToClipboard = (text, label) => {
    navigator.clipboard.writeText(text).then(() => {
      toast.success(`${label} copied`);
    });
  };

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
            <button
              className="copy-btn"
              onClick={() => copyToClipboard(result.pincode || result.extracted_pin, 'PIN')}
              title="Copy PIN"
            >
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                <rect x="5" y="5" width="9" height="9" rx="1.5" stroke="currentColor" strokeWidth="1.5" fill="none"/>
                <path d="M11 5V3.5A1.5 1.5 0 009.5 2h-6A1.5 1.5 0 002 3.5v6A1.5 1.5 0 003.5 11H5" stroke="currentColor" strokeWidth="1.5" fill="none"/>
              </svg>
            </button>
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
                <span className="detail-val mono">
                  {recipient.pincode}
                  <button className="copy-btn-inline" onClick={() => copyToClipboard(recipient.pincode, 'PIN')} title="Copy PIN">
                    <svg width="12" height="12" viewBox="0 0 16 16" fill="none">
                      <rect x="5" y="5" width="9" height="9" rx="1.5" stroke="currentColor" strokeWidth="1.5" fill="none"/>
                      <path d="M11 5V3.5A1.5 1.5 0 009.5 2h-6A1.5 1.5 0 002 3.5v6A1.5 1.5 0 003.5 11H5" stroke="currentColor" strokeWidth="1.5" fill="none"/>
                    </svg>
                  </button>
                </span>
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

      {/* ---- Map View ---- */}
      {isValid && hasCoords && (
        <div className="card card-map">
          <div className="card-header">
            <div className="card-icon">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M8 1C5.2 1 3 3.2 3 6c0 4 5 9 5 9s5-5 5-9c0-2.8-2.2-5-5-5z" stroke="currentColor" strokeWidth="1.5" fill="none"/>
                <circle cx="8" cy="6" r="2" stroke="currentColor" strokeWidth="1.5" fill="none"/>
              </svg>
            </div>
            <h3 className="card-label">Location</h3>
            {nearbyPins.length > 0 && (
              <span className="pill">{nearbyPins.length} nearby</span>
            )}
            <a
              href={`https://www.google.com/maps/search/post+office/@${result.latitude},${result.longitude},14z`}
              target="_blank"
              rel="noopener noreferrer"
              className="map-link"
            >
              Open in Google Maps
              <svg width="12" height="12" viewBox="0 0 16 16" fill="none">
                <path d="M6 3h7v7M13 3L6 10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </a>
          </div>
          <div className="map-container">
            <MapContainer
              center={[parseFloat(result.latitude), parseFloat(result.longitude)]}
              zoom={13}
              scrollWheelZoom={false}
              style={{ height: '100%', width: '100%', borderRadius: '8px' }}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              {/* Main PIN marker */}
              <Marker
                position={[parseFloat(result.latitude), parseFloat(result.longitude)]}
                icon={mainIcon}
              >
                <Popup>
                  <strong>{result.pincode}</strong> (searched)<br/>
                  {result.district}, {result.state}
                </Popup>
              </Marker>
              {/* Nearby PIN markers */}
              {nearbyPins.map((np, i) => (
                <Marker
                  key={i}
                  position={[np.latitude, np.longitude]}
                  icon={nearbyIcon}
                >
                  <Popup>
                    <strong>{np.pincode}</strong><br/>
                    {np.officename}<br/>
                    {np.district}
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
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
              <span className="suggestion-pin">
                {result.suggestion.suggested_pin}
                <button className="copy-btn-inline" onClick={() => copyToClipboard(result.suggestion.suggested_pin, 'Suggested PIN')} title="Copy PIN">
                  <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                    <rect x="5" y="5" width="9" height="9" rx="1.5" stroke="currentColor" strokeWidth="1.5" fill="none"/>
                    <path d="M11 5V3.5A1.5 1.5 0 009.5 2h-6A1.5 1.5 0 002 3.5v6A1.5 1.5 0 003.5 11H5" stroke="currentColor" strokeWidth="1.5" fill="none"/>
                  </svg>
                </button>
              </span>
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
    </div>
  );
}

export default ResultSection;
