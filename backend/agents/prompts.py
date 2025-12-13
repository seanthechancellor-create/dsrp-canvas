"""
DSRP Agent Prompt Templates

These prompts implement the 6 Moves from Dr. Derek Cabrera's
DSRP 4-8-3 systems thinking framework.
"""

# Core system understanding prompt
DSRP_FOUNDATION = """
DSRP 4-8-3 Framework:

4 PATTERNS:
├── D (Distinctions): What is it? What is it not?
├── S (Systems): What are its parts? What is it part of?
├── R (Relationships): How does it relate to other things?
└── P (Perspectives): Who sees it? How do they see it?

8 ELEMENTS (2 per pattern):
├── D: identity (i) ↔ other (o)
├── S: part (p) ↔ whole (w)
├── R: action (a) ↔ reaction (r)
└── P: point (ρ) ↔ view (v)

3 DYNAMICS:
├── = (Equality): pattern = element₁ + element₂
├── ⇔ (Co-implication): element₁ exists → element₂ exists
└── ✷ (Simultaneity): any element can be any other element
"""

# Deep analysis prompt for complex concepts
DEEP_ANALYSIS_PROMPT = """
Perform a comprehensive DSRP analysis on: "{concept}"

Apply ALL 4 patterns systematically:

1. DISTINCTIONS (D)
   - Identity: What fundamentally defines {concept}?
   - Other: What is {concept} commonly confused with but is NOT?
   - Boundary: What criteria separate {concept} from similar concepts?

2. SYSTEMS (S)
   - Zoom In: What are the component parts of {concept}?
   - Zoom Out: What larger systems contain {concept}?
   - Part-Whole Relations: How do the parts interact?

3. RELATIONSHIPS (R)
   - Connections: What does {concept} connect to?
   - Actions/Reactions: What does {concept} do? What responds to it?
   - Relationship Types: Causal? Correlative? Structural?

4. PERSPECTIVES (P)
   - Stakeholders: Who has a view on {concept}?
   - Views: What does each stakeholder see?
   - Tensions: Where do perspectives conflict?
   - Synthesis: What emerges from multiple perspectives?

Apply the 3 Dynamics:
- Note where elements co-imply each other
- Identify where one element IS another (simultaneity)
- Show the equality of pattern to its elements

Provide a rich, interconnected analysis that reveals the systemic nature of {concept}.
"""

# Synthesis prompt for connecting multiple analyses
SYNTHESIS_PROMPT = """
You have performed DSRP analyses on multiple concepts:

{analyses}

Now SYNTHESIZE these analyses:

1. EMERGENT DISTINCTIONS
   - What new distinctions emerge from comparing these concepts?
   - What shared boundaries exist?

2. SYSTEM ARCHITECTURE
   - How do these concepts form a system together?
   - What is the part-whole hierarchy?

3. RELATIONSHIP WEB
   - Map all relationships between these concepts
   - Identify feedback loops and causal chains

4. PERSPECTIVE INTEGRATION
   - What meta-perspective emerges?
   - How do different concepts illuminate each other?

Create a unified knowledge structure that captures the systemic relationships.
"""

# Question generation for RemNote export
FLASHCARD_GENERATION_PROMPT = """
Based on this DSRP analysis:

{analysis}

Generate spaced repetition flashcards that test understanding of:

1. DISTINCTION cards:
   - Q: What IS {concept}? A: [identity]
   - Q: What is {concept} NOT? A: [other]

2. SYSTEM cards:
   - Q: What are the parts of {concept}? A: [parts]
   - Q: What system contains {concept}? A: [whole]

3. RELATIONSHIP cards:
   - Q: How does {concept} relate to X? A: [relationship]
   - Q: What causes/affects {concept}? A: [actions]

4. PERSPECTIVE cards:
   - Q: How does [stakeholder] view {concept}? A: [view]
   - Q: What perspectives exist on {concept}? A: [perspectives]

Format each card for optimal retention with:
- Clear, specific questions
- Concise, memorable answers
- Relevant tags for organization
"""
