import { Editor, TLShapeId, createShapeId } from '@tldraw/tldraw'
import { useCallback } from 'react'
import { DSRPPattern } from '../types/dsrp'

// Compact node dimensions - height adjusted for text
const NODE_WIDTH = 110
const NODE_HEIGHT = 24
const NODE_SPACING = 12
const MAIN_NODE_WIDTH = 130
const MAIN_NODE_HEIGHT = 28
const COLUMN_GAP = 50 // Gap between columns

interface AnalysisResult {
  pattern: string
  elements: Record<string, unknown>
  move: string
  reasoning: string
  related_concepts?: string[]
  confidence?: number
}

interface ShapePosition {
  x: number
  y: number
}

// Color mapping for DSRP patterns
function getPatternColor(pattern: DSRPPattern): string {
  const colorMap: Record<DSRPPattern, string> = {
    D: 'light-blue',
    S: 'light-green',
    R: 'orange',
    P: 'light-violet',
  }
  return colorMap[pattern] || 'grey'
}

/**
 * Extract short concept keywords from text
 */
function extractConceptKeywords(text: string, max: number = 4): string[] {
  if (!text) return []

  let concepts = text
    .split(/[,.\n;•\-:()]+/)
    .map(s => s.trim())
    .filter(s => s.length > 1)

  concepts = concepts.map(c => {
    c = c.replace(/^(it is |this is |these are |a |an |the |and |or |but |with |for |to |of |in |on |at |by |as )/gi, '')
    const words = c.split(/\s+/)
    if (words.length > 2) {
      return words.slice(0, 2).join(' ')
    }
    return c
  })

  concepts = concepts.filter(c => c.length >= 2 && c.length <= 20)
  return [...new Set(concepts)].slice(0, max)
}

export function useCanvasShapes(editor: Editor | null) {
  /**
   * Create a rounded rectangle node using frame shape (has rounded corners)
   */
  const createRoundedNode = useCallback(
    (
      label: string,
      color: string,
      position: ShapePosition,
      width: number = NODE_WIDTH,
      height: number = NODE_HEIGHT
    ): TLShapeId | null => {
      if (!editor) return null

      const nodeId = createShapeId()

      // Truncate label to fit
      const maxChars = Math.floor(width / 7)
      const displayLabel = label.length > maxChars
        ? label.substring(0, maxChars - 1) + '…'
        : label

      // Use 'rectangle' with 'draw' dash style for softer edges
      // Or use note shape which has rounded corners
      editor.createShape({
        id: nodeId,
        type: 'geo',
        x: position.x,
        y: position.y,
        props: {
          geo: 'rectangle',
          w: width,
          h: height,
          color,
          fill: 'solid',
          dash: 'draw', // 'draw' style gives softer/rounded appearance
          size: 's',
          text: displayLabel,
          font: 'sans',
          align: 'middle',
          verticalAlign: 'middle',
        },
      })

      return nodeId
    },
    [editor]
  )

  /**
   * Create a small dynamics label (=, ⇔, ✷)
   */
  const createDynamicsLabel = useCallback(
    (position: ShapePosition, dynamic: '=' | '⇔' | '✷'): TLShapeId | null => {
      if (!editor) return null

      const id = createShapeId()

      editor.createShape({
        id,
        type: 'text',
        x: position.x,
        y: position.y,
        props: {
          text: dynamic,
          size: 's',
          color: 'grey',
          font: 'sans',
        },
      })

      return id
    },
    [editor]
  )

  /**
   * Create shapes for a complete DSRP analysis result
   */
  const createAnalysisShapes = useCallback(
    (concept: string, result: AnalysisResult): TLShapeId[] => {
      if (!editor) return []

      const createdIds: TLShapeId[] = []
      const pattern = result.pattern as DSRPPattern
      const center = getCenterPosition(editor)

      // Create main concept node (centered)
      const mainPos = { x: center.x - MAIN_NODE_WIDTH / 2, y: center.y - MAIN_NODE_HEIGHT / 2 }
      const mainId = createRoundedNode(concept, getPatternColor(pattern), mainPos, MAIN_NODE_WIDTH, MAIN_NODE_HEIGHT)
      if (mainId) createdIds.push(mainId)

      const elements = result.elements

      if (result.move === 'is-is-not') {
        // IS concepts on the left
        if (elements.identity) {
          const identityConcepts = extractConceptKeywords(elements.identity as string, 4)
          if (identityConcepts.length === 0) {
            identityConcepts.push((elements.identity as string).substring(0, 15))
          }

          const stackHeight = identityConcepts.length * (NODE_HEIGHT + NODE_SPACING) - NODE_SPACING
          const startY = center.y - stackHeight / 2

          identityConcepts.forEach((item, i) => {
            const pos = {
              x: center.x - MAIN_NODE_WIDTH / 2 - NODE_WIDTH - COLUMN_GAP,
              y: startY + i * (NODE_HEIGHT + NODE_SPACING)
            }
            const itemId = createRoundedNode(item, 'light-blue', pos)
            if (itemId) {
              createdIds.push(itemId)
              createEdgeArrow(editor, itemId, mainId!, 'right', 'left', createdIds, 'light-blue')
            }
          })

          // Add "=" dynamic between IS concepts and main
          const eqPos = {
            x: center.x - MAIN_NODE_WIDTH / 2 - COLUMN_GAP / 2 - 8,
            y: center.y - 8
          }
          const eqId = createDynamicsLabel(eqPos, '=')
          if (eqId) createdIds.push(eqId)
        }

        // IS NOT concepts on the right
        if (elements.other) {
          const otherConcepts = extractConceptKeywords(elements.other as string, 4)
          if (otherConcepts.length === 0) {
            otherConcepts.push((elements.other as string).substring(0, 15))
          }

          const stackHeight = otherConcepts.length * (NODE_HEIGHT + NODE_SPACING) - NODE_SPACING
          const startY = center.y - stackHeight / 2

          otherConcepts.forEach((item, i) => {
            const pos = {
              x: center.x + MAIN_NODE_WIDTH / 2 + COLUMN_GAP,
              y: startY + i * (NODE_HEIGHT + NODE_SPACING)
            }
            const itemId = createRoundedNode(item, 'orange', pos)
            if (itemId) {
              createdIds.push(itemId)
              createEdgeArrow(editor, mainId!, itemId, 'right', 'left', createdIds, 'orange')
            }
          })

          // Add "⇔" dynamic between main and IS NOT concepts
          const coimpPos = {
            x: center.x + MAIN_NODE_WIDTH / 2 + COLUMN_GAP / 2 - 8,
            y: center.y - 8
          }
          const coimpId = createDynamicsLabel(coimpPos, '⇔')
          if (coimpId) createdIds.push(coimpId)
        }

        // Add "✷" simultaneity dynamic below main concept
        const simPos = {
          x: center.x - 6,
          y: center.y + MAIN_NODE_HEIGHT / 2 + 8
        }
        const simId = createDynamicsLabel(simPos, '✷')
        if (simId) createdIds.push(simId)

      } else if (result.move === 'zoom-in' && Array.isArray(elements.parts)) {
        const parts = (elements.parts as string[]).slice(0, 4)
        const startY = center.y + MAIN_NODE_HEIGHT / 2 + 35

        parts.forEach((part, i) => {
          const pos = {
            x: center.x - NODE_WIDTH / 2,
            y: startY + i * (NODE_HEIGHT + NODE_SPACING)
          }
          const partId = createRoundedNode(part, 'light-green', pos)
          if (partId) {
            createdIds.push(partId)
            createEdgeArrow(editor, mainId!, partId, 'bottom', 'top', createdIds, 'light-green')
          }
        })

        // Add dynamics
        const dynPos = { x: center.x + MAIN_NODE_WIDTH / 2 + 10, y: center.y - 4 }
        const dynId = createDynamicsLabel(dynPos, '⇔')
        if (dynId) createdIds.push(dynId)

      } else if (result.move === 'zoom-out' && elements.whole) {
        const wholeText = typeof elements.whole === 'string' ? elements.whole : String(elements.whole)
        const wholePos = {
          x: center.x - NODE_WIDTH / 2,
          y: center.y - MAIN_NODE_HEIGHT / 2 - NODE_HEIGHT - 35
        }
        const wholeId = createRoundedNode(wholeText.substring(0, 15), 'light-green', wholePos)
        if (wholeId) {
          createdIds.push(wholeId)
          createEdgeArrow(editor, wholeId, mainId!, 'bottom', 'top', createdIds, 'light-green')
        }

        const dynPos = { x: center.x + MAIN_NODE_WIDTH / 2 + 10, y: center.y - 4 }
        const dynId = createDynamicsLabel(dynPos, '⇔')
        if (dynId) createdIds.push(dynId)

      } else if (result.move === 'p-circle' && Array.isArray(elements.perspectives)) {
        const perspectives = (elements.perspectives as Array<{ point: string; view: string }>).slice(0, 4)
        const radius = 90

        perspectives.forEach((persp, i) => {
          const angle = (i / perspectives.length) * Math.PI * 2 - Math.PI / 2
          const pos = {
            x: center.x + Math.cos(angle) * radius - NODE_WIDTH / 2,
            y: center.y + Math.sin(angle) * radius - NODE_HEIGHT / 2
          }
          const label = typeof persp === 'string' ? persp : persp.point || String(persp)
          const perspId = createRoundedNode(label.substring(0, 14), 'light-violet', pos)
          if (perspId) {
            createdIds.push(perspId)
            createEdgeArrow(editor, perspId, mainId!, 'center', 'center', createdIds, 'light-violet')
          }
        })

        const dynPos = { x: center.x + MAIN_NODE_WIDTH / 2 + 10, y: center.y - 4 }
        const dynId = createDynamicsLabel(dynPos, '✷')
        if (dynId) createdIds.push(dynId)

      } else if (result.move === 'rds-barbell' && Array.isArray(elements.reactions)) {
        const reactions = (elements.reactions as string[]).slice(0, 4)
        const stackHeight = reactions.length * (NODE_HEIGHT + NODE_SPACING) - NODE_SPACING
        const startY = center.y - stackHeight / 2

        reactions.forEach((reaction, i) => {
          const pos = {
            x: center.x + MAIN_NODE_WIDTH / 2 + COLUMN_GAP,
            y: startY + i * (NODE_HEIGHT + NODE_SPACING)
          }
          const reactionId = createRoundedNode(reaction.substring(0, 14), 'orange', pos)
          if (reactionId) {
            createdIds.push(reactionId)
            createEdgeArrow(editor, mainId!, reactionId, 'right', 'left', createdIds, 'orange')
          }
        })

        const dynPos = { x: center.x + MAIN_NODE_WIDTH / 2 + COLUMN_GAP / 2 - 8, y: center.y - 8 }
        const dynId = createDynamicsLabel(dynPos, '⇔')
        if (dynId) createdIds.push(dynId)

      } else if (result.move === 'part-party' && Array.isArray(elements.parts)) {
        const parts = (elements.parts as string[]).slice(0, 4)
        const radius = 90
        const partIds: TLShapeId[] = []

        parts.forEach((part, i) => {
          const angle = (i / parts.length) * Math.PI * 2 - Math.PI / 2
          const pos = {
            x: center.x + Math.cos(angle) * radius - NODE_WIDTH / 2,
            y: center.y + Math.sin(angle) * radius - NODE_HEIGHT / 2
          }
          const partId = createRoundedNode(part.substring(0, 14), 'light-green', pos)
          if (partId) {
            createdIds.push(partId)
            partIds.push(partId)
            createEdgeArrow(editor, mainId!, partId, 'center', 'center', createdIds, 'light-green')
          }
        })

        // Connect adjacent parts
        for (let i = 0; i < partIds.length; i++) {
          const nextIdx = (i + 1) % partIds.length
          createEdgeArrow(editor, partIds[i], partIds[nextIdx], 'center', 'center', createdIds, 'grey')
        }

        const dynPos = { x: center.x + MAIN_NODE_WIDTH / 2 + 10, y: center.y - 4 }
        const dynId = createDynamicsLabel(dynPos, '=')
        if (dynId) createdIds.push(dynId)
      }

      // Zoom to fit all shapes
      if (createdIds.length > 0) {
        editor.select(...createdIds)
        editor.zoomToSelection()
      }

      return createdIds
    },
    [editor, createRoundedNode, createDynamicsLabel]
  )

  const clearAnalysisShapes = useCallback(() => {
    if (!editor) return

    const shapes = editor.getCurrentPageShapes()
    const analysisShapes = shapes.filter((s) =>
      s.type === 'geo' || s.type === 'arrow' || s.type === 'text' || s.type === 'note'
    )
    if (analysisShapes.length > 0) {
      editor.deleteShapes(analysisShapes.map((s) => s.id))
    }
  }, [editor])

  return {
    createAnalysisShapes,
    clearAnalysisShapes,
  }
}

// Helper functions

function getCenterPosition(editor: Editor): ShapePosition {
  const viewport = editor.getViewportScreenBounds()
  const camera = editor.getCamera()
  return {
    x: -camera.x + viewport.width / 2 / camera.z,
    y: -camera.y + viewport.height / 2 / camera.z,
  }
}

type EdgePosition = 'left' | 'right' | 'top' | 'bottom' | 'center'

function getEdgePoint(
  shape: { x: number; y: number },
  bounds: { width: number; height: number },
  edge: EdgePosition
): { x: number; y: number } {
  const centerX = shape.x + bounds.width / 2
  const centerY = shape.y + bounds.height / 2

  switch (edge) {
    case 'left':
      return { x: shape.x, y: centerY }
    case 'right':
      return { x: shape.x + bounds.width, y: centerY }
    case 'top':
      return { x: centerX, y: shape.y }
    case 'bottom':
      return { x: centerX, y: shape.y + bounds.height }
    case 'center':
    default:
      return { x: centerX, y: centerY }
  }
}

function createEdgeArrow(
  editor: Editor,
  fromId: TLShapeId,
  toId: TLShapeId,
  fromEdge: EdgePosition,
  toEdge: EdgePosition,
  createdIds: TLShapeId[],
  color: string = 'black'
): TLShapeId | null {
  try {
    const id = createShapeId()

    const fromShape = editor.getShape(fromId)
    const toShape = editor.getShape(toId)

    if (!fromShape || !toShape) return null

    const fromBounds = editor.getShapeGeometry(fromId).bounds
    const toBounds = editor.getShapeGeometry(toId).bounds

    const fromPoint = getEdgePoint(fromShape, fromBounds, fromEdge)
    const toPoint = getEdgePoint(toShape, toBounds, toEdge)

    const arrowX = Math.min(fromPoint.x, toPoint.x)
    const arrowY = Math.min(fromPoint.y, toPoint.y)

    editor.createShape({
      id,
      type: 'arrow',
      x: arrowX,
      y: arrowY,
      props: {
        start: { x: fromPoint.x - arrowX, y: fromPoint.y - arrowY },
        end: { x: toPoint.x - arrowX, y: toPoint.y - arrowY },
        color,
        size: 's',
        arrowheadEnd: 'arrow',
        arrowheadStart: 'none',
      },
    })

    createdIds.push(id)
    return id
  } catch (e) {
    console.error('Failed to create arrow:', e)
    return null
  }
}
