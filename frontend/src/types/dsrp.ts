// DSRP 4-8-3 Type Definitions

// The 4 Patterns
export type DSRPPattern = 'D' | 'S' | 'R' | 'P'

// The 8 Elements (2 per pattern)
export interface DSRPElements {
  D: { identity: string; other: string }
  S: { part: string; whole: string }
  R: { action: string; reaction: string }
  P: { point: string; view: string }
}

// The 3 Dynamics
export type DSRPDynamic = 'equality' | 'coimplication' | 'simultaneity'

// The 8 Moves (6 core + 2 causal)
export type DSRPMove =
  | 'is-is-not'
  | 'zoom-in'
  | 'zoom-out'
  | 'part-party'
  | 'rds-barbell'
  | 'p-circle'
  | 'woc'   // Web of Causality
  | 'waoc'  // Web of Anticausality

export interface Concept {
  id: string
  name: string
  description?: string
  sourceIds: string[]
  analyses: DSRPAnalysis[]
  createdAt: Date
  updatedAt: Date
}

export interface DSRPAnalysis {
  id: string
  conceptId: string
  pattern: DSRPPattern
  elementType: keyof DSRPElements[DSRPPattern]
  move: DSRPMove
  reasoning: string
  confidenceScore: number
  createdAt: Date
}

export interface Distinction {
  id: string
  identity: Concept
  other: Concept
  label?: string
}

export interface SystemStructure {
  id: string
  whole: Concept
  parts: Concept[]
  label?: string
}

export interface Relationship {
  id: string
  action: Concept
  reaction: Concept
  relationshipType: 'causal' | 'correlative' | 'structural' | 'temporal'
  label?: string
}

export interface Perspective {
  id: string
  point: Concept // the observer
  view: Concept // what is observed
  label?: string
}

// Canvas-specific types
export interface CanvasNote {
  id: string
  conceptId?: string
  x: number
  y: number
  scale: number
  content: string
  color: string
  dsrpPattern?: DSRPPattern
}

// Export formats
export interface MarkdownExport {
  title: string
  concepts: Concept[]
  analyses: DSRPAnalysis[]
  format: 'obsidian' | 'remnote' | 'plain'
}

export interface RemNoteCard {
  front: string
  back: string
  tags: string[]
  sourceConceptId: string
}
