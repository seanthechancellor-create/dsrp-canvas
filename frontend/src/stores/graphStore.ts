/**
 * Graph Store - Zustand store for G6/Graphin graph state
 *
 * Manages nodes, edges, combos for DSRP knowledge graph visualization.
 * Converts DSRP analysis results into graph data structures.
 */

import { create } from 'zustand'
import { DSRPPattern, DSRPMove } from '../types/dsrp'

export interface DSRPNode {
  id: string
  label: string
  type?: 'circle' | 'rect' | 'ellipse' | 'diamond'
  dsrpPattern?: DSRPPattern
  dsrpRole?: string // identity, other, part, whole, action, reaction, point, view
  comboId?: string
  metadata?: Record<string, unknown>
}

export interface DSRPEdge {
  id?: string
  source: string
  target: string
  label?: string
  dsrpRelation?: DSRPPattern // D, S, R, P
  relationType?: string // distinction, system-structure, relationship-link, perspective-view
}

export interface DSRPCombo {
  id: string
  label: string
  parentId?: string
  dsrpPattern?: DSRPPattern
}

interface AnalysisResult {
  pattern: string
  elements: Record<string, unknown>
  move: string
  reasoning: string
  related_concepts?: string[]
  confidence?: number
}

interface GraphState {
  nodes: DSRPNode[]
  edges: DSRPEdge[]
  combos: DSRPCombo[]
  currentMove: DSRPMove | null
  selectedNodeId: string | null
  focusedConceptId: string | null

  // Actions
  setSelectedNode: (id: string | null) => void
  setCurrentMove: (move: DSRPMove | null) => void
  addAnalysisToGraph: (concept: string, result: AnalysisResult) => void
  clearGraph: () => void
  removeNode: (id: string) => void
  updateNodeLabel: (id: string, label: string) => void
}

// Helper to generate unique IDs
const generateId = () => `node-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`

export const useGraphStore = create<GraphState>((set, get) => ({
  nodes: [],
  edges: [],
  combos: [],
  currentMove: null,
  selectedNodeId: null,
  focusedConceptId: null,

  setSelectedNode: (id) => set({ selectedNodeId: id }),

  setCurrentMove: (move) => set({ currentMove: move }),

  clearGraph: () => set({ nodes: [], edges: [], combos: [], selectedNodeId: null }),

  removeNode: (id) =>
    set((state) => ({
      nodes: state.nodes.filter((n) => n.id !== id),
      edges: state.edges.filter((e) => e.source !== id && e.target !== id),
      selectedNodeId: state.selectedNodeId === id ? null : state.selectedNodeId,
    })),

  updateNodeLabel: (id, label) =>
    set((state) => ({
      nodes: state.nodes.map((n) => (n.id === id ? { ...n, label } : n)),
    })),

  addAnalysisToGraph: (concept, result) => {
    const move = result.move as DSRPMove
    const pattern = result.pattern as DSRPPattern
    const elements = result.elements

    set({ currentMove: move })

    // Find or create main concept node
    const existingNode = get().nodes.find(
      (n) => n.label.toLowerCase() === concept.toLowerCase()
    )
    const mainNodeId = existingNode?.id || generateId()

    const newNodes: DSRPNode[] = []
    const newEdges: DSRPEdge[] = []
    const newCombos: DSRPCombo[] = []

    // Add main concept if not exists
    if (!existingNode) {
      newNodes.push({
        id: mainNodeId,
        label: concept,
        dsrpPattern: pattern,
        dsrpRole: 'concept',
        type: 'circle',
      })
    }

    // Build graph based on move type
    switch (move) {
      case 'is-is-not': {
        // Distinction: identity <-> concept <-> other
        if (elements.identity) {
          const identityId = generateId()
          const identityText = typeof elements.identity === 'string'
            ? elements.identity.slice(0, 50)
            : 'Identity'
          newNodes.push({
            id: identityId,
            label: `IS: ${identityText}`,
            dsrpPattern: 'D',
            dsrpRole: 'identity',
            type: 'rect',
          })
          newEdges.push({
            source: identityId,
            target: mainNodeId,
            label: 'identity',
            dsrpRelation: 'D',
            relationType: 'distinction',
          })
        }
        if (elements.other) {
          const otherId = generateId()
          const otherText = typeof elements.other === 'string'
            ? elements.other.slice(0, 50)
            : 'Other'
          newNodes.push({
            id: otherId,
            label: `IS NOT: ${otherText}`,
            dsrpPattern: 'D',
            dsrpRole: 'other',
            type: 'rect',
          })
          newEdges.push({
            source: mainNodeId,
            target: otherId,
            label: 'other',
            dsrpRelation: 'D',
            relationType: 'distinction',
          })
        }
        break
      }

      case 'zoom-in': {
        // System: whole -> parts
        const comboId = `combo-${mainNodeId}`
        newCombos.push({
          id: comboId,
          label: `${concept} (System)`,
          dsrpPattern: 'S',
        })

        // Update main node to be in combo
        set((state) => ({
          nodes: state.nodes.map((n) =>
            n.id === mainNodeId ? { ...n, comboId } : n
          ),
        }))

        if (Array.isArray(elements.parts)) {
          elements.parts.slice(0, 8).forEach((part: unknown) => {
            if (typeof part !== 'string') return
            const partId = generateId()
            newNodes.push({
              id: partId,
              label: part,
              dsrpPattern: 'S',
              dsrpRole: 'part',
              comboId,
              type: 'circle',
            })
            newEdges.push({
              source: mainNodeId,
              target: partId,
              label: 'has part',
              dsrpRelation: 'S',
              relationType: 'system-structure',
            })
          })
        }
        break
      }

      case 'zoom-out': {
        // System: part -> whole
        if (elements.whole && typeof elements.whole === 'string') {
          const wholeId = generateId()
          const comboId = `combo-${wholeId}`

          newNodes.push({
            id: wholeId,
            label: elements.whole,
            dsrpPattern: 'S',
            dsrpRole: 'whole',
            type: 'circle',
          })

          newCombos.push({
            id: comboId,
            label: `${elements.whole} (System)`,
            dsrpPattern: 'S',
          })

          newEdges.push({
            source: wholeId,
            target: mainNodeId,
            label: 'contains',
            dsrpRelation: 'S',
            relationType: 'system-structure',
          })

          // Update main node to be part of whole's combo
          set((state) => ({
            nodes: state.nodes.map((n) =>
              n.id === mainNodeId ? { ...n, comboId, dsrpRole: 'part' } : n
            ),
          }))
        }

        // Add context layers if available
        if (Array.isArray(elements.context_layers)) {
          let parentComboId: string | undefined
          elements.context_layers.forEach((layer: unknown, index: number) => {
            if (typeof layer !== 'string') return
            const layerId = `layer-${index}-${generateId()}`
            newCombos.push({
              id: layerId,
              label: layer,
              parentId: parentComboId,
              dsrpPattern: 'S',
            })
            parentComboId = layerId
          })
        }
        break
      }

      case 'part-party': {
        // System with internal relationships
        const comboId = `combo-${mainNodeId}`
        newCombos.push({
          id: comboId,
          label: `${concept} (Part Party)`,
          dsrpPattern: 'S',
        })

        const partIds: string[] = []

        if (Array.isArray(elements.parts)) {
          elements.parts.slice(0, 8).forEach((part: unknown) => {
            if (typeof part !== 'string') return
            const partId = generateId()
            partIds.push(partId)
            newNodes.push({
              id: partId,
              label: part,
              dsrpPattern: 'S',
              dsrpRole: 'part',
              comboId,
              type: 'circle',
            })
            newEdges.push({
              source: mainNodeId,
              target: partId,
              label: 'has part',
              dsrpRelation: 'S',
              relationType: 'system-structure',
            })
          })
        }

        // Add relationships between parts
        if (Array.isArray(elements.relationships)) {
          elements.relationships.forEach((rel: unknown) => {
            if (typeof rel !== 'object' || rel === null) return
            const r = rel as { from?: string; to?: string; relationship?: string }
            const fromNode = newNodes.find((n) => n.label === r.from)
            const toNode = newNodes.find((n) => n.label === r.to)
            if (fromNode && toNode) {
              newEdges.push({
                source: fromNode.id,
                target: toNode.id,
                label: r.relationship || 'relates to',
                dsrpRelation: 'R',
                relationType: 'relationship-link',
              })
            }
          })
        }
        break
      }

      case 'rds-barbell': {
        // Relationships: concept <-> related things
        if (Array.isArray(elements.reactions)) {
          elements.reactions.slice(0, 8).forEach((reaction: unknown) => {
            if (typeof reaction !== 'string') return
            const reactionId = generateId()
            newNodes.push({
              id: reactionId,
              label: reaction,
              dsrpPattern: 'R',
              dsrpRole: 'reaction',
              type: 'circle',
            })
            newEdges.push({
              source: mainNodeId,
              target: reactionId,
              label: 'relates to',
              dsrpRelation: 'R',
              relationType: 'relationship-link',
            })
          })
        }

        // Add RDS analysis details
        if (Array.isArray(elements.rds_analysis)) {
          elements.rds_analysis.forEach((rds: unknown) => {
            if (typeof rds !== 'object' || rds === null) return
            const _rds = rds as { relate?: string; distinguish?: string; systematize?: string }
            // Could add more detailed nodes for each RDS step
            void _rds
          })
        }
        break
      }

      case 'p-circle': {
        // Perspectives: observers around concept
        if (Array.isArray(elements.perspectives)) {
          elements.perspectives.slice(0, 8).forEach((persp: unknown) => {
            if (typeof persp !== 'object' || persp === null) return
            const p = persp as { point?: string; view?: string }
            if (!p.point) return

            const perspId = generateId()
            newNodes.push({
              id: perspId,
              label: p.point,
              dsrpPattern: 'P',
              dsrpRole: 'point',
              type: 'diamond',
              metadata: { view: p.view },
            })
            newEdges.push({
              source: perspId,
              target: mainNodeId,
              label: p.view?.slice(0, 30) || 'views',
              dsrpRelation: 'P',
              relationType: 'perspective-view',
            })
          })
        }
        break
      }
    }

    // Merge new data with existing
    set((state) => ({
      nodes: [...state.nodes.filter((n) => n.id !== mainNodeId || existingNode), ...newNodes],
      edges: [...state.edges, ...newEdges],
      combos: [...state.combos, ...newCombos],
      focusedConceptId: mainNodeId,
    }))
  },
}))
