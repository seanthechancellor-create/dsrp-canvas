# Prompts package for DSRP Knowledge Ingestion Pipeline
from .dsrp_extraction import (
    DSRP_EXTRACTION_SYSTEM_PROMPT,
    DSRP_VALIDATION_PROMPT,
    DSRP_CONTEXT_PROMPT,
    DSRP_OUTPUT_SCHEMA,
    get_extraction_prompt,
)

__all__ = [
    "DSRP_EXTRACTION_SYSTEM_PROMPT",
    "DSRP_VALIDATION_PROMPT",
    "DSRP_CONTEXT_PROMPT",
    "DSRP_OUTPUT_SCHEMA",
    "get_extraction_prompt",
]
