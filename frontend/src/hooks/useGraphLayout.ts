/**
 * useGraphLayout - Hook for managing G6 graph layouts based on DSRP moves
 *
 * Provides layout configuration and animation for different DSRP analysis types.
 */

import { useMemo, useCallback } from 'react'
import { DSRPMove } from '../types/dsrp'

export interface LayoutConfig {
  type: string
  direction?: string
  rankdir?: 'TB' | 'BT' | 'LR' | 'RL'
  align?: 'UL' | 'UR' | 'DL' | 'DR'
  nodesep?: number
  ranksep?: number
  controlPoints?: boolean
  center?: [number, number]
  focusNode?: string
  unitRadius?: number
  linkDistance?: number
  nodeStrength?: number
  edgeStrength?: number
  preventOverlap?: boolean
  nodeSize?: number
  nodeSpacing?: number
  sortBy?: string
  clockwise?: boolean
  startAngle?: number
  endAngle?: number
  divisions?: number
  radius?: number | null
  startRadius?: number | null
  endRadius?: number | null
}

// Comprehensive layout configurations for each DSRP move
const LAYOUT_CONFIGS: Record<DSRPMove, LayoutConfig> = {
  // Distinctions: Horizontal flow (IS -> Concept -> IS NOT)
  'is-is-not': {
    type: 'dagre',
    rankdir: 'LR',
    align: 'UL',
    nodesep: 80,
    ranksep: 150,
    controlPoints: true,
  },

  // Systems (Zoom In): Top-down hierarchy (Whole -> Parts)
  'zoom-in': {
    type: 'dagre',
    rankdir: 'TB',
    align: 'UL',
    nodesep: 60,
    ranksep: 100,
    controlPoints: true,
  },

  // Systems (Zoom Out): Bottom-up hierarchy (Part -> Whole -> Context)
  'zoom-out': {
    type: 'dagre',
    rankdir: 'BT',
    align: 'DL',
    nodesep: 60,
    ranksep: 120,
    controlPoints: true,
  },

  // Systems (Part Party): Circular with relationships
  'part-party': {
    type: 'circular',
    radius: null, // Auto-calculate
    startAngle: 0,
    endAngle: 2 * Math.PI,
    clockwise: true,
    divisions: 1,
    preventOverlap: true,
    nodeSpacing: 30,
  },

  // Relationships (RDS Barbell): Force-directed clustering
  'rds-barbell': {
    type: 'force',
    linkDistance: 150,
    nodeStrength: -300,
    edgeStrength: 0.1,
    preventOverlap: true,
    nodeSize: 60,
    nodeSpacing: 20,
  },

  // Perspectives (P-Circle): Radial with concept at center
  'p-circle': {
    type: 'radial',
    unitRadius: 180,
    linkDistance: 200,
    preventOverlap: true,
    nodeSize: 60,
    nodeSpacing: 30,
    sortBy: 'degree',
  },
}

// Alternative layouts for special cases
const ALTERNATIVE_LAYOUTS: Record<string, LayoutConfig> = {
  // Tree layout for deep hierarchies
  tree: {
    type: 'compactBox',
    direction: 'TB',
    preventOverlap: true,
    nodeSize: 60,
  },

  // Grid for many nodes
  grid: {
    type: 'grid',
    preventOverlap: true,
    nodeSize: 60,
    sortBy: 'degree',
  },

  // Concentric for layered systems
  concentric: {
    type: 'concentric',
    preventOverlap: true,
    nodeSize: 60,
    sortBy: 'degree',
  },
}

export function useGraphLayout() {
  /**
   * Get the recommended layout for a DSRP move
   */
  const getLayoutForMove = useCallback((move: DSRPMove): LayoutConfig => {
    return LAYOUT_CONFIGS[move] || LAYOUT_CONFIGS['zoom-in']
  }, [])

  /**
   * Get layout with custom overrides
   */
  const getCustomLayout = useCallback(
    (move: DSRPMove, overrides?: Partial<LayoutConfig>): LayoutConfig => {
      const baseLayout = getLayoutForMove(move)
      return { ...baseLayout, ...overrides }
    },
    [getLayoutForMove]
  )

  /**
   * Get alternative layout by name
   */
  const getAlternativeLayout = useCallback((name: string): LayoutConfig | null => {
    return ALTERNATIVE_LAYOUTS[name] || null
  }, [])

  /**
   * Determine best layout based on node count
   */
  const getBestLayout = useCallback(
    (move: DSRPMove, nodeCount: number): LayoutConfig => {
      const baseLayout = getLayoutForMove(move)

      // For very large graphs, use force layout
      if (nodeCount > 100) {
        return {
          ...ALTERNATIVE_LAYOUTS.grid,
          nodeSpacing: Math.max(10, 60 - nodeCount / 10),
        }
      }

      // For medium graphs with hierarchy, use tree
      if (nodeCount > 30 && (move === 'zoom-in' || move === 'zoom-out')) {
        return ALTERNATIVE_LAYOUTS.tree
      }

      return baseLayout
    },
    [getLayoutForMove]
  )

  /**
   * Get animation configuration for layout transitions
   */
  const getAnimationConfig = useCallback((move: DSRPMove) => {
    const baseConfig = {
      duration: 500,
      easing: 'easeOutQuad',
    }

    // Slower animation for complex layouts
    if (move === 'rds-barbell' || move === 'part-party') {
      return { ...baseConfig, duration: 800 }
    }

    return baseConfig
  }, [])

  /**
   * Layout descriptions for UI
   */
  const layoutDescriptions = useMemo(
    () => ({
      'is-is-not': {
        name: 'Horizontal Flow',
        description: 'Shows IS and IS NOT on opposite sides',
        icon: '↔️',
      },
      'zoom-in': {
        name: 'Top-Down Hierarchy',
        description: 'Shows parts below the whole',
        icon: '⬇️',
      },
      'zoom-out': {
        name: 'Bottom-Up Hierarchy',
        description: 'Shows context above the part',
        icon: '⬆️',
      },
      'part-party': {
        name: 'Circular',
        description: 'Parts arranged in a circle with relationships',
        icon: '⭕',
      },
      'rds-barbell': {
        name: 'Force-Directed',
        description: 'Related concepts cluster naturally',
        icon: '🔗',
      },
      'p-circle': {
        name: 'Radial',
        description: 'Perspectives around central concept',
        icon: '🎯',
      },
    }),
    []
  )

  return {
    getLayoutForMove,
    getCustomLayout,
    getAlternativeLayout,
    getBestLayout,
    getAnimationConfig,
    layoutDescriptions,
    LAYOUT_CONFIGS,
    ALTERNATIVE_LAYOUTS,
  }
}
