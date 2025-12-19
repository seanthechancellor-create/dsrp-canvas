import { useState, useCallback } from 'react'
import { useSourceStore, ExtractedConcept } from '../stores/sourceStore'
import { DSRP_PATTERNS, DSRPIcon } from './DSRPIcons'
import { GlobalSearch } from './GlobalSearch'
import { DomainSelector } from './DomainSelector'

interface SearchResult {
  id: string
  name: string | null
  content: string
  similarity: number
  type: 'concept' | 'analysis' | 'source'
  metadata?: Record<string, unknown>
}

interface SidebarProps {
  onConceptSelect?: (concept: string, move: string) => void
  onPatternFilter?: (patterns: string[]) => void
  renderMode?: 'canvas' | 'webgl'
  onRenderModeChange?: (mode: 'canvas' | 'webgl') => void
  collapsed?: boolean
  onToggleCollapse?: () => void
  selectedDomain?: string | null
  selectedTopic?: string | null
  onDomainChange?: (domain: string | null) => void
  onTopicChange?: (topic: string | null) => void
}

export function Sidebar({
  onConceptSelect,
  onPatternFilter,
  renderMode = 'canvas',
  onRenderModeChange,
  collapsed = false,
  onToggleCollapse,
  selectedDomain,
  selectedTopic,
  onDomainChange,
  onTopicChange,
}: SidebarProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [expandedSource, setExpandedSource] = useState<string | null>(null)
  const [activePatterns, setActivePatterns] = useState<string[]>(['D', 'S', 'R', 'P'])
  const { sources, addSource, isUploading } = useSourceStore()

  const togglePattern = (patternId: string) => {
    const newPatterns = activePatterns.includes(patternId)
      ? activePatterns.filter(p => p !== patternId)
      : [...activePatterns, patternId]
    setActivePatterns(newPatterns)
    onPatternFilter?.(newPatterns)
  }

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const files = Array.from(e.dataTransfer.files)
    for (const file of files) {
      await addSource(file)
    }
  }

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    for (const file of files) {
      await addSource(file)
    }
  }

  const handleConceptClick = (concept: ExtractedConcept) => {
    if (onConceptSelect) {
      onConceptSelect(concept.name, concept.suggested_move)
    }
  }

  const toggleSource = (sourceId: string) => {
    setExpandedSource(expandedSource === sourceId ? null : sourceId)
  }

  // Handle search result selection
  const handleSearchSelect = useCallback((result: SearchResult) => {
    if (onConceptSelect) {
      // Determine appropriate move based on result type
      const move = result.type === 'analysis'
        ? (result.metadata?.move_type as string) || 'is-is-not'
        : 'is-is-not'

      let conceptName: string

      if (result.type === 'source') {
        // Extract main concept (1-2 words) from chunk content
        conceptName = extractMainConcept(result.content)
      } else {
        conceptName = result.name || result.id
      }

      onConceptSelect(conceptName, move)
    }
  }, [onConceptSelect])

  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        {collapsed ? (
          <>
            <div className="collapsed-logo" title="DSRP Canvas">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#e94560" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 6v6l4 2" />
              </svg>
            </div>
            {/* Expand Button - diagonal arrows pointing outward (NotebookLM style) */}
            <button className="collapse-toggle" onClick={onToggleCollapse} title="Expand">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="15 3 21 3 21 9" />
                <polyline points="9 21 3 21 3 15" />
                <line x1="21" y1="3" x2="14" y2="10" />
                <line x1="3" y1="21" x2="10" y2="14" />
              </svg>
            </button>
          </>
        ) : (
          <>
            <div style={{ display: 'flex', alignItems: 'center', width: '100%' }}>
              <h1 style={{ margin: 0 }}>DSRP Canvas</h1>
              <div style={{ flex: 1 }} />
              {/* Collapse Button - diagonal arrows pointing inward (NotebookLM style) */}
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
                }}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="4 14 10 14 10 20" />
                  <polyline points="20 10 14 10 14 4" />
                  <line x1="14" y1="10" x2="21" y2="3" />
                  <line x1="3" y1="21" x2="10" y2="14" />
                </svg>
              </button>
            </div>
            <span className="subtitle">4-8-3 Knowledge Analysis</span>
          </>
        )}
      </div>

      {/* Global Search */}
      {!collapsed && (
        <div className="section search-section">
          <GlobalSearch
            onResultSelect={handleSearchSelect}
            placeholder="Search knowledge base..."
          />
        </div>
      )}

      {/* Domain Selector */}
      <div className="section">
        {!collapsed && <h2 className="section-title">Categories</h2>}
        <DomainSelector
          selectedDomain={selectedDomain || null}
          selectedTopic={selectedTopic || null}
          onDomainChange={onDomainChange || (() => {})}
          onTopicChange={onTopicChange || (() => {})}
          onTopicAnalyze={onConceptSelect ? (topic) => onConceptSelect(topic, 'zoom-in') : undefined}
          collapsed={collapsed}
        />
      </div>

      {/* Pattern Filters */}
      <div className="section">
        {!collapsed && <h2 className="section-title">Patterns</h2>}
        <div className={`pattern-filters ${collapsed ? 'collapsed' : ''}`}>
          {DSRP_PATTERNS.map(pattern => (
            <button
              key={pattern.id}
              className={`pattern-chip ${activePatterns.includes(pattern.id) ? 'active' : ''}`}
              style={{
                '--pattern-color': pattern.color,
                borderColor: activePatterns.includes(pattern.id) ? pattern.color : 'transparent',
                background: activePatterns.includes(pattern.id) ? `${pattern.color}20` : 'rgba(255,255,255,0.05)'
              } as React.CSSProperties}
              onClick={() => togglePattern(pattern.id)}
              title={pattern.name}
            >
              <DSRPIcon pattern={pattern.id} size={16} color={pattern.color} />
              {!collapsed && <span className="chip-name">{pattern.name}</span>}
            </button>
          ))}
        </div>
      </div>

      {/* Render Mode Toggle - Hidden when collapsed */}
      {!collapsed && (
        <div className="section">
          <h2 className="section-title">Render Mode</h2>
          <div className="render-toggle">
            <button
              className={`mode-btn ${renderMode === 'canvas' ? 'active' : ''}`}
              onClick={() => onRenderModeChange?.('canvas')}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="3" width="18" height="18" rx="2" />
                <circle cx="12" cy="12" r="3" />
              </svg>
              Canvas
            </button>
            <button
              className={`mode-btn ${renderMode === 'webgl' ? 'active' : ''}`}
              onClick={() => onRenderModeChange?.('webgl')}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2" />
                <line x1="12" y1="22" x2="12" y2="15.5" />
                <polyline points="22 8.5 12 15.5 2 8.5" />
              </svg>
              WebGL
            </button>
          </div>
        </div>
      )}

      {/* Ingestion Panel */}
      <div className="section">
        {!collapsed && <h2 className="section-title">Ingestion</h2>}
        <div
          className={`upload-zone ${isDragging ? 'dragging' : ''} ${collapsed ? 'collapsed' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          onClick={() => document.getElementById('file-upload')?.click()}
          title={collapsed ? 'Drop files to ingest' : undefined}
        >
          <input
            type="file"
            id="file-upload"
            multiple
            accept=".pdf,.mp3,.wav,.mp4,.webm,.mov,.avi,.ogg,.m4a"
            onChange={handleFileSelect}
            style={{ display: 'none' }}
          />
          <div className="upload-content">
            <svg className="upload-icon" width={collapsed ? 20 : 24} height={collapsed ? 20 : 24} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            {!collapsed && (
              <>
                <span className="upload-text">
                  {isUploading ? 'Processing...' : 'Drop files here'}
                </span>
                <span className="upload-hint">PDF, Audio, Video</span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Sources List - Show icons only when collapsed */}
      <div className={`sources-list ${collapsed ? 'collapsed' : ''}`}>
        {!collapsed && <h2>Sources</h2>}
        {sources.length === 0 ? (
          !collapsed && <p className="empty-state">No sources added yet</p>
        ) : collapsed ? (
          <div className="sources-icons">
            {sources.slice(0, 5).map((source) => (
              <div
                key={source.id}
                className={`source-icon-item ${source.status}`}
                title={`${source.name} (${source.concepts?.length || 0} concepts)`}
              >
                <span className="source-icon">{getSourceIcon(source.type)}</span>
              </div>
            ))}
            {sources.length > 5 && (
              <div className="source-icon-item more">+{sources.length - 5}</div>
            )}
          </div>
        ) : (
          <ul>
            {sources.map((source) => (
              <li key={source.id} className="source-item-wrapper">
                <div
                  className={`source-item ${source.status}`}
                  onClick={() => source.concepts?.length && toggleSource(source.id)}
                >
                  <span className="source-icon">{getSourceIcon(source.type)}</span>
                  <span className="source-name">{source.name}</span>
                  <span className="source-status">
                    {source.status === 'ready' && source.concepts?.length
                      ? `${source.concepts.length} concepts`
                      : source.status}
                  </span>
                  {source.concepts?.length ? (
                    <span className="expand-icon">{expandedSource === source.id ? '▼' : '▶'}</span>
                  ) : null}
                </div>

                {/* Expanded concepts list */}
                {expandedSource === source.id && source.concepts && (
                  <div className="concepts-list">
                    {source.sourceSummary && (
                      <p className="source-summary">{source.sourceSummary}</p>
                    )}
                    {source.concepts.map((concept, idx) => (
                      <div
                        key={idx}
                        className="concept-item"
                        onClick={() => handleConceptClick(concept)}
                        title={concept.importance}
                      >
                        <span className="concept-name">{concept.name}</span>
                        <span className="concept-move">{concept.suggested_move}</span>
                      </div>
                    ))}
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>

      <style>{`
        .sidebar {
          width: var(--sidebar-width, 280px);
          background: var(--color-surface);
          border-right: 1px solid rgba(255,255,255,0.1);
          display: flex;
          flex-direction: column;
          padding: 16px;
          overflow-y: auto;
          font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif;
          transition: width 0.3s ease, padding 0.3s ease;
          position: relative;
        }
        .sidebar.collapsed {
          width: 56px;
          padding: 12px 8px;
          align-items: center;
        }
        .sidebar-header {
          margin-bottom: 20px;
          width: 100%;
          align-self: stretch;
          box-sizing: border-box;
        }
        .sidebar.collapsed .sidebar-header {
          margin-bottom: 16px;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
        }
        .collapsed-logo {
          display: flex;
          justify-content: center;
        }
        .sidebar-header h1 {
          font-size: 1.25rem;
          margin: 0;
          font-weight: 600;
          color: #fff;
        }
        .subtitle {
          color: rgba(255,255,255,0.5);
          font-size: 0.75rem;
          margin-top: 4px;
        }
        .collapse-toggle {
          width: 24px;
          height: 24px;
          background: rgba(255,255,255,0.05);
          border: 1px solid rgba(255,255,255,0.2);
          border-radius: 6px;
          color: rgba(255,255,255,0.6);
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.2s;
          flex-shrink: 0;
          margin-left: auto;
        }
        .collapse-toggle:hover {
          background: #e94560;
          border-color: #e94560;
          color: white;
        }
        .sidebar.collapsed .collapse-toggle {
          margin-top: 4px;
        }

        /* Sections */
        .section {
          margin-bottom: 20px;
        }
        .section-title {
          font-size: 0.7rem;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          color: rgba(255,255,255,0.4);
          margin: 0 0 10px 0;
        }

        /* Search Section */
        .search-section {
          margin-bottom: 16px;
          position: relative;
          z-index: 100;
        }

        /* Pattern Filters */
        .pattern-filters {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 6px;
        }
        .pattern-filters.collapsed {
          grid-template-columns: 1fr;
          gap: 4px;
        }
        .pattern-chip {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 6px 8px;
          border: 1px solid transparent;
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.15s;
        }
        .sidebar.collapsed .pattern-chip {
          padding: 6px;
          justify-content: center;
        }
        .pattern-chip:hover {
          background: rgba(255,255,255,0.08);
        }
        .pattern-chip.active {
          border-color: var(--pattern-color);
        }
        .chip-name {
          font-size: 10px;
          color: rgba(255,255,255,0.7);
        }

        /* Render Mode Toggle */
        .render-toggle {
          display: flex;
          gap: 6px;
        }
        .mode-btn {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          padding: 8px 12px;
          background: rgba(255,255,255,0.05);
          border: 1px solid transparent;
          border-radius: 6px;
          color: rgba(255,255,255,0.5);
          font-size: 12px;
          cursor: pointer;
          transition: all 0.15s;
        }
        .mode-btn:hover {
          background: rgba(255,255,255,0.08);
          color: rgba(255,255,255,0.8);
        }
        .mode-btn.active {
          background: rgba(233, 69, 96, 0.15);
          border-color: #e94560;
          color: #fff;
        }
        .mode-btn svg {
          opacity: 0.7;
        }
        .mode-btn.active svg {
          opacity: 1;
        }

        /* Upload Zone */
        .upload-zone {
          border: 2px dashed rgba(255,255,255,0.2);
          border-radius: 8px;
          padding: 20px;
          text-align: center;
          cursor: pointer;
          transition: all 0.2s;
        }
        .upload-zone.collapsed {
          padding: 10px;
          border-radius: 6px;
        }
        .upload-zone:hover, .upload-zone.dragging {
          border-color: #e94560;
          background: rgba(233, 69, 96, 0.1);
        }
        .upload-content {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
        }
        .upload-icon {
          color: rgba(255,255,255,0.4);
        }
        .upload-zone:hover .upload-icon,
        .upload-zone.dragging .upload-icon {
          color: #e94560;
        }
        .upload-text {
          font-size: 0.8rem;
          color: rgba(255,255,255,0.7);
        }
        .upload-hint {
          font-size: 0.7rem;
          color: rgba(255,255,255,0.4);
        }

        /* Sources List */
        .sources-list {
          flex: 1;
          overflow-y: auto;
        }
        .sources-list.collapsed {
          overflow: visible;
        }
        .sources-list h2 {
          font-size: 0.7rem;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          color: rgba(255,255,255,0.4);
          margin: 0 0 10px 0;
        }
        .empty-state {
          color: rgba(255,255,255,0.4);
          font-size: 0.8rem;
        }
        .sources-icons {
          display: flex;
          flex-direction: column;
          gap: 4px;
          align-items: center;
        }
        .source-icon-item {
          width: 36px;
          height: 36px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: rgba(255,255,255,0.05);
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.15s;
        }
        .source-icon-item:hover {
          background: rgba(255,255,255,0.1);
        }
        .source-icon-item.processing {
          opacity: 0.5;
        }
        .source-icon-item.more {
          font-size: 10px;
          color: rgba(255,255,255,0.5);
        }
        .source-item-wrapper {
          margin-bottom: 4px;
        }
        .source-item {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 10px;
          border-radius: 6px;
          cursor: pointer;
          background: rgba(255,255,255,0.03);
          transition: all 0.15s;
        }
        .source-item:hover {
          background: rgba(255,255,255,0.08);
        }
        .source-item.processing {
          opacity: 0.6;
        }
        .source-icon {
          font-size: 1rem;
        }
        .source-name {
          flex: 1;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          font-size: 0.8rem;
          color: #fff;
        }
        .source-status {
          font-size: 0.65rem;
          color: rgba(255,255,255,0.4);
          background: rgba(255,255,255,0.1);
          padding: 2px 6px;
          border-radius: 3px;
        }
        .expand-icon {
          font-size: 0.65rem;
          color: rgba(255,255,255,0.4);
        }
        .concepts-list {
          padding: 8px;
          background: rgba(0,0,0,0.2);
          border-radius: 6px;
          margin-top: 4px;
        }
        .source-summary {
          font-size: 0.7rem;
          color: rgba(255,255,255,0.5);
          margin-bottom: 8px;
          font-style: italic;
        }
        .concept-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 6px 8px;
          border-radius: 4px;
          cursor: pointer;
          margin-bottom: 4px;
          background: rgba(255,255,255,0.05);
          transition: all 0.15s;
        }
        .concept-item:hover {
          background: #e94560;
          color: white;
        }
        .concept-name {
          font-size: 0.75rem;
          font-weight: 500;
        }
        .concept-move {
          font-size: 0.6rem;
          color: rgba(255,255,255,0.5);
          background: rgba(0,0,0,0.2);
          padding: 2px 6px;
          border-radius: 3px;
        }
        .concept-item:hover .concept-move {
          background: rgba(0,0,0,0.3);
          color: white;
        }
      `}</style>
    </aside>
  )
}

function getSourceIcon(type: string): string {
  switch (type) {
    case 'pdf': return '📄'
    case 'audio': return '🎵'
    case 'video': return '🎬'
    default: return '📁'
  }
}

/**
 * Extract the main concept (1-2 words) from chunk content
 * Looks for capitalized terms, key phrases, or falls back to first noun phrase
 */
function extractMainConcept(content: string): string {
  const text = content.trim()

  // Common GDPR/legal concepts to look for
  const knownConcepts = [
    'Data Controller', 'Data Processor', 'Data Subject', 'Personal Data',
    'Data Protection', 'GDPR', 'Privacy', 'Consent', 'Lawful Basis',
    'Data Breach', 'DPO', 'Supervisory Authority', 'Data Transfer',
    'Right to Access', 'Right to Erasure', 'Data Portability',
    'Privacy by Design', 'Impact Assessment', 'Processing',
    'European Commission', 'European Parliament', 'European Council',
    'Charter of Fundamental Rights', 'Treaty of Lisbon', 'Convention 108',
    'Accountability', 'Transparency', 'Purpose Limitation', 'Data Minimisation',
    'Storage Limitation', 'Integrity', 'Confidentiality'
  ]

  // Check for known concepts first (case-insensitive)
  for (const concept of knownConcepts) {
    if (text.toLowerCase().includes(concept.toLowerCase())) {
      return concept
    }
  }

  // Look for capitalized multi-word terms (likely proper nouns/concepts)
  const capitalizedPattern = /\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b/g
  const capitalizedMatches = text.match(capitalizedPattern)
  if (capitalizedMatches && capitalizedMatches.length > 0) {
    // Return the first capitalized phrase (max 3 words)
    const phrase = capitalizedMatches[0]
    const words = phrase.split(/\s+/)
    return words.slice(0, 3).join(' ')
  }

  // Look for bold or quoted terms (often key concepts)
  const quotedPattern = /"([^"]+)"|'([^']+)'|\*\*([^*]+)\*\*/
  const quotedMatch = text.match(quotedPattern)
  if (quotedMatch) {
    const term = quotedMatch[1] || quotedMatch[2] || quotedMatch[3]
    if (term && term.split(/\s+/).length <= 3) {
      return term
    }
  }

  // Extract first significant noun phrase (skip common words)
  const skipWords = new Set([
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'must', 'shall', 'can', 'this', 'that',
    'these', 'those', 'it', 'its', 'of', 'in', 'on', 'at', 'to', 'for',
    'with', 'by', 'from', 'as', 'and', 'or', 'but', 'if', 'then', 'so'
  ])

  const words = text.split(/\s+/)
  const significantWords: string[] = []

  for (const word of words) {
    const cleanWord = word.replace(/[^a-zA-Z]/g, '')
    if (cleanWord.length > 2 && !skipWords.has(cleanWord.toLowerCase())) {
      significantWords.push(cleanWord)
      if (significantWords.length >= 2) break
    }
  }

  if (significantWords.length > 0) {
    return significantWords.join(' ')
  }

  // Fallback: first 2 words
  return words.slice(0, 2).join(' ')
}
