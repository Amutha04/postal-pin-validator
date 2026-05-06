import React, { useState, useEffect } from 'react';
import './ResultSection.css';
import { toast } from 'react-toastify';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import axios from 'axios';
import 'leaflet/dist/leaflet.css';
import API_BASE_URL from '../apiConfig';

function ResultSection({ result }) {
  const isValid = result.valid;
  const [nearbyPins, setNearbyPins] = useState([]);
  const recipient = result.groq_data?.recipient;
  const suggestion = result.suggestion;
  const displayPin = result.pincode || result.extracted_pin;

  const postalData = isValid ? result : suggestion;
  const postalPin = isValid ? displayPin : suggestion?.suggested_pin;
  const postalOffices = isValid ? result.post_offices : suggestion?.post_offices;

  const hasCoords = postalData?.latitude && postalData?.longitude &&
    postalData.latitude !== 'NA' && postalData.longitude !== 'NA' &&
    !isNaN(parseFloat(postalData.latitude)) &&
    !isNaN(parseFloat(postalData.longitude));

  useEffect(() => {
    if (!hasCoords) {
      setNearbyPins([]);
      return;
    }

    axios.post(`${API_BASE_URL}/api/nearby`, {
      lat: parseFloat(postalData.latitude),
      lng: parseFloat(postalData.longitude),
      exclude: postalPin,
    }).then(res => setNearbyPins(res.data))
      .catch(() => setNearbyPins([]));
  }, [hasCoords, postalData?.latitude, postalData?.longitude, postalPin]);

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
    navigator.clipboard.writeText(text).then(() => toast.success(`${label} copied`));
  };

  return (
    <div className="results">
      <div className={`status-banner ${isValid ? 'status-valid' : 'status-invalid'}`}>
        <div className="status-icon-wrap">
          {isValid ? (
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path d="M5 12l5 5 9-9" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          ) : (
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path d="M6 6l12 12M6 18L18 6" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"/>
            </svg>
          )}
        </div>
        <div className="status-content">
          <div className="status-top">
            <span className={`status-badge ${isValid ? 'badge-valid' : 'badge-invalid'}`}>
              {isValid ? 'VERIFIED' : 'MISMATCH'}
            </span>
            <span className="status-pin">
              {displayPin}
              <button className="copy-btn-inline" onClick={() => copyToClipboard(displayPin, 'PIN')} title="Copy PIN">
                <svg width="12" height="12" viewBox="0 0 16 16" fill="none">
                  <rect x="5" y="5" width="9" height="9" rx="1.5" stroke="currentColor" strokeWidth="1.5" fill="none"/>
                  <path d="M11 5V3.5A1.5 1.5 0 009.5 2h-6A1.5 1.5 0 002 3.5v6A1.5 1.5 0 003.5 11H5" stroke="currentColor" strokeWidth="1.5" fill="none"/>
                </svg>
              </button>
            </span>
          </div>
          <p className="status-message">{result.message}</p>
        </div>
      </div>

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
            {recipient.name && <div className="detail-row"><span className="detail-key">Name</span><span className="detail-val">{recipient.name}</span></div>}
            {recipient.address && <div className="detail-row"><span className="detail-key">Address</span><span className="detail-val">{recipient.address}</span></div>}
            {recipient.city && <div className="detail-row"><span className="detail-key">City</span><span className="detail-val">{recipient.city}</span></div>}
            {recipient.district && <div className="detail-row"><span className="detail-key">District</span><span className="detail-val">{recipient.district}</span></div>}
            {recipient.state && <div className="detail-row"><span className="detail-key">State</span><span className="detail-val">{recipient.state}</span></div>}
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

      {!isValid && suggestion && (
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
                {suggestion.suggested_pin}
                <button className="copy-btn-inline" onClick={() => copyToClipboard(suggestion.suggested_pin, 'Suggested PIN')} title="Copy PIN">
                  <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                    <rect x="5" y="5" width="9" height="9" rx="1.5" stroke="currentColor" strokeWidth="1.5" fill="none"/>
                    <path d="M11 5V3.5A1.5 1.5 0 009.5 2h-6A1.5 1.5 0 002 3.5v6A1.5 1.5 0 003.5 11H5" stroke="currentColor" strokeWidth="1.5" fill="none"/>
                  </svg>
                </button>
              </span>
            </div>
            <div className="suggestion-details">
              {suggestion.district && <div className="detail-row compact"><span className="detail-key">District</span><span className="detail-val">{suggestion.district}</span></div>}
              {suggestion.state && <div className="detail-row compact"><span className="detail-key">State</span><span className="detail-val">{suggestion.state}</span></div>}
              {suggestion.circle && <div className="detail-row compact"><span className="detail-key">Circle</span><span className="detail-val">{suggestion.circle}</span></div>}
            </div>
          </div>
        </div>
      )}

      {postalData && (
        <div className="card">
          <div className="card-header">
            <div className="card-icon">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <rect x="2" y="2" width="12" height="12" rx="2" stroke="currentColor" strokeWidth="1.5" fill="none"/>
                <path d="M2 6h12" stroke="currentColor" strokeWidth="1.5"/>
                <path d="M6 2v12" stroke="currentColor" strokeWidth="1.5"/>
              </svg>
            </div>
            <h3 className="card-label">{isValid ? 'Postal Information' : 'Suggested Postal Information'}</h3>
          </div>
          <div className="info-grid">
            {[
              ['District', postalData.district],
              ['State', postalData.state],
              ['Circle', postalData.circle],
              ['Region', postalData.region],
              ['Division', postalData.division],
              hasCoords ? ['Coordinates', `${postalData.latitude}, ${postalData.longitude}`] : null,
            ].filter(Boolean).map(([label, value], i) => (
              <div key={i} className="info-cell">
                <span className="cell-label">{label}</span>
                <span className="cell-value">{value}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {postalData && hasCoords && (
        <div className="card card-map">
          <div className="card-header">
            <div className="card-icon">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M8 1C5.2 1 3 3.2 3 6c0 4 5 9 5 9s5-5 5-9c0-2.8-2.2-5-5-5z" stroke="currentColor" strokeWidth="1.5" fill="none"/>
                <circle cx="8" cy="6" r="2" stroke="currentColor" strokeWidth="1.5" fill="none"/>
              </svg>
            </div>
            <h3 className="card-label">{isValid ? 'Location' : 'Suggested Location'}</h3>
            {nearbyPins.length > 0 && <span className="pill">{nearbyPins.length} nearby</span>}
            <a href={`https://www.google.com/maps/search/post+office/@${postalData.latitude},${postalData.longitude},14z`}
              target="_blank" rel="noopener noreferrer" className="map-link">
              Open in Google Maps
              <svg width="12" height="12" viewBox="0 0 16 16" fill="none">
                <path d="M6 3h7v7M13 3L6 10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </a>
          </div>
          <div className="map-container">
            <MapContainer
              center={[parseFloat(postalData.latitude), parseFloat(postalData.longitude)]}
              zoom={13} scrollWheelZoom={false}
              style={{ height: '100%', width: '100%' }}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <Marker position={[parseFloat(postalData.latitude), parseFloat(postalData.longitude)]} icon={mainIcon}>
                <Popup><strong>{postalPin}</strong><br/>{postalData.district}, {postalData.state}</Popup>
              </Marker>
              {nearbyPins.map((np, i) => (
                <Marker key={i} position={[np.latitude, np.longitude]} icon={nearbyIcon}>
                  <Popup><strong>{np.pincode}</strong><br/>{np.officename}<br/>{np.district}</Popup>
                </Marker>
              ))}
            </MapContainer>
          </div>
        </div>
      )}

      {postalOffices?.length > 0 && (
        <div className="card">
          <div className="card-header">
            <div className="card-icon">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <rect x="2" y="3" width="12" height="10" rx="2" stroke="currentColor" strokeWidth="1.5" fill="none"/>
                <path d="M2 6h12" stroke="currentColor" strokeWidth="1.5"/>
              </svg>
            </div>
            <h3 className="card-label">{isValid ? 'Post Offices' : 'Suggested PIN Post Offices'}</h3>
            <span className="pill">{postalOffices.length}</span>
          </div>
          <div className="office-list">
            {postalOffices.map((o, i) => (
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
    </div>
  );
}

export default ResultSection;
