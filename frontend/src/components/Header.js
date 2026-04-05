import React from 'react';
import './Header.css';

function Header() {
  return (
    <header className="header">
      <div className="header-inner">
        <div className="header-left">
          <div className="envelope-icon">
            <div className="env-body">
              <div className="env-flap"></div>
            </div>
          </div>
          <div>
            <span className="brand">PINCheck</span>
            <span className="brand-dot">.</span>
          </div>
        </div>
        <div className="header-right">
          <span className="header-badge">INDIA POST</span>
        </div>
      </div>
    </header>
  );
}

export default Header;
