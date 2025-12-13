import { useState, useEffect } from 'react'
import { useDSRPAnalysis } from '../hooks/useDSRPAnalysis'
import { useExport } from '../hooks/useExport'
import { useConceptStore } from '../stores/conceptStore'

interface AnalysisResult {
  pattern: string
  elements: Record<string, unknown>
  move: string
  reasoning?: string
}

interface DSRPPanelProps {
  onAnalysisComplete?: (concept: string, result: AnalysisResult) => void
  onClear?: () => void
  drillDownConcept?: string | null
  initialMove?: string
}

const DSRP_PATTERNS = [
  { id: 'D', name: 'Distinctions', elements: ['identity', 'other'], color: '#1976D2' },
  { id: 'S', name: 'Systems', elements: ['part', 'whole'], color: '#388E3C' },
  { id: 'R', name: 'Relationships', elements: ['action', 'reaction'], color: '#F57C00' },
  { id: 'P', name: 'Perspectives', elements: ['point', 'view'], color: '#7B1FA2' },
]

const SIX_MOVES = [
  { id: 'is-is-not', name: 'Is/Is Not', pattern: 'D', description: 'Define what it IS and IS NOT' },
  { id: 'zoom-in', name: 'Zoom In', pattern: 'S', description: 'Examine the parts' },
  { id: 'zoom-out', name: 'Zoom Out', pattern: 'S', description: 'Examine the whole' },
  { id: 'part-party', name: 'Part Party', pattern: 'S', description: 'Parts + relationships' },
  { id: 'rds-barbell', name: 'RDS Barbell', pattern: 'R', description: 'Relate → Distinguish → Systematize' },
  { id: 'p-circle', name: 'P-Circle', pattern: 'P', description: 'Map perspectives' },
]

const DYNAMICS = [
  { symbol: '=', name: 'Equality', description: 'Elements are equally important' },
  { symbol: '⇔', name: 'Co-implication', description: 'Elements imply each other' },
  { symbol: '✷', name: 'Simultaneity', description: 'Elements occur together' },
]

export function DSRPPanel({ onAnalysisComplete, onClear, drillDownConcept, initialMove }: DSRPPanelProps) {
  const [selectedMove, setSelectedMove] = useState<string>(initialMove || 'is-is-not')
  const [selectedConcept, setSelectedConcept] = useState<string>('')

  const { analyze, isAnalyzing, result } = useDSRPAnalysis()
  const { exportToMarkdown, downloadFile, isExporting } = useExport()
  const { concepts, fetchConcepts } = useConceptStore()

  useEffect(() => {
    fetchConcepts()
  }, [fetchConcepts])

  // Update move when initialMove changes (from PDF concept selection)
  useEffect(() => {
    if (initialMove) {
      setSelectedMove(initialMove)
    }
  }, [initialMove])

  // Handle drill-down: auto-fill concept and trigger analysis
  useEffect(() => {
    if (drillDownConcept && drillDownConcept !== selectedConcept) {
      setSelectedConcept(drillDownConcept)
      // Trigger analysis after a brief delay to allow state to update
      const timer = setTimeout(() => {
        analyze(drillDownConcept, selectedMove)
      }, 100)
      return () => clearTimeout(timer)
    }
  }, [drillDownConcept, analyze, selectedMove])

  // When analysis completes, pass to parent
  useEffect(() => {
    if (result && selectedConcept && onAnalysisComplete) {
      onAnalysisComplete(selectedConcept, result as AnalysisResult)
    }
  }, [result, selectedConcept, onAnalysisComplete])

  const handleAnalyze = async () => {
    if (selectedConcept && selectedMove) {
      await analyze(selectedConcept, selectedMove)
    }
  }

  const handleExport = async () => {
    const conceptIds = concepts.map((c) => c.id)
    if (conceptIds.length === 0) {
      alert('No concepts to export')
      return
    }
    const content = await exportToMarkdown({ conceptIds })
    if (content) {
      downloadFile(content, 'dsrp-export.md')
    }
  }

  const handleClear = () => {
    setSelectedConcept('')
    if (onClear) onClear()
  }

  return (
    <aside className="dsrp-panel">
      <div className="panel-header">
        <h2>DSRP Analysis</h2>
      </div>

      {/* 4 Patterns */}
      <div className="section">
        <h3>4 Patterns</h3>
        <div className="patterns-grid">
          {DSRP_PATTERNS.map((p) => (
            <div key={p.id} className="pattern-card" style={{ borderColor: p.color }}>
              <span className="pattern-id" style={{ color: p.color }}>{p.id}</span>
              <span className="pattern-name">{p.name}</span>
              <span className="pattern-elements">{p.elements.join(' / ')}</span>
            </div>
          ))}
        </div>
      </div>

      {/* 3 Dynamics */}
      <div className="section">
        <h3>3 Dynamics</h3>
        <div className="dynamics-row">
          {DYNAMICS.map((d) => (
            <div key={d.symbol} className="dynamic-item" title={d.description}>
              <span className="dynamic-symbol">{d.symbol}</span>
              <span className="dynamic-name">{d.name}</span>
            </div>
          ))}
        </div>
      </div>

      {/* 6 Moves */}
      <div className="section">
        <h3>6 Moves</h3>
        <div className="moves-list">
          {SIX_MOVES.map((move) => (
            <button
              key={move.id}
              className={`move-btn ${selectedMove === move.id ? 'selected' : ''}`}
              onClick={() => setSelectedMove(move.id)}
              title={move.description}
            >
              {move.name}
            </button>
          ))}
        </div>
      </div>

      {/* Analysis */}
      <div className="section">
        <h3>Analyze Concept</h3>
        <div className="input-wrapper">
          <input
            type="text"
            placeholder={isAnalyzing ? 'Analyzing...' : 'Type concept + Enter'}
            value={selectedConcept}
            onChange={(e) => setSelectedConcept(e.target.value)}
            className={`concept-input ${isAnalyzing ? 'analyzing' : ''}`}
            disabled={isAnalyzing}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && selectedConcept && !isAnalyzing) {
                e.preventDefault()
                handleAnalyze()
              }
            }}
          />
          {isAnalyzing && <div className="input-spinner" />}
        </div>
      </div>

      {/* Actions */}
      <div className="section actions">
        <button className="action-btn" onClick={handleExport} disabled={isExporting}>
          Export
        </button>
        <button className="action-btn clear" onClick={handleClear}>
          Clear
        </button>
      </div>

      <style>{`
        .dsrp-panel {
          width: 280px;
          background: var(--color-surface, #16213e);
          border-left: 1px solid rgba(255,255,255,0.1);
          display: flex;
          flex-direction: column;
          padding: 16px;
          overflow-y: auto;
          font-family: Calibri, -apple-system, sans-serif;
        }
        .panel-header h2 {
          font-size: 16px;
          margin: 0 0 16px 0;
          color: #fff;
        }
        .section {
          margin-bottom: 20px;
        }
        .section h3 {
          font-size: 12px;
          color: #888;
          margin: 0 0 10px 0;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }
        .patterns-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 8px;
        }
        .pattern-card {
          background: rgba(255,255,255,0.05);
          border: 2px solid;
          border-radius: 6px;
          padding: 8px;
          text-align: center;
        }
        .pattern-id {
          display: block;
          font-size: 18px;
          font-weight: bold;
        }
        .pattern-name {
          display: block;
          font-size: 11px;
          color: #ccc;
        }
        .pattern-elements {
          display: block;
          font-size: 9px;
          color: #888;
          margin-top: 2px;
        }
        .dynamics-row {
          display: flex;
          gap: 8px;
        }
        .dynamic-item {
          flex: 1;
          background: rgba(255,255,255,0.05);
          border-radius: 6px;
          padding: 8px;
          text-align: center;
          cursor: help;
        }
        .dynamic-symbol {
          display: block;
          font-size: 18px;
          color: #e94560;
        }
        .dynamic-name {
          display: block;
          font-size: 9px;
          color: #888;
          margin-top: 2px;
        }
        .moves-list {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
        }
        .move-btn {
          background: rgba(255,255,255,0.05);
          border: 1px solid rgba(255,255,255,0.1);
          color: #aaa;
          padding: 6px 10px;
          border-radius: 4px;
          cursor: pointer;
          font-size: 11px;
          transition: all 0.15s;
        }
        .move-btn:hover {
          border-color: #e94560;
          color: #fff;
        }
        .move-btn.selected {
          background: #e94560;
          border-color: #e94560;
          color: #fff;
        }
        .concept-input {
          width: 100%;
          padding: 10px;
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 4px;
          background: rgba(0,0,0,0.2);
          color: #fff;
          font-size: 13px;
          margin-bottom: 10px;
        }
        .concept-input::placeholder {
          color: #666;
        }
        .concept-input.analyzing {
          opacity: 0.7;
        }
        .input-wrapper {
          position: relative;
        }
        .input-spinner {
          position: absolute;
          right: 12px;
          top: 50%;
          transform: translateY(-50%);
          width: 16px;
          height: 16px;
          border: 2px solid rgba(233, 69, 96, 0.3);
          border-top-color: #e94560;
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }
        @keyframes spin {
          to { transform: translateY(-50%) rotate(360deg); }
        }
        .actions {
          display: flex;
          gap: 8px;
          margin-top: auto;
        }
        .action-btn {
          flex: 1;
          padding: 10px;
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 4px;
          background: transparent;
          color: #888;
          font-size: 12px;
          cursor: pointer;
          transition: all 0.15s;
        }
        .action-btn:hover {
          border-color: #666;
          color: #fff;
        }
        .action-btn.clear:hover {
          border-color: #e74c3c;
          color: #e74c3c;
        }
      `}</style>
    </aside>
  )
}
