# DSRP Canvas Architecture Recommendations

## 1. MCP Server Options

### Current State
No MCP server implemented. The backend uses direct REST API calls to Claude.

### Recommendation: FastMCP 2.0

**Why FastMCP?**
- Pythonic, decorator-based API matches existing FastAPI backend style
- Built-in support for Tools, Resources, and Prompts
- Enterprise auth support (GitHub, Azure, Auth0)
- SSE transport for web deployments
- Actively maintained (incorporated into official MCP SDK)

### Implementation Example

```python
# backend/mcp/dsrp_server.py
from fastmcp import FastMCP, Context

mcp = FastMCP("DSRP Canvas MCP Server")

# Expose DSRP analysis as a tool
@mcp.tool()
async def analyze_concept(
    concept: str,
    move: str,  # is-is-not, zoom-in, zoom-out, part-party, rds-barbell, p-circle
    ctx: Context
) -> dict:
    """Analyze a concept using DSRP framework"""
    from app.agents.dsrp_agent import DSRPAgent
    agent = DSRPAgent()
    return await agent.analyze(concept, move)

# Expose knowledge graph as a resource
@mcp.resource("dsrp://concepts/{concept_id}")
async def get_concept(concept_id: str) -> dict:
    """Get a concept and its DSRP analyses"""
    from app.services.typedb_service import TypeDBService
    service = TypeDBService()
    return await service.get_concept(concept_id)

# Expose sources as resources
@mcp.resource("dsrp://sources")
async def list_sources() -> list:
    """List all ingested sources"""
    from app.services.typedb_service import TypeDBService
    service = TypeDBService()
    return await service.get_sources()

# DSRP prompt templates
@mcp.prompt()
def dsrp_analysis_prompt(concept: str, pattern: str) -> str:
    """Generate DSRP analysis prompt"""
    prompts = {
        'D': f"Apply Distinctions to '{concept}': What IS it? What is it NOT?",
        'S': f"Apply Systems thinking to '{concept}': What are its PARTS? What WHOLE is it part of?",
        'R': f"Apply Relationships to '{concept}': What does it RELATE to? How?",
        'P': f"Apply Perspectives to '{concept}': Who views it? What do they see?",
    }
    return prompts.get(pattern, prompts['D'])
```

### Running the MCP Server

```bash
# Install FastMCP
pip install fastmcp

# Run with STDIO (for Claude Desktop)
fastmcp run backend/mcp/dsrp_server.py

# Run with SSE (for web)
fastmcp run backend/mcp/dsrp_server.py --transport sse --port 8001
```

### Benefits for DSRP Canvas
1. **Claude Desktop Integration**: Users can query their knowledge graph directly from Claude
2. **Standardized Protocol**: Any MCP-compatible client can use DSRP Canvas
3. **Resource Exposure**: Knowledge graph accessible as MCP resources
4. **Tool Chaining**: LLMs can chain multiple DSRP analyses

---

## 2. Database Comparison

### Option A: TypeDB (Current)

| Aspect | Rating | Notes |
|--------|--------|-------|
| DSRP Fit | ⭐⭐⭐⭐⭐ | Native support for relationships, type system matches DSRP patterns |
| Schema | ⭐⭐⭐⭐⭐ | Enforced semantics, perfect for D/S/R/P relations |
| AI/RAG | ⭐⭐⭐⭐⭐ | TypeQL optimized for LLM generation |
| Learning Curve | ⭐⭐ | Steep, TypeQL is unique |
| Community | ⭐⭐ | Smaller community |
| Hosting | ⭐⭐ | Self-hosted or TypeDB Cloud |

**Best for**: Pure knowledge graph use cases, semantic reasoning, AI-native applications

### Option B: Microsoft SQL Server

| Aspect | Rating | Notes |
|--------|--------|-------|
| DSRP Fit | ⭐⭐⭐ | Graph features exist but bolted-on |
| Schema | ⭐⭐⭐⭐ | Strong relational schema |
| AI/RAG | ⭐⭐⭐ | SQL Server 2025 adds vector search |
| Learning Curve | ⭐⭐⭐⭐ | Widely known T-SQL |
| Community | ⭐⭐⭐⭐⭐ | Massive ecosystem |
| Hosting | ⭐⭐⭐⭐⭐ | Azure SQL, on-prem, many options |

**SQL Server Graph Features:**
- Node and Edge tables
- MATCH clause for graph patterns
- SHORTEST_PATH function
- Edge constraints
- GraphQL support via Data API Builder (SQL Server 2025)

**Limitations for DSRP:**
- No native inference/reasoning
- JOINs still needed for complex traversals
- Graph features feel "added on" rather than native
- No nested relationships (must reify to nodes)

### Option C: Neo4j

| Aspect | Rating | Notes |
|--------|--------|-------|
| DSRP Fit | ⭐⭐⭐⭐ | Excellent graph model, Cypher is intuitive |
| Schema | ⭐⭐⭐ | Optional schema (can be good or bad) |
| AI/RAG | ⭐⭐⭐ | Java functions required, not LLM-friendly |
| Learning Curve | ⭐⭐⭐⭐ | Cypher is readable |
| Community | ⭐⭐⭐⭐⭐ | Largest graph DB community |
| Hosting | ⭐⭐⭐⭐ | Neo4j Aura, self-hosted |

**Best for**: General graph applications, well-known patterns

### Option D: PostgreSQL + Apache AGE

| Aspect | Rating | Notes |
|--------|--------|-------|
| DSRP Fit | ⭐⭐⭐⭐ | Graph extension with Cypher support |
| Schema | ⭐⭐⭐⭐ | PostgreSQL's strong typing |
| AI/RAG | ⭐⭐⭐⭐ | pgvector for embeddings |
| Learning Curve | ⭐⭐⭐⭐⭐ | SQL + Cypher, widely known |
| Community | ⭐⭐⭐⭐⭐ | PostgreSQL's massive community |
| Hosting | ⭐⭐⭐⭐⭐ | Supabase, Neon, any PG host |

**Best for**: Teams wanting graph + relational + vector in one DB

---

## 3. Recommendation Matrix

### For DSRP Canvas Specifically

| Priority | Database | Why |
|----------|----------|-----|
| 1st | **TypeDB** | Native semantic modeling matches DSRP 4-8-3 perfectly |
| 2nd | **PostgreSQL + AGE** | Best balance of graph + relational + hosting options |
| 3rd | **Neo4j** | If you need mature graph ecosystem |
| 4th | **SQL Server** | Only if you're already in Microsoft ecosystem |

### SQL Server Verdict

**Should you use SQL Server for DSRP Canvas?**

**No, unless:**
- You're already heavily invested in Microsoft/Azure
- Your organization mandates SQL Server
- You need to integrate with existing SQL Server data

**Reasons:**
1. Graph features are secondary, not native
2. DSRP's relationship-heavy model needs true graph database
3. TypeQL's semantic types map 1:1 to DSRP patterns
4. SQL Server's JOINs become unwieldy for deep graph traversals
5. No built-in inference for DSRP's co-implication dynamics

---

## 4. Recommended Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Claude Desktop                            │
│                              │                                   │
│                         MCP Protocol                             │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  FastMCP Server                          │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────────────────────┐  │    │
│  │  │ Tools   │  │Resources│  │ Prompts                 │  │    │
│  │  │ analyze │  │concepts │  │ dsrp_analysis_prompt    │  │    │
│  │  │ ingest  │  │sources  │  │ six_moves_prompt        │  │    │
│  │  │ export  │  │analyses │  │                         │  │    │
│  │  └─────────┘  └─────────┘  └─────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  FastAPI Backend                         │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌───────────┐  │    │
│  │  │ Sources │  │Concepts │  │Analysis │  │  Export   │  │    │
│  │  │   API   │  │   API   │  │   API   │  │    API    │  │    │
│  │  └─────────┘  └─────────┘  └─────────┘  └───────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│            ┌─────────────────┼─────────────────┐                │
│            ▼                 ▼                 ▼                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   TypeDB     │  │  pgvector    │  │    Redis     │          │
│  │ Knowledge    │  │  Embeddings  │  │   Cache      │          │
│  │   Graph      │  │              │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     React Frontend                               │
│  ┌─────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │
│  │ Sidebar │  │   tldraw    │  │     G6      │  │ DSRPPanel │  │
│  │ Sources │  │   Canvas    │  │    Graph    │  │  Analysis │  │
│  └─────────┘  └─────────────┘  └─────────────┘  └───────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Quick Wins to Implement Now

### 1. Add FastMCP Server (1-2 hours)
```bash
pip install fastmcp
```
Create `backend/mcp/dsrp_server.py` with tools exposing existing API.

### 2. Add Vector Search (2-3 hours)
```bash
pip install pgvector
```
Store concept embeddings for semantic search across analyses.

### 3. Add Redis Cache (1 hour)
```bash
pip install redis
```
Cache TypeDB queries for faster UI response.

### 4. GraphQL API (Optional, 3-4 hours)
Use Strawberry GraphQL to expose knowledge graph with subscriptions for real-time updates.

---

## Sources

- [FastMCP GitHub](https://github.com/jlowin/fastmcp)
- [Official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [FastMCP Documentation](https://www.prefect.io/fastmcp)
- [SQL Server Graph Overview](https://learn.microsoft.com/en-us/sql/relational-databases/graphs/sql-graph-overview)
- [SQL Server 2025 What's New](https://learn.microsoft.com/en-us/sql/sql-server/what-s-new-in-sql-server-2025)
- [TypeDB Enhanced Knowledge Graphs](https://typedb.com/applications/enhanced-knowledge-graphs/)
- [Neo4j vs TypeDB Comparison](https://db-engines.com/en/system/Neo4j%3BTypeDB)
- [Graph Database vs Relational Database](https://neo4j.com/blog/graph-database/graph-database-vs-relational-database/)
