import React from 'react';
import './Header.css';
import { MdLocalPostOffice } from 'react-icons/md';

function Header() {
  return (
    <header className="header">
      <div className="header-content">
        <div className="header-logo">
          <MdLocalPostOffice size={36} color="white" />
        </div>
        <div className="header-text">
          <h1>Indian Postal PIN Validator</h1>
          <p>Upload envelope image to validate PIN code</p>
        </div>
      </div>
    </header>
  );
}

export default Header;