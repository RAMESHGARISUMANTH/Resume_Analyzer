import React, { useEffect, useState } from 'react';

/* ── helper: animate a number from 0 → target ─────────── */
const useCountUp = (target, duration = 1500) => {
  const [val, setVal] = useState(0);
  useEffect(() => {
    let start = 0;
    const step = target / (duration / 16);
    const iv = setInterval(() => {
      start = Math.min(start + step, target);
      setVal(Math.round(start));
      if (start >= target) clearInterval(iv);
    }, 16);
    return () => clearInterval(iv);
  }, [target, duration]);
  return val;
};

/* ── Score ring colors ─────────────────────────────────── */
const ringColor = (s) => {
  if (s >= 80) return { stroke: '#00ff88', text: '#00ff88' };
  if (s >= 60) return { stroke: '#00d4ff', text: '#00d4ff' };
  if (s >= 40) return { stroke: '#f59e0b', text: '#f59e0b' };
  return { stroke: '#ff6b35', text: '#ff6b35' };
};

const levelLabel = (s) => {
  if (s >= 80) return 'Strong Match 🔥';
  if (s >= 60) return 'Good Match ✅';
  if (s >= 40) return 'Moderate Match ⚡';
  return 'Needs Work 🔧';
};

const resumeMsg = (s) => {
  if (s >= 90) return 'Outstanding resume — you\'re a top candidate!';
  if (s >= 75) return 'Great resume! A few tweaks can make it perfect.';
  if (s >= 60) return 'Solid foundation — keep adding skills.';
  return 'Improve your resume to unlock more opportunities.';
};

/* ── circular SVG ring ─────────────────────────────────── */
const ScoreRing = ({ score, label, message }) => {
  const animated = useCountUp(score);
  const { stroke, text } = ringColor(score);
  const R = 60, C = 2 * Math.PI * R;
  const offset = C - (C * animated) / 100;

  return (
    <div className="score-ring-card glass-card">
      <div className="score-ring-wrapper">
        <svg className="score-ring-svg" viewBox="0 0 160 160">
          <circle className="score-ring-bg" cx="80" cy="80" r={R} />
          <circle
            className="score-ring-fill"
            cx="80" cy="80" r={R}
            stroke={stroke}
            strokeDasharray={C}
            strokeDashoffset={offset}
          />
        </svg>
        <div className="score-ring-label">
          <span className="score-number" style={{ color: text }}>{animated}</span>
          <span className="score-unit">/ 100</span>
        </div>
      </div>
      <div className="score-level" style={{ color: text }}>{label}</div>
      <div className="score-message">{message}</div>
    </div>
  );
};

/* ── skill chip ────────────────────────────────────────── */
const Chip = ({ label, variant }) => (
  <span className={`skill-chip chip-${variant}`}>
    <span className="chip-dot" />
    {label}
  </span>
);

/* ── section card ──────────────────────────────────────── */
const InfoCard = ({ emoji, color, title, items }) => (
  <div className="info-card glass-card">
    <div className="info-card-title" style={{ color }}>
      <span>{emoji}</span>
      <span>{title}</span>
    </div>
    <div className="info-items">
      {items && items.length > 0
        ? items.map((item, i) => (
            <div key={i} className="info-item">
              <span className="info-bullet" style={{ color }}>▸</span>
              <span>{item}</span>
            </div>
          ))
        : <div className="empty-state">No data found</div>
      }
    </div>
  </div>
);

/* ══════════════════════════════════════════════════════════
   MAIN COMPONENT
   ══════════════════════════════════════════════════════════ */
const AnalysisResults = ({ results, onReset }) => {
  const jm = results.job_match;

  /* animated match % */
  const matchAnim = useCountUp(jm ? jm.match_score : 0);

  return (
    <div className="results-page">
      {/* Header */}
      <div className="results-header">
        <div className="results-title">Analysis Complete</div>
        <div className="results-subtitle">
          {jm ? 'Resume · Skills · Job Match · Suggestions' : 'Resume · Skills · Education · Experience'}
        </div>
        <button id="analyze-again-btn" className="reset-btn" onClick={onReset}>
          ↩ Analyze another resume
        </button>
      </div>

      {/* ── Row 1: Resume Score + JD Match Score ── */}
      <div style={{ display: 'grid', gridTemplateColumns: jm ? '1fr 1fr' : '1fr', gap: '1.25rem', marginBottom: '2rem' }}>
        <ScoreRing
          score={results.score || 0}
          label={results.score >= 75 ? 'Strong Resume 🌟' : results.score >= 55 ? 'Good Resume 👍' : 'Fair Resume 📋'}
          message={resumeMsg(results.score)}
        />
        {jm && (
          <ScoreRing
            score={jm.match_score}
            label={levelLabel(jm.match_score)}
            message={`${jm.compatibility_level} with the provided job description`}
          />
        )}
      </div>

      {/* ── JD Match Panel ── */}
      {jm && (
        <div className="match-panel glass-card" style={{ padding: '1.75rem', marginBottom: '1.5rem' }}>
          <div className="panel-title" style={{ color: '#a855f7' }}>
            <span>🎯</span> Job Description Match Breakdown
          </div>

          {/* match bar */}
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#94a3b8' }}>
            <span>Match Score</span>
            <span style={{ color: ringColor(jm.match_score).text, fontWeight: 700 }}>{matchAnim}%</span>
          </div>
          <div className="match-score-bar-wrap">
            <div
              className="match-score-bar"
              style={{
                width: `${jm.match_score}%`,
                background: `linear-gradient(90deg, ${ringColor(jm.match_score).stroke}, #a855f7)`,
              }}
            />
          </div>

          {/* Matched skills */}
          <div style={{ marginTop: '1.25rem' }}>
            <div className="panel-title" style={{ color: '#00ff88', marginBottom: '0.5rem' }}>
              <span>✅</span> Matched Skills ({jm.matching_skills.length})
            </div>
            <div className="skill-chips">
              {jm.matching_skills.length > 0
                ? jm.matching_skills.map((s, i) => <Chip key={i} label={s} variant="match" />)
                : <span style={{ color: '#64748b', fontSize: '0.85rem' }}>No matching skills found</span>
              }
            </div>
          </div>

          {/* Missing skills */}
          <div style={{ marginTop: '1.25rem' }}>
            <div className="panel-title" style={{ color: '#ff6b35', marginBottom: '0.5rem' }}>
              <span>⚠️</span> Missing Skills ({jm.missing_skills.length})
            </div>
            <div className="skill-chips">
              {jm.missing_skills.length > 0
                ? jm.missing_skills.map((s, i) => <Chip key={i} label={s} variant="missing" />)
                : <span style={{ color: '#00ff88', fontSize: '0.85rem' }}>🎉 You have all required skills!</span>
              }
            </div>
          </div>
        </div>
      )}

      <div className="neon-divider" />

      {/* ── All Resume Skills ── */}
      <div className="match-panel glass-card" style={{ padding: '1.75rem', marginBottom: '1.5rem' }}>
        <div className="panel-title" style={{ color: '#00d4ff' }}>
          <span>💡</span> All Detected Skills ({results.skills?.length || 0})
        </div>
        <div className="skill-chips">
          {results.skills && results.skills.length > 0
            ? results.skills.map((s, i) => <Chip key={i} label={s} variant="skill" />)
            : <div className="empty-state">No skills extracted</div>
          }
        </div>
      </div>

      {/* ── Education / Experience / Certifications ── */}
      <div className="info-grid">
        <InfoCard
          emoji="🎓"
          color="#00d4ff"
          title="Education"
          items={results.education}
        />
        <InfoCard
          emoji="💼"
          color="#a855f7"
          title="Experience & Projects"
          items={results.experience}
        />
        <InfoCard
          emoji="🏆"
          color="#f59e0b"
          title="Certifications"
          items={results.certifications}
        />
      </div>

      {/* ── Suggestions ── */}
      {jm && jm.suggestions && jm.suggestions.length > 0 && (
        <>
          <div className="neon-divider" />
          <div className="match-panel glass-card" style={{ padding: '1.75rem' }}>
            <div className="panel-title" style={{ color: '#c084fc', marginBottom: '1rem' }}>
              <span>🚀</span> AI Suggestions to Improve Your Match
            </div>
            <div className="suggestions-list">
              {jm.suggestions.map((s, i) => (
                <div key={i} className="suggestion-item">
                  <div className="suggestion-num">{i + 1}</div>
                  <span>{s}</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {/* ── Recommendations (no JD) ── */}
      {!jm && results.recommendations && results.recommendations.length > 0 && (
        <>
          <div className="neon-divider" />
          <div className="match-panel glass-card" style={{ padding: '1.75rem' }}>
            <div className="panel-title" style={{ color: '#c084fc', marginBottom: '1rem' }}>
              <span>💫</span> Career Recommendations
            </div>
            <div className="suggestions-list">
              {results.recommendations.map((r, i) => (
                <div key={i} className="suggestion-item">
                  <div className="suggestion-num">{i + 1}</div>
                  <span>{r}</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default AnalysisResults;