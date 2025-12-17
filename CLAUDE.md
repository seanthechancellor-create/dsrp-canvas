# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DSRP Canvas is a full-stack knowledge analysis application that uses Dr. Derek Cabrera's DSRP 4-8-3 systems thinking framework. It features an infinite canvas UI for visualizing knowledge, AI-powered analysis agents, and export capabilities for Obsidian/RemNote.

## DSRP 4-8-3 Framework

Understanding this framework is essential for working on this codebase:

**4 Patterns:**
- **D** (Distinctions): identity/other - what something IS and IS NOT
- **S** (Systems): part/whole - components and containers
- **R** (Relationships): action/reaction - connections between things
- **P** (Perspectives): point/view - different viewpoints

**8 Elements:** Each pattern has 2 co-implying elements (D: i/o, S: p/w, R: a/r, P: ρ/v)

**3 Dynamics:** Equality (=), Co-implication (⇔), Simultaneity (✷)

**8 Moves (implemented in `backend/agents/dsrp_agent.py`):**
1. Is/Is Not - Define boundaries (D)
2. Zoom In - Examine parts (S)
3. Zoom Out - Examine whole/context (S)
4. Part Party - Parts + their relationships (S)
5. RDS Barbell - Relate → Distinguish → Systematize (R)
6. P-Circle - Map multiple perspectives (P)
7. WoC (Web of Causality) - Forward causal analysis, map downstream effects (R)
8. WAoC (Web of Anticausality) - Root cause analysis, trace upstream causes (R)

## Commands

### Development

```bash
# Start all services (TypeDB, backend, frontend)
docker-compose up

# Or run individually:

# Backend (requires Python 3.11+)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (requires Node 20+)
cd frontend
npm install
npm run dev

# TypeDB (requires Docker)
docker run -p 1729:1729 vaticle/typedb:2.28.0
```

### Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Linting

```bash
# Backend
cd backend
ruff check .
ruff format .

# Frontend
cd frontend
npm run lint
```

### TypeDB Schema

```bash
# Load schema (TypeDB must be running)
typedb console
> database create dsrp_canvas
> transaction dsrp_canvas schema write
> source typedb/schema/dsrp-schema.tql
> commit
```

## Architecture

```
dsrp-canvas/
├── frontend/                 # React + tldraw infinite canvas
│   ├── src/
│   │   ├── components/       # UI components (Sidebar, DSRPPanel)
│   │   ├── stores/           # Zustand state (canvasStore, sourceStore)
│   │   ├── hooks/            # Custom hooks (useDSRPAnalysis)
│   │   └── types/            # TypeScript types for DSRP
│   └── package.json
│
├── backend/                  # Python FastAPI
│   ├── app/
│   │   ├── api/              # REST endpoints
│   │   │   ├── sources.py    # File upload/processing
│   │   │   ├── analysis.py   # DSRP analysis endpoints
│   │   │   ├── concepts.py   # Knowledge graph CRUD
│   │   │   └── export.py     # Markdown/RemNote export
│   │   ├── models/           # Pydantic models
│   │   └── services/         # Business logic
│   ├── agents/
│   │   ├── dsrp_agent.py     # Claude AI integration for 8 Moves
│   │   └── prompts.py        # DSRP prompt templates
│   └── requirements.txt
│
├── typedb/
│   └── schema/
│       └── dsrp-schema.tql   # Knowledge graph schema
│
└── docker-compose.yml
```

## Key Integration Points

### AI Analysis Flow
1. User selects a concept and move in `DSRPPanel.tsx`
2. Frontend calls `/api/analysis/dsrp` via `useDSRPAnalysis` hook
3. Backend routes to `DSRPAgent.analyze()` in `agents/dsrp_agent.py`
4. Agent uses Claude API with move-specific prompts
5. Results stored in TypeDB and returned to canvas

### File Ingestion Flow
1. Files dropped in `Sidebar.tsx` upload zone
2. `sourceStore.ts` uploads to `/api/sources/upload`
3. `ingestion.py` processes PDF/audio/video in background
4. Extracted text available for DSRP analysis

### Export Flow
1. User triggers export in `DSRPPanel.tsx`
2. `/api/export/{format}` generates output
3. Markdown uses `[[wikilinks]]` for Obsidian
4. RemNote format creates Q&A flashcards from analyses

## Environment Variables

Copy `.env.example` to `.env` and configure:
- `ANTHROPIC_API_KEY` - Required for AI analysis
- `TYPEDB_HOST/PORT` - Knowledge graph connection
- `VITE_API_URL` - Backend URL for frontend

## TypeDB Schema Concepts

The schema models DSRP patterns as relations:
- `distinction` relates `identity` ↔ `other`
- `system-structure` relates `part` ↔ `whole`
- `relationship-link` relates `action` ↔ `reaction`
- `perspective-view` relates `point` ↔ `view`

Causal analysis relations (WoC/WAoC):
- `causal_link` relates `cause` → `effect` with strength/time_horizon
- `web_of_causality` maps forward effects from a focal cause
- `web_of_anticausality` traces root causes to a focal effect

Concepts can play multiple roles simultaneously (Simultaneity dynamic).
