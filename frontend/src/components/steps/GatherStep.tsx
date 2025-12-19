/**
 * GatherStep - Step 1: Upload and process source materials
 *
 * Clean, focused interface for uploading PDFs, audio, video, or text.
 * Shows upload progress and extracted text preview.
 */

import { useState, useCallback } from 'react'

interface GatherStepProps {
  onComplete: (result: {
    sessionId: string
    sourceName: string
    sourceType: string
    text: string
    textLength: number
    chunks: number
  }) => void
}

export function GatherStep({ onComplete }: GatherStepProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [extractedText, setExtractedText] = useState('')
  const [error, setError] = useState<string | null>(null)

  const processFile = useCallback(async (selectedFile: File) => {
    setFile(selectedFile)
    setIsProcessing(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)

      // Upload and extract text
      const response = await fetch('/api/sources/upload', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Failed to process file')
      }

      const data = await response.json()

      // For now, use a simple text extraction or the returned data
      const text = data.extracted_text || data.text || `Content from ${selectedFile.name}`
      setExtractedText(text)

      // Create study session
      const sessionResponse = await fetch('/api/study/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_id: data.id || `source-${Date.now()}`,
          source_name: selectedFile.name,
          source_type: getFileType(selectedFile.name),
        }),
      })

      if (!sessionResponse.ok) {
        throw new Error('Failed to create study session')
      }

      const session = await sessionResponse.json()

      // Complete gather step
      const gatherResponse = await fetch('/api/study/steps/gather', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: session.session_id,
          text: text,
        }),
      })

      if (!gatherResponse.ok) {
        throw new Error('Failed to complete gather step')
      }

      const gatherResult = await gatherResponse.json()

      onComplete({
        sessionId: session.session_id,
        sourceName: selectedFile.name,
        sourceType: getFileType(selectedFile.name),
        text: text,
        textLength: gatherResult.text_length || text.length,
        chunks: gatherResult.chunks || 1,
      })
    } catch (err) {
      console.error('File processing error:', err)
      setError(err instanceof Error ? err.message : 'Failed to process file')
    } finally {
      setIsProcessing(false)
    }
  }, [onComplete])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile) {
      processFile(droppedFile)
    }
  }, [processFile])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      processFile(selectedFile)
    }
  }, [processFile])

  // Demo mode: use sample text
  const handleDemoMode = useCallback(async () => {
    setIsProcessing(true)
    setError(null)

    try {
      const demoText = `DSRP Theory Overview

DSRP is a theory of cognition developed by Dr. Derek Cabrera at Cornell University. It stands for Distinctions, Systems, Relationships, and Perspectives - the four patterns of thinking that underlie all human cognition.

Distinctions (D): The ability to differentiate between and among things. Every distinction has an identity (what something is) and an other (what it is not).

Systems (S): The ability to organize things into groups or wholes with parts. Every system has parts and a whole, and every part can be a whole with its own parts.

Relationships (R): The ability to identify connections between things. Every relationship has an action and a reaction.

Perspectives (P): The ability to see things from different points of view. Every perspective has a point (the viewer) and a view (what is seen).

The 8 Moves are cognitive tools based on DSRP:
1. Is/Is Not - Define what something is and is not
2. Zoom In - Examine the parts of something
3. Zoom Out - Examine what something is part of
4. Part Party - Identify parts and their relationships
5. RDS Barbell - Relate, Distinguish, Systematize
6. P-Circle - Map multiple perspectives
7. WoC - Web of Causality (forward effects)
8. WAoC - Web of Anticausality (root causes)`

      // Create study session
      const sessionResponse = await fetch('/api/study/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_id: `demo-${Date.now()}`,
          source_name: 'DSRP Theory Demo',
          source_type: 'text',
        }),
      })

      const session = await sessionResponse.json()

      // Complete gather step
      await fetch('/api/study/steps/gather', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: session.session_id,
          text: demoText,
        }),
      })

      setExtractedText(demoText)
      setFile(null)

      onComplete({
        sessionId: session.session_id,
        sourceName: 'DSRP Theory Demo',
        sourceType: 'text',
        text: demoText,
        textLength: demoText.length,
        chunks: 1,
      })
    } catch (err) {
      setError('Failed to start demo mode')
    } finally {
      setIsProcessing(false)
    }
  }, [onComplete])

  return (
    <div className="gather-step">
      <div className="step-header">
        <div className="step-icon">1</div>
        <div className="step-info">
          <h2>Gather Sources</h2>
          <p>Upload a document, audio, or video to begin your study session</p>
        </div>
      </div>

      {!file && !extractedText ? (
        <>
          <div
            className={`upload-zone ${isDragging ? 'dragging' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            onClick={() => document.getElementById('file-input')?.click()}
          >
            <input
              type="file"
              id="file-input"
              accept=".pdf,.txt,.md,.mp3,.wav,.mp4,.webm"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />

            <div className="upload-content">
              <div className="upload-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
              </div>
              <h3>Drop your file here</h3>
              <p>or click to browse</p>
              <div className="supported-types">
                <span>PDF</span>
                <span>Text</span>
                <span>Audio</span>
                <span>Video</span>
              </div>
            </div>
          </div>

          <div className="divider">
            <span>or</span>
          </div>

          <button type="button" className="demo-btn" onClick={handleDemoMode} disabled={isProcessing}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polygon points="5 3 19 12 5 21 5 3" />
            </svg>
            {isProcessing ? 'Loading...' : 'Try Demo Mode'}
          </button>
        </>
      ) : (
        <div className="file-preview">
          {isProcessing ? (
            <div className="processing">
              <div className="spinner" />
              <p>Processing {file?.name || 'content'}...</p>
            </div>
          ) : (
            <>
              <div className="file-info">
                <span className="file-icon">{getFileIcon(file?.name || 'text')}</span>
                <span className="file-name">{file?.name || 'Demo Content'}</span>
                <button type="button" className="clear-btn" onClick={() => { setFile(null); setExtractedText(''); }}>
                  Change
                </button>
              </div>

              {extractedText && (
                <div className="text-preview">
                  <h4>Extracted Content Preview</h4>
                  <pre>{extractedText.slice(0, 500)}{extractedText.length > 500 ? '...' : ''}</pre>
                  <span className="char-count">{extractedText.length.toLocaleString()} characters</span>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {error && (
        <div className="error-message">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          {error}
        </div>
      )}

      <style>{`
        .gather-step {
          max-width: 600px;
          margin: 0 auto;
          padding-bottom: 24px;
        }

        .step-header {
          display: flex;
          align-items: center;
          gap: 16px;
          margin-bottom: 24px;
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

        .step-info h2 {
          margin: 0;
          font-size: 1.5rem;
        }

        .step-info p {
          margin: 4px 0 0;
          color: rgba(255, 255, 255, 0.6);
        }

        .upload-zone {
          border: 2px dashed rgba(255, 255, 255, 0.2);
          border-radius: 16px;
          padding: 32px;
          text-align: center;
          cursor: pointer;
          transition: all 0.3s;
        }

        .upload-zone:hover,
        .upload-zone.dragging {
          border-color: #e94560;
          background: rgba(233, 69, 96, 0.1);
        }

        .upload-icon {
          color: rgba(255, 255, 255, 0.4);
          margin-bottom: 16px;
        }

        .upload-zone:hover .upload-icon,
        .upload-zone.dragging .upload-icon {
          color: #e94560;
        }

        .upload-content h3 {
          margin: 0 0 8px;
          font-size: 1.25rem;
        }

        .upload-content p {
          margin: 0;
          color: rgba(255, 255, 255, 0.5);
        }

        .supported-types {
          display: flex;
          gap: 8px;
          justify-content: center;
          margin-top: 16px;
        }

        .supported-types span {
          padding: 4px 12px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 4px;
          font-size: 0.75rem;
          color: rgba(255, 255, 255, 0.6);
        }

        .divider {
          display: flex;
          align-items: center;
          gap: 16px;
          margin: 16px 0;
          color: rgba(255, 255, 255, 0.4);
        }

        .divider::before,
        .divider::after {
          content: '';
          flex: 1;
          height: 1px;
          background: rgba(255, 255, 255, 0.1);
        }

        .demo-btn {
          width: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          padding: 16px;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.2);
          border-radius: 12px;
          color: rgba(255, 255, 255, 0.8);
          font-size: 1rem;
          cursor: pointer;
          transition: all 0.2s;
        }

        .demo-btn:hover {
          background: rgba(255, 255, 255, 0.1);
          border-color: rgba(255, 255, 255, 0.3);
        }

        .file-preview {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 12px;
          padding: 24px;
        }

        .processing {
          text-align: center;
          padding: 32px;
        }

        .spinner {
          width: 48px;
          height: 48px;
          border: 3px solid rgba(233, 69, 96, 0.2);
          border-top-color: #e94560;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin: 0 auto 16px;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .file-info {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .file-icon {
          font-size: 1.5rem;
        }

        .file-name {
          flex: 1;
          font-weight: 500;
        }

        .clear-btn {
          padding: 8px 16px;
          background: transparent;
          border: 1px solid rgba(255, 255, 255, 0.2);
          border-radius: 6px;
          color: rgba(255, 255, 255, 0.6);
          cursor: pointer;
          transition: all 0.2s;
        }

        .clear-btn:hover {
          border-color: #e94560;
          color: #e94560;
        }

        .text-preview {
          margin-top: 20px;
          padding-top: 20px;
          border-top: 1px solid rgba(255, 255, 255, 0.1);
        }

        .text-preview h4 {
          margin: 0 0 12px;
          font-size: 0.85rem;
          color: rgba(255, 255, 255, 0.6);
        }

        .text-preview pre {
          background: rgba(0, 0, 0, 0.2);
          padding: 16px;
          border-radius: 8px;
          font-size: 0.8rem;
          line-height: 1.5;
          white-space: pre-wrap;
          word-break: break-word;
          max-height: 200px;
          overflow-y: auto;
        }

        .char-count {
          display: block;
          margin-top: 8px;
          font-size: 0.75rem;
          color: rgba(255, 255, 255, 0.4);
        }

        .error-message {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-top: 16px;
          padding: 12px 16px;
          background: rgba(244, 67, 54, 0.1);
          border: 1px solid rgba(244, 67, 54, 0.3);
          border-radius: 8px;
          color: #f44336;
          font-size: 0.9rem;
        }
      `}</style>
    </div>
  )
}

function getFileType(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase()
  if (['pdf'].includes(ext || '')) return 'pdf'
  if (['mp3', 'wav', 'm4a', 'ogg'].includes(ext || '')) return 'audio'
  if (['mp4', 'webm', 'mov', 'avi'].includes(ext || '')) return 'video'
  return 'text'
}

function getFileIcon(filename: string): string {
  const type = getFileType(filename)
  switch (type) {
    case 'pdf': return '📄'
    case 'audio': return '🎵'
    case 'video': return '🎬'
    default: return '📝'
  }
}
