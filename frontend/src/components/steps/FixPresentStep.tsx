/**
 * FixPresentStep - Step 4: Review and correct analyses
 */

import { useState, useCallback } from 'react'

interface FixPresentStepProps {
  sessionId: string
  metacognitionResult?: any
  onComplete: (result: any) => void
}

export function FixPresentStep({ sessionId, metacognitionResult, onComplete }: FixPresentStepProps) {
  const [isProcessing, setIsProcessing] = useState(false)
  const [corrections] = useState<any[]>([])

  const handleComplete = useCallback(async () => {
    setIsProcessing(true)

    try {
      const response = await fetch('/api/study/steps/fix-present', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          corrections: corrections,
        }),
      })

      if (!response.ok) throw new Error('Failed')

      const data = await response.json()
      onComplete(data)
    } catch (err) {
      console.error(err)
    } finally {
      setIsProcessing(false)
    }
  }, [sessionId, corrections, onComplete])

  const nodes = metacognitionResult?.nodes || []
  const edges = metacognitionResult?.edges || []

  return (
    <div className="fix-present-step">
      <div className="step-header">
        <div className="step-icon">4</div>
        <div className="step-info">
          <h2>Review & Fix</h2>
          <p>Review the analysis and make any corrections</p>
        </div>
      </div>

      <div className="review-content">
        <div className="review-stats">
          <div className="stat">
            <span className="stat-value">{nodes.length}</span>
            <span className="stat-label">Concepts</span>
          </div>
          <div className="stat">
            <span className="stat-value">{edges.length}</span>
            <span className="stat-label">Relationships</span>
          </div>
          <div className="stat">
            <span className="stat-value">{corrections.length}</span>
            <span className="stat-label">Corrections</span>
          </div>
        </div>

        <div className="review-message">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
          <div>
            <h4>Analysis Complete</h4>
            <p>Your knowledge has been analyzed and structured. Review the results and proceed to generate study questions.</p>
          </div>
        </div>

        <button className="continue-btn" onClick={handleComplete} disabled={isProcessing}>
          {isProcessing ? 'Processing...' : 'Continue to Questions'}
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M9 18l6-6-6-6"/>
          </svg>
        </button>
      </div>

      <style>{`
        .fix-present-step {
          max-width: 600px;
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

        .review-content {
          background: rgba(255,255,255,0.05);
          border-radius: 16px;
          padding: 24px;
        }

        .review-stats {
          display: flex;
          gap: 24px;
          padding-bottom: 20px;
          border-bottom: 1px solid rgba(255,255,255,0.1);
          margin-bottom: 20px;
        }

        .stat { text-align: center; }
        .stat-value { display: block; font-size: 2rem; font-weight: 700; color: #e94560; }
        .stat-label { font-size: 0.8rem; color: rgba(255,255,255,0.5); }

        .review-message {
          display: flex;
          gap: 16px;
          padding: 20px;
          background: rgba(76,175,80,0.1);
          border: 1px solid rgba(76,175,80,0.3);
          border-radius: 12px;
          margin-bottom: 24px;
        }

        .review-message svg { color: #4caf50; flex-shrink: 0; }
        .review-message h4 { margin: 0 0 4px; color: #4caf50; }
        .review-message p { margin: 0; color: rgba(255,255,255,0.7); font-size: 0.9rem; }

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
        }

        .continue-btn:hover { background: #d63850; }
        .continue-btn:disabled { opacity: 0.5; cursor: not-allowed; }
      `}</style>
    </div>
  )
}
