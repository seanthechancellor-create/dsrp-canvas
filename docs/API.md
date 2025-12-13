# DSRP Canvas API Documentation

## Overview

The DSRP Canvas API provides endpoints for managing knowledge concepts, performing DSRP analysis using AI, handling file sources, and exporting knowledge graphs.

**Base URL:** `http://localhost:8000/api`

**Authentication:** Currently no authentication required (development mode)

---

## Endpoints

### Health Check

#### GET /health

Check if the API is running.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

---

## Concepts API

### POST /api/concepts/

Create a new concept in the knowledge graph.

**Request Body:**
```json
{
  "name": "string (required)",
  "description": "string (optional)",
  "source_ids": ["string"] (optional, default: [])
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "name": "string",
  "description": "string | null",
  "source_ids": ["string"],
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/concepts/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Democracy", "description": "A system of government"}'
```

---

### GET /api/concepts/

List all concepts with pagination.

**Query Parameters:**
- `limit` (int, default: 50): Maximum number of concepts to return
- `offset` (int, default: 0): Number of concepts to skip

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "name": "string",
    "description": "string | null",
    "source_ids": ["string"],
    "created_at": "datetime",
    "updated_at": "datetime"
  }
]
```

---

### GET /api/concepts/{concept_id}

Get a specific concept by ID.

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "name": "string",
  "description": "string | null",
  "source_ids": ["string"],
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

**Error:** `404 Not Found` if concept doesn't exist

---

### DELETE /api/concepts/{concept_id}

Delete a concept.

**Response:** `200 OK`
```json
{
  "deleted": "uuid"
}
```

---

## Analysis API

### POST /api/analysis/dsrp

Perform DSRP analysis on a concept using AI.

**Request Body:**
```json
{
  "concept": "string (required)",
  "move": "string (required)",
  "context": "string (optional)"
}
```

**Valid Moves:**
| Move | Pattern | Description |
|------|---------|-------------|
| `is-is-not` | D (Distinctions) | Define what it is AND is not |
| `zoom-in` | S (Systems) | Examine the parts |
| `zoom-out` | S (Systems) | Examine the broader system |
| `part-party` | S (Systems) | Break into parts and relate them |
| `rds-barbell` | R (Relationships) | Relate → Distinguish → Systematize |
| `p-circle` | P (Perspectives) | Map multiple perspectives |

**Response:** `200 OK`
```json
{
  "pattern": "D | S | R | P",
  "elements": {
    // Varies by move type
  },
  "move": "string",
  "reasoning": "string",
  "related_concepts": ["string"],
  "confidence": 0.0-1.0
}
```

**Example Response (is-is-not):**
```json
{
  "pattern": "D",
  "elements": {
    "identity": "A system of government by the whole population",
    "other": "Autocracy, dictatorship, monarchy"
  },
  "boundary": "Citizen participation in governance",
  "move": "is-is-not",
  "reasoning": "Democracy is defined by collective decision-making...",
  "related_concepts": ["Government", "Voting", "Citizens"],
  "confidence": 0.85
}
```

**Example Response (zoom-in):**
```json
{
  "pattern": "S",
  "elements": {
    "whole": "Democracy",
    "parts": ["Voting System", "Legislative Branch", "Executive Branch"]
  },
  "part_descriptions": {
    "Voting System": "The mechanism for citizen participation"
  },
  "move": "zoom-in",
  "reasoning": "Democracy consists of several interconnected systems...",
  "related_concepts": ["Voting System", "Legislative Branch"],
  "confidence": 0.9
}
```

**Example Response (p-circle):**
```json
{
  "pattern": "P",
  "elements": {
    "concept": "Democracy",
    "perspectives": [
      {"point": "Citizen", "view": "A system that gives me a voice"},
      {"point": "Politician", "view": "A framework for legitimate authority"}
    ]
  },
  "tensions": ["Individual rights vs collective good"],
  "synthesis": "Different stakeholders value different aspects...",
  "move": "p-circle",
  "reasoning": "Multiple perspectives reveal different facets...",
  "related_concepts": ["Citizen", "Politician"],
  "confidence": 0.85
}
```

**Error:** `400 Bad Request` if move is invalid

---

### POST /api/analysis/batch

Analyze multiple concepts with all or specified moves.

**Request Body:** Array of concept names
```json
["Democracy", "Freedom", "Justice"]
```

**Query Parameters:**
- `moves` (array, optional): Specific moves to apply. Default: all 6 moves

**Response:** `200 OK`
```json
[
  {
    "concept": "Democracy",
    "analyses": {
      "is-is-not": { ... },
      "zoom-in": { ... },
      // ...
    }
  }
]
```

---

## Sources API

### POST /api/sources/upload

Upload a file (PDF, audio, or video) for text extraction.

**Request:** `multipart/form-data`
- `file`: The file to upload

**Supported Formats:**
- PDF: `.pdf`
- Audio: `.mp3`, `.wav`, `.ogg`, `.m4a`
- Video: `.mp4`, `.webm`, `.mov`, `.avi`

**Response:** `200 OK`
```json
{
  "source_id": "uuid",
  "file_path": "string",
  "status": "processing"
}
```

---

### GET /api/sources/{source_id}/status

Check the processing status of an uploaded source.

**Response:** `200 OK`
```json
{
  "source_id": "uuid",
  "status": "uploading | processing | ready | error",
  "extracted_text": "string | null",
  "error": "string | null"
}
```

---

### GET /api/sources/

List all sources.

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "filename": "string",
    "source_type": "pdf | audio | video",
    "status": "string"
  }
]
```

---

## Export API

### POST /api/export/markdown

Export concepts to plain Markdown format.

**Request Body:**
```json
{
  "concept_ids": ["uuid"],
  "include_analyses": true,
  "include_relationships": true
}
```

**Response:** `200 OK`
```json
{
  "content": "# DSRP Knowledge Export\n\n## Concept Name\n..."
}
```

---

### POST /api/export/obsidian

Export to Obsidian-compatible Markdown with `[[wikilinks]]`.

**Request Body:**
```json
{
  "concept_ids": ["uuid"],
  "include_analyses": true,
  "include_relationships": true
}
```

**Response:** `200 OK`
```json
{
  "content": "# DSRP Knowledge Export\n\nTags: #dsrp #systems-thinking\n\n## [[Concept Name]]\n..."
}
```

---

### POST /api/export/remnote

Export to RemNote flashcard format for spaced repetition.

**Request Body:**
```json
{
  "concept_ids": ["uuid"],
  "include_analyses": true
}
```

**Response:** `200 OK`
```json
{
  "cards": [
    {
      "front": "What IS Democracy?",
      "back": "A system of government by the whole population",
      "tags": ["dsrp", "distinctions", "Democracy"]
    }
  ],
  "count": 1
}
```

---

## Error Responses

All endpoints may return these error responses:

### 400 Bad Request
```json
{
  "detail": "Error message describing what went wrong"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## TypeDB Schema

The API stores data in TypeDB with the following schema:

### Entities
- `concept`: Knowledge concepts with name, description
- `source`: Uploaded files (PDF, audio, video)
- `dsrp-analysis`: Analysis results from AI
- `canvas-note`: Canvas UI notes

### DSRP Relations
- `distinction`: identity ↔ other (D pattern)
- `system-structure`: whole ↔ part (S pattern)
- `relationship-link`: action ↔ reaction (R pattern)
- `perspective-view`: point ↔ view (P pattern)

### Supporting Relations
- `extraction`: Links sources to extracted concepts
- `analysis`: Links concepts to their DSRP analyses
- `note-link`: Links canvas notes to concepts

---

## Semantic Search API

### GET /api/search/concepts

Search concepts by semantic similarity using vector embeddings.

**Query Parameters:**
- `q` (string, required): Search query (min 2 characters)
- `limit` (int, default: 10): Maximum results (1-50)
- `threshold` (float, default: 0.7): Minimum similarity score (0-1)

**Response:** `200 OK`
```json
{
  "query": "government systems",
  "results": [
    {
      "id": "uuid",
      "name": "Democracy",
      "content": "Concept: Democracy\nDescription: A system of government",
      "similarity": 0.89,
      "type": "concept"
    }
  ],
  "total": 1
}
```

---

### GET /api/search/analyses

Search DSRP analyses by semantic similarity.

**Query Parameters:**
- `q` (string, required): Search query
- `move` (string, optional): Filter by move type (e.g., `zoom-in`, `p-circle`)
- `limit` (int, default: 10): Maximum results
- `threshold` (float, default: 0.7): Minimum similarity

**Response:** `200 OK`
```json
{
  "query": "parts and components",
  "results": [
    {
      "id": "analysis-uuid",
      "name": "zoom-in analysis",
      "content": "DSRP Analysis (zoom-in): Democracy consists of...",
      "similarity": 0.85,
      "type": "analysis"
    }
  ],
  "total": 1
}
```

---

### GET /api/search/sources

Search source content by semantic similarity (RAG retrieval).

**Query Parameters:**
- `q` (string, required): Search query
- `source_ids` (string, optional): Comma-separated source IDs to filter
- `limit` (int, default: 10): Maximum results
- `threshold` (float, default: 0.7): Minimum similarity

**Response:** `200 OK`
```json
{
  "query": "machine learning",
  "results": [
    {
      "id": "source-uuid:5",
      "name": "Source chunk 5",
      "content": "Machine learning is a subset of AI...",
      "similarity": 0.92,
      "type": "source"
    }
  ],
  "total": 1
}
```

---

### GET /api/search/similar/{concept_id}

Find concepts similar to a given concept.

**Query Parameters:**
- `limit` (int, default: 5): Maximum results (1-20)

**Response:** `200 OK`
```json
{
  "concept_id": "uuid",
  "similar": [
    {
      "concept_id": "uuid2",
      "concept_name": "Government",
      "similarity": 0.82
    }
  ]
}
```

---

### POST /api/search/initialize

Initialize the vector store tables (PostgreSQL + pgvector).

**Response:** `200 OK`
```json
{
  "status": "initialized"
}
```

---

## Cache API

### GET /api/cache/stats

Get cache statistics including hit/miss ratios and memory usage.

**Response:** `200 OK`
```json
{
  "available": true,
  "hits": 1234,
  "misses": 56,
  "memory_used": "2.5M",
  "total_keys": 89,
  "keys_by_type": {
    "concepts": 45,
    "analyses": 30,
    "relations": 10,
    "sources": 4,
    "searches": 0,
    "exports": 0
  }
}
```

---

### GET /api/cache/health

Check if cache (Redis) is available and healthy.

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "message": "Redis connected and operational"
}
```

---

### POST /api/cache/invalidate/concept/{concept_id}

Invalidate all cache entries for a concept.

**Response:** `200 OK`
```json
{
  "status": "invalidated",
  "concept_id": "uuid"
}
```

---

### POST /api/cache/warmup

Pre-populate cache with commonly accessed data.

**Response:** `200 OK`
```json
{
  "status": "warmed",
  "concepts_cached": 45,
  "sources_cached": 10
}
```

---

### POST /api/cache/clear

Clear all DSRP cache entries (use with caution).

**Response:** `200 OK`
```json
{
  "status": "cleared",
  "message": "All DSRP cache entries removed"
}
```

---

## MCP Server

The DSRP Canvas includes an MCP (Model Context Protocol) server for Claude Desktop integration.

### Running the MCP Server

```bash
# With STDIO (for Claude Desktop)
fastmcp run backend/mcp/dsrp_server.py

# With SSE (for web)
fastmcp run backend/mcp/dsrp_server.py --transport sse --port 8001
```

### Available Tools

| Tool | Description |
|------|-------------|
| `analyze_concept` | Analyze a concept using one of the 6 DSRP moves |
| `explain_dsrp_framework` | Get explanation of DSRP 4-8-3 framework |
| `create_concept` | Create a new concept in the knowledge graph |
| `search_concepts` | Search for concepts by name |
| `get_concept_analysis` | Get all analyses for a concept |
| `export_to_markdown` | Export knowledge graph to Markdown |
| `export_to_obsidian` | Export with Obsidian [[wikilinks]] |

### Available Resources

| Resource | Description |
|----------|-------------|
| `dsrp://concepts` | List all concepts |
| `dsrp://concepts/{id}` | Get specific concept with analyses |
| `dsrp://sources` | List all sources |

### Available Prompts

| Prompt | Description |
|--------|-------------|
| `dsrp_analysis_prompt` | Generate analysis prompt for a pattern (D/S/R/P) |
| `six_moves_prompt` | Generate comprehensive 6-moves analysis prompt |

---

## Interactive Documentation

FastAPI provides automatic interactive documentation:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
