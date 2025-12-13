# DSRP Canvas

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

**6 Moves (implemented in `backend/agents/dsrp_agent.py`):**
1. Is/Is Not - Define boundaries (D)
2. Zoom In - Examine parts (S)
3. Zoom Out - Examine whole/context (S)
4. Part Party - Parts + their relationships (S)
5. RDS Barbell - Relate → Distinguish → Systematize (R)
6. P-Circle - Map multiple perspectives (P)

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Node.js 20+
- Python 3.11+

### Quick Start
Start all services (TypeDB, backend, frontend):
```bash
docker-compose up
```

### Manual Setup

**Backend**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

**TypeDB**
```bash
docker run -p 1729:1729 vaticle/typedb:2.28.0
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
│   │   ├── models/           # Pydantic models
│   │   └── services/         # Business logic
│   ├── agents/
│   │   ├── dsrp_agent.py     # Claude AI integration for 6 Moves
│   │   └── prompts.py        # DSRP prompt templates
│   └── requirements.txt
│
├── typedb/
│   └── schema/
│       └── dsrp-schema.tql   # Knowledge graph schema
│
└── docker-compose.yml
```

## Key Features

### AI Analysis
- User selects a concept and move in `DSRPPanel.tsx`
- Backend routes to `DSRPAgent.analyze()` in `agents/dsrp_agent.py`
- Agent uses Claude API with move-specific prompts
- Results stored in TypeDB and returned to canvas

### File Ingestion
- Files dropped in `Sidebar.tsx` upload zone
- `ingestion.py` processes PDF/audio/video in background
- Extracted text available for DSRP analysis

### Export
- Markdown uses `[[wikilinks]]` for Obsidian
- RemNote format creates Q&A flashcards from analyses

## Configuration

Copy `.env.example` to `.env` and configure:
- `ANTHROPIC_API_KEY` - Required for AI analysis
- `TYPEDB_HOST/PORT` - Knowledge graph connection
- `VITE_API_URL` - Backend URL for frontend
