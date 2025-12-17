"""
DSRP Extraction Prompts for Knowledge Ingestion Pipeline

This module contains the system prompts that instruct the LLM to extract
DSRP patterns (Distinctions, Systems, Relationships, Perspectives) from text.

The prompts are designed to force valid JSON output that maps directly to
our TypeDB schema.
"""

# =============================================================================
# MAIN DSRP EXTRACTION PROMPT
# =============================================================================

DSRP_EXTRACTION_SYSTEM_PROMPT = """You are a DSRP Knowledge Extractor. Your job is to analyze text and identify the four universal patterns of cognition from Dr. Derek Cabrera's DSRP Theory.

## THE FOUR PATTERNS (DSRP):

**D - DISTINCTIONS** (Identity/Other)
- What concepts are being defined or distinguished in this text?
- What is something, and what is it NOT?
- Example: "Privacy IS the right to control personal information. It is NOT the same as secrecy."

**S - SYSTEMS** (Part/Whole)
- What systems or structures are described?
- What are the parts, and what is the whole?
- Example: "A privacy program (whole) consists of policies, training, and audits (parts)."

**R - RELATIONSHIPS** (Action/Reaction)
- What cause-effect or correlational relationships exist?
- What actions lead to what reactions?
- Example: "Data breaches (action) lead to regulatory fines and reputation damage (reactions)."

**P - PERSPECTIVES** (Point/View)
- Whose viewpoint is represented? What do they see?
- Different stakeholders see things differently.
- Example: "From a user's perspective (point), privacy means control. From a business perspective (point), privacy means compliance."

## YOUR TASK:

Analyze the provided text chunk and extract ALL instances of each pattern you can identify. Be thorough but only extract what is explicitly stated or strongly implied.

## OUTPUT FORMAT:

You MUST respond with ONLY valid JSON in this exact structure:

```json
{
  "distinctions": [
    {
      "identity": "What the concept IS (the thing being distinguished)",
      "other": "What it is NOT or what it is distinguished FROM",
      "boundary": "The criteria or property that separates identity from other",
      "confidence": 0.85
    }
  ],
  "systems": [
    {
      "whole": "The containing system or larger entity",
      "parts": ["Part 1", "Part 2", "Part 3"],
      "relationship_type": "composition|hierarchy|membership",
      "confidence": 0.90
    }
  ],
  "relationships": [
    {
      "action": "The cause, input, or initiating concept",
      "reaction": "The effect, output, or resulting concept",
      "relationship_type": "causal|correlative|structural|temporal",
      "strength": 0.75,
      "confidence": 0.80
    }
  ],
  "perspectives": [
    {
      "point": "The observer or stakeholder (WHO is looking)",
      "view": "What they see or how they interpret it (WHAT they see)",
      "context": "Additional context about this perspective",
      "confidence": 0.85
    }
  ],
  "concepts": [
    "List of all unique concepts/entities mentioned in the text"
  ],
  "summary": "A 1-2 sentence summary of the main ideas in this text chunk"
}
```

## RULES:

1. **JSON Only**: Return ONLY the JSON object. No markdown, no explanations, no preamble.
2. **Arrays Can Be Empty**: If no instances of a pattern are found, use an empty array `[]`.
3. **Confidence Scores**: Rate your confidence from 0.0 to 1.0 for each extraction.
4. **Be Specific**: Use exact phrases from the text when possible.
5. **No Hallucination**: Only extract what is stated or strongly implied. Do not invent relationships.
6. **Deduplication**: List each concept only once in the "concepts" array.

## EXAMPLE INPUT:
"GDPR requires organizations to implement appropriate technical and organizational measures. From the regulator's view, this means documented policies and regular audits. Failure to comply can result in fines up to 4% of global revenue."

## EXAMPLE OUTPUT:
```json
{
  "distinctions": [
    {
      "identity": "GDPR compliance",
      "other": "Non-compliance",
      "boundary": "Implementation of appropriate measures",
      "confidence": 0.90
    }
  ],
  "systems": [
    {
      "whole": "Appropriate measures",
      "parts": ["Technical measures", "Organizational measures"],
      "relationship_type": "composition",
      "confidence": 0.95
    },
    {
      "whole": "Organizational measures",
      "parts": ["Documented policies", "Regular audits"],
      "relationship_type": "composition",
      "confidence": 0.85
    }
  ],
  "relationships": [
    {
      "action": "Failure to comply with GDPR",
      "reaction": "Fines up to 4% of global revenue",
      "relationship_type": "causal",
      "strength": 0.90,
      "confidence": 0.95
    }
  ],
  "perspectives": [
    {
      "point": "Regulator",
      "view": "Compliance means documented policies and regular audits",
      "context": "Regulatory enforcement perspective",
      "confidence": 0.90
    }
  ],
  "concepts": [
    "GDPR",
    "Organizations",
    "Technical measures",
    "Organizational measures",
    "Documented policies",
    "Regular audits",
    "Compliance",
    "Fines",
    "Global revenue",
    "Regulator"
  ],
  "summary": "GDPR requires technical and organizational compliance measures, with non-compliance resulting in significant fines."
}
```

Now analyze the following text and extract DSRP patterns:"""


# =============================================================================
# VALIDATION PROMPT (for checking extraction quality)
# =============================================================================

DSRP_VALIDATION_PROMPT = """Review this DSRP extraction for quality and accuracy.

Original Text:
{original_text}

Extracted DSRP:
{extracted_json}

Rate the extraction on these criteria (0.0 to 1.0):
1. Completeness: Were all patterns in the text captured?
2. Accuracy: Are the extractions factually correct?
3. Relevance: Are the extractions meaningful, not trivial?

Respond with JSON:
{
  "completeness": 0.85,
  "accuracy": 0.90,
  "relevance": 0.80,
  "issues": ["List any specific problems found"],
  "suggestions": ["List improvements if any"]
}"""


# =============================================================================
# CHUNK CONTEXT PROMPT (for maintaining context across chunks)
# =============================================================================

DSRP_CONTEXT_PROMPT = """You are analyzing chunk {chunk_number} of {total_chunks} from the document "{document_name}".

Previous context summary:
{previous_summary}

Keep this context in mind as you extract DSRP patterns from the following text.
If concepts reference things from previous chunks, note those connections.

Text to analyze:"""


def get_extraction_prompt(text: str, chunk_number: int = 1, total_chunks: int = 1,
                          document_name: str = "document", previous_summary: str = "") -> str:
    """
    Build the complete prompt for DSRP extraction.

    Args:
        text: The text chunk to analyze
        chunk_number: Which chunk this is (1-indexed)
        total_chunks: Total number of chunks in the document
        document_name: Name of the source document
        previous_summary: Summary from previous chunk (for context continuity)

    Returns:
        Complete prompt string to send to the LLM
    """
    # If this is part of a multi-chunk document, add context
    if total_chunks > 1:
        context_header = DSRP_CONTEXT_PROMPT.format(
            chunk_number=chunk_number,
            total_chunks=total_chunks,
            document_name=document_name,
            previous_summary=previous_summary or "This is the first chunk."
        )
        return f"{DSRP_EXTRACTION_SYSTEM_PROMPT}\n\n{context_header}\n\n{text}"
    else:
        return f"{DSRP_EXTRACTION_SYSTEM_PROMPT}\n\n{text}"


# =============================================================================
# JSON SCHEMA FOR VALIDATION
# =============================================================================

DSRP_OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["distinctions", "systems", "relationships", "perspectives", "concepts", "summary"],
    "properties": {
        "distinctions": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["identity", "other"],
                "properties": {
                    "identity": {"type": "string"},
                    "other": {"type": "string"},
                    "boundary": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                }
            }
        },
        "systems": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["whole", "parts"],
                "properties": {
                    "whole": {"type": "string"},
                    "parts": {"type": "array", "items": {"type": "string"}},
                    "relationship_type": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                }
            }
        },
        "relationships": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["action", "reaction"],
                "properties": {
                    "action": {"type": "string"},
                    "reaction": {"type": "string"},
                    "relationship_type": {"type": "string"},
                    "strength": {"type": "number", "minimum": 0, "maximum": 1},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                }
            }
        },
        "perspectives": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["point", "view"],
                "properties": {
                    "point": {"type": "string"},
                    "view": {"type": "string"},
                    "context": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                }
            }
        },
        "concepts": {
            "type": "array",
            "items": {"type": "string"}
        },
        "summary": {"type": "string"}
    }
}
