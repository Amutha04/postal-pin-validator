import React, { useEffect, useState } from 'react';
import './App.css';
import axios from 'axios';
import AuthModal from './components/AuthModal';
import Header from './components/Header';
import UploadSection from './components/UploadSection';
import API_BASE_URL from './apiConfig';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const AUTH_STORAGE_KEY = 'pincheck_auth';
const HISTORY_STORAGE_KEY = 'pincheck_validation_history';

function App() {
  const [auth, setAuth] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(AUTH_STORAGE_KEY)) || null;
    } catch (error) {
      return null;
    }
  });
  const [showAuth, setShowAuth] = useState(false);

  useEffect(() => {
    if (!auth?.token) return;

    axios.get(`${API_BASE_URL}/api/auth/me`, {
      headers: { Authorization: `Bearer ${auth.token}` },
    }).then((response) => {
      setAuth(prev => ({ ...prev, user: response.data.user }));
    }).catch(() => {
      localStorage.removeItem(AUTH_STORAGE_KEY);
      localStorage.removeItem(HISTORY_STORAGE_KEY);
      setAuth(null);
    });
  }, [auth?.token]);

  const handleAuth = (data) => {
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(data));
    setAuth(data);
    setShowAuth(false);
  };

  const logout = () => {
    localStorage.removeItem(AUTH_STORAGE_KEY);
    localStorage.removeItem(HISTORY_STORAGE_KEY);
    setAuth(null);
  };

  return (
    <div className="app">
      <Header user={auth?.user} onLogin={() => setShowAuth(true)} onLogout={logout} />
      <main className="main-content">
        <UploadSection key={auth?.user?.id || 'guest'} authToken={auth?.token} user={auth?.user} />
      </main>
      {showAuth && <AuthModal onClose={() => setShowAuth(false)} onAuth={handleAuth} />}
      <ToastContainer position="top-right" autoClose={3000} />
    </div>
  );
}

export default App;
