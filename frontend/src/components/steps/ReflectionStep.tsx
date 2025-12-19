/**
 * ReflectionStep - Step 2: Apply DSRP 4-8-3 analysis
 *
 * Shows AI agents processing content with the 8 moves.
 * Displays extracted concepts and DSRP analyses.
 */

import { useState, useCallback } from 'react'

interface ReflectionStepProps {
  sessionId: string
  text: string
  sourceName: string
  onComplete: (result: any) => void
}

const MOVES = [
  { id: 'is-is-not', name: 'Is/Is Not', pattern: 'D', color: '#1976D2' },
  { id: 'zoom-in', name: 'Zoom In', pattern: 'S', color: '#388E3C' },
  { id: 'zoom-out', name: 'Zoom Out', pattern: 'S', color: '#388E3C' },
  { id: 'part-party', name: 'Part Party', pattern: 'S', color: '#388E3C' },
  { id: 'rds-barbell', name: 'RDS Barbell', pattern: 'R', color: '#F57C00' },
  { id: 'p-circle', name: 'P-Circle', pattern: 'P', color: '#7B1FA2' },
  { id: 'woc', name: 'WoC', pattern: 'R', color: '#F57C00' },
  { id: 'waoc', name: 'WAoC', pattern: 'R', color: '#F57C00' },
]

export function ReflectionStep({ sessionId, text, sourceName, onComplete }: ReflectionStepProps) {
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [currentAgent, setCurrentAgent] = useState('')
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [analysisDepth, setAnalysisDepth] = useState<'quick' | 'standard' | 'deep'>('standard')

  const startAnalysis = useCallback(async () => {
    setIsAnalyzing(true)
    setError(null)
    setProgress(0)

    try {
      // Simulate agent progress
      setCurrentAgent('Summary Agent')
      setProgress(10)

      const response = await fetch('/api/study/steps/reflection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          text: text,
          analysis_depth: analysisDepth,
        }),
      })

      setProgress(50)
      setCurrentAgent('DSRP Agents')

      if (!response.ok) {
        throw new Error('Analysis failed')
      }

      const data = await response.json()
      setProgress(100)
      setCurrentAgent('Complete')
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed')
    } finally {
      setIsAnalyzing(false)
    }
  }, [sessionId, text, analysisDepth])

  const handleComplete = useCallback(() => {
    if (result) {
      onComplete(result)
    }
  }, [result, onComplete])

  return (
    <div className="reflection-step">
      <div className="step-header">
        <div className="step-icon">2</div>
        <div className="step-info">
          <h2>Reflection</h2>
          <p>Apply DSRP 4-8-3 analysis to extract knowledge</p>
        </div>
      </div>

      {!result ? (
        <div className="analysis-config">
          <div className="source-info">
            <span className="label">Source:</span>
            <span className="value">{sourceName}</span>
            <span className="chars">{text.length.toLocaleString()} characters</span>
          </div>

          <div className="depth-selector">
            <h4>Analysis Depth</h4>
            <div className="depth-options">
              {(['quick', 'standard', 'deep'] as const).map((depth) => (
                <button
                  type="button"
                  key={depth}
                  className={`depth-btn ${analysisDepth === depth ? 'selected' : ''}`}
                  onClick={() => setAnalysisDepth(depth)}
                >
                  <span className="depth-name">{depth.charAt(0).toUpperCase() + depth.slice(1)}</span>
                  <span className="depth-desc">
                    {depth === 'quick' && '2 moves per concept'}
                    {depth === 'standard' && '4 moves per concept'}
                    {depth === 'deep' && 'All 8 moves'}
                  </span>
                </button>
              ))}
            </div>
          </div>

          <div className="moves-preview">
            <h4>DSRP Moves</h4>
            <div className="moves-grid">
              {MOVES.map((move) => (
                <div key={move.id} className="move-chip" style={{ borderColor: move.color }}>
                  <span className="pattern" style={{ color: move.color }}>{move.pattern}</span>
                  <span className="name">{move.name}</span>
                </div>
              ))}
            </div>
          </div>

          {isAnalyzing ? (
            <div className="progress-section">
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${progress}%` }} />
              </div>
              <p className="progress-text">
                <span className="agent">{currentAgent}</span> - {progress}%
              </p>
            </div>
          ) : (
            <button type="button" className="start-btn" onClick={startAnalysis}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="5 3 19 12 5 21 5 3" />
              </svg>
              Start Analysis
            </button>
          )}

          {error && <div className="error">{error}</div>}
        </div>
      ) : (
        <div className="analysis-results">
          <div className="result-summary">
            <div className="stat">
              <span className="stat-value">{result.concepts?.length || 0}</span>
              <span className="stat-label">Concepts</span>
            </div>
            <div className="stat">
              <span className="stat-value">{result.dsrp_analyses?.length || 0}</span>
              <span className="stat-label">Analyses</span>
            </div>
          </div>

          {result.summary && (
            <div className="summary-section">
              <h4>Summary</h4>
              <p>{result.summary.executive_summary || 'No summary available'}</p>

              {result.summary.key_themes && (
                <div className="themes">
                  <h5>Key Themes</h5>
                  <div className="theme-chips">
                    {result.summary.key_themes.map((theme: string, i: number) => (
                      <span key={i} className="theme-chip">{theme}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {result.concepts && result.concepts.length > 0 && (
            <div className="concepts-section">
              <h4>Extracted Concepts</h4>
              <div className="concepts-list">
                {result.concepts.map((concept: string, i: number) => (
                  <div key={i} className="concept-item">
                    <span className="concept-num">{i + 1}</span>
                    <span className="concept-name">{concept}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <button type="button" className="continue-btn" onClick={handleComplete}>
            Continue to Metacognition
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 18l6-6-6-6"/>
            </svg>
          </button>
        </div>
      )}

      <style>{`
        .reflection-step {
          max-width: 700px;
          margin: 0 auto;
        }

        .step-header {
          display: flex;
          align-items: center;
          gap: 16px;
          margin-bottom: 32px;
        }

        .step-icon {
          width: 48px;
          height: 48px;
          background: linear-gradient(135deg, #e94560, #d63850);
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1.5rem;
          font-weight: 700;
        }

        .step-info h2 {
          margin: 0;
          font-size: 1.5rem;
        }

        .step-info p {
          margin: 4px 0 0;
          color: rgba(255, 255, 255, 0.6);
        }

        .analysis-config {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 16px;
          padding: 24px;
        }

        .source-info {
          display: flex;
          align-items: center;
          gap: 12px;
          padding-bottom: 20px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
          margin-bottom: 20px;
        }

        .source-info .label {
          color: rgba(255, 255, 255, 0.5);
        }

        .source-info .value {
          font-weight: 500;
        }

        .source-info .chars {
          margin-left: auto;
          font-size: 0.8rem;
          color: rgba(255, 255, 255, 0.4);
          background: rgba(255, 255, 255, 0.1);
          padding: 4px 8px;
          border-radius: 4px;
        }

        .depth-selector h4,
        .moves-preview h4 {
          margin: 0 0 12px;
          font-size: 0.9rem;
          color: rgba(255, 255, 255, 0.7);
        }

        .depth-options {
          display: flex;
          gap: 12px;
        }

        .depth-btn {
          flex: 1;
          padding: 16px;
          background: rgba(0, 0, 0, 0.2);
          border: 2px solid transparent;
          border-radius: 12px;
          color: rgba(255, 255, 255, 0.7);
          cursor: pointer;
          transition: all 0.2s;
          text-align: left;
        }

        .depth-btn:hover {
          background: rgba(255, 255, 255, 0.05);
        }

        .depth-btn.selected {
          border-color: #e94560;
          background: rgba(233, 69, 96, 0.1);
        }

        .depth-name {
          display: block;
          font-weight: 600;
          margin-bottom: 4px;
        }

        .depth-desc {
          display: block;
          font-size: 0.75rem;
          opacity: 0.7;
        }

        .moves-preview {
          margin-top: 24px;
        }

        .moves-grid {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
        }

        .move-chip {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid;
          border-radius: 8px;
          font-size: 0.8rem;
        }

        .move-chip .pattern {
          font-weight: 700;
        }

        .start-btn {
          width: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          margin-top: 24px;
          padding: 16px;
          background: #e94560;
          border: none;
          border-radius: 12px;
          color: white;
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }

        .start-btn:hover {
          background: #d63850;
        }

        .progress-section {
          margin-top: 24px;
        }

        .progress-bar {
          height: 8px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 4px;
          overflow: hidden;
        }

        .progress-fill {
          height: 100%;
          background: #e94560;
          transition: width 0.3s;
        }

        .progress-text {
          margin-top: 8px;
          text-align: center;
          font-size: 0.85rem;
          color: rgba(255, 255, 255, 0.6);
        }

        .progress-text .agent {
          color: #e94560;
          font-weight: 500;
        }

        .error {
          margin-top: 16px;
          padding: 12px;
          background: rgba(244, 67, 54, 0.1);
          border-radius: 8px;
          color: #f44336;
        }

        .analysis-results {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 16px;
          padding: 24px;
        }

        .result-summary {
          display: flex;
          gap: 24px;
          padding-bottom: 20px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
          margin-bottom: 20px;
        }

        .stat {
          text-align: center;
        }

        .stat-value {
          display: block;
          font-size: 2rem;
          font-weight: 700;
          color: #e94560;
        }

        .stat-label {
          font-size: 0.8rem;
          color: rgba(255, 255, 255, 0.5);
        }

        .summary-section,
        .concepts-section {
          margin-bottom: 24px;
        }

        .summary-section h4,
        .concepts-section h4 {
          margin: 0 0 12px;
          font-size: 0.9rem;
          color: rgba(255, 255, 255, 0.7);
        }

        .summary-section p {
          line-height: 1.6;
          color: rgba(255, 255, 255, 0.8);
        }

        .themes {
          margin-top: 16px;
        }

        .themes h5 {
          margin: 0 0 8px;
          font-size: 0.8rem;
          color: rgba(255, 255, 255, 0.5);
        }

        .theme-chips {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
        }

        .theme-chip {
          padding: 6px 12px;
          background: rgba(233, 69, 96, 0.2);
          border-radius: 16px;
          font-size: 0.8rem;
          color: #e94560;
        }

        .concepts-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
          max-height: 200px;
          overflow-y: auto;
        }

        .concept-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px;
          background: rgba(0, 0, 0, 0.2);
          border-radius: 8px;
        }

        .concept-num {
          width: 24px;
          height: 24px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 0.75rem;
          font-weight: 600;
        }

        .concept-name {
          font-weight: 500;
        }

        .continue-btn {
          width: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          padding: 16px;
          background: #e94560;
          border: none;
          border-radius: 12px;
          color: white;
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }

        .continue-btn:hover {
          background: #d63850;
        }
      `}</style>
    </div>
  )
}
