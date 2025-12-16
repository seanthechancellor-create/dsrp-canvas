/**
 * DSRPGraph - G6 v5 based graph visualization for DSRP Canvas
 *
 * Features:
 * - Rounded rectangle nodes with proper spacing
 * - 3 Dynamics labels (= equality, ⇔ co-implication, ✷ simultaneity)
 * - Click to show full text and drill down
 * - Cumulative concept map
 */

import { useEffect, useRef, useCallback, useState } from 'react'
import { Graph } from '@antv/g6'

// DSRP Color scheme
const DSRP_COLORS = {
  D: { fill: '#E3F2FD', stroke: '#1976D2', text: '#0D47A1' },
  S: { fill: '#E8F5E9', stroke: '#388E3C', text: '#1B5E20' },
  R: { fill: '#FFF3E0', stroke: '#F57C00', text: '#E65100' },
  P: { fill: '#F3E5F5', stroke: '#7B1FA2', text: '#4A148C' },
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

interface DSRPGraphProps {
  concept: string
  result: AnalysisResult | null
  onNodeClick?: (nodeId: string, label: string) => void
  conceptMap?: { nodes: ConceptMapNode[]; edges: ConceptMapEdge[] }
  showConceptMap?: boolean
}

interface SelectionState {
  visible: boolean
  title: string
  content: string
}

export function DSRPGraph({ concept, result, onNodeClick, conceptMap, showConceptMap }: DSRPGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const graphRef = useRef<Graph | null>(null)
  const [selection, setSelection] = useState<SelectionState>({
    visible: false,
    title: '',
    content: '',
  })

  // Resizing state
  const [panelHeight, setPanelHeight] = useState(250)
  const [isResizing, setIsResizing] = useState(false)

  // ... (buildGraphData and useEffect logic remains mostly the same, ensuring they don't break) ...

  // Build graph data from analysis result
  const buildGraphData = useCallback(() => {
    // If showing concept map, use that data
    if (showConceptMap && conceptMap) {
      const nodes = conceptMap.nodes.map(node => ({
        id: node.id,
        data: {
          label: node.label.length > 16 ? node.label.slice(0, 15) + '…' : node.label,
          fullLabel: node.label,
          fullText: node.fullText,
          pattern: node.pattern,
          isMain: node.isMain,
          fill: DSRP_COLORS[node.pattern as keyof typeof DSRP_COLORS]?.fill || DSRP_COLORS.D.fill,
          stroke: DSRP_COLORS[node.pattern as keyof typeof DSRP_COLORS]?.stroke || DSRP_COLORS.D.stroke,
          textColor: DSRP_COLORS[node.pattern as keyof typeof DSRP_COLORS]?.text || DSRP_COLORS.D.text,
        },
      }))
      const edges = conceptMap.edges.map(edge => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        data: { dynamic: edge.dynamic || '' },
      }))
      return { nodes, edges }
    }

    const nodes: any[] = []
    const edges: any[] = []

    if (!concept) {
      return { nodes: [], edges: [] }
    }

    const pattern = (result?.pattern as keyof typeof DSRP_COLORS) || 'D'
    const colors = DSRP_COLORS[pattern]

    // Main concept node
    nodes.push({
      id: 'main',
      data: {
        label: concept.length > 18 ? concept.slice(0, 17) + '…' : concept,
        fullLabel: concept,
        fullText: concept,
        pattern,
        isMain: true,
        fill: colors.fill,
        stroke: colors.stroke,
        textColor: colors.text,
      },
    })

    if (!result) {
      return { nodes, edges }
    }

    const elements = result.elements
    const move = result.move

    if (move === 'is-is-not') {
      if (elements.identity) {
        const concepts = extractConcepts(elements.identity as string, 4)
        concepts.forEach((item, i) => {
          const nodeColors = DSRP_COLORS.D
          nodes.push({
            id: `is-${i}`,
            data: {
              label: item.length > 14 ? item.slice(0, 13) + '…' : item,
              fullLabel: item,
              fullText: elements.identity as string,
              pattern: 'D',
              fill: nodeColors.fill,
              stroke: nodeColors.stroke,
              textColor: nodeColors.text,
            },
          })
          edges.push({
            id: `e-is-${i}`,
            source: `is-${i}`,
            target: 'main',
            data: { dynamic: '=' },
          })
        })
      }
      if (elements.other) {
        const concepts = extractConcepts(elements.other as string, 4)
        concepts.forEach((item, i) => {
          nodes.push({
            id: `not-${i}`,
            data: {
              label: item.length > 14 ? item.slice(0, 13) + '…' : item,
              fullLabel: item,
              fullText: elements.other as string,
              pattern: 'D',
              fill: '#FFF3E0',
              stroke: '#F57C00',
              textColor: '#E65100',
            },
          })
          edges.push({
            id: `e-not-${i}`,
            source: 'main',
            target: `not-${i}`,
            data: { dynamic: '⇔' },
          })
        })
      }

    } else if (move === 'zoom-in' && Array.isArray(elements.parts)) {
      const nodeColors = DSRP_COLORS.S
      elements.parts.slice(0, 4).forEach((part: string, i: number) => {
        nodes.push({
          id: `part-${i}`,
          data: {
            label: part.length > 14 ? part.slice(0, 13) + '…' : part,
            fullLabel: part,
            fullText: part,
            pattern: 'S',
            fill: nodeColors.fill,
            stroke: nodeColors.stroke,
            textColor: nodeColors.text,
          },
        })
        edges.push({
          id: `e-part-${i}`,
          source: 'main',
          target: `part-${i}`,
          data: { dynamic: '⇔' },
        })
      })

    } else if (move === 'zoom-out' && elements.whole) {
      const wholeLabel = typeof elements.whole === 'string' ? elements.whole : String(elements.whole)
      const nodeColors = DSRP_COLORS.S
      nodes.push({
        id: 'whole',
        data: {
          label: wholeLabel.length > 18 ? wholeLabel.slice(0, 17) + '…' : wholeLabel,
          fullLabel: wholeLabel,
          fullText: wholeLabel,
          pattern: 'S',
          isMain: true,
          fill: nodeColors.fill,
          stroke: nodeColors.stroke,
          textColor: nodeColors.text,
        },
      })
      edges.push({
        id: 'e-whole',
        source: 'whole',
        target: 'main',
        data: { dynamic: '⇔' },
      })

    } else if (move === 'p-circle' && Array.isArray(elements.perspectives)) {
      const nodeColors = DSRP_COLORS.P
      elements.perspectives.slice(0, 4).forEach((persp: any, i: number) => {
        const label = typeof persp === 'string' ? persp : persp.point || String(persp)
        const view = typeof persp === 'object' ? persp.view : ''
        nodes.push({
          id: `persp-${i}`,
          data: {
            label: label.length > 14 ? label.slice(0, 13) + '…' : label,
            fullLabel: label,
            fullText: view || label,
            pattern: 'P',
            fill: nodeColors.fill,
            stroke: nodeColors.stroke,
            textColor: nodeColors.text,
          },
        })
        edges.push({
          id: `e-persp-${i}`,
          source: `persp-${i}`,
          target: 'main',
          data: { dynamic: '✷' },
        })
      })

    } else if (move === 'rds-barbell' && Array.isArray(elements.reactions)) {
      const nodeColors = DSRP_COLORS.R
      elements.reactions.slice(0, 4).forEach((reaction: string, i: number) => {
        nodes.push({
          id: `react-${i}`,
          data: {
            label: reaction.length > 14 ? reaction.slice(0, 13) + '…' : reaction,
            fullLabel: reaction,
            fullText: reaction,
            pattern: 'R',
            fill: nodeColors.fill,
            stroke: nodeColors.stroke,
            textColor: nodeColors.text,
          },
        })
        edges.push({
          id: `e-react-${i}`,
          source: 'main',
          target: `react-${i}`,
          data: { dynamic: '⇔' },
        })
      })

    } else if (move === 'part-party' && Array.isArray(elements.parts)) {
      const nodeColors = DSRP_COLORS.S
      const partIds: string[] = []
      elements.parts.slice(0, 4).forEach((part: string, i: number) => {
        const id = `part-${i}`
        partIds.push(id)
        nodes.push({
          id,
          data: {
            label: part.length > 14 ? part.slice(0, 13) + '…' : part,
            fullLabel: part,
            fullText: part,
            pattern: 'S',
            fill: nodeColors.fill,
            stroke: nodeColors.stroke,
            textColor: nodeColors.text,
          },
        })
        edges.push({
          id: `e-main-${id}`,
          source: 'main',
          target: id,
          data: { dynamic: '=' },
        })
      })
      partIds.forEach((id, i) => {
        const nextId = partIds[(i + 1) % partIds.length]
        edges.push({
          id: `e-${id}-${nextId}`,
          source: id,
          target: nextId,
          data: {},
        })
      })
    }

    return { nodes, edges }
  }, [concept, result, conceptMap, showConceptMap])

  // Initialize graph
  useEffect(() => {
    if (!containerRef.current) return

    const container = containerRef.current
    const width = container.clientWidth || 700
    const height = container.clientHeight || 500

    if (graphRef.current) {
      graphRef.current.destroy()
      graphRef.current = null
    }

    const data = buildGraphData()

    if (data.nodes.length === 0) {
      return
    }

    const move = result?.move || 'is-is-not'
    const nodeCount = data.nodes.length

    // Choose layout based on move and node count
    let layoutConfig: any = {
      type: 'dagre',
      rankdir: 'LR',
      nodesep: 80,
      ranksep: 150,
    }

    if (showConceptMap && nodeCount > 5) {
      layoutConfig = { type: 'force', preventOverlap: true, nodeSpacing: 100 }
    } else if (move === 'zoom-in' || move === 'zoom-out') {
      layoutConfig = { type: 'dagre', rankdir: 'TB', nodesep: 60, ranksep: 120 }
    } else if (move === 'p-circle' || move === 'part-party') {
      layoutConfig = { type: 'circular', radius: 180 }
    }

    try {
      const graph = new Graph({
        container,
        width,
        height,
        data,
        layout: layoutConfig,
        autoFit: 'view',
        padding: 60,
        animation: true,
        node: {
          type: 'rect',
          style: {
            size: (d: any) => d.data?.isMain ? [150, 40] : [120, 32],
            fill: (d: any) => d.data?.fill || '#E3F2FD',
            stroke: (d: any) => d.data?.stroke || '#1976D2',
            lineWidth: (d: any) => d.data?.isMain ? 2 : 1.5,
            radius: 8,
            cursor: 'pointer',
            shadowColor: 'rgba(0,0,0,0.15)',
            shadowBlur: 10,
            shadowOffsetY: 3,
            labelText: (d: any) => d.data?.label || '',
            labelFill: (d: any) => d.data?.textColor || '#333',
            labelFontSize: (d: any) => d.data?.isMain ? 14 : 12,
            labelFontWeight: (d: any) => d.data?.isMain ? 600 : 400,
            labelFontFamily: "'IBM Plex Sans', -apple-system, sans-serif",
            labelPlacement: 'center',
          },
          state: {
            hover: {
              shadowBlur: 15,
              lineWidth: 2,
            },
            selected: {
              lineWidth: 3,
            },
          },
        },
        edge: {
          type: 'line',
          style: {
            stroke: '#999',
            lineWidth: 1.5,
            endArrow: true,
            endArrowSize: 8,
            labelText: (d: any) => d.data?.dynamic || '',
            labelFill: '#666',
            labelFontSize: 16,
            labelFontWeight: 600,
            labelBackground: true,
            labelBackgroundFill: '#fff',
            labelBackgroundRadius: 10,
            labelBackgroundOpacity: 1,
            labelPadding: [4, 8],
          },
        },
        behaviors: ['drag-canvas', 'zoom-canvas', 'drag-element'],
      })

      graph.render().then(() => {
        console.log('G6 graph rendered')
      }).catch((err: any) => {
        console.error('G6 render error:', err)
      })

      // Node click handler - update panel selection
      graph.on('node:click', (evt: any) => {
        // G6 v5 uses different event structure
        const nodeId = evt.targetType === 'node' ? evt.target?.id : null
        if (!nodeId) {
          console.log('No nodeId found in click event', evt)
          return
        }

        const nodeData = graph.getNodeData(nodeId)
        if (!nodeData) {
          console.log('No nodeData for', nodeId)
          return
        }

        const data = nodeData.data as Record<string, unknown> | undefined
        const title = String(data?.fullLabel || data?.label || nodeId)
        const content = String(data?.fullText || data?.fullLabel || 'No details available')

        console.log('Node clicked:', { nodeId, title, content: content.slice(0, 100) })

        setSelection({
          visible: true,
          title,
          content,
        })
      })

      graphRef.current = graph

      const handleResize = () => {
        if (graphRef.current && containerRef.current) {
          graphRef.current.setSize(
            containerRef.current.clientWidth,
            containerRef.current.clientHeight
          )
          graphRef.current.fitView()
        }
      }
      window.addEventListener('resize', handleResize)

      return () => {
        window.removeEventListener('resize', handleResize)
        if (graphRef.current) {
          graphRef.current.destroy()
          graphRef.current = null
        }
      }
    } catch (err) {
      console.error('Failed to create G6 graph:', err)
    }
  }, [concept, result, buildGraphData, showConceptMap])

  // Resize handling
  const startResizing = useCallback(() => {
    setIsResizing(true)
  }, [])

  const stopResizing = useCallback(() => {
    setIsResizing(false)
  }, [])

  const resize = useCallback(
    (mouseMoveEvent: MouseEvent) => {
      if (isResizing && containerRef.current) {
        const totalHeight = containerRef.current.parentElement?.clientHeight || window.innerHeight
        const newPanelHeight = totalHeight - mouseMoveEvent.clientY
        // Min 100px, Max 80% of screen
        if (newPanelHeight > 100 && newPanelHeight < totalHeight * 0.8) {
          setPanelHeight(newPanelHeight)
        }
      }
    },
    [isResizing]
  )

  useEffect(() => {
    window.addEventListener('mousemove', resize)
    window.addEventListener('mouseup', stopResizing)
    return () => {
      window.removeEventListener('mousemove', resize)
      window.removeEventListener('mouseup', stopResizing)
    }
  }, [resize, stopResizing])

  // Force graph resize when panel height changes
  useEffect(() => {
    const timer = setTimeout(() => {
      if (graphRef.current && containerRef.current) {
        graphRef.current.setSize(
          containerRef.current.clientWidth,
          containerRef.current.clientHeight
        )
        graphRef.current.fitView()
      }
    }, 100)
    return () => clearTimeout(timer)
  }, [panelHeight, selection.visible])

  const handleDrillDown = () => {
    if (onNodeClick && selection.title) {
      onNodeClick('drill', selection.title)
      setSelection({ ...selection, visible: false })
    }
  }

  const closePanel = () => {
    setSelection({ ...selection, visible: false })
  }

  return (
    <div className="dsrp-graph-wrapper">
      <div
        ref={containerRef}
        className="dsrp-graph-canvas"
        style={{ height: selection.visible ? `calc(100% - ${panelHeight}px)` : '100%' }}
      />

      {!concept && !showConceptMap && (
        <div className="dsrp-empty-state">
          <p>Enter a concept and press Enter to analyze</p>
        </div>
      )}

      {/* Details Panel */}
      {selection.visible && (
        <div
          className="details-panel"
          style={{ height: panelHeight }}
        >
          {/* Taco / Drag Handle */}
          <div className="resize-handle" onMouseDown={startResizing}>
            <div className="taco-grip" />
          </div>

          <div className="panel-header">
            <h4>{selection.title}</h4>
            <div className="panel-controls">
              <button className="drill-btn" onClick={handleDrillDown}>
                Analyze →
              </button>
              <button className="close-btn" onClick={closePanel}>×</button>
            </div>
          </div>
          <div className="panel-content">
            <p>{selection.content}</p>
          </div>
        </div>
      )}

      <div className="dsrp-legend" style={{ bottom: selection.visible ? `${panelHeight + 10}px` : '10px' }}>
        <div className="legend-section">
          <span className="legend-title">Patterns:</span>
          <span style={{ color: DSRP_COLORS.D.stroke }}>D</span>
          <span style={{ color: DSRP_COLORS.S.stroke }}>S</span>
          <span style={{ color: DSRP_COLORS.R.stroke }}>R</span>
          <span style={{ color: DSRP_COLORS.P.stroke }}>P</span>
        </div>
        <div className="legend-section">
          <span className="legend-title">Dynamics:</span>
          <span>= equal</span>
          <span>⇔ co-imp</span>
          <span>✷ simult</span>
        </div>
      </div>

      <style>{`
        .dsrp-graph-wrapper {
          width: 100%;
          height: 100%;
          position: relative;
          background: linear-gradient(180deg, #0a0a0f 0%, #0d1117 100%);
          border-radius: 0;
          overflow: hidden;
          display: flex;
          flex-direction: column;
        }
        .dsrp-graph-canvas {
          width: 100%;
          transition: height 0.1s ease; /* Fast transition for resize */
        }
        .dsrp-empty-state {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          text-align: center;
          color: rgba(255,255,255,0.4);
          font-family: 'IBM Plex Sans', -apple-system, sans-serif;
          font-size: 14px;
        }
        .details-panel {
          background: #16213e;
          border-top: 1px solid rgba(255,255,255,0.1);
          box-shadow: 0 -2px 10px rgba(0,0,0,0.3);
          display: flex;
          flex-direction: column;
          z-index: 100;
          position: relative;
        }
        .resize-handle {
          height: 12px;
          width: 100%;
          background: rgba(255,255,255,0.03);
          cursor: row-resize;
          display: flex;
          align-items: center;
          justify-content: center;
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .resize-handle:hover {
          background: rgba(255,255,255,0.06);
        }
        .taco-grip {
          width: 40px;
          height: 4px;
          background: rgba(255,255,255,0.2);
          border-radius: 2px;
        }
        .panel-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 15px;
          background: rgba(255,255,255,0.03);
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .panel-header h4 {
          margin: 0;
          font-size: 16px;
          color: #fff;
        }
        .panel-controls {
          display: flex;
          gap: 10px;
          align-items: center;
        }
        .panel-content {
          flex: 1;
          padding: 15px;
          overflow-y: auto;
          font-family: 'IBM Plex Sans', -apple-system, sans-serif;
        }
        .panel-content p {
          margin: 0;
          font-size: 14px;
          line-height: 1.6;
          color: rgba(255,255,255,0.8);
          white-space: pre-wrap;
        }
        .close-btn {
          background: none;
          border: none;
          font-size: 24px;
          cursor: pointer;
          color: rgba(255,255,255,0.5);
          line-height: 1;
          padding: 0 5px;
        }
        .close-btn:hover { color: #fff; }
        .drill-btn {
          padding: 6px 12px;
          background: #e94560;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 13px;
          font-weight: 500;
        }
        .drill-btn:hover { background: #d63850; }
        .dsrp-legend {
          position: absolute;
          left: 10px;
          display: flex;
          gap: 20px;
          font-size: 11px;
          font-family: 'IBM Plex Sans', -apple-system, sans-serif;
          background: rgba(22, 33, 62, 0.95);
          color: rgba(255,255,255,0.8);
          padding: 8px 14px;
          border-radius: 6px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.3);
          border: 1px solid rgba(255,255,255,0.1);
          transition: bottom 0.1s ease;
        }
        .legend-section {
          display: flex;
          gap: 8px;
          align-items: center;
        }
        .legend-title {
          font-weight: 600;
          color: rgba(255,255,255,0.5);
        }
      `}</style>
    </div >
  )
}

function extractConcepts(text: unknown, max: number = 4): string[] {
  if (!text) return []

  // Handle array input (e.g. from JSON list)
  if (Array.isArray(text)) {
    return text.map(t => String(t)).slice(0, max)
  }

  // Handle number or other types
  const str = String(text)

  return str
    .split(/[,.\n;•\-:()]+/)
    .map(s => s.trim().replace(/^(it is |this is |a |an |the |and |or )/gi, ''))
    .filter(s => s.length >= 2 && s.length <= 25)
    .map(s => s.split(/\s+/).slice(0, 3).join(' '))
    .slice(0, max)
}
