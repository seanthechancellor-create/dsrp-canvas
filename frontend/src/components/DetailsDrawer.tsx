/**
 * DetailsDrawer - Bottom drawer with tabbed interface for DSRP analysis details
 *
 * Inspired by Kumu.io/Ogma style - shows element pairs, relationships, metadata
 * Implements DSRP 3 Dynamics: = (equality), co-implication, simultaneity
 */

import { useState, useCallback, useEffect } from 'react'

// DSRP Pattern colors
const PATTERN_COLORS: Record<string, string> = {
  D: '#1976D2',
  S: '#388E3C',
  R: '#F57C00',
  P: '#7B1FA2',
}

const PATTERN_NAMES: Record<string, string> = {
  D: 'Distinctions',
  S: 'Systems',
  R: 'Relationships',
  P: 'Perspectives',
}

interface AnalysisResult {
  pattern: string
  elements: Record<string, unknown>
  move: string
  reasoning?: string
  relatedConcepts?: string[]
  confidence?: number
}

interface DetailsDrawerProps {
  isOpen: boolean
  onClose: () => void
  concept: string
  result: AnalysisResult | null
  onDrillDown?: (concept: string) => void
}

type TabId = 'elements' | 'relationships' | 'metadata' | 'source'

export function DetailsDrawer({ isOpen, onClose, concept, result, onDrillDown }: DetailsDrawerProps) {
  const [activeTab, setActiveTab] = useState<TabId>('elements')
  const [drawerHeight, setDrawerHeight] = useState(320)
  const [isResizing, setIsResizing] = useState(false)

  // Resize handling
  const startResizing = useCallback(() => setIsResizing(true), [])
  const stopResizing = useCallback(() => setIsResizing(false), [])

  const resize = useCallback(
    (e: MouseEvent) => {
      if (isResizing) {
        const newHeight = window.innerHeight - e.clientY
        if (newHeight > 150 && newHeight < window.innerHeight * 0.7) {
          setDrawerHeight(newHeight)
        }
      }
    },
    [isResizing]
  )

  useEffect(() => {
    if (isResizing) {
      window.addEventListener('mousemove', resize)
      window.addEventListener('mouseup', stopResizing)
      return () => {
        window.removeEventListener('mousemove', resize)
        window.removeEventListener('mouseup', stopResizing)
      }
    }
  }, [isResizing, resize, stopResizing])

  // Extract element pairs based on the move type
  const getElementPairs = () => {
    if (!result) return []
    const elements = result.elements
    const move = result.move

    if (move === 'is-is-not') {
      return [
        { left: 'identity', right: 'other', leftValue: elements.identity, rightValue: elements.other, dynamic: 'co-implication' }
      ]
    } else if (move === 'zoom-in' || move === 'part-party') {
      const parts = Array.isArray(elements.parts) ? elements.parts : []
      return [
        { left: 'part', right: 'whole', leftValue: parts.join(', '), rightValue: elements.whole || concept, dynamic: 'co-implication' }
      ]
    } else if (move === 'zoom-out') {
      return [
        { left: 'part', right: 'whole', leftValue: concept, rightValue: elements.whole, dynamic: 'co-implication' }
      ]
    } else if (move === 'rds-barbell') {
      const reactions = Array.isArray(elements.reactions) ? elements.reactions : []
      return [
        { left: 'action', right: 'reaction', leftValue: elements.action || concept, rightValue: reactions.join(', '), dynamic: 'co-implication' }
      ]
    } else if (move === 'p-circle') {
      const perspectives = Array.isArray(elements.perspectives) ? elements.perspectives : []
      return perspectives.map((p: any) => ({
        left: 'point',
        right: 'view',
        leftValue: typeof p === 'string' ? p : p.point,
        rightValue: typeof p === 'object' ? p.view : '',
        dynamic: 'simultaneity'
      }))
    }
    return []
  }

  // Extract relationships from analysis
  const getRelationships = () => {
    if (!result) return []
    const relations: Array<{ from: string; to: string; type: string }> = []
    const elements = result.elements

    if (result.move === 'rds-barbell' && Array.isArray(elements.reactions)) {
      elements.reactions.forEach((r: string) => {
        relations.push({ from: concept, to: r, type: 'causes' })
      })
    } else if ((result.move === 'zoom-in' || result.move === 'part-party') && Array.isArray(elements.parts)) {
      elements.parts.forEach((p: string) => {
        relations.push({ from: concept, to: p, type: 'contains' })
      })
    } else if (result.move === 'zoom-out' && elements.whole) {
      relations.push({ from: String(elements.whole), to: concept, type: 'contains' })
    }

    return relations
  }

  const handleDrillDown = (value: string) => {
    if (onDrillDown && value) {
      // Extract first concept from comma-separated list
      const firstConcept = value.split(',')[0].trim()
      onDrillDown(firstConcept)
    }
  }

  const patternColor = PATTERN_COLORS[result?.pattern || 'D']
  const patternName = PATTERN_NAMES[result?.pattern || 'D']

  if (!isOpen) return null

  return (
    <div className="details-drawer" style={{ height: drawerHeight }}>
      {/* Resize handle */}
      <div className="drawer-handle" onMouseDown={startResizing}>
        <div className="handle-grip" />
      </div>

      {/* Header with pattern badge */}
      <div className="drawer-header">
        <div className="header-left">
          <span className="pattern-badge" style={{ background: patternColor }}>
            {result?.pattern || 'D'}
          </span>
          <h3 className="concept-title">{concept || 'Select a concept'}</h3>
          <span className="pattern-name">{patternName}</span>
        </div>
        <button className="close-btn" onClick={onClose} aria-label="Close drawer">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M18 6L6 18M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Tab navigation */}
      <div className="tab-nav">
        {(['elements', 'relationships', 'metadata', 'source'] as TabId[]).map(tab => (
          <button
            key={tab}
            className={`tab-btn ${activeTab === tab ? 'active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="tab-content">
        {activeTab === 'elements' && (
          <div className="elements-tab">
            {/* Simultaneity notice */}
            <div className="simultaneity-notice">
              <span className="star-icon">★</span>
              <span>Elements exist simultaneously - one implies the other</span>
            </div>

            {/* Element pairs */}
            <div className="element-pairs">
              {getElementPairs().map((pair, idx) => (
                <div key={idx} className="element-pair">
                  <div
                    className="element-box left"
                    onClick={() => handleDrillDown(String(pair.leftValue))}
                    title="Click to analyze"
                  >
                    <span className="element-label">{pair.left}</span>
                    <span className="element-value">{String(pair.leftValue || '-').slice(0, 100)}</span>
                  </div>
                  <div className="co-implication">
                    <span className="arrow">⟺</span>
                    <span className="dynamic-label">
                      {pair.dynamic === 'simultaneity' ? 'simultaneity' : 'co-implication'}
                    </span>
                  </div>
                  <div
                    className="element-box right"
                    onClick={() => handleDrillDown(String(pair.rightValue))}
                    title="Click to analyze"
                  >
                    <span className="element-label">{pair.right}</span>
                    <span className="element-value">{String(pair.rightValue || '-').slice(0, 100)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'relationships' && (
          <div className="relationships-tab">
            {getRelationships().length > 0 ? (
              <ul className="relations-list">
                {getRelationships().map((rel, idx) => (
                  <li key={idx} className="relation-item">
                    <span className="rel-from">{rel.from}</span>
                    <span className="rel-type">{rel.type}</span>
                    <span className="rel-to">{rel.to}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="empty-state">No explicit relationships in this analysis</p>
            )}
          </div>
        )}

        {activeTab === 'metadata' && (
          <div className="metadata-tab">
            <div className="meta-grid">
              <div className="meta-item">
                <span className="meta-label">Pattern</span>
                <span className="meta-value">{patternName} ({result?.pattern || '-'})</span>
              </div>
              <div className="meta-item">
                <span className="meta-label">Move</span>
                <span className="meta-value">{result?.move || '-'}</span>
              </div>
              <div className="meta-item">
                <span className="meta-label">Confidence</span>
                <span className="meta-value">{result?.confidence ? `${(result.confidence * 100).toFixed(0)}%` : '-'}</span>
              </div>
            </div>
            {result?.relatedConcepts && result.relatedConcepts.length > 0 && (
              <div className="related-concepts">
                <h4>Related Concepts</h4>
                <div className="concept-chips">
                  {result.relatedConcepts.map((c, idx) => (
                    <button
                      key={idx}
                      className="concept-chip"
                      onClick={() => onDrillDown?.(c)}
                    >
                      {c}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'source' && (
          <div className="source-tab">
            <div className="reasoning-section">
              <h4>AI Reasoning</h4>
              <p className="reasoning-text">{result?.reasoning || 'No reasoning provided'}</p>
            </div>
          </div>
        )}
      </div>

      <style>{`
        .details-drawer {
          position: fixed;
          bottom: 0;
          left: 0;
          right: 0;
          background: #16213e;
          border-top: 1px solid rgba(255,255,255,0.1);
          z-index: 1000;
          display: flex;
          flex-direction: column;
          font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif;
          animation: slideUp 0.3s ease;
        }
        @keyframes slideUp {
          from { transform: translateY(100%); }
          to { transform: translateY(0); }
        }

        .drawer-handle {
          height: 16px;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: row-resize;
          background: rgba(255,255,255,0.03);
        }
        .drawer-handle:hover {
          background: rgba(255,255,255,0.06);
        }
        .handle-grip {
          width: 40px;
          height: 4px;
          background: rgba(255,255,255,0.2);
          border-radius: 2px;
        }

        .drawer-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 20px;
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .header-left {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .pattern-badge {
          padding: 4px 10px;
          border-radius: 4px;
          font-weight: 600;
          font-size: 14px;
          color: white;
        }
        .concept-title {
          margin: 0;
          font-size: 18px;
          font-weight: 600;
          color: #fff;
        }
        .pattern-name {
          color: rgba(255,255,255,0.5);
          font-size: 14px;
        }
        .close-btn {
          background: none;
          border: none;
          color: rgba(255,255,255,0.5);
          cursor: pointer;
          padding: 8px;
          border-radius: 4px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .close-btn:hover {
          background: rgba(255,255,255,0.1);
          color: #fff;
        }

        .tab-nav {
          display: flex;
          gap: 4px;
          padding: 8px 20px;
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .tab-btn {
          padding: 8px 16px;
          background: transparent;
          border: none;
          color: rgba(255,255,255,0.5);
          font-size: 13px;
          font-weight: 500;
          cursor: pointer;
          border-radius: 6px;
          transition: all 0.15s;
        }
        .tab-btn:hover {
          background: rgba(255,255,255,0.05);
          color: rgba(255,255,255,0.8);
        }
        .tab-btn.active {
          background: #e94560;
          color: white;
        }

        .tab-content {
          flex: 1;
          overflow-y: auto;
          padding: 16px 20px;
        }

        /* Elements Tab */
        .simultaneity-notice {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 14px;
          background: rgba(233, 69, 96, 0.1);
          border: 1px solid rgba(233, 69, 96, 0.3);
          border-radius: 6px;
          margin-bottom: 16px;
          font-size: 13px;
          color: rgba(255,255,255,0.7);
        }
        .star-icon {
          color: #e94560;
          font-size: 16px;
        }

        .element-pairs {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .element-pair {
          display: flex;
          align-items: stretch;
          gap: 8px;
        }
        .element-box {
          flex: 1;
          background: rgba(255,255,255,0.05);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 8px;
          padding: 12px;
          cursor: pointer;
          transition: all 0.15s;
        }
        .element-box:hover {
          background: rgba(255,255,255,0.08);
          border-color: rgba(255,255,255,0.2);
        }
        .element-label {
          display: block;
          font-size: 11px;
          text-transform: uppercase;
          color: rgba(255,255,255,0.4);
          margin-bottom: 4px;
          letter-spacing: 0.5px;
        }
        .element-value {
          display: block;
          font-size: 14px;
          color: #fff;
          line-height: 1.4;
        }

        .co-implication {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 0 8px;
        }
        .arrow {
          font-size: 24px;
          color: #e94560;
        }
        .dynamic-label {
          font-size: 10px;
          color: rgba(255,255,255,0.4);
          text-transform: uppercase;
          white-space: nowrap;
        }

        /* Relationships Tab */
        .relations-list {
          list-style: none;
          padding: 0;
          margin: 0;
        }
        .relation-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 10px;
          background: rgba(255,255,255,0.03);
          border-radius: 6px;
          margin-bottom: 8px;
        }
        .rel-from, .rel-to {
          padding: 4px 10px;
          background: rgba(255,255,255,0.1);
          border-radius: 4px;
          font-size: 13px;
          color: #fff;
        }
        .rel-type {
          color: #e94560;
          font-size: 12px;
          text-transform: uppercase;
        }

        /* Metadata Tab */
        .meta-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
          gap: 12px;
          margin-bottom: 20px;
        }
        .meta-item {
          background: rgba(255,255,255,0.03);
          padding: 12px;
          border-radius: 6px;
        }
        .meta-label {
          display: block;
          font-size: 11px;
          text-transform: uppercase;
          color: rgba(255,255,255,0.4);
          margin-bottom: 4px;
        }
        .meta-value {
          font-size: 14px;
          color: #fff;
        }
        .related-concepts h4 {
          font-size: 13px;
          color: rgba(255,255,255,0.6);
          margin: 0 0 10px 0;
        }
        .concept-chips {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
        }
        .concept-chip {
          padding: 6px 12px;
          background: rgba(255,255,255,0.1);
          border: none;
          border-radius: 16px;
          color: #fff;
          font-size: 12px;
          cursor: pointer;
          transition: all 0.15s;
        }
        .concept-chip:hover {
          background: #e94560;
        }

        /* Source Tab */
        .reasoning-section h4 {
          font-size: 13px;
          color: rgba(255,255,255,0.6);
          margin: 0 0 10px 0;
        }
        .reasoning-text {
          font-size: 14px;
          line-height: 1.6;
          color: rgba(255,255,255,0.8);
          margin: 0;
          white-space: pre-wrap;
        }

        .empty-state {
          color: rgba(255,255,255,0.4);
          font-size: 14px;
          text-align: center;
          padding: 20px;
        }

        /* Mobile styles */
        @media (max-width: 768px) {
          .element-pair {
            flex-direction: column;
          }
          .co-implication {
            flex-direction: row;
            padding: 8px 0;
          }
          .arrow {
            transform: rotate(90deg);
          }
          .tab-nav {
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
          }
        }
      `}</style>
    </div>
  )
}
