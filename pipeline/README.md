# DSRP Knowledge Ingestion Pipeline

A Python-based document processing pipeline that analyzes documents using the DSRP-483 framework and stores results in both PostgreSQL/pgvector (vector search) and TypeDB (knowledge graph).

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Document  │────▶│   Chunker   │────▶│  Embedder   │
│  (PDF/TXT)  │     │ (LangChain) │     │(Sentence-   │
└─────────────┘     └─────────────┘     │ Transformers)│
                                        └──────┬──────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          │                          │
                    ▼                          ▼                          ▼
           ┌───────────────┐          ┌───────────────┐          ┌───────────────┐
           │  PostgreSQL   │          │    Claude     │          │    TypeDB     │
           │  + pgvector   │          │   (DSRP       │─────────▶│  (Semantic    │
           │  (Episodic)   │          │  Extraction)  │          │   Memory)     │
           └───────────────┘          └───────────────┘          └───────────────┘
                 │                                                      │
                 │  Vector Search (RAG)                                 │  Knowledge Graph
                 │  - Find similar chunks                               │  - Distinctions (D)
                 │  - Context retrieval                                 │  - Systems (S)
                 └──────────────────────────┬───────────────────────────┘  - Relationships (R)
                                            │                              - Perspectives (P)
                                            ▼
                                    ┌───────────────┐
                                    │   Frontend    │
                                    │  (React +     │
                                    │   Canvas)     │
                                    └───────────────┘
```

## Quick Start

### 1. Start the required services

```bash
# Start PostgreSQL and TypeDB
docker-compose up -d postgres typedb

# Wait for services to be healthy
docker-compose ps
```

### 2. Place documents in the inbox

```bash
# Copy your documents to the inbox folder
cp your_document.pdf ./documents/inbox/
```

### 3. Run the pipeline

**Option A: Run in Docker (recommended)**

```bash
# Build the pipeline container
docker-compose build pipeline

# Run the pipeline
docker-compose --profile tools run --rm pipeline python ingest.py
```

**Option B: Run locally**

```bash
cd pipeline

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ANTHROPIC_API_KEY="your-api-key"
export POSTGRES_URL="postgresql://dsrp:dsrp_password@localhost:5432/dsrp_canvas"
export TYPEDB_HOST="localhost"
export TYPEDB_PORT="1729"

# Run the pipeline
python ingest.py
```

## Usage Examples

```bash
# Process all files in inbox
python ingest.py

# Process a specific file
python ingest.py --file /path/to/document.pdf

# Enable verbose logging
python ingest.py --verbose
```

## Supported File Types

- **PDF** (.pdf) - Requires `pypdf` library
- **Text** (.txt, .md, .text) - Plain text files

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `ANTHROPIC_API_KEY` | (required) | Your Anthropic API key for Claude |
| `GOOGLE_API_KEY` | (optional) | Google API key for Gemini (alternative LLM) |
| `OPENAI_API_KEY` | (optional) | OpenAI API key for GPT (alternative LLM) |
| `POSTGRES_URL` | `postgresql://dsrp:dsrp_password@localhost:5432/dsrp_canvas` | PostgreSQL connection string |
| `TYPEDB_HOST` | `localhost` | TypeDB server hostname |
| `TYPEDB_PORT` | `1729` | TypeDB server port |
| `TYPEDB_DATABASE` | `dsrp_483` | TypeDB database name |
| `TYPEDB_USERNAME` | `admin` | TypeDB username |
| `TYPEDB_PASSWORD` | `password` | TypeDB password |

## Pipeline Stages

### 1. Ingest
Load documents from the inbox folder. PDFs are converted to text using `pypdf`.

### 2. Chunk
Split text into manageable pieces using LangChain's `RecursiveCharacterTextSplitter`:
- Chunk size: 1500 characters (~375 tokens)
- Overlap: 200 characters (maintains context between chunks)
- Splits on: paragraphs → sentences → words

### 3. Embed
Generate vector embeddings using `sentence-transformers`:
- Model: `all-MiniLM-L6-v2`
- Dimensions: 384
- Runs locally (no API key needed)

### 4. Store Episodic Memory (PostgreSQL/pgvector)
Save each chunk with its embedding:
```json
{
  "id": "doc123_chunk_1",
  "document_id": "doc123",
  "chunk_number": 1,
  "text": "The actual text content...",
  "embedding": [0.123, -0.456, ...],
  "dsrp_extracted": true
}
```

### 5. Extract DSRP (Claude/Gemini/GPT)
Send each chunk to the LLM with a specialized prompt that extracts:
- **Distinctions (D)**: Identity/Other pairs
- **Systems (S)**: Part/Whole relationships
- **Relationships (R)**: Action/Reaction pairs
- **Perspectives (P)**: Point/View pairs

### 6. Store Semantic Memory (TypeDB)
Insert structured DSRP patterns into the knowledge graph:
- Concepts (nodes)
- Distinction relations
- System structure relations
- Relationship links
- Perspective views

## Output Example

```
2024-01-15 10:30:15 | INFO     | Processing: privacy_policy.pdf
2024-01-15 10:30:16 | INFO     | Extracted 15,234 characters of text
2024-01-15 10:30:16 | INFO     | Split into 12 chunks
2024-01-15 10:30:17 | INFO     | Processing chunk 1/12 (1,423 chars)
2024-01-15 10:30:20 | INFO     | Stored distinction: 'Personal Data' vs 'Anonymous Data'
2024-01-15 10:30:20 | INFO     | Stored system: 'Privacy Program' with 4 parts
...
2024-01-15 10:32:45 | INFO     | ----------------------------------------
2024-01-15 10:32:45 | INFO     | COMPLETED: privacy_policy.pdf
2024-01-15 10:32:45 | INFO     |   Chunks: 12
2024-01-15 10:32:45 | INFO     |   DSRP Extractions: 12
2024-01-15 10:32:45 | INFO     |   Distinctions (D): 8
2024-01-15 10:32:45 | INFO     |   Systems (S): 5
2024-01-15 10:32:45 | INFO     |   Relationships (R): 11
2024-01-15 10:32:45 | INFO     |   Perspectives (P): 4
2024-01-15 10:32:45 | INFO     | ----------------------------------------
```

## Querying the Results

### PostgreSQL/pgvector (Vector Search)

```python
import psycopg

conn = psycopg.connect("postgresql://dsrp:dsrp_password@localhost:5432/dsrp_canvas")

# Find similar chunks (for RAG)
with conn.cursor() as cur:
    cur.execute("""
        SELECT id, text, 1 - (embedding <=> %s::vector) as similarity
        FROM pipeline_chunks
        ORDER BY embedding <=> %s::vector
        LIMIT 5;
    """, (query_embedding, query_embedding))
    results = cur.fetchall()
```

### TypeDB (Knowledge Graph)

```
# Find all distinctions
match $d isa distinction; get $d;

# Find all systems with their parts
match
  $s (whole: $whole, part: $part) isa system_structure;
  $whole has name $whole_name;
  $part has name $part_name;
get $whole_name, $part_name;

# Find all relationships
match
  $r (action: $a, reaction: $re) isa relationship_link;
  $a has name $action_name;
  $re has name $reaction_name;
get $action_name, $reaction_name;
```

## Troubleshooting

### "pypdf not installed"
```bash
pip install pypdf
```

### "TypeDB not connected"
```bash
# Check TypeDB is running
docker-compose ps typedb

# Check logs
docker-compose logs typedb
```

### "No API key set"
```bash
# Set at least one LLM API key
export ANTHROPIC_API_KEY="sk-ant-..."
# OR
export GOOGLE_API_KEY="..."
# OR
export OPENAI_API_KEY="sk-..."
```

### "PostgreSQL connection failed"
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Test connection
docker-compose exec postgres psql -U dsrp -d dsrp_canvas -c "SELECT 1;"
```

## Scale Considerations

For large knowledge maps with thousands of documents:

1. **HNSW Index**: The pgvector HNSW index provides efficient approximate nearest neighbor search
2. **Batch Processing**: Process documents in batches to manage memory
3. **Pagination**: Use LIMIT/OFFSET or cursor-based pagination for large result sets
4. **Connection Pooling**: The pipeline uses psycopg connection pooling for efficiency
