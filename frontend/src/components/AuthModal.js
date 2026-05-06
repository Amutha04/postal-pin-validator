import React, { useState } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import API_BASE_URL from '../apiConfig';
import './AuthModal.css';

function AuthModal({ onClose, onAuth }) {
  const [mode, setMode] = useState('login');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      const payload = mode === 'register'
        ? { name, email, password }
        : { email, password };
      const response = await axios.post(`${API_BASE_URL}/api/auth/${mode}`, payload);
      onAuth(response.data);
      toast.success(mode === 'register' ? 'Account created' : 'Logged in');
    } catch (error) {
      toast.error(error.response?.data?.error || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-backdrop">
      <div className="auth-modal">
        <button className="auth-close" onClick={onClose} aria-label="Close">x</button>
        <h2 className="auth-title">{mode === 'login' ? 'Log in' : 'Create account'}</h2>
        <p className="auth-sub">Save dashboard history securely with your account.</p>

        <form onSubmit={submit} className="auth-form">
          {mode === 'register' && (
            <label>
              Name
              <input value={name} onChange={(e) => setName(e.target.value)} required />
            </label>
          )}
          <label>
            Email
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </label>
          <label>
            Password
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} minLength={6} required />
          </label>
          <button className="auth-submit" type="submit" disabled={loading}>
            {loading ? 'Please wait...' : mode === 'login' ? 'Log in' : 'Create account'}
          </button>
        </form>

        <button className="auth-switch" onClick={() => setMode(mode === 'login' ? 'register' : 'login')}>
          {mode === 'login' ? 'Need an account? Create one' : 'Already have an account? Log in'}
        </button>
      </div>
    </div>
  );
}

export default AuthModal;
