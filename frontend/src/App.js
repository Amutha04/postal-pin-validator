import React from 'react';
import './App.css';
import Header from './components/Header';
import UploadSection from './components/UploadSection';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

function App() {
  return (
    <div className="app">
      <Header />
      <main className="main-content">
        <UploadSection />
      </main>
      <ToastContainer position="top-right" autoClose={3000} />
    </div>
  );
}

export default App;
