# DSRP Canvas - Product Requirements Document

## Executive Summary

DSRP Canvas is a knowledge analysis and visualization application that implements Dr. Derek Cabrera's DSRP 4-8-3 systems thinking framework. It provides an infinite canvas interface for visualizing knowledge graphs, AI-powered analysis using Claude, and export capabilities for popular knowledge management tools like Obsidian and RemNote.

**Version:** 1.0
**Author:** Sean Forrester
**Last Updated:** December 2024

---

## Problem Statement

Knowledge workers and researchers struggle to:
1. **Organize complex information** into meaningful structures
2. **See relationships** between concepts clearly
3. **Apply systematic thinking frameworks** consistently
4. **Export knowledge** to their preferred tools

DSRP Canvas solves these problems by providing a visual, AI-assisted platform for applying the proven DSRP systems thinking methodology.

---

## Target Users

### Primary Users
- **Researchers** organizing literature and concepts
- **Students** learning systems thinking
- **Knowledge workers** building personal knowledge bases
- **Educators** teaching conceptual analysis

### User Personas

**Sarah - Academic Researcher**
- Needs to organize hundreds of papers and concepts
- Wants to find hidden connections between ideas
- Uses Obsidian for long-term knowledge storage

**Marcus - Systems Thinking Student**
- Learning DSRP methodology
- Needs guidance on applying the 6 moves
- Values visual representations of concepts

---

## DSRP 4-8-3 Framework

### The 4 Patterns
| Pattern | Symbol | Description |
|---------|--------|-------------|
| **D**istinctions | D | Defining what something IS and IS NOT |
| **S**ystems | S | Understanding parts and wholes |
| **R**elationships | R | Connections between things |
| **P**erspectives | P | Different viewpoints |

### The 8 Elements (2 per pattern)
- **D:** identity / other
- **S:** part / whole
- **R:** action / reaction
- **P:** point / view

### The 3 Dynamics
1. **Equality (=):** Each pattern equals its co-implying elements
2. **Co-implication (⇔):** If one element exists, so does the other
3. **Simultaneity (✷):** Any element can be any other element

### The 6 Moves
| Move | Pattern | Description |
|------|---------|-------------|
| Is/Is Not | D | Define boundaries of a concept |
| Zoom In | S | Examine constituent parts |
| Zoom Out | S | Examine containing systems |
| Part Party | S | Parts AND their relationships |
| RDS Barbell | R | Relate → Distinguish → Systematize |
| P-Circle | P | Map multiple perspectives |

---

## Features

### Core Features (MVP)

#### 1. Infinite Canvas
- **Description:** Zoomable, pannable workspace for visual knowledge organization
- **Implementation:** tldraw library
- **User Value:** Unlimited space for complex knowledge maps

#### 2. AI-Powered DSRP Analysis
- **Description:** Claude AI applies the 6 moves to any concept
- **Implementation:** Anthropic Claude API with custom DSRP prompts
- **User Value:** Expert-level systems thinking analysis on demand

#### 3. File Ingestion
- **Description:** Upload PDFs, audio, and video for text extraction
- **Supported Formats:** PDF, MP3, WAV, MP4, WebM
- **Implementation:** pypdf, OpenAI Whisper, ffmpeg
- **User Value:** Analyze content from any source

#### 4. Knowledge Graph Storage
- **Description:** Persist concepts, relationships, and analyses
- **Implementation:** TypeDB knowledge graph database
- **User Value:** Build cumulative knowledge over time

#### 5. Export Capabilities
- **Markdown:** Plain text export
- **Obsidian:** Wikilink format with `[[concept]]` syntax
- **RemNote:** Flashcard format for spaced repetition
- **User Value:** Use knowledge in preferred tools

### Canvas Visualization

#### Concept Notes
- Color-coded by DSRP pattern:
  - 🔵 Blue: Distinctions (D)
  - 🟢 Green: Systems (S)
  - 🟠 Orange: Relationships (R)
  - 🟣 Purple: Perspectives (P)

#### Automatic Layout
- Analysis results automatically create connected note structures
- Arrows show relationships between concepts
- Pattern-appropriate layouts (circular for P-Circle, hierarchical for zoom-in/out)

---

## Technical Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   tldraw    │  │  DSRPPanel  │  │      Sidebar        │  │
│  │   Canvas    │  │  Analysis   │  │   File Upload       │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                           │                                  │
│                    Zustand Stores                           │
│         (canvasStore, sourceStore, conceptStore)            │
└─────────────────────────────────────────────────────────────┘
                            │
                       HTTP/REST
                            │
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │  /concepts │  │ /analysis  │  │  /sources  │            │
│  └────────────┘  └────────────┘  └────────────┘            │
│         │               │               │                   │
│  ┌──────────────────────────────────────────────┐          │
│  │              DSRP Agent (Claude)              │          │
│  └──────────────────────────────────────────────┘          │
│         │                                                   │
│  ┌──────────────────────────────────────────────┐          │
│  │           TypeDB Service Layer                │          │
│  └──────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                     TypeDB Database                          │
│                                                              │
│  Entities: concept, source, dsrp-analysis, canvas-note      │
│  Relations: distinction, system-structure, relationship-link│
│             perspective-view, extraction, analysis          │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | React 18 + TypeScript | UI framework |
| Canvas | tldraw 2.4 | Infinite canvas |
| State | Zustand | State management |
| Backend | FastAPI | REST API |
| AI | Claude API (Anthropic) | DSRP analysis |
| Database | TypeDB | Knowledge graph |
| PDF | pypdf | PDF text extraction |
| Audio | OpenAI Whisper | Audio transcription |
| Video | ffmpeg + Whisper | Video transcription |

---

## Data Model

### Concept Entity
```typescript
interface Concept {
  id: string
  name: string
  description?: string
  sourceIds: string[]
  analyses: DSRPAnalysis[]
  createdAt: Date
  updatedAt: Date
}
```

### DSRP Analysis
```typescript
interface DSRPAnalysis {
  id: string
  conceptId: string
  pattern: 'D' | 'S' | 'R' | 'P'
  move: DSRPMove
  elements: Record<string, unknown>
  reasoning: string
  confidenceScore: number
  relatedConcepts: string[]
  createdAt: Date
}
```

### DSRP Relations (stored in TypeDB)
- **Distinction:** identity concept ↔ other concept
- **System Structure:** whole concept ↔ part concept
- **Relationship Link:** action concept ↔ reaction concept
- **Perspective View:** observer concept ↔ observed concept

---

## User Flows

### Flow 1: Analyze a Concept

```
1. User enters concept name (e.g., "Climate Change")
2. User selects a move (e.g., "Zoom In")
3. User clicks "Analyze with AI"
4. System sends request to Claude API
5. Claude returns structured analysis
6. System stores analysis in TypeDB
7. System creates related concepts from analysis
8. System creates DSRP relations between concepts
9. Canvas displays concept notes with arrows
```

### Flow 2: Upload and Analyze a Document

```
1. User drops PDF file in upload zone
2. System extracts text from PDF
3. User views extracted text
4. User selects concept from document
5. User runs DSRP analysis on concept
6. Analysis linked to source document
```

### Flow 3: Export Knowledge Graph

```
1. User clicks "Export to Obsidian"
2. System queries all concepts and analyses from TypeDB
3. System generates Markdown with wikilinks
4. System downloads file to user's device
5. User imports into Obsidian vault
```

---

## Non-Functional Requirements

### Performance
- API response time < 500ms (excluding AI analysis)
- AI analysis < 10 seconds
- Canvas smooth at 60fps with 1000+ notes
- File upload progress feedback

### Reliability
- Graceful degradation when TypeDB unavailable
- In-memory fallback for data operations
- Error handling with user-friendly messages

### Security
- Input validation on all endpoints
- SQL/injection prevention (TypeQL parameterization)
- File type validation for uploads
- No sensitive data in logs

### Scalability
- Stateless backend (horizontal scaling ready)
- TypeDB handles graph queries efficiently
- Canvas virtualization for large graphs

---

## Success Metrics

### Engagement
- Analyses performed per session
- Concepts created per user
- Export downloads

### Quality
- AI analysis confidence scores
- User corrections/edits to analyses
- Time spent per analysis

### Adoption
- Daily active users
- Knowledge graphs created
- Return user rate

---

## Roadmap

### Phase 1: MVP (Current)
- ✅ Infinite canvas with tldraw
- ✅ DSRP analysis with 6 moves
- ✅ File upload (PDF, audio, video)
- ✅ TypeDB integration
- ✅ Export to Markdown/Obsidian/RemNote
- ✅ Canvas visualization of analyses

### Phase 2: Collaboration
- [ ] User authentication
- [ ] Shared canvases
- [ ] Real-time collaboration
- [ ] Comment threads on concepts

### Phase 3: Intelligence
- [ ] Automatic concept extraction from documents
- [ ] Suggested analyses based on context
- [ ] Pattern recognition across knowledge base
- [ ] Knowledge graph visualization (force-directed)

### Phase 4: Integration
- [ ] Obsidian plugin (direct sync)
- [ ] RemNote integration
- [ ] Notion import/export
- [ ] Zotero bibliography integration

---

## Appendix

### A. DSRP Research References

1. Cabrera, D., & Cabrera, L. (2015). *Systems Thinking Made Simple: New Hope for Solving Wicked Problems*. Odyssean Press.

2. Cabrera, D., Cabrera, L., & Powers, E. (2015). A unifying theory of systems thinking with psychosocial applications. *Systems Research and Behavioral Science*, 32(5), 534-545.

### B. Glossary

| Term | Definition |
|------|------------|
| DSRP | Distinctions, Systems, Relationships, Perspectives |
| Co-implication | Two elements that necessarily exist together |
| Simultaneity | Any element can function as any other element |
| Wikilink | Obsidian's `[[concept]]` linking syntax |
| Knowledge Graph | Database storing entities and their relationships |

### C. API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/concepts/ | Create concept |
| GET | /api/concepts/ | List concepts |
| GET | /api/concepts/{id} | Get concept |
| DELETE | /api/concepts/{id} | Delete concept |
| POST | /api/analysis/dsrp | DSRP analysis |
| POST | /api/analysis/batch | Batch analysis |
| POST | /api/sources/upload | Upload file |
| GET | /api/sources/{id}/status | Check status |
| POST | /api/export/markdown | Export markdown |
| POST | /api/export/obsidian | Export obsidian |
| POST | /api/export/remnote | Export remnote |
