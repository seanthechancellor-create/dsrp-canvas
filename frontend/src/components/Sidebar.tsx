import { useState } from 'react'
import { useSourceStore, ExtractedConcept } from '../stores/sourceStore'
import { DSRP_PATTERNS, DSRPIcon } from './DSRPIcons'

interface SidebarProps {
  onConceptSelect?: (concept: string, move: string) => void
  onPatternFilter?: (patterns: string[]) => void
  renderMode?: 'canvas' | 'webgl'
  onRenderModeChange?: (mode: 'canvas' | 'webgl') => void
}

export function Sidebar({ onConceptSelect, onPatternFilter, renderMode = 'canvas', onRenderModeChange }: SidebarProps) {
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

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h1>DSRP Canvas</h1>
        <span className="subtitle">4-8-3 Knowledge Analysis</span>
      </div>

      {/* Pattern Filters */}
      <div className="section">
        <h2 className="section-title">Patterns</h2>
        <div className="pattern-filters">
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
              <span className="chip-name">{pattern.name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Render Mode Toggle */}
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

      {/* Ingestion Panel */}
      <div className="section">
        <h2 className="section-title">Ingestion</h2>
        <div
          className={`upload-zone ${isDragging ? 'dragging' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          onClick={() => document.getElementById('file-upload')?.click()}
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
            <svg className="upload-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            <span className="upload-text">
              {isUploading ? 'Processing...' : 'Drop files here'}
            </span>
            <span className="upload-hint">PDF, Audio, Video</span>
          </div>
        </div>
      </div>

      <div className="sources-list">
        <h2>Sources</h2>
        {sources.length === 0 ? (
          <p className="empty-state">No sources added yet</p>
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
          width: var(--sidebar-width);
          background: var(--color-surface);
          border-right: 1px solid rgba(255,255,255,0.1);
          display: flex;
          flex-direction: column;
          padding: 16px;
          overflow-y: auto;
          font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        .sidebar-header {
          margin-bottom: 20px;
        }
        .sidebar-header h1 {
          font-size: 1.25rem;
          margin: 0 0 4px 0;
          font-weight: 600;
          color: #fff;
        }
        .subtitle {
          color: rgba(255,255,255,0.5);
          font-size: 0.75rem;
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

        /* Pattern Filters */
        .pattern-filters {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 6px;
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
