import React, { useCallback, useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';

const LOADING_STEPS = [
  'Reading PDF document…',
  'Extracting text content…',
  'Identifying skills…',
  'Parsing education & experience…',
  'Matching job description…',
  'Calculating score…',
];

const ResumeUpload = ({ onAnalysisComplete, onError }) => {
  const [file, setFile]               = useState(null);
  const [jobDesc, setJobDesc]         = useState('');
  const [loading, setLoading]         = useState(false);
  const [stepIndex, setStepIndex]     = useState(0);
  const [progress, setProgress]       = useState(0);
  const [dragOver, setDragOver]       = useState(false);

  /* ── animate loading steps ───────────────────────────── */
  useEffect(() => {
    if (!loading) { setStepIndex(0); setProgress(0); return; }
    const total = LOADING_STEPS.length;
    let idx = 0;
    const iv = setInterval(() => {
      idx++;
      setStepIndex(idx);
      setProgress(Math.round((idx / total) * 100));
      if (idx >= total) clearInterval(iv);
    }, 700);
    return () => clearInterval(iv);
  }, [loading]);

  /* ── file drop ───────────────────────────────────────── */
  const onDrop = useCallback((accepted) => {
    const f = accepted[0];
    if (!f) return;
    if (!f.name.endsWith('.pdf')) { onError('Please upload a PDF file'); return; }
    if (f.size > 2 * 1024 * 1024) { onError('File size must be under 2 MB'); return; }
    setFile(f);
  }, [onError]);

  const { getRootProps, getInputProps } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    multiple: false,
    onDragEnter: () => setDragOver(true),
    onDragLeave: () => setDragOver(false),
    onDropAccepted: () => setDragOver(false),
  });

  /* ── submit ──────────────────────────────────────────── */
  const handleAnalyze = async () => {
    if (!file) { onError('Please select a PDF resume first'); return; }
    const formData = new FormData();
    formData.append('file', file);
    if (jobDesc.trim()) formData.append('job_description', jobDesc.trim());
    try {
      setLoading(true);
      const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const res = await axios.post(`${API_URL}/api/analyze`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      onAnalysisComplete(res.data);
    } catch (err) {
      onError(err.response?.data?.detail || 'Error analyzing resume');
    } finally {
      setLoading(false);
    }
  };

  /* ── loading view ────────────────────────────────────── */
  if (loading) {
    return (
      <div className="loading-overlay">
        {/* Scanner animation */}
        <div className="scanner-wrapper">
          <div className="orbit-ring orbit-ring-1" />
          <div className="orbit-ring orbit-ring-2" />
          <div className="scanner-doc">
            <div className="scanner-lines">
              {[...Array(6)].map((_, i) => <div key={i} className="scanner-line" />)}
            </div>
          </div>
        </div>

        <div className="loading-title">⚡ Analyzing Resume…</div>

        {/* Step list */}
        <div className="loading-steps">
          {LOADING_STEPS.map((step, i) => {
            const status = i < stepIndex ? 'done' : i === stepIndex ? 'active' : '';
            return (
              <div key={i} className={`loading-step ${status}`}>
                <div className="step-dot" />
                <span>{status === 'done' ? '✓ ' : ''}{step}</span>
              </div>
            );
          })}
        </div>

        {/* Progress bar */}
        <div className="load-bar-wrap">
          <div className="load-bar-fill" style={{ width: `${progress}%` }} />
        </div>
      </div>
    );
  }

  /* ── upload form ─────────────────────────────────────── */
  return (
    <div className="upload-section">
      <div className="glass-card" style={{ padding: '2rem' }}>

        {/* Drop Zone */}
        <div
          {...getRootProps()}
          className={`drop-zone ${dragOver ? 'drag-over' : ''}`}
        >
          <input {...getInputProps()} />
          <span className="drop-zone-icon">📄</span>
          <div className="drop-zone-title">
            {file ? 'Click or drop to replace' : 'Drag & Drop your Resume here'}
          </div>
          <div className="drop-zone-sub">
            or <span>click to browse</span> &nbsp;·&nbsp; PDF only &nbsp;·&nbsp; max 2 MB
          </div>
        </div>

        {/* Selected file badge */}
        {file && (
          <div className="file-selected">
            <span className="file-icon">📎</span>
            <div>
              <div className="file-name">{file.name}</div>
              <div className="file-size">{(file.size / 1024).toFixed(1)} KB</div>
            </div>
          </div>
        )}

        {/* Job Description */}
        <div className="jd-section">
          <div className="jd-label">
            <span>🎯</span>
            <span>Job Description</span>
            <span style={{ color: '#3a4a6b', fontWeight: 400, textTransform: 'none', letterSpacing: 0 }}>
              — paste the JD to get a skill match score
            </span>
          </div>
          <textarea
            className="jd-textarea"
            placeholder={`Paste the full job description here…\n\nExample:\n  "We are looking for a Python developer with experience in FastAPI, Docker, and AWS. Must be familiar with REST APIs and CI/CD pipelines…"`}
            value={jobDesc}
            onChange={e => setJobDesc(e.target.value)}
          />
        </div>

        {/* Analyze Button */}
        <button
          id="analyze-resume-btn"
          className="analyze-btn"
          onClick={handleAnalyze}
          disabled={!file}
        >
          <span>
            {file ? '⚡ Analyze My Resume' : 'Upload a PDF to Continue'}
          </span>
        </button>
      </div>
    </div>
  );
};

export default ResumeUpload;