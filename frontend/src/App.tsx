import { useState, useCallback, Component, ReactNode } from 'react'
import { Sidebar } from './components/Sidebar'
import { DSRPPanel } from './components/DSRPPanel'
import { DSRPGraph } from './components/DSRPGraph'
import { DetailsDrawer } from './components/DetailsDrawer'

// Error boundary
class ErrorBoundary extends Component<{ children: ReactNode }, { hasError: boolean; error: Error | null }> {
  constructor(props: { children: ReactNode }) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 20, color: '#e94560', background: '#1a1a2e', minHeight: '100vh' }}>
          <h2>Something went wrong</h2>
          <pre style={{ whiteSpace: 'pre-wrap', fontSize: 12 }}>
            {this.state.error?.message}
          </pre>
          <button onClick={() => window.location.reload()} style={{ marginTop: 20, padding: '10px 20px' }}>
            Reload
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

interface AnalysisResult {
  pattern: string
  elements: Record<string, unknown>
  move: string
  reasoning?: string
}

interface ConceptMapNode {
  id: string
  label: string
  fullText: string
  pattern: string
  isMain?: boolean
}

interface ConceptMapEdge {
  id: string
  source: string
  target: string
  dynamic?: string
}

function AppContent() {
  const [concept, setConcept] = useState<string>('')
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [showConceptMap, setShowConceptMap] = useState(false)
  const [conceptMap, setConceptMap] = useState<{ nodes: ConceptMapNode[]; edges: ConceptMapEdge[] }>({
    nodes: [],
    edges: [],
  })
  const [drillDownConcept, setDrillDownConcept] = useState<string | null>(null)
  const [selectedMove, setSelectedMove] = useState<string>('is-is-not')
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)

  // Add nodes and edges to the cumulative concept map
  const addToConceptMap = useCallback((newConcept: string, newResult: AnalysisResult) => {
    setConceptMap(prev => {
      const nodes = [...prev.nodes]
      const edges = [...prev.edges]

      // Create a unique ID for the main concept
      const mainId = `concept-${newConcept.toLowerCase().replace(/\s+/g, '-')}`

      // Add main concept if not exists
      if (!nodes.find(n => n.id === mainId)) {
        nodes.push({
          id: mainId,
          label: newConcept,
          fullText: newResult.reasoning || newConcept,
          pattern: newResult.pattern,
          isMain: true,
        })
      }

      const elements = newResult.elements
      const move = newResult.move

      // Add related concepts based on move type
      if (move === 'is-is-not') {
        if (elements.identity) {
          const text = elements.identity as string
          const nodeId = `is-${mainId}`
          if (!nodes.find(n => n.id === nodeId)) {
            nodes.push({
              id: nodeId,
              label: 'Identity',
              fullText: text,
              pattern: 'D',
            })
            edges.push({ id: `e-${nodeId}`, source: nodeId, target: mainId, dynamic: '=' })
          }
        }
        if (elements.other) {
          const text = elements.other as string
          const nodeId = `not-${mainId}`
          if (!nodes.find(n => n.id === nodeId)) {
            nodes.push({
              id: nodeId,
              label: 'Other',
              fullText: text,
              pattern: 'D',
            })
            edges.push({ id: `e-${nodeId}`, source: mainId, target: nodeId, dynamic: '⇔' })
          }
        }
      } else if (move === 'zoom-in' && Array.isArray(elements.parts)) {
        elements.parts.slice(0, 4).forEach((part: string, i: number) => {
          const nodeId = `part-${i}-${mainId}`
          if (!nodes.find(n => n.id === nodeId)) {
            nodes.push({
              id: nodeId,
              label: part,
              fullText: part,
              pattern: 'S',
            })
            edges.push({ id: `e-${nodeId}`, source: mainId, target: nodeId, dynamic: '⇔' })
          }
        })
      } else if (move === 'zoom-out' && elements.whole) {
        const whole = elements.whole as string
        const nodeId = `whole-${mainId}`
        if (!nodes.find(n => n.id === nodeId)) {
          nodes.push({
            id: nodeId,
            label: whole,
            fullText: whole,
            pattern: 'S',
            isMain: true,
          })
          edges.push({ id: `e-${nodeId}`, source: nodeId, target: mainId, dynamic: '⇔' })
        }
      } else if (move === 'p-circle' && Array.isArray(elements.perspectives)) {
        elements.perspectives.slice(0, 4).forEach((persp: any, i: number) => {
          const label = typeof persp === 'string' ? persp : persp.point || String(persp)
          const nodeId = `persp-${i}-${mainId}`
          if (!nodes.find(n => n.id === nodeId)) {
            nodes.push({
              id: nodeId,
              label,
              fullText: typeof persp === 'object' ? persp.view || label : label,
              pattern: 'P',
            })
            edges.push({ id: `e-${nodeId}`, source: nodeId, target: mainId, dynamic: '✷' })
          }
        })
      } else if (move === 'rds-barbell' && Array.isArray(elements.reactions)) {
        elements.reactions.slice(0, 4).forEach((reaction: string, i: number) => {
          const nodeId = `react-${i}-${mainId}`
          if (!nodes.find(n => n.id === nodeId)) {
            nodes.push({
              id: nodeId,
              label: reaction,
              fullText: reaction,
              pattern: 'R',
            })
            edges.push({ id: `e-${nodeId}`, source: mainId, target: nodeId, dynamic: '⇔' })
          }
        })
      }

      return { nodes, edges }
    })
  }, [])

  const handleAnalysisComplete = useCallback((newConcept: string, newResult: AnalysisResult) => {
    setConcept(newConcept)
    setResult(newResult)
    addToConceptMap(newConcept, newResult)
    setDrillDownConcept(null) // Clear drill-down after analysis
    setIsDrawerOpen(true) // Open drawer to show analysis details
  }, [addToConceptMap])

  const handleNodeClick = useCallback((nodeId: string, label: string) => {
    // When clicking "Analyze" button in tooltip, trigger drill-down
    if (nodeId === 'drill') {
      setDrillDownConcept(label)
    }
  }, [])

  // Handle concept selection from sidebar (PDF extracted concepts)
  const handleConceptSelect = useCallback((conceptName: string, move: string) => {
    setSelectedMove(move)
    setDrillDownConcept(conceptName)
  }, [])

  const handleClear = useCallback(() => {
    setConcept('')
    setResult(null)
    setIsDrawerOpen(false)
  }, [])

  const handleDrawerDrillDown = useCallback((conceptName: string) => {
    setDrillDownConcept(conceptName)
  }, [])

  const handleDrawerClose = useCallback(() => {
    setIsDrawerOpen(false)
  }, [])

  const handleClearMap = useCallback(() => {
    setConceptMap({ nodes: [], edges: [] })
  }, [])

  const toggleView = useCallback(() => {
    setShowConceptMap(prev => !prev)
  }, [])

  return (
    <div className="app-container">
      <Sidebar onConceptSelect={handleConceptSelect} />
      <main className="canvas-container">
        {/* View toggle and map controls */}
        <div className="view-controls">
          <button
            className={`view-toggle ${!showConceptMap ? 'active' : ''}`}
            onClick={toggleView}
          >
            Current Analysis
          </button>
          <button
            className={`view-toggle ${showConceptMap ? 'active' : ''}`}
            onClick={toggleView}
          >
            Concept Map ({conceptMap.nodes.length})
          </button>
          {showConceptMap && conceptMap.nodes.length > 0 && (
            <button className="clear-map-btn" onClick={handleClearMap}>
              Clear Map
            </button>
          )}
        </div>

        <DSRPGraph
          concept={concept}
          result={result}
          onNodeClick={handleNodeClick}
          conceptMap={conceptMap}
          showConceptMap={showConceptMap}
        />
      </main>
      <DSRPPanel
        onAnalysisComplete={handleAnalysisComplete}
        onClear={handleClear}
        drillDownConcept={drillDownConcept}
        initialMove={selectedMove}
      />

      {/* Details Drawer - shows when analysis completes */}
      <DetailsDrawer
        isOpen={isDrawerOpen}
        onClose={handleDrawerClose}
        concept={concept}
        result={result}
        onDrillDown={handleDrawerDrillDown}
      />

      <style>{`
        .app-container {
          display: flex;
          width: 100vw;
          height: 100vh;
          background: var(--color-bg, #1a1a2e);
          overflow: hidden;
        }
        .canvas-container {
          flex: 1;
          position: relative;
          overflow: hidden;
        }
        .view-controls {
          position: absolute;
          top: 10px;
          left: 50%;
          transform: translateX(-50%);
          display: flex;
          gap: 8px;
          z-index: 100;
          background: rgba(255,255,255,0.95);
          padding: 6px;
          border-radius: 8px;
          box-shadow: 0 2px 10px rgba(0,0,0,0.15);
        }
        .view-toggle {
          padding: 8px 16px;
          border: none;
          border-radius: 6px;
          font-size: 13px;
          font-weight: 500;
          cursor: pointer;
          background: #e0e0e0;
          color: #555;
          transition: all 0.2s;
          font-family: Calibri, -apple-system, sans-serif;
        }
        .view-toggle:hover {
          background: #d0d0d0;
        }
        .view-toggle.active {
          background: #1976D2;
          color: white;
        }
        .clear-map-btn {
          padding: 8px 12px;
          border: none;
          border-radius: 6px;
          font-size: 13px;
          cursor: pointer;
          background: #f44336;
          color: white;
          transition: all 0.2s;
          font-family: Calibri, -apple-system, sans-serif;
        }
        .clear-map-btn:hover {
          background: #d32f2f;
        }
      `}</style>
    </div>
  )
}

export default function App() {
  return (
    <ErrorBoundary>
      <AppContent />
    </ErrorBoundary>
  )
}
