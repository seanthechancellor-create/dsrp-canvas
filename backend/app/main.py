from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import sources, analysis, export, concepts, search, cache, patterns, websocket, jobs, quiz, seed, categories, study

app = FastAPI(
    title="DSRP Canvas API",
    description="Knowledge analysis backend using DSRP 4-8-3 framework",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core API routes
app.include_router(sources.router, prefix="/api/sources", tags=["sources"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(export.router, prefix="/api/export", tags=["export"])
app.include_router(concepts.router, prefix="/api/concepts", tags=["concepts"])
app.include_router(patterns.router, prefix="/api/dsrp", tags=["dsrp"])
app.include_router(quiz.router, prefix="/api/quiz", tags=["quiz"])
app.include_router(seed.router, prefix="/api/seed", tags=["seed"])
app.include_router(categories.router, prefix="/api/categories", tags=["categories"])
app.include_router(study.router, prefix="/api/study", tags=["study"])

# New services
app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(cache.router, prefix="/api", tags=["cache"])
app.include_router(jobs.router, prefix="/api", tags=["jobs"])

# WebSocket endpoints (no prefix - handled by router)
app.include_router(websocket.router)


@app.get("/health")
async def health_check():
    """Health check endpoint with service status."""
    from app.services.cache_service import get_cache_service
    from app.services.vector_service import _get_pool
    from app.services.typedb_service import get_typedb_service

    cache = get_cache_service()
    pg_pool = _get_pool()
    typedb = get_typedb_service()

    return {
        "status": "healthy",
        "framework": "DSRP 4-8-3",
        "services": {
            "redis": "connected" if cache.available else "unavailable",
            "pgvector": "connected" if pg_pool else "unavailable",
            "typedb": "connected" if typedb.is_connected() else "unavailable",
        },
    }
