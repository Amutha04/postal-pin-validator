import React, { useState } from 'react';
import './App.css';
import Header from './components/Header';
import UploadSection from './components/UploadSection';
import ResultSection from './components/ResultSection';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

function App() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  return (
    <div className="app">
      <Header />
      <main className="main-content">
        <UploadSection 
          setResult={setResult} 
          setLoading={setLoading}
          loading={loading}
        />
        {result && <ResultSection result={result} />}
      </main>
      <ToastContainer position="top-right" autoClose={3000} />
    </div>
  );
}

export default App;