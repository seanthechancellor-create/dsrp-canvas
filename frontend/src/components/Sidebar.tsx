import { useState } from 'react'
import { useSourceStore, ExtractedConcept } from '../stores/sourceStore'

interface SidebarProps {
  onConceptSelect?: (concept: string, move: string) => void
}

export function Sidebar({ onConceptSelect }: SidebarProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [expandedSource, setExpandedSource] = useState<string | null>(null)
  const { sources, addSource, isUploading } = useSourceStore()

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
          <span className="upload-icon">📁</span>
          <span className="upload-text">
            {isUploading ? 'Uploading...' : 'Click to browse or drop files'}
          </span>
          <span className="upload-hint">PDF, Audio, Video</span>
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
          border-right: 1px solid var(--color-primary);
          display: flex;
          flex-direction: column;
          padding: 16px;
          overflow-y: auto;
        }
        .sidebar-header {
          margin-bottom: 24px;
        }
        .sidebar-header h1 {
          font-size: 1.5rem;
          margin-bottom: 4px;
        }
        .subtitle {
          color: var(--color-text-muted);
          font-size: 0.875rem;
        }
        .upload-zone {
          border: 2px dashed var(--color-primary);
          border-radius: 8px;
          padding: 24px;
          text-align: center;
          cursor: pointer;
          transition: all 0.2s;
          margin-bottom: 24px;
        }
        .upload-zone:hover, .upload-zone.dragging {
          border-color: var(--color-accent);
          background: rgba(233, 69, 96, 0.1);
        }
        .upload-content {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 4px;
        }
        .upload-icon {
          font-size: 1.5rem;
        }
        .upload-text {
          font-size: 0.875rem;
          color: var(--color-text);
        }
        .upload-hint {
          font-size: 0.75rem;
          color: var(--color-text-muted);
        }
        .sources-list {
          flex: 1;
          overflow-y: auto;
        }
        .sources-list h2 {
          font-size: 1rem;
          margin-bottom: 12px;
          color: var(--color-text-muted);
        }
        .empty-state {
          color: var(--color-text-muted);
          font-size: 0.875rem;
        }
        .source-item-wrapper {
          margin-bottom: 4px;
        }
        .source-item {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px;
          border-radius: 4px;
          cursor: pointer;
        }
        .source-item:hover {
          background: var(--color-primary);
        }
        .source-item.processing {
          opacity: 0.7;
        }
        .source-icon {
          font-size: 1.25rem;
        }
        .source-name {
          flex: 1;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          font-size: 0.875rem;
        }
        .source-status {
          font-size: 0.7rem;
          color: var(--color-text-muted);
        }
        .expand-icon {
          font-size: 0.7rem;
          color: var(--color-text-muted);
        }
        .concepts-list {
          padding: 8px 8px 8px 24px;
          background: rgba(0,0,0,0.2);
          border-radius: 4px;
          margin-top: 4px;
        }
        .source-summary {
          font-size: 0.75rem;
          color: var(--color-text-muted);
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
        }
        .concept-item:hover {
          background: var(--color-accent);
          color: white;
        }
        .concept-name {
          font-size: 0.8rem;
          font-weight: 500;
        }
        .concept-move {
          font-size: 0.65rem;
          color: var(--color-text-muted);
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
