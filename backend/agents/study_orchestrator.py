"""
DSRP 4-8-3 Study System Orchestrator

Implements the 5-step study workflow:
1. GATHER - Collect and ingest source materials
2. REFLECTION - Apply DSRP 4-8-3 analysis with AI agents
3. METACOGNITION - Visualize and understand the knowledge graph
4. FIX/PRESENT - Correct errors and present knowledge
5. ACTIVE RECALL - Generate questions for spaced repetition

The orchestrator coordinates multiple specialized agents:
- Summary Agent: Creates hierarchical summaries
- Structure Agent: Extracts document structure (TOC, sections)
- DSRP Agents: Apply the 8 moves for deep analysis
- Cross-Reference Agent: Finds connections across concepts
- Question Agent: Generates questions for active recall
"""

import os
import json
import uuid
import logging
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from agents.dsrp_agent import DSRPAgent, MOVE_PROMPTS

logger = logging.getLogger(__name__)


class StudyStep(Enum):
    """The 5 steps of the study system."""
    GATHER = "gather"
    REFLECTION = "reflection"
    METACOGNITION = "metacognition"
    FIX_PRESENT = "fix_present"
    ACTIVE_RECALL = "active_recall"


@dataclass
class StudySession:
    """Represents a study session for a source material."""
    session_id: str
    source_id: str
    source_name: str
    current_step: StudyStep
    created_at: datetime
    updated_at: datetime

    # Step 1: Gather results
    source_type: str = ""
    total_chunks: int = 0
    extracted_text_length: int = 0

    # Step 2: Reflection results
    summary: dict = field(default_factory=dict)
    structure: dict = field(default_factory=dict)
    dsrp_analyses: list = field(default_factory=list)
    concepts_extracted: int = 0

    # Step 3: Metacognition results
    knowledge_graph_nodes: int = 0
    knowledge_graph_edges: int = 0
    cross_references: list = field(default_factory=list)

    # Step 4: Fix/Present results
    corrections: list = field(default_factory=list)
    presentation_ready: bool = False

    # Step 5: Active Recall results
    questions_generated: int = 0
    question_bank: list = field(default_factory=list)


# =============================================================================
# SUMMARY AGENT
# Creates hierarchical summaries at different levels of detail
# =============================================================================

SUMMARY_SYSTEM_PROMPT = """You are an expert at creating hierarchical summaries of educational content.
Your task is to analyze text and create structured summaries at multiple levels:

1. HIGH-LEVEL: 1-2 sentence executive summary
2. CHAPTER/SECTION LEVEL: Key points for each major section
3. DETAILED: Important concepts, definitions, and examples

For each level, identify:
- Main themes and topics
- Key terminology
- Important relationships between concepts
- Practical applications or examples

Always respond with structured JSON."""

SUMMARY_PROMPT = """Analyze this text and create a hierarchical summary:

SOURCE: {source_name}
TEXT:
\"\"\"
{text}
\"\"\"

Create a structured summary at multiple levels:

1. EXECUTIVE SUMMARY: 1-2 sentences capturing the main point
2. KEY THEMES: 3-5 major themes or topics covered
3. SECTION SUMMARIES: For each logical section, provide:
   - Section title
   - Main points (3-5 bullet points)
   - Key terms introduced
4. CONCEPTS: List the 10-15 most important concepts with brief definitions
5. CONNECTIONS: How do the main ideas connect to each other?

Respond in JSON format:
{{
  "executive_summary": "1-2 sentence overview",
  "key_themes": ["theme1", "theme2", "theme3"],
  "sections": [
    {{
      "title": "Section Title",
      "main_points": ["point1", "point2", "point3"],
      "key_terms": ["term1", "term2"]
    }}
  ],
  "concepts": [
    {{
      "name": "Concept Name",
      "definition": "Brief definition",
      "importance": "Why this matters"
    }}
  ],
  "connections": [
    {{
      "from": "concept1",
      "to": "concept2",
      "relationship": "How they connect"
    }}
  ],
  "suggested_dsrp_moves": [
    {{
      "concept": "Concept to analyze",
      "move": "suggested-move",
      "rationale": "Why this move"
    }}
  ]
}}"""


# =============================================================================
# STRUCTURE AGENT
# Extracts document structure and organization
# =============================================================================

STRUCTURE_SYSTEM_PROMPT = """You are an expert at analyzing document structure and organization.
Your task is to identify the hierarchical structure of educational content:

- Chapter/Module organization
- Section and subsection breakdown
- Learning objectives if present
- Prerequisites and dependencies
- Logical flow and sequencing

Always respond with structured JSON."""

STRUCTURE_PROMPT = """Analyze the structure of this text:

SOURCE: {source_name}
TEXT:
\"\"\"
{text}
\"\"\"

Identify the document's organizational structure:

1. What type of document is this? (textbook, article, guide, etc.)
2. What is the hierarchical structure?
3. What is the logical learning sequence?
4. What are dependencies between sections?

Respond in JSON format:
{{
  "document_type": "textbook/article/guide/etc",
  "title": "Inferred or actual title",
  "hierarchy": [
    {{
      "level": 1,
      "title": "Chapter/Module Title",
      "children": [
        {{
          "level": 2,
          "title": "Section Title",
          "children": []
        }}
      ]
    }}
  ],
  "learning_objectives": ["objective1", "objective2"],
  "prerequisites": ["prereq1", "prereq2"],
  "sequence": [
    {{
      "order": 1,
      "topic": "First topic",
      "depends_on": []
    }},
    {{
      "order": 2,
      "topic": "Second topic",
      "depends_on": ["First topic"]
    }}
  ],
  "key_sections": [
    {{
      "title": "Most important section",
      "why_important": "Reason"
    }}
  ]
}}"""


# =============================================================================
# QUESTION GENERATION AGENT
# Creates questions for active recall / spaced repetition
# =============================================================================

QUESTION_SYSTEM_PROMPT = """You are an expert at creating effective study questions for active recall and spaced repetition.

You create questions based on DSRP patterns:
- D (Distinctions): "What distinguishes X from Y?" / "What is X NOT?"
- S (Systems): "What are the parts of X?" / "What is X part of?"
- R (Relationships): "What causes X?" / "What does X cause?" / "How does X relate to Y?"
- P (Perspectives): "How would [stakeholder] view X?" / "What are different views on X?"

Question types to generate:
1. DEFINITION questions (What is X?)
2. DISTINCTION questions (How is X different from Y?)
3. PART-WHOLE questions (What are the components of X?)
4. CAUSE-EFFECT questions (What causes X? What does X cause?)
5. PERSPECTIVE questions (How do different stakeholders view X?)
6. APPLICATION questions (How would you apply X in situation Y?)
7. SYNTHESIS questions (How do X and Y work together?)

Always respond with structured JSON compatible with RemNote/Anki."""

QUESTION_PROMPT = """Generate study questions based on this DSRP analysis:

CONCEPT: {concept}
DSRP ANALYSIS:
{dsrp_analysis}

CONTEXT:
{context}

Generate {num_questions} questions for active recall, ensuring variety across:
- Question types (definition, distinction, cause-effect, perspective, application)
- Difficulty levels (basic, intermediate, advanced)
- DSRP patterns (D, S, R, P)

For each question, provide:
1. The question itself
2. The correct answer
3. Why this question tests understanding (rationale)
4. The DSRP pattern it relates to
5. Difficulty level
6. Tags for organization

Respond in JSON format:
{{
  "concept": "{concept}",
  "questions": [
    {{
      "id": "q1",
      "type": "distinction",
      "dsrp_pattern": "D",
      "difficulty": "intermediate",
      "question": "The question text?",
      "answer": "The correct answer",
      "rationale": "Why this tests understanding",
      "tags": ["tag1", "tag2"],
      "wrong_answers": ["distractor1", "distractor2"]
    }}
  ],
  "study_tips": ["tip1", "tip2"]
}}"""


# =============================================================================
# CROSS-REFERENCE AGENT
# Finds connections between concepts across the knowledge base
# =============================================================================

CROSSREF_SYSTEM_PROMPT = """You are an expert at finding connections and relationships between concepts.
Your task is to identify how concepts relate to each other, including:

- Direct relationships (A causes B, A is part of B)
- Indirect relationships (A and B share common properties)
- Analogies (A is to B as C is to D)
- Contradictions (A and B conflict in context of C)
- Dependencies (Understanding A requires understanding B)

Always respond with structured JSON."""

CROSSREF_PROMPT = """Find connections between these concepts:

FOCAL CONCEPT: {focal_concept}

OTHER CONCEPTS IN KNOWLEDGE BASE:
{other_concepts}

CONTEXT:
{context}

Identify relationships between the focal concept and others:

1. Direct relationships (the focal concept directly relates to)
2. Indirect relationships (share common themes/properties)
3. Analogies (similar patterns in different domains)
4. Dependencies (what must be understood first)
5. Potential conflicts or tensions

Respond in JSON format:
{{
  "focal_concept": "{focal_concept}",
  "relationships": [
    {{
      "target_concept": "Related concept",
      "relationship_type": "direct/indirect/analogy/dependency/conflict",
      "description": "How they relate",
      "strength": 0.8,
      "dsrp_pattern": "R",
      "bidirectional": true
    }}
  ],
  "clusters": [
    {{
      "name": "Cluster name",
      "concepts": ["concept1", "concept2"],
      "common_theme": "What unites them"
    }}
  ],
  "learning_path": ["concept1", "concept2", "concept3"]
}}"""


class StudyOrchestrator:
    """
    Orchestrates the 5-step study workflow using multiple AI agents.

    Leverages the existing DSRPAgent with its 8 moves while adding
    specialized agents for summary, structure, questions, and cross-referencing.
    """

    def __init__(self, preferred_provider: str | None = None):
        """Initialize the orchestrator with AI providers."""
        self.dsrp_agent = DSRPAgent(preferred_provider)
        self.sessions: dict[str, StudySession] = {}

        if not self.dsrp_agent.active_provider:
            logger.warning("No AI provider available for study orchestrator")

    async def create_session(
        self,
        source_id: str,
        source_name: str,
        source_type: str = "document"
    ) -> StudySession:
        """Create a new study session for a source material."""
        session = StudySession(
            session_id=str(uuid.uuid4()),
            source_id=source_id,
            source_name=source_name,
            source_type=source_type,
            current_step=StudyStep.GATHER,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.sessions[session.session_id] = session
        logger.info(f"Created study session: {session.session_id} for {source_name}")
        return session

    async def get_session(self, session_id: str) -> Optional[StudySession]:
        """Get a study session by ID."""
        return self.sessions.get(session_id)

    # =========================================================================
    # STEP 1: GATHER
    # =========================================================================

    async def step_gather(
        self,
        session_id: str,
        text: str,
        chunks: list[str] | None = None
    ) -> dict:
        """
        Step 1: Gather and prepare source material.

        Args:
            session_id: The study session ID
            text: The full extracted text
            chunks: Optional pre-chunked text segments

        Returns:
            Summary of gathered material
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        session.current_step = StudyStep.GATHER
        session.extracted_text_length = len(text)
        session.total_chunks = len(chunks) if chunks else 1
        session.updated_at = datetime.utcnow()

        logger.info(f"Step 1 GATHER: {session.source_name} - {len(text)} chars, {session.total_chunks} chunks")

        return {
            "step": "gather",
            "source_name": session.source_name,
            "source_type": session.source_type,
            "text_length": len(text),
            "chunks": session.total_chunks,
            "status": "complete"
        }

    # =========================================================================
    # STEP 2: REFLECTION - The core DSRP analysis step
    # =========================================================================

    async def step_reflection(
        self,
        session_id: str,
        text: str,
        analysis_depth: str = "standard"
    ) -> dict:
        """
        Step 2: Reflection - Apply DSRP 4-8-3 analysis.

        This step orchestrates multiple agents:
        1. Summary Agent - Create hierarchical summaries
        2. Structure Agent - Extract document structure
        3. DSRP Agents - Apply the 8 moves to key concepts

        Args:
            session_id: The study session ID
            text: The source text to analyze
            analysis_depth: "quick", "standard", or "deep"

        Returns:
            Complete reflection analysis
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        session.current_step = StudyStep.REFLECTION
        session.updated_at = datetime.utcnow()

        logger.info(f"Step 2 REFLECTION: Starting analysis for {session.source_name}")

        results = {
            "step": "reflection",
            "source_name": session.source_name,
            "summary": None,
            "structure": None,
            "concepts": [],
            "dsrp_analyses": [],
            "status": "in_progress"
        }

        # Truncate text if too long
        analysis_text = text[:15000] if len(text) > 15000 else text

        # --- Run Summary Agent ---
        try:
            summary = await self._run_summary_agent(session.source_name, analysis_text)
            session.summary = summary
            results["summary"] = summary
            logger.info(f"Summary complete: {len(summary.get('concepts', []))} concepts identified")
        except Exception as e:
            logger.error(f"Summary agent failed: {e}")
            results["summary"] = {"error": str(e)}

        # --- Run Structure Agent ---
        try:
            structure = await self._run_structure_agent(session.source_name, analysis_text)
            session.structure = structure
            results["structure"] = structure
            logger.info(f"Structure complete: {structure.get('document_type', 'unknown')}")
        except Exception as e:
            logger.error(f"Structure agent failed: {e}")
            results["structure"] = {"error": str(e)}

        # --- Apply DSRP Moves to Key Concepts ---
        concepts = session.summary.get("concepts", [])[:10]  # Top 10 concepts
        suggested_moves = session.summary.get("suggested_dsrp_moves", [])

        # Determine which moves to apply based on depth
        moves_per_concept = {
            "quick": 2,
            "standard": 4,
            "deep": 8
        }.get(analysis_depth, 4)

        for concept_data in concepts:
            concept_name = concept_data.get("name", "")
            if not concept_name:
                continue

            # Find suggested move or use defaults
            suggested = next(
                (s for s in suggested_moves if s.get("concept") == concept_name),
                None
            )

            # Apply DSRP moves
            concept_analyses = []
            moves_to_apply = self._select_moves_for_concept(concept_data, suggested, moves_per_concept)

            for move in moves_to_apply:
                try:
                    analysis = await self.dsrp_agent.analyze(
                        concept=concept_name,
                        move=move,
                        context=f"From source: {session.source_name}. Definition: {concept_data.get('definition', '')}"
                    )
                    concept_analyses.append(analysis)
                except Exception as e:
                    logger.warning(f"DSRP move {move} failed for {concept_name}: {e}")

            if concept_analyses:
                session.dsrp_analyses.append({
                    "concept": concept_name,
                    "definition": concept_data.get("definition"),
                    "analyses": concept_analyses
                })
                results["dsrp_analyses"].append({
                    "concept": concept_name,
                    "moves_applied": [a.get("move") for a in concept_analyses],
                    "patterns": list(set(a.get("pattern") for a in concept_analyses))
                })

        session.concepts_extracted = len(concepts)
        results["concepts"] = [c.get("name") for c in concepts]
        results["status"] = "complete"

        logger.info(f"Step 2 REFLECTION complete: {len(session.dsrp_analyses)} concepts analyzed")

        return results

    def _select_moves_for_concept(
        self,
        concept_data: dict,
        suggested: dict | None,
        max_moves: int
    ) -> list[str]:
        """Select which DSRP moves to apply to a concept."""
        all_moves = [
            "is-is-not", "zoom-in", "zoom-out", "part-party",
            "rds-barbell", "p-circle", "woc", "waoc"
        ]

        # Start with suggested move if available
        moves = []
        if suggested and suggested.get("move") in all_moves:
            moves.append(suggested["move"])

        # Add is-is-not as it's fundamental for distinctions
        if "is-is-not" not in moves and len(moves) < max_moves:
            moves.append("is-is-not")

        # Add zoom-in for understanding parts
        if "zoom-in" not in moves and len(moves) < max_moves:
            moves.append("zoom-in")

        # Fill remaining with other moves
        for move in all_moves:
            if move not in moves and len(moves) < max_moves:
                moves.append(move)

        return moves[:max_moves]

    async def _run_summary_agent(self, source_name: str, text: str) -> dict:
        """Run the summary agent."""
        if not self.dsrp_agent.active_provider:
            raise RuntimeError("No AI provider available")

        prompt = SUMMARY_PROMPT.format(source_name=source_name, text=text)
        response = await self.dsrp_agent.active_provider.generate(
            SUMMARY_SYSTEM_PROMPT, prompt
        )

        # Parse JSON response
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]

        return json.loads(response.strip())

    async def _run_structure_agent(self, source_name: str, text: str) -> dict:
        """Run the structure agent."""
        if not self.dsrp_agent.active_provider:
            raise RuntimeError("No AI provider available")

        prompt = STRUCTURE_PROMPT.format(source_name=source_name, text=text)
        response = await self.dsrp_agent.active_provider.generate(
            STRUCTURE_SYSTEM_PROMPT, prompt
        )

        # Parse JSON response
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]

        return json.loads(response.strip())

    # =========================================================================
    # STEP 3: METACOGNITION
    # =========================================================================

    async def step_metacognition(self, session_id: str) -> dict:
        """
        Step 3: Metacognition - Understand the knowledge graph.

        Uses the DSRP analyses to build a knowledge map and find cross-references.

        Returns:
            Knowledge graph summary and cross-references
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        session.current_step = StudyStep.METACOGNITION
        session.updated_at = datetime.utcnow()

        logger.info(f"Step 3 METACOGNITION: Building knowledge map for {session.source_name}")

        # Build knowledge graph from analyses
        nodes = []
        edges = []

        for analysis in session.dsrp_analyses:
            concept_name = analysis.get("concept")
            nodes.append({
                "id": concept_name,
                "label": concept_name,
                "type": "concept"
            })

            for move_analysis in analysis.get("analyses", []):
                elements = move_analysis.get("elements", {})

                # Extract related concepts based on pattern
                if move_analysis.get("pattern") == "S":
                    # System - add parts
                    for part in elements.get("parts", []):
                        if part and part != concept_name:
                            nodes.append({"id": part, "label": part, "type": "part"})
                            edges.append({
                                "source": concept_name,
                                "target": part,
                                "type": "has_part"
                            })
                    if elements.get("whole"):
                        nodes.append({"id": elements["whole"], "label": elements["whole"], "type": "whole"})
                        edges.append({
                            "source": elements["whole"],
                            "target": concept_name,
                            "type": "contains"
                        })

                elif move_analysis.get("pattern") == "R":
                    # Relationship - add causes/effects
                    for effect in elements.get("effects", []):
                        if isinstance(effect, dict):
                            effect_name = effect.get("effect", "")
                        else:
                            effect_name = effect
                        if effect_name and effect_name != concept_name:
                            nodes.append({"id": effect_name, "label": effect_name, "type": "effect"})
                            edges.append({
                                "source": concept_name,
                                "target": effect_name,
                                "type": "causes"
                            })

        # Deduplicate nodes
        seen_ids = set()
        unique_nodes = []
        for node in nodes:
            if node["id"] not in seen_ids:
                seen_ids.add(node["id"])
                unique_nodes.append(node)

        session.knowledge_graph_nodes = len(unique_nodes)
        session.knowledge_graph_edges = len(edges)

        # Find cross-references between concepts
        cross_refs = await self._find_cross_references(session)
        session.cross_references = cross_refs

        logger.info(f"Step 3 METACOGNITION complete: {len(unique_nodes)} nodes, {len(edges)} edges")

        return {
            "step": "metacognition",
            "source_name": session.source_name,
            "knowledge_graph": {
                "nodes": unique_nodes,
                "edges": edges
            },
            "cross_references": cross_refs,
            "status": "complete"
        }

    async def _find_cross_references(self, session: StudySession) -> list:
        """Find cross-references between concepts."""
        if not session.dsrp_analyses:
            return []

        concept_names = [a.get("concept") for a in session.dsrp_analyses]

        cross_refs = []
        for i, analysis in enumerate(session.dsrp_analyses):
            focal_concept = analysis.get("concept")
            other_concepts = [c for c in concept_names if c != focal_concept]

            if other_concepts and self.dsrp_agent.active_provider:
                try:
                    prompt = CROSSREF_PROMPT.format(
                        focal_concept=focal_concept,
                        other_concepts=json.dumps(other_concepts),
                        context=f"From source: {session.source_name}"
                    )
                    response = await self.dsrp_agent.active_provider.generate(
                        CROSSREF_SYSTEM_PROMPT, prompt
                    )

                    if "```json" in response:
                        response = response.split("```json")[1].split("```")[0]
                    elif "```" in response:
                        response = response.split("```")[1].split("```")[0]

                    refs = json.loads(response.strip())
                    cross_refs.append(refs)
                except Exception as e:
                    logger.warning(f"Cross-reference failed for {focal_concept}: {e}")

        return cross_refs

    # =========================================================================
    # STEP 4: FIX/PRESENT
    # =========================================================================

    async def step_fix_present(
        self,
        session_id: str,
        corrections: list[dict] | None = None
    ) -> dict:
        """
        Step 4: Fix errors and prepare for presentation.

        Args:
            session_id: The study session ID
            corrections: Optional list of corrections from user review

        Returns:
            Presentation-ready summary
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        session.current_step = StudyStep.FIX_PRESENT
        session.updated_at = datetime.utcnow()

        if corrections:
            session.corrections = corrections
            logger.info(f"Applied {len(corrections)} corrections")

        session.presentation_ready = True

        return {
            "step": "fix_present",
            "source_name": session.source_name,
            "corrections_applied": len(session.corrections),
            "presentation_ready": True,
            "summary": session.summary.get("executive_summary", ""),
            "concepts_count": session.concepts_extracted,
            "status": "complete"
        }

    # =========================================================================
    # STEP 5: ACTIVE RECALL - Question Generation
    # =========================================================================

    async def step_active_recall(
        self,
        session_id: str,
        questions_per_concept: int = 5,
        difficulty_distribution: dict | None = None
    ) -> dict:
        """
        Step 5: Active Recall - Generate questions for spaced repetition.

        Args:
            session_id: The study session ID
            questions_per_concept: Number of questions per concept
            difficulty_distribution: Dict of difficulty level percentages

        Returns:
            Question bank for RemNote/Anki export
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        session.current_step = StudyStep.ACTIVE_RECALL
        session.updated_at = datetime.utcnow()

        logger.info(f"Step 5 ACTIVE_RECALL: Generating questions for {session.source_name}")

        question_bank = []

        for analysis in session.dsrp_analyses:
            concept_name = analysis.get("concept")
            dsrp_analysis = json.dumps(analysis.get("analyses", []), indent=2)

            try:
                questions = await self._generate_questions(
                    concept=concept_name,
                    dsrp_analysis=dsrp_analysis,
                    context=f"From source: {session.source_name}",
                    num_questions=questions_per_concept
                )
                question_bank.append(questions)
            except Exception as e:
                logger.warning(f"Question generation failed for {concept_name}: {e}")

        session.question_bank = question_bank
        session.questions_generated = sum(
            len(qb.get("questions", [])) for qb in question_bank
        )

        logger.info(f"Step 5 ACTIVE_RECALL complete: {session.questions_generated} questions generated")

        return {
            "step": "active_recall",
            "source_name": session.source_name,
            "questions_generated": session.questions_generated,
            "concepts_covered": len(question_bank),
            "question_bank": question_bank,
            "export_formats": ["remnote", "anki", "markdown"],
            "status": "complete"
        }

    async def _generate_questions(
        self,
        concept: str,
        dsrp_analysis: str,
        context: str,
        num_questions: int
    ) -> dict:
        """Generate questions for a concept using the question agent."""
        if not self.dsrp_agent.active_provider:
            raise RuntimeError("No AI provider available")

        prompt = QUESTION_PROMPT.format(
            concept=concept,
            dsrp_analysis=dsrp_analysis,
            context=context,
            num_questions=num_questions
        )

        response = await self.dsrp_agent.active_provider.generate(
            QUESTION_SYSTEM_PROMPT, prompt
        )

        # Parse JSON response
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]

        return json.loads(response.strip())

    # =========================================================================
    # COMPLETE WORKFLOW
    # =========================================================================

    async def run_complete_workflow(
        self,
        source_id: str,
        source_name: str,
        text: str,
        source_type: str = "document",
        analysis_depth: str = "standard",
        questions_per_concept: int = 5
    ) -> dict:
        """
        Run the complete 5-step study workflow.

        Args:
            source_id: Unique ID for the source material
            source_name: Name of the source (e.g., "CIPP-E Study Guide")
            text: The extracted text content
            source_type: Type of source (document, video, audio)
            analysis_depth: "quick", "standard", or "deep"
            questions_per_concept: Number of questions to generate per concept

        Returns:
            Complete workflow results
        """
        # Create session
        session = await self.create_session(source_id, source_name, source_type)

        results = {
            "session_id": session.session_id,
            "source_name": source_name,
            "steps": {}
        }

        # Step 1: Gather
        results["steps"]["gather"] = await self.step_gather(
            session.session_id, text
        )

        # Step 2: Reflection
        results["steps"]["reflection"] = await self.step_reflection(
            session.session_id, text, analysis_depth
        )

        # Step 3: Metacognition
        results["steps"]["metacognition"] = await self.step_metacognition(
            session.session_id
        )

        # Step 4: Fix/Present (no corrections in automated flow)
        results["steps"]["fix_present"] = await self.step_fix_present(
            session.session_id
        )

        # Step 5: Active Recall
        results["steps"]["active_recall"] = await self.step_active_recall(
            session.session_id, questions_per_concept
        )

        results["status"] = "complete"
        results["summary"] = {
            "concepts_extracted": session.concepts_extracted,
            "dsrp_analyses": len(session.dsrp_analyses),
            "knowledge_graph_nodes": session.knowledge_graph_nodes,
            "knowledge_graph_edges": session.knowledge_graph_edges,
            "questions_generated": session.questions_generated
        }

        return results


# Singleton instance
_orchestrator: StudyOrchestrator | None = None


def get_study_orchestrator() -> StudyOrchestrator:
    """Get the singleton study orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = StudyOrchestrator()
    return _orchestrator
