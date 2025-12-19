/**
 * MetacognitionStep - Step 3: Visualize and understand the knowledge graph
 */

import { useState, useCallback, useEffect } from 'react'

interface MetacognitionStepProps {
  sessionId: string
  reflectionResult?: any
  onComplete: (result: any) => void
}

export function MetacognitionStep({ sessionId, onComplete }: MetacognitionStepProps) {
  const [isProcessing, setIsProcessing] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const buildKnowledgeGraph = useCallback(async () => {
    setIsProcessing(true)
    setError(null)

    try {
      const response = await fetch('/api/study/steps/metacognition', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId }),
      })

      if (!response.ok) throw new Error('Failed to build knowledge graph')

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed')
    } finally {
      setIsProcessing(false)
    }
  }, [sessionId])

  useEffect(() => {
    buildKnowledgeGraph()
  }, [buildKnowledgeGraph])

  return (
    <div className="metacognition-step">
      <div className="step-header">
        <div className="step-icon">3</div>
        <div className="step-info">
          <h2>Metacognition</h2>
          <p>Visualize your knowledge graph and connections</p>
        </div>
      </div>

      {isProcessing ? (
        <div className="loading">
          <div className="spinner" />
          <p>Building knowledge graph...</p>
        </div>
      ) : result ? (
        <div className="graph-preview">
          <div className="stats-row">
            <div className="stat">
              <span className="stat-value">{result.knowledge_graph?.nodes?.length || 0}</span>
              <span className="stat-label">Nodes</span>
            </div>
            <div className="stat">
              <span className="stat-value">{result.knowledge_graph?.edges?.length || 0}</span>
              <span className="stat-label">Connections</span>
            </div>
            <div className="stat">
              <span className="stat-value">{result.cross_references?.length || 0}</span>
              <span className="stat-label">Cross-refs</span>
            </div>
          </div>

          <div className="graph-placeholder">
            <div className="node-grid">
              {(result.knowledge_graph?.nodes || []).slice(0, 12).map((node: any, i: number) => (
                <div key={i} className={`node ${node.type}`}>
                  <span className="node-label">{node.label}</span>
                </div>
              ))}
            </div>
          </div>

          <button type="button" className="continue-btn" onClick={() => onComplete(result)}>
            Continue to Review
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 18l6-6-6-6"/>
            </svg>
          </button>
        </div>
      ) : error ? (
        <div className="error">{error}</div>
      ) : null}

      <style>{`
        .metacognition-step {
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

        .loading {
          text-align: center;
          padding: 48px;
        }

        .spinner {
          width: 48px;
          height: 48px;
          border: 3px solid rgba(233,69,96,0.2);
          border-top-color: #e94560;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin: 0 auto 16px;
        }

        @keyframes spin { to { transform: rotate(360deg); } }

        .graph-preview {
          background: rgba(255,255,255,0.05);
          border-radius: 16px;
          padding: 24px;
        }

        .stats-row {
          display: flex;
          gap: 24px;
          padding-bottom: 20px;
          border-bottom: 1px solid rgba(255,255,255,0.1);
          margin-bottom: 20px;
        }

        .stat { text-align: center; }
        .stat-value { display: block; font-size: 2rem; font-weight: 700; color: #e94560; }
        .stat-label { font-size: 0.8rem; color: rgba(255,255,255,0.5); }

        .graph-placeholder {
          min-height: 200px;
          background: rgba(0,0,0,0.2);
          border-radius: 12px;
          padding: 24px;
          margin-bottom: 20px;
        }

        .node-grid {
          display: flex;
          flex-wrap: wrap;
          gap: 12px;
        }

        .node {
          padding: 10px 16px;
          background: rgba(255,255,255,0.1);
          border-radius: 8px;
          border: 2px solid rgba(255,255,255,0.2);
        }

        .node.concept { border-color: #e94560; }
        .node.part { border-color: #388E3C; }
        .node.effect { border-color: #F57C00; }

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

        .error {
          padding: 16px;
          background: rgba(244,67,54,0.1);
          border-radius: 8px;
          color: #f44336;
        }
      `}</style>
    </div>
  )
}
