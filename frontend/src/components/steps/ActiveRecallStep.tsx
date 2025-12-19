/**
 * ActiveRecallStep - Step 5: Generate questions for spaced repetition
 */

import { useState, useCallback } from 'react'

interface ActiveRecallStepProps {
  sessionId: string
  onComplete: (result: any) => void
}

export function ActiveRecallStep({ sessionId, onComplete }: ActiveRecallStepProps) {
  const [isGenerating, setIsGenerating] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [questionsPerConcept, setQuestionsPerConcept] = useState(5)
  const [error, setError] = useState<string | null>(null)

  const generateQuestions = useCallback(async () => {
    setIsGenerating(true)
    setError(null)

    try {
      const response = await fetch('/api/study/steps/active-recall', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          questions_per_concept: questionsPerConcept,
        }),
      })

      if (!response.ok) throw new Error('Failed to generate questions')

      const data = await response.json()
      setResult(data)
      onComplete(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed')
    } finally {
      setIsGenerating(false)
    }
  }, [sessionId, questionsPerConcept, onComplete])

  const handleExport = useCallback(async (format: 'remnote' | 'anki' | 'markdown') => {
    try {
      const response = await fetch(`/api/study/sessions/${sessionId}/export/${format}`)
      if (!response.ok) throw new Error('Export failed')

      const data = await response.json()

      if (format === 'markdown') {
        const blob = new Blob([data.content], { type: 'text/markdown' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `study-notes-${sessionId.slice(0, 8)}.md`
        a.click()
      } else {
        const blob = new Blob([JSON.stringify(data.data, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `study-${format}-${sessionId.slice(0, 8)}.json`
        a.click()
      }
    } catch (err) {
      console.error('Export error:', err)
    }
  }, [sessionId])

  return (
    <div className="active-recall-step">
      <div className="step-header">
        <div className="step-icon">5</div>
        <div className="step-info">
          <h2>Active Recall</h2>
          <p>Generate questions for spaced repetition learning</p>
        </div>
      </div>

      {!result ? (
        <div className="generate-config">
          <div className="config-option">
            <label>Questions per concept</label>
            <div className="slider-row">
              <input
                type="range"
                min="3"
                max="10"
                value={questionsPerConcept}
                onChange={(e) => setQuestionsPerConcept(Number(e.target.value))}
              />
              <span className="slider-value">{questionsPerConcept}</span>
            </div>
          </div>

          <div className="question-types">
            <h4>Question Types (DSRP-based)</h4>
            <div className="type-grid">
              <div className="type-item" style={{ borderColor: '#1976D2' }}>
                <span className="type-pattern">D</span>
                <span className="type-name">Distinction</span>
                <span className="type-example">"What distinguishes X from Y?"</span>
              </div>
              <div className="type-item" style={{ borderColor: '#388E3C' }}>
                <span className="type-pattern">S</span>
                <span className="type-name">System</span>
                <span className="type-example">"What are the parts of X?"</span>
              </div>
              <div className="type-item" style={{ borderColor: '#F57C00' }}>
                <span className="type-pattern">R</span>
                <span className="type-name">Relationship</span>
                <span className="type-example">"What causes X?"</span>
              </div>
              <div className="type-item" style={{ borderColor: '#7B1FA2' }}>
                <span className="type-pattern">P</span>
                <span className="type-name">Perspective</span>
                <span className="type-example">"How would [expert] view X?"</span>
              </div>
            </div>
          </div>

          <button className="generate-btn" onClick={generateQuestions} disabled={isGenerating}>
            {isGenerating ? (
              <>
                <div className="btn-spinner" />
                Generating Questions...
              </>
            ) : (
              <>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
                  <line x1="12" y1="17" x2="12.01" y2="17" />
                </svg>
                Generate Questions
              </>
            )}
          </button>

          {error && <div className="error">{error}</div>}
        </div>
      ) : (
        <div className="results">
          <div className="result-header">
            <div className="stat">
              <span className="stat-value">{result.questions_generated || 0}</span>
              <span className="stat-label">Questions Generated</span>
            </div>
            <div className="stat">
              <span className="stat-value">{result.concepts_covered || 0}</span>
              <span className="stat-label">Concepts Covered</span>
            </div>
          </div>

          <div className="questions-preview">
            <h4>Sample Questions</h4>
            <div className="questions-list">
              {(result.question_bank || []).slice(0, 3).map((qb: any, i: number) => (
                <div key={i} className="question-card">
                  <div className="question-concept">{qb.concept}</div>
                  {(qb.questions || []).slice(0, 2).map((q: any, j: number) => (
                    <div key={j} className="question-item">
                      <span className="q-label">Q:</span>
                      <span className="q-text">{q.question}</span>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>

          <div className="export-section">
            <h4>Export Questions</h4>
            <div className="export-buttons">
              <button className="export-btn" onClick={() => handleExport('remnote')}>
                <span className="export-icon">📝</span>
                RemNote
              </button>
              <button className="export-btn" onClick={() => handleExport('anki')}>
                <span className="export-icon">🃏</span>
                Anki
              </button>
              <button className="export-btn" onClick={() => handleExport('markdown')}>
                <span className="export-icon">📄</span>
                Markdown
              </button>
            </div>
          </div>

          <div className="complete-message">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#4caf50" strokeWidth="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
            <div>
              <h4>Study Session Complete!</h4>
              <p>Your questions are ready. Export them to your preferred spaced repetition app.</p>
            </div>
          </div>
        </div>
      )}

      <style>{`
        .active-recall-step {
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

        .step-info h2 { margin: 0; font-size: 1.5rem; }
        .step-info p { margin: 4px 0 0; color: rgba(255,255,255,0.6); }

        .generate-config, .results {
          background: rgba(255,255,255,0.05);
          border-radius: 16px;
          padding: 24px;
        }

        .config-option {
          margin-bottom: 24px;
        }

        .config-option label {
          display: block;
          margin-bottom: 8px;
          color: rgba(255,255,255,0.7);
        }

        .slider-row {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .slider-row input[type="range"] {
          flex: 1;
          accent-color: #e94560;
        }

        .slider-value {
          width: 32px;
          height: 32px;
          background: #e94560;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 700;
        }

        .question-types h4 {
          margin: 0 0 12px;
          color: rgba(255,255,255,0.7);
        }

        .type-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 12px;
        }

        .type-item {
          padding: 16px;
          background: rgba(0,0,0,0.2);
          border: 2px solid;
          border-radius: 12px;
        }

        .type-pattern {
          display: block;
          font-size: 1.5rem;
          font-weight: 700;
          margin-bottom: 4px;
        }

        .type-name {
          display: block;
          font-weight: 500;
          margin-bottom: 4px;
        }

        .type-example {
          display: block;
          font-size: 0.75rem;
          color: rgba(255,255,255,0.5);
          font-style: italic;
        }

        .generate-btn {
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
        }

        .generate-btn:hover { background: #d63850; }
        .generate-btn:disabled { opacity: 0.7; cursor: wait; }

        .btn-spinner {
          width: 20px;
          height: 20px;
          border: 2px solid rgba(255,255,255,0.3);
          border-top-color: white;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin { to { transform: rotate(360deg); } }

        .result-header {
          display: flex;
          gap: 24px;
          padding-bottom: 20px;
          border-bottom: 1px solid rgba(255,255,255,0.1);
          margin-bottom: 20px;
        }

        .stat { text-align: center; }
        .stat-value { display: block; font-size: 2rem; font-weight: 700; color: #e94560; }
        .stat-label { font-size: 0.8rem; color: rgba(255,255,255,0.5); }

        .questions-preview h4, .export-section h4 {
          margin: 0 0 12px;
          color: rgba(255,255,255,0.7);
        }

        .questions-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
          margin-bottom: 24px;
        }

        .question-card {
          padding: 16px;
          background: rgba(0,0,0,0.2);
          border-radius: 8px;
        }

        .question-concept {
          font-weight: 600;
          color: #e94560;
          margin-bottom: 8px;
        }

        .question-item {
          display: flex;
          gap: 8px;
          padding: 8px 0;
          border-top: 1px solid rgba(255,255,255,0.1);
          font-size: 0.9rem;
        }

        .q-label {
          color: rgba(255,255,255,0.5);
          font-weight: 600;
        }

        .export-buttons {
          display: flex;
          gap: 12px;
        }

        .export-btn {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
          padding: 20px;
          background: rgba(255,255,255,0.05);
          border: 1px solid rgba(255,255,255,0.2);
          border-radius: 12px;
          color: white;
          cursor: pointer;
          transition: all 0.2s;
        }

        .export-btn:hover {
          background: rgba(255,255,255,0.1);
          border-color: #e94560;
        }

        .export-icon {
          font-size: 1.5rem;
        }

        .complete-message {
          display: flex;
          align-items: center;
          gap: 16px;
          margin-top: 24px;
          padding: 20px;
          background: rgba(76,175,80,0.1);
          border: 1px solid rgba(76,175,80,0.3);
          border-radius: 12px;
        }

        .complete-message h4 {
          margin: 0 0 4px;
          color: #4caf50;
        }

        .complete-message p {
          margin: 0;
          color: rgba(255,255,255,0.7);
          font-size: 0.9rem;
        }

        .error {
          margin-top: 16px;
          padding: 12px;
          background: rgba(244,67,54,0.1);
          border-radius: 8px;
          color: #f44336;
        }
      `}</style>
    </div>
  )
}
