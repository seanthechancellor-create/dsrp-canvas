import { useState, useEffect, useRef } from 'react'
import { useDSRPAnalysis } from '../hooks/useDSRPAnalysis'
import { useExport } from '../hooks/useExport'
import { useConceptStore } from '../stores/conceptStore'
import { DSRP_PATTERNS, DSRPIcon } from './DSRPIcons'


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
  collapsed?: boolean
  onToggleCollapse?: () => void
}

const DSRP_MOVES = [
  { id: 'is-is-not', name: 'Is/Is Not', pattern: 'D', description: 'Define what it IS and IS NOT' },
  { id: 'zoom-in', name: 'Zoom In', pattern: 'S', description: 'Examine the parts' },
  { id: 'zoom-out', name: 'Zoom Out', pattern: 'S', description: 'Examine the whole' },
  { id: 'part-party', name: 'Part Party', pattern: 'S', description: 'Parts + relationships' },
  { id: 'rds-barbell', name: 'RDS Barbell', pattern: 'R', description: 'Relate → Distinguish → Systematize' },
  { id: 'p-circle', name: 'P-Circle', pattern: 'P', description: 'Map perspectives' },
  { id: 'woc', name: 'WoC', pattern: 'R', description: 'Web of Causality - forward effects' },
  { id: 'waoc', name: 'WAoC', pattern: 'R', description: 'Web of Anticausality - root causes' },
]

const DYNAMICS = [
  { symbol: '=', name: 'Equality', description: 'Elements are equally important' },
  { symbol: '⇔', name: 'Co-implication', description: 'Elements imply each other' },
  { symbol: '✷', name: 'Simultaneity', description: 'Elements occur together' },
]

export function DSRPPanel({ onAnalysisComplete, onClear, drillDownConcept, initialMove, collapsed = false, onToggleCollapse }: DSRPPanelProps) {
  const [selectedMove, setSelectedMove] = useState<string>(initialMove || 'is-is-not')
  const [selectedConcept, setSelectedConcept] = useState<string>('')

  const { analyze, isAnalyzing, result, error, useMock, toggleMock, aiProvider } = useDSRPAnalysis()
  const { exportToMarkdown, downloadFile, isExporting } = useExport()
  const { concepts, fetchConcepts } = useConceptStore()

  // Track the last processed drillDownConcept to avoid re-processing
  const lastDrillDownRef = useRef<string | null>(null)

  useEffect(() => {
    fetchConcepts()
  }, [fetchConcepts])

  // Update move when initialMove changes (from PDF concept selection)
  useEffect(() => {
    if (initialMove) {
      setSelectedMove(initialMove)
    }
  }, [initialMove])

  // Handle drill-down: auto-fill concept and auto-analyze
  useEffect(() => {
    if (drillDownConcept && drillDownConcept !== lastDrillDownRef.current) {
      console.log('Drill-down triggered for:', drillDownConcept)
      lastDrillDownRef.current = drillDownConcept
      setSelectedConcept(drillDownConcept)
      // Auto-analyze the concept
      setTimeout(() => {
        analyze(drillDownConcept, selectedMove)
      }, 100)
    }
  }, [drillDownConcept, selectedMove, analyze])

  // When analysis completes, pass to parent
  useEffect(() => {
    if (result && selectedConcept && onAnalysisComplete) {
      onAnalysisComplete(selectedConcept, result as AnalysisResult)
    }
  }, [result, selectedConcept, onAnalysisComplete])

  const handleAnalyze = async () => {
    if (isAnalyzing) return
    const concept = selectedConcept.trim()
    console.log('Manual analysis triggered:', { concept, move: selectedMove })
    if (concept && selectedMove) {
      await analyze(concept, selectedMove)
    } else {
      console.warn('Analysis skipped: missing concept or move', { concept, selectedMove })
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

  // Get icon for move
  const getMoveIcon = (moveId: string) => {
    switch (moveId) {
      case 'is-is-not': return '◐'
      case 'zoom-in': return '🔍'
      case 'zoom-out': return '🔭'
      case 'part-party': return '⚙️'
      case 'rds-barbell': return '⇄'
      case 'p-circle': return '👁'
      case 'woc': return '→'
      case 'waoc': return '←'
      default: return '•'
    }
  }

  return (
    <aside className={`dsrp-panel ${collapsed ? 'collapsed' : ''}`}>
      <div className="panel-header">
        {collapsed ? (
          <>
            {/* Expand Button - diagonal arrows pointing outward */}
            <button
              onClick={onToggleCollapse}
              title="Expand"
              style={{
                width: 24,
                height: 24,
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.2)',
                borderRadius: 6,
                color: 'rgba(255,255,255,0.6)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: 8,
              }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="15 3 21 3 21 9" />
                <polyline points="9 21 3 21 3 15" />
                <line x1="21" y1="3" x2="14" y2="10" />
                <line x1="3" y1="21" x2="10" y2="14" />
              </svg>
            </button>
            <div className="collapsed-title" title="DSRP Analysis">
              <span>D</span><span>S</span><span>R</span><span>P</span>
            </div>
          </>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', width: '100%' }}>
            {/* Collapse Button - diagonal arrows pointing inward (on LEFT/inside edge) */}
            <button
              onClick={onToggleCollapse}
              title="Collapse"
              style={{
                width: 24,
                height: 24,
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.2)',
                borderRadius: 6,
                color: 'rgba(255,255,255,0.6)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
              }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="4 14 10 14 10 20" />
                <polyline points="20 10 14 10 14 4" />
                <line x1="14" y1="10" x2="21" y2="3" />
                <line x1="3" y1="21" x2="10" y2="14" />
              </svg>
            </button>
            <h2 style={{ flex: 1, textAlign: 'center', fontSize: '1rem', margin: 0 }}>DSRP Analysis</h2>
          </div>
        )}
      </div>

      {/* 4 Patterns */}
      <div className="section">
        {!collapsed && <h3>4 Patterns</h3>}
        <div className={`patterns-grid ${collapsed ? 'collapsed' : ''}`}>
          {DSRP_PATTERNS.map((p) => (
            <div key={p.id} className="pattern-card" style={{ borderColor: p.color }} title={collapsed ? `${p.name}: ${p.elements.join(' / ')}` : undefined}>
              <DSRPIcon pattern={p.id} size={collapsed ? 16 : 20} />
              {!collapsed && (
                <div className="pattern-info">
                  <span className="pattern-name">{p.name}</span>
                  <span className="pattern-elements">{p.elements.join(' / ')}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 3 Dynamics - Hidden when collapsed */}
      {!collapsed && (
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
      )}

      {/* 8 Moves */}
      <div className="section">
        {!collapsed && <h3>8 Moves</h3>}
        <div className={`moves-list ${collapsed ? 'collapsed' : ''}`}>
          {DSRP_MOVES.map((move) => (
            <button
              key={move.id}
              className={`move-btn ${selectedMove === move.id ? 'selected' : ''}`}
              onClick={() => setSelectedMove(move.id)}
              title={move.description}
            >
              {collapsed ? getMoveIcon(move.id) : move.name}
            </button>
          ))}
        </div>
      </div>

      {/* Analysis - Show compact version when collapsed */}
      {!collapsed ? (
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
              onKeyUp={(e) => {
                if (e.key === 'Enter' && selectedConcept.trim() && !isAnalyzing) {
                  handleAnalyze()
                }
              }}
            />
            {isAnalyzing && <div className="input-spinner" />}
          </div>
          <button
            className="analyze-btn"
            onClick={handleAnalyze}
            disabled={isAnalyzing || !selectedConcept.trim()}
          >
            {isAnalyzing ? 'Analyzing...' : 'Analyze'}
          </button>
        </div>
      ) : (
        <div className="section collapsed-analyze">
          <button
            className="analyze-icon-btn"
            onClick={handleAnalyze}
            disabled={isAnalyzing || !selectedConcept.trim()}
            title={selectedConcept ? `Analyze: ${selectedConcept}` : 'Enter concept to analyze'}
          >
            {isAnalyzing ? (
              <div className="mini-spinner" />
            ) : (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 16v-4M12 8h.01" />
              </svg>
            )}
          </button>
        </div>
      )}

      {/* AI Mode Toggle - Hidden when collapsed */}
      {!collapsed && (
        <div className="section mock-toggle">
          <label className="toggle-label">
            <input
              type="checkbox"
              checked={useMock}
              onChange={toggleMock}
            />
            <span className="toggle-text">
              {useMock ? '🧪 Mock Mode (Fake Data)' : `🤖 AI Mode${aiProvider ? ` (${aiProvider})` : ''}`}
            </span>
          </label>
          <span className="toggle-hint">
            {useMock
              ? 'Uses sample data for testing UI'
              : 'Uses real AI analysis (Ollama/Gemini/Claude)'}
          </span>
        </div>
      )}

      {/* Error Message */}
      {error && !collapsed && (
        <div className="error-message" style={{ color: '#ff6b6b', fontSize: '12px', marginBottom: '10px', textAlign: 'center' }}>
          {error}
        </div>
      )}

      {/* Actions */}
      <div className={`section actions ${collapsed ? 'collapsed' : ''}`}>
        {collapsed ? (
          <>
            <button
              className="action-icon-btn"
              onClick={handleAnalyze}
              disabled={isAnalyzing}
              title="Analyze"
            >
              ▶
            </button>
            <button
              className="action-icon-btn"
              onClick={handleExport}
              disabled={isExporting}
              title="Export"
            >
              ↓
            </button>
            <button
              className="action-icon-btn"
              onClick={handleClear}
              title="Clear"
            >
              ✕
            </button>
          </>
        ) : (
          <>
            <button
              className="action-btn analyze"
              onClick={handleAnalyze}
              disabled={isAnalyzing || !selectedConcept.trim()}
              style={{
                borderColor: '#e94560',
                color: '#e94560',
                fontWeight: 'bold',
                flex: 2
              }}
            >
              {isAnalyzing ? 'Analyzing...' : 'Analyze AI'}
            </button>
            <button className="action-btn" onClick={handleExport} disabled={isExporting}>
              Export
            </button>
            <button className="action-btn clear" onClick={handleClear}>
              Clear
            </button>
          </>
        )}
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
          font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif;
          transition: width 0.3s ease, padding 0.3s ease;
          position: relative;
        }
        .dsrp-panel.collapsed {
          width: 56px;
          padding: 12px 8px;
          align-items: center;
        }
        .collapsed-title {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 2px;
          font-size: 12px;
          font-weight: bold;
        }
        .collapsed-title span:nth-child(1) { color: #1976D2; }
        .collapsed-title span:nth-child(2) { color: #388E3C; }
        .collapsed-title span:nth-child(3) { color: #F57C00; }
        .collapsed-title span:nth-child(4) { color: #7B1FA2; }
        .panel-header h2 {
          font-size: 16px;
          margin: 0 0 16px 0;
          color: #fff;
        }
        .dsrp-panel.collapsed .panel-header {
          margin-bottom: 12px;
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
          gap: 6px;
        }
        .patterns-grid.collapsed {
          grid-template-columns: 1fr;
          gap: 4px;
        }
        .pattern-card {
          display: flex;
          align-items: center;
          gap: 8px;
          background: rgba(255,255,255,0.05);
          border: 2px solid;
          border-radius: 6px;
          padding: 6px 8px;
        }
        .dsrp-panel.collapsed .pattern-card {
          padding: 6px;
          justify-content: center;
        }
        .pattern-info {
          flex: 1;
          min-width: 0;
        }
        .pattern-name {
          display: block;
          font-size: 11px;
          color: #ccc;
          font-weight: 500;
        }
        .pattern-elements {
          display: block;
          font-size: 9px;
          color: #888;
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
        .moves-list.collapsed {
          flex-direction: column;
          align-items: center;
          gap: 4px;
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
        .dsrp-panel.collapsed .move-btn {
          width: 36px;
          height: 36px;
          padding: 0;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 14px;
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
        .analyze-btn {
          width: 100%;
          padding: 10px;
          background: #e94560;
          border: none;
          border-radius: 4px;
          color: #fff;
          font-size: 13px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.15s;
        }
        .analyze-btn:hover:not(:disabled) {
          background: #d63850;
        }
        .analyze-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .actions {
          display: flex;
          gap: 8px;
          margin-top: auto;
        }
        .actions.collapsed {
          flex-direction: column;
          align-items: center;
          gap: 6px;
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
        .action-icon-btn {
          width: 36px;
          height: 36px;
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 6px;
          background: transparent;
          color: #888;
          font-size: 14px;
          cursor: pointer;
          transition: all 0.15s;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .action-icon-btn:hover {
          border-color: #e94560;
          color: #e94560;
        }
        .action-icon-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .collapsed-analyze {
          display: flex;
          justify-content: center;
        }
        .analyze-icon-btn {
          width: 40px;
          height: 40px;
          border: 2px solid #e94560;
          border-radius: 50%;
          background: rgba(233, 69, 96, 0.1);
          color: #e94560;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.2s;
        }
        .analyze-icon-btn:hover:not(:disabled) {
          background: #e94560;
          color: white;
        }
        .analyze-icon-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .mini-spinner {
          width: 16px;
          height: 16px;
          border: 2px solid rgba(233, 69, 96, 0.3);
          border-top-color: #e94560;
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }
        .mock-toggle {
          padding: 8px;
          background: rgba(255,255,255,0.03);
          border-radius: 6px;
          margin-bottom: 10px;
        }
        .toggle-label {
          display: flex;
          align-items: center;
          gap: 8px;
          cursor: pointer;
          font-size: 12px;
          color: #aaa;
        }
        .toggle-label input {
          width: 16px;
          height: 16px;
          cursor: pointer;
        }
        .toggle-text {
          flex: 1;
        }
        .toggle-hint {
          display: block;
          font-size: 10px;
          color: rgba(255,255,255,0.4);
          margin-top: 4px;
          margin-left: 24px;
        }
      `}</style>
    </aside>
  )
}
