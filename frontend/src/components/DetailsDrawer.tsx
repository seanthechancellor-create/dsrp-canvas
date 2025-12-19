/**
 * DetailsDrawer - Bottom drawer with tabbed interface for DSRP analysis details
 *
 * Inspired by Kumu.io/Ogma style - shows element pairs, relationships, metadata
 * Implements DSRP 3 Dynamics: = (equality), co-implication, simultaneity
 */

import { useState, useCallback, useEffect } from 'react'
import { DSRP_COLORS, DSRP_NAMES, DSRPIcon, DSRPPattern } from './DSRPIcons'
import { QuizPanel } from './QuizPanel'

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
  selectedDomain?: string | null
  selectedTopic?: string | null
}

type TabId = 'elements' | 'relationships' | 'notes' | 'quiz' | 'metadata'

export function DetailsDrawer({ isOpen, onClose, concept, result, onDrillDown, selectedDomain, selectedTopic }: DetailsDrawerProps) {
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
    } else if (move === 'woc') {
      const effects = Array.isArray(elements.effects) ? elements.effects : []
      return effects.map((e: any) => ({
        left: 'cause',
        right: 'effect',
        leftValue: elements.cause || concept,
        rightValue: typeof e === 'string' ? e : e.effect,
        dynamic: 'causality'
      }))
    } else if (move === 'waoc') {
      const causes = Array.isArray(elements.causes) ? elements.causes : []
      return causes.map((c: any) => ({
        left: 'cause',
        right: 'effect',
        leftValue: typeof c === 'string' ? c : c.cause,
        rightValue: elements.effect || concept,
        dynamic: 'causality'
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
    } else if (result.move === 'woc' && Array.isArray(elements.effects)) {
      elements.effects.forEach((e: any) => {
        const effectName = typeof e === 'string' ? e : e.effect
        relations.push({ from: concept, to: effectName, type: 'causes →' })
      })
    } else if (result.move === 'waoc' && Array.isArray(elements.causes)) {
      elements.causes.forEach((c: any) => {
        const causeName = typeof c === 'string' ? c : c.cause
        relations.push({ from: causeName, to: concept, type: '→ leads to' })
      })
    }

    return relations
  }

  // Generate RemNote-style DSRP notes
  const getDSRPNotes = () => {
    if (!result) return []
    const notes: Array<{ type: string; content: string; children?: string[] }> = []
    const elements = result.elements
    const move = result.move

    // Main concept note
    notes.push({
      type: 'concept',
      content: `📌 ${concept}`,
      children: [`Pattern: ${patternName} (${result.pattern})`, `Move: ${move}`]
    })

    // Pattern-specific notes
    if (move === 'is-is-not') {
      notes.push({
        type: 'distinction',
        content: '◐ Distinction',
        children: [
          `✓ IS: ${String(elements.identity || '').slice(0, 150)}`,
          `✗ IS NOT: ${String(elements.other || '').slice(0, 150)}`
        ]
      })
    } else if (move === 'zoom-in' || move === 'part-party') {
      const parts = Array.isArray(elements.parts) ? elements.parts : []
      notes.push({
        type: 'system',
        content: '⚙️ System Parts',
        children: parts.map((p: string) => `• ${p}`)
      })
    } else if (move === 'zoom-out') {
      notes.push({
        type: 'system',
        content: '🔭 Context',
        children: [`Whole: ${String(elements.whole || '')}`, `Part: ${concept}`]
      })
    } else if (move === 'p-circle') {
      const perspectives = Array.isArray(elements.perspectives) ? elements.perspectives : []
      notes.push({
        type: 'perspectives',
        content: '👁 Perspectives',
        children: perspectives.map((p: any) =>
          `${typeof p === 'string' ? p : p.point}: ${typeof p === 'object' ? p.view : ''}`
        )
      })
    } else if (move === 'woc') {
      const effects = Array.isArray(elements.effects) ? elements.effects : []
      notes.push({
        type: 'causality',
        content: '→ Effects (WoC)',
        children: effects.map((e: any) => `→ ${typeof e === 'string' ? e : e.effect}`)
      })
    } else if (move === 'waoc') {
      const causes = Array.isArray(elements.causes) ? elements.causes : []
      notes.push({
        type: 'causality',
        content: '← Root Causes (WAoC)',
        children: causes.map((c: any) => `← ${typeof c === 'string' ? c : c.cause}`)
      })
    }

    // Reasoning note
    if (result.reasoning) {
      notes.push({
        type: 'reasoning',
        content: '💡 Reasoning',
        children: [result.reasoning]
      })
    }

    return notes
  }

  const handleDrillDown = (value: string) => {
    if (onDrillDown && value) {
      // Extract first concept from comma-separated list
      const firstConcept = value.split(',')[0].trim()
      onDrillDown(firstConcept)
    }
  }

  const patternKey = (result?.pattern || 'D') as DSRPPattern
  const patternColor = DSRP_COLORS[patternKey]
  const patternName = DSRP_NAMES[patternKey]

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
            <DSRPIcon pattern={patternKey} size={18} color="#fff" />
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
        {(['elements', 'relationships', 'notes', 'quiz', 'metadata'] as TabId[]).map(tab => (
          <button
            key={tab}
            className={`tab-btn ${activeTab === tab ? 'active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab === 'notes' ? '📝 Notes' : tab === 'quiz' ? '🧠 Quiz' : tab.charAt(0).toUpperCase() + tab.slice(1)}
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

        {activeTab === 'notes' && (
          <div className="notes-tab">
            <div className="notes-header">
              <span className="notes-title">DSRP Analysis Notes</span>
              <button
                className="copy-notes-btn"
                onClick={() => {
                  const notes = getDSRPNotes()
                  const markdown = notes.map(n =>
                    `## ${n.content}\n${n.children?.map(c => `- ${c}`).join('\n') || ''}`
                  ).join('\n\n')
                  navigator.clipboard.writeText(markdown)
                }}
                title="Copy as Markdown"
              >
                📋 Copy
              </button>
            </div>
            <div className="notes-list">
              {getDSRPNotes().map((note, idx) => (
                <div key={idx} className={`note-block note-${note.type}`}>
                  <div className="note-header">{note.content}</div>
                  {note.children && (
                    <ul className="note-children">
                      {note.children.map((child, cidx) => (
                        <li key={cidx} className="note-child">{child}</li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'quiz' && (
          <div className="quiz-tab">
            <QuizPanel domain={selectedDomain} topic={selectedTopic} />
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
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 6px;
          border-radius: 6px;
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
          gap: 8px;
          padding: 12px 20px;
          background: rgba(0,0,0,0.2);
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .tab-btn {
          padding: 10px 18px;
          background: rgba(255,255,255,0.05);
          border: 1px solid rgba(255,255,255,0.1);
          color: rgba(255,255,255,0.6);
          font-size: 13px;
          font-weight: 600;
          cursor: pointer;
          border-radius: 12px 12px 4px 4px;
          transition: all 0.2s ease;
          position: relative;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }
        .tab-btn::before {
          content: '';
          position: absolute;
          bottom: 0;
          left: 50%;
          transform: translateX(-50%);
          width: 0;
          height: 2px;
          background: #e94560;
          transition: width 0.2s ease;
        }
        .tab-btn:hover {
          background: rgba(255,255,255,0.1);
          color: rgba(255,255,255,0.9);
          border-color: rgba(255,255,255,0.2);
          transform: translateY(-2px);
        }
        .tab-btn:hover::before {
          width: 60%;
        }
        .tab-btn.active {
          background: linear-gradient(135deg, #e94560 0%, #c73e54 100%);
          color: white;
          border-color: #e94560;
          box-shadow: 0 4px 12px rgba(233, 69, 96, 0.3);
        }
        .tab-btn.active::before {
          width: 80%;
          background: white;
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

        /* Notes Tab - RemNote style */
        .notes-tab {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .notes-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }
        .notes-title {
          font-size: 14px;
          font-weight: 600;
          color: rgba(255,255,255,0.7);
        }
        .copy-notes-btn {
          padding: 6px 12px;
          background: rgba(255,255,255,0.1);
          border: none;
          border-radius: 4px;
          color: rgba(255,255,255,0.7);
          font-size: 12px;
          cursor: pointer;
          transition: all 0.15s;
        }
        .copy-notes-btn:hover {
          background: #e94560;
          color: white;
        }
        .notes-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .note-block {
          background: rgba(255,255,255,0.03);
          border-left: 3px solid;
          border-radius: 0 6px 6px 0;
          padding: 12px 16px;
        }
        .note-concept { border-color: #e94560; }
        .note-distinction { border-color: #1976D2; }
        .note-system { border-color: #388E3C; }
        .note-perspectives { border-color: #7B1FA2; }
        .note-causality { border-color: #F57C00; }
        .note-reasoning { border-color: #666; }
        .note-header {
          font-size: 14px;
          font-weight: 600;
          color: #fff;
          margin-bottom: 8px;
        }
        .note-children {
          list-style: none;
          padding: 0;
          margin: 0;
        }
        .note-child {
          font-size: 13px;
          color: rgba(255,255,255,0.75);
          padding: 4px 0 4px 12px;
          border-left: 1px solid rgba(255,255,255,0.1);
          margin-left: 4px;
          line-height: 1.5;
        }
        .note-child:hover {
          background: rgba(255,255,255,0.03);
        }

        /* Quiz Tab */
        .quiz-tab {
          padding: 4px 0;
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
