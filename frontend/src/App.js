import React, { useState } from 'react';
import ResumeUpload from './components/ResumeUpload';
import AnalysisResults from './components/AnalysisResults';
import './styles.css';

function App() {
  const [results, setResults] = useState(null);
  const [error, setError]     = useState(null);

  const handleError = (msg) => {
    setError(msg);
    setTimeout(() => setError(null), 5000);
  };

  const handleReset = () => setResults(null);

  return (
    <div className="app-container">
      {/* ── Hero Header ── */}
      <header className="hero-header">
        <h1 className="hero-title">Resume Analyzer</h1>
        <p className="hero-sub">AI-powered · Skills Extraction · Job Match Scoring</p>
        <div className="hero-line" />
      </header>

      {/* ── Error Toast ── */}
      {error && (
        <div
          id="error-toast"
          style={{
            background: 'rgba(255,107,53,0.12)',
            border: '1px solid rgba(255,107,53,0.4)',
            color: '#ff6b35',
            borderRadius: '12px',
            padding: '0.75rem 1.25rem',
            marginBottom: '1.5rem',
            fontSize: '0.9rem',
            maxWidth: '760px',
            width: '100%',
            textAlign: 'center',
            animation: 'fadeUp 0.3s ease-out',
          }}
        >
          ⚠️ {error}
        </div>
      )}

      {/* ── Main Content ── */}
      {!results ? (
        <ResumeUpload
          onError={handleError}
          onAnalysisComplete={setResults}
        />
      ) : (
        <AnalysisResults
          results={results}
          onReset={handleReset}
        />
      )}
    </div>
  );
}

export default App;