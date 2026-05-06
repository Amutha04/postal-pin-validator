import React from 'react';
import './Header.css';

function Header({ user, onLogin, onLogout }) {
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
          {user ? (
            <div className="user-menu">
              <span className="user-name">{user.name}</span>
              <button className="header-action" onClick={onLogout}>Logout</button>
            </div>
          ) : (
            <button className="header-action" onClick={onLogin}>Login</button>
          )}
        </div>
      </div>
    </header>
  );
}

export default Header;
