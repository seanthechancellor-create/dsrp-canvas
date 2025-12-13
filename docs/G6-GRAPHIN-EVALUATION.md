# G6/Graphin Evaluation for DSRP Canvas

## Executive Summary

**Recommendation: G6/Graphin is an excellent fit for DSRP Canvas** and should replace tldraw for the graph visualization layer.

G6 is a TypeScript-based graph visualization engine from Ant Group (AntV) with 10+ built-in layouts including hierarchical options. Graphin is a lightweight React wrapper that makes G6 easy to use in React applications.

---

## G6 Core Capabilities

### 1. Rich Elements
- Built-in node, edge, and **Combo** (grouping) UI elements
- Extensive style configurations
- Custom extension mechanisms
- **DSRP Fit**: Perfect for representing concepts (nodes), relations (edges), and systems (combos)

### 2. Layout Algorithms (10+)
| Layout | Description | DSRP Use Case |
|--------|-------------|---------------|
| **Dagre** | Hierarchical directed graph | Zoom-in/out (part-whole) |
| **Dendrogram** | Tree layout | System structures |
| **Radial** | Circular/radial | P-Circle perspectives |
| **Force** | Force-directed | RDS-Barbell relationships |
| **Concentric** | Concentric circles | Layered systems |
| **Grid** | Grid arrangement | Part-party organization |
| **Combo** | Nested grouping | Nested systems |
| **Circular** | Circular arrangement | Perspective mapping |

### 3. Interaction Behaviors (10+)
- Drag, zoom, pan
- Node/edge selection
- Collapse/expand (perfect for zoom-in/out)
- Tooltips, context menus
- Custom behaviors

### 4. Multi-Environment Rendering
- Canvas (default, good for <5k nodes)
- SVG (good for <2k nodes)
- WebGL (good for 10k+ nodes)
- Server-side rendering (Node.js)

### 5. React Integration
- Native React node support
- React component rendering inside nodes
- Full React ecosystem compatibility

---

## Graphin (React Wrapper)

**Version**: 3.0.5 (April 2025)
**Stars**: 1.1k
**License**: MIT

### Key Benefits
1. **React-first**: Designed as React components
2. **Declarative**: Configure via props, not imperative API
3. **Lightweight**: Thin wrapper, full G6 power
4. **GISDK**: Pre-built graph analysis components

### Installation
```bash
npm install @antv/graphin @antv/g6
```

---

## DSRP Pattern Mapping to G6

### Distinctions (D) - Is/Is Not
```javascript
// Two nodes with a distinction edge
const data = {
  nodes: [
    { id: 'concept', label: 'Democracy', style: { fill: '#4285F4' } },
    { id: 'identity', label: 'IS: Self-governance', style: { fill: '#4285F4' } },
    { id: 'other', label: 'IS NOT: Autocracy', style: { fill: '#E74C3C' } },
  ],
  edges: [
    { source: 'identity', target: 'concept', label: 'identity' },
    { source: 'concept', target: 'other', label: 'other' },
  ]
}
// Layout: Force or custom horizontal
```

### Systems (S) - Zoom In/Out
```javascript
// Hierarchical layout with Combos for nesting
const data = {
  nodes: [
    { id: 'democracy', label: 'Democracy', comboId: 'system' },
    { id: 'voting', label: 'Voting System', comboId: 'democracy-parts' },
    { id: 'legislative', label: 'Legislative Branch', comboId: 'democracy-parts' },
    { id: 'executive', label: 'Executive Branch', comboId: 'democracy-parts' },
  ],
  edges: [
    { source: 'democracy', target: 'voting' },
    { source: 'democracy', target: 'legislative' },
    { source: 'democracy', target: 'executive' },
  ],
  combos: [
    { id: 'system', label: 'Political Systems' },
    { id: 'democracy-parts', label: 'Parts', parentId: 'system' },
  ]
}
// Layout: Dagre (hierarchical) or Dendrogram (tree)
```

### Relationships (R) - RDS Barbell
```javascript
// Force-directed layout shows relationship clusters
const data = {
  nodes: [
    { id: 'democracy', label: 'Democracy' },
    { id: 'education', label: 'Education' },
    { id: 'economy', label: 'Economy' },
    { id: 'media', label: 'Free Media' },
  ],
  edges: [
    { source: 'democracy', target: 'education', label: 'enables' },
    { source: 'democracy', target: 'economy', label: 'stabilizes' },
    { source: 'democracy', target: 'media', label: 'requires' },
  ]
}
// Layout: Force-directed
```

### Perspectives (P) - P-Circle
```javascript
// Radial layout with concept at center
const data = {
  nodes: [
    { id: 'democracy', label: 'Democracy', type: 'center' },
    { id: 'citizen', label: 'Citizen POV' },
    { id: 'politician', label: 'Politician POV' },
    { id: 'philosopher', label: 'Philosopher POV' },
    { id: 'economist', label: 'Economist POV' },
  ],
  edges: [
    { source: 'citizen', target: 'democracy', label: 'voice' },
    { source: 'politician', target: 'democracy', label: 'authority' },
    { source: 'philosopher', target: 'democracy', label: 'ideal' },
    { source: 'economist', target: 'democracy', label: 'market' },
  ]
}
// Layout: Radial with democracy as focal point
```

---

## Comparison: G6/Graphin vs tldraw

| Feature | G6/Graphin | tldraw |
|---------|------------|--------|
| **Purpose** | Graph visualization | Whiteboard/drawing |
| **Hierarchical Layout** | ✅ Built-in (Dagre, Dendrogram) | ❌ Manual positioning |
| **Graph Algorithms** | ✅ 10+ layouts | ❌ None |
| **Combo/Grouping** | ✅ Native support | ⚠️ Limited |
| **Edge Routing** | ✅ Automatic | ⚠️ Basic arrows |
| **Collapse/Expand** | ✅ Built-in behavior | ❌ Not available |
| **Performance (10k nodes)** | ✅ WebGL rendering | ⚠️ May struggle |
| **React Integration** | ✅ Graphin wrapper | ✅ Native |
| **License** | MIT | Custom (watermark) |
| **Freeform Drawing** | ❌ Not designed for | ✅ Excellent |
| **Learning Curve** | Medium | Low |

---

## Migration Strategy

### Phase 1: Parallel Implementation
Keep tldraw for freeform notes, add G6/Graphin for DSRP graph visualization.

### Phase 2: Integration
- DSRP analysis results → G6 graph
- Click node in G6 → Create tldraw note
- Export G6 graph to Obsidian/RemNote

### Phase 3: Full Migration (Optional)
Replace tldraw entirely if freeform drawing isn't needed.

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────┐
│                    App.tsx                          │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │   Sidebar   │  │  G6/Graphin │  │  DSRPPanel  │ │
│  │   Sources   │  │    Graph    │  │  Analysis   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘ │
│                          │                          │
│                   ┌──────┴──────┐                   │
│                   │ Graph Store │                   │
│                   │  (Zustand)  │                   │
│                   └─────────────┘                   │
└─────────────────────────────────────────────────────┘
```

---

## Proof of Concept Files

See the following files for implementation:
- `frontend/src/components/DSRPGraph.tsx` - Main G6/Graphin component
- `frontend/src/hooks/useGraphLayout.ts` - Layout selection by DSRP move
- `frontend/src/stores/graphStore.ts` - Graph state management

---

## Conclusion

**G6/Graphin is strongly recommended** for DSRP Canvas because:

1. **Native hierarchical layouts** solve the zoom-in/out visualization problem
2. **Combo nodes** perfectly represent DSRP systems (nested part-whole)
3. **Multiple layout algorithms** match different DSRP moves
4. **Collapse/expand** enables interactive exploration
5. **MIT license** with no watermark requirements
6. **Active development** (v3.0.5, April 2025)
7. **Ant Group backing** ensures long-term support

The main trade-off is losing tldraw's freeform drawing, but this can be mitigated by keeping tldraw as an optional annotation layer or using G6's custom node capabilities.
