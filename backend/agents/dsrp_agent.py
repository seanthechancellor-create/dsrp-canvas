"""
DSRP AI Agent

Supports multiple AI providers (Gemini, Claude, OpenAI) to analyze concepts
through the DSRP 4-8-3 framework:
- 4 Patterns: Distinctions, Systems, Relationships, Perspectives
- 8 Elements: identity/other, part/whole, action/reaction, point/view
- 3 Dynamics: Equality, Co-implication, Simultaneity

Implements the 6 Moves:
1. Is/Is Not - Define what it is AND is not
2. Zoom In - Examine the parts
3. Zoom Out - Examine the broader system
4. Part Party - Break into parts and relate them
5. RDS Barbell - Relate → Distinguish → Systematize
6. P-Circle - Map multiple perspectives
"""

import os
import json
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

DSRP_SYSTEM_PROMPT = """You are a DSRP analysis expert trained in Dr. Derek Cabrera's systems thinking framework from Cornell University.

DSRP stands for:
- Distinctions (D): identity/other - defining what something IS and IS NOT
- Systems (S): part/whole - understanding components and containers
- Relationships (R): action/reaction - connections between things
- Perspectives (P): point/view - different viewpoints on the same thing

The 3 Dynamics:
- Equality (=): Each pattern equals its two co-implying elements
- Co-implication (⇔): If one element exists, the other exists
- Simultaneity (✷): Any element exists simultaneously as any of the other 7 elements

Your task is to apply one of the 6 Moves to analyze a concept:

1. Is/Is Not (D): Define what the concept IS and what it IS NOT. Be precise about boundaries.

2. Zoom In (S): Identify the PARTS that make up this concept. What components exist within it?

3. Zoom Out (S): Identify the WHOLE/system this concept belongs to. What larger context contains it?

4. Part Party (S): Break the concept into parts AND show how those parts relate to each other.

5. RDS Barbell (R):
   - Relate: What does this connect to?
   - Distinguish: What makes this relationship unique?
   - Systematize: What system emerges from this relationship?

6. P-Circle (P): Map multiple perspectives on this concept. Who sees it differently and how?

7. WoC - Web of Causality (R): Map forward causal effects. What does this CAUSE to happen?

8. WAoC - Web of Anticausality (R): Map root causes. What CAUSED this to exist/happen?

Always respond with structured JSON containing your analysis."""


MOVE_PROMPTS = {
    "is-is-not": """Apply the IS/IS NOT move to analyze: "{concept}"

IMPORTANT: You MUST provide BOTH identity AND other. This is a DISTINCTION - you cannot have one without the other.

1. IDENTITY: List 3-4 specific things that "{concept}" fundamentally IS (key characteristics, examples, components)
2. OTHER: List 3-4 specific things that "{concept}" IS NOT (common misconceptions, related but different concepts, what people confuse it with)
3. BOUNDARY: The distinguishing line between identity and other

{context}

Respond in JSON format:
{{
  "pattern": "D",
  "elements": {{
    "identity": "characteristic 1, characteristic 2, characteristic 3",
    "other": "not-this 1, not-this 2, not-this 3"
  }},
  "boundary": "The distinguishing criteria...",
  "reasoning": "Your analysis explaining the distinction..."
}}

CRITICAL: The "other" field must contain specific concepts that {concept} is NOT. Do not leave it empty.""",
    "zoom-in": """Apply the ZOOM IN move to analyze: "{concept}"

Identify the PARTS that make up this concept:
1. What are its components?
2. What elements exist within it?
3. How can it be decomposed?

{context}

Respond in JSON format:
{{
  "pattern": "S",
  "elements": {{
    "whole": "{concept}",
    "parts": ["part1", "part2", "part3", ...]
  }},
  "part_descriptions": {{
    "part1": "description...",
    "part2": "description..."
  }},
  "reasoning": "Your analysis of the internal structure..."
}}""",
    "zoom-out": """Apply the ZOOM OUT move to analyze: "{concept}"

Identify the larger WHOLE/SYSTEM this concept belongs to:
1. What contains this concept?
2. What larger context does it exist within?
3. What is it a part of?

{context}

Respond in JSON format:
{{
  "pattern": "S",
  "elements": {{
    "part": "{concept}",
    "whole": "The larger system..."
  }},
  "context_layers": ["immediate context", "broader context", "broadest context"],
  "reasoning": "Your analysis of the external context..."
}}""",
    "part-party": """Apply the PART PARTY move to analyze: "{concept}"

1. Break the concept into its constituent PARTS
2. Show how those PARTS RELATE to each other
3. Map the internal relationship structure

{context}

Respond in JSON format:
{{
  "pattern": "S",
  "elements": {{
    "whole": "{concept}",
    "parts": ["part1", "part2", "part3", ...]
  }},
  "relationships": [
    {{"from": "part1", "to": "part2", "relationship": "description..."}},
    {{"from": "part2", "to": "part3", "relationship": "description..."}}
  ],
  "reasoning": "Your analysis of internal part relationships..."
}}""",
    "rds-barbell": """Apply the RDS BARBELL move to analyze: "{concept}"

RDS = Relate, Distinguish, Systematize

1. RELATE: What does this concept connect to? Identify key relationships.
2. DISTINGUISH: For each relationship, what makes it unique/distinct?
3. SYSTEMATIZE: What system or pattern emerges from these relationships?

{context}

Respond in JSON format:
{{
  "pattern": "R",
  "elements": {{
    "action": "{concept}",
    "reactions": ["related thing 1", "related thing 2", ...]
  }},
  "rds_analysis": [
    {{
      "relate": "Connection to X",
      "distinguish": "What makes this relationship unique",
      "systematize": "The system that emerges"
    }}
  ],
  "reasoning": "Your analysis of relationships..."
}}""",
    "p-circle": """Apply the P-CIRCLE move to analyze: "{concept}"

Map multiple PERSPECTIVES on this concept:
1. Who are the different observers/stakeholders?
2. What does each one see (their view)?
3. How do perspectives differ?

{context}

Respond in JSON format:
{{
  "pattern": "P",
  "elements": {{
    "concept": "{concept}",
    "perspectives": [
      {{"point": "Observer 1", "view": "What they see/believe..."}},
      {{"point": "Observer 2", "view": "What they see/believe..."}},
      {{"point": "Observer 3", "view": "What they see/believe..."}}
    ]
  }},
  "tensions": ["Where perspectives conflict..."],
  "synthesis": "How perspectives complement each other...",
  "reasoning": "Your analysis of multiple viewpoints..."
}}""",
    "woc": """Apply the WEB OF CAUSALITY (WoC) move to analyze: "{concept}"

Map the FORWARD CAUSAL EFFECTS - what does this concept CAUSE to happen?

1. Identify immediate effects (what happens directly because of this)
2. Identify secondary effects (what happens because of those effects)
3. Map the causal chain forward in time

{context}

Respond in JSON format:
{{
  "pattern": "R",
  "elements": {{
    "cause": "{concept}",
    "effects": [
      {{"effect": "Immediate effect 1", "level": 1, "description": "How this happens..."}},
      {{"effect": "Immediate effect 2", "level": 1, "description": "How this happens..."}},
      {{"effect": "Secondary effect 1", "level": 2, "description": "Caused by effect 1..."}},
      {{"effect": "Secondary effect 2", "level": 2, "description": "Caused by effect 2..."}}
    ]
  }},
  "causal_chain": "Description of the overall causal flow...",
  "time_horizon": "How far into the future these effects extend",
  "reasoning": "Your analysis of causal relationships..."
}}""",
    "waoc": """Apply the WEB OF ANTICAUSALITY (WAoC) move to analyze: "{concept}"

Map the ROOT CAUSES - what CAUSED this concept to exist or happen?

1. Identify immediate causes (what directly led to this)
2. Identify deeper causes (what caused those causes)
3. Trace the causal chain backward in time

{context}

Respond in JSON format:
{{
  "pattern": "R",
  "elements": {{
    "effect": "{concept}",
    "causes": [
      {{"cause": "Immediate cause 1", "level": 1, "description": "How this led to the concept..."}},
      {{"cause": "Immediate cause 2", "level": 1, "description": "How this led to the concept..."}},
      {{"cause": "Root cause 1", "level": 2, "description": "What caused cause 1..."}},
      {{"cause": "Root cause 2", "level": 2, "description": "What caused cause 2..."}}
    ]
  }},
  "root_analysis": "Description of the fundamental origins...",
  "historical_context": "How far back the causal chain extends",
  "reasoning": "Your analysis of root causes..."
}}""",
}


class BaseAIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a response from the AI model."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider name."""
        pass


class GeminiProvider(BaseAIProvider):
    """Google Gemini AI provider."""

    def __init__(self):
        try:
            import google.generativeai as genai
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY not set")
            genai.configure(api_key=api_key)
            # Use gemini-1.5-flash for better rate limits on free tier
            self.model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=DSRP_SYSTEM_PROMPT,
            )
            self._available = True
            logger.info("Gemini provider initialized successfully")
        except Exception as e:
            logger.warning(f"Gemini provider not available: {e}")
            self._available = False
            self.model = None

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def available(self) -> bool:
        return self._available

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not self._available:
            raise RuntimeError("Gemini provider not available")

        import time
        import random
        
        max_retries = 5
        base_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                # Add a small system prompt hint to ensure JSON if missing
                full_prompt = f"{user_prompt}\n\nIMPORTANT: Return ONLY valid JSON."
                
                response = self.model.generate_content(full_prompt)
                return response.text
                
            except Exception as e:
                error_str = str(e).lower()
                is_rate_limit = "429" in error_str or "quota" in error_str or "resource exhausted" in error_str
                
                if is_rate_limit and attempt < max_retries - 1:
                    delay = (base_delay * (2 ** attempt)) + (random.random() * 1)
                    logger.warning(f"Gemini rate limit hit. Retrying in {delay:.2f}s... (Attempt {attempt+1}/{max_retries})")
                    # Ideally use asyncio.sleep but this is sync call in async wrapper for now, 
                    # genai library is sync unless using async_generate_content. 
                    # Assuming we can block this thread or use asyncio.sleep if the method is async.
                    # The method signature is async def generate, but generate_content is sync blocking usually.
                    # We should use time.sleep for blockage if the library is blocking, or better yet switch to async if possible.
                    # For now, to keep it simple and safe within this structure:
                    time.sleep(delay)
                    continue
                
                if attempt == max_retries - 1:
                    logger.error(f"Gemini generation failed after {max_retries} attempts: {e}")
                    # Return a friendly JSON error if possible so frontend doesn't crash
                    if is_rate_limit:
                         # Fail gracefully with a JSON that informs the user
                         return json.dumps({
                             "error": "RateLimitError",
                             "message": "AI quota exceeded. Please wait a moment and try again.",
                             "pattern": "Error",
                             "elements": {},
                             "move": "error",
                             "related_concepts": []
                         })
                    raise e
        return ""


class ClaudeProvider(BaseAIProvider):
    """Anthropic Claude AI provider."""

    def __init__(self):
        try:
            from anthropic import Anthropic
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not set")
            self.client = Anthropic(api_key=api_key)
            self.model_name = "claude-sonnet-4-20250514"
            self._available = True
            logger.info("Claude provider initialized successfully")
        except Exception as e:
            logger.warning(f"Claude provider not available: {e}")
            self._available = False
            self.client = None

    @property
    def name(self) -> str:
        return "claude"

    @property
    def available(self) -> bool:
        return self._available

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not self._available:
            raise RuntimeError("Claude provider not available")

        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text


class OpenAIProvider(BaseAIProvider):
    """OpenAI GPT provider."""

    def __init__(self):
        try:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set")
            self.client = OpenAI(api_key=api_key)
            self.model_name = "gpt-4o"
            self._available = True
            logger.info("OpenAI provider initialized successfully")
        except Exception as e:
            logger.warning(f"OpenAI provider not available: {e}")
            self._available = False
            self.client = None

    @property
    def name(self) -> str:
        return "openai"

    @property
    def available(self) -> bool:
        return self._available

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not self._available:
            raise RuntimeError("OpenAI provider not available")

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=2000,
        )
        return response.choices[0].message.content


class OllamaProvider(BaseAIProvider):
    """Ollama local LLM provider."""

    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model_name = os.getenv("OLLAMA_MODEL", "llama3.2")
        self._available = False

        # Check if Ollama is reachable
        try:
            import httpx
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    model_names = [m.get("name", "").split(":")[0] for m in models]
                    if self.model_name.split(":")[0] in model_names or any(self.model_name in m for m in model_names):
                        self._available = True
                        logger.info(f"Ollama provider initialized with model: {self.model_name}")
                    else:
                        logger.warning(f"Ollama model '{self.model_name}' not found. Available: {model_names}")
        except Exception as e:
            logger.warning(f"Ollama provider not available: {e}")

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def available(self) -> bool:
        return self._available

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not self._available:
            raise RuntimeError("Ollama provider not available")

        import httpx

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": f"{system_prompt}\n\n{user_prompt}\n\nIMPORTANT: Return ONLY valid JSON.",
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 2000,
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")


class DSRPAgent:
    """AI agent for DSRP analysis supporting multiple providers."""

    def __init__(self, preferred_provider: str | None = None):
        """
        Initialize the DSRP agent.

        Args:
            preferred_provider: Preferred AI provider ("gemini", "claude", "openai").
                               If None, uses first available in order: gemini, claude, openai.
        """
        self.providers: dict[str, BaseAIProvider] = {}
        self.preferred_provider = preferred_provider or os.getenv("AI_PROVIDER", "gemini")

        # Initialize all providers (they handle their own availability)
        self.providers["gemini"] = GeminiProvider()
        self.providers["claude"] = ClaudeProvider()
        self.providers["openai"] = OpenAIProvider()
        self.providers["ollama"] = OllamaProvider()

        # Determine active provider
        self.active_provider = self._get_active_provider()
        if self.active_provider:
            logger.info(f"DSRP Agent using provider: {self.active_provider.name}")
        else:
            logger.warning("No AI providers available! Set AI_PROVIDER=ollama or configure API keys.")

    def _get_active_provider(self) -> BaseAIProvider | None:
        """Get the active provider based on preference and availability."""
        # Try preferred provider first
        if self.preferred_provider in self.providers:
            provider = self.providers[self.preferred_provider]
            if provider.available:
                return provider

        # Fall back to any available provider
        for name in ["gemini", "claude", "openai", "ollama"]:
            provider = self.providers.get(name)
            if provider and provider.available:
                return provider

        return None

    def get_available_providers(self) -> list[str]:
        """Return list of available provider names."""
        return [name for name, p in self.providers.items() if p.available]

    def set_provider(self, provider_name: str) -> bool:
        """Switch to a different provider."""
        if provider_name in self.providers and self.providers[provider_name].available:
            self.active_provider = self.providers[provider_name]
            logger.info(f"Switched to provider: {provider_name}")
            return True
        return False

    async def analyze(
        self,
        concept: str,
        move: str,
        context: str | None = None,
    ) -> dict:
        """
        Analyze a concept using one of the 6 DSRP moves.

        Args:
            concept: The concept to analyze
            move: One of: is-is-not, zoom-in, zoom-out, part-party, rds-barbell, p-circle
            context: Optional additional context about the concept

        Returns:
            Dictionary with analysis results
        """
        if not self.active_provider:
            raise RuntimeError(
                "No AI provider available. Please set GOOGLE_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY."
            )

        prompt_template = MOVE_PROMPTS.get(move)
        if not prompt_template:
            raise ValueError(f"Unknown move: {move}")

        context_str = f"Additional context: {context}" if context else ""
        user_prompt = prompt_template.format(concept=concept, context=context_str)

        # Get response from active provider
        response_text = await self.active_provider.generate(DSRP_SYSTEM_PROMPT, user_prompt)

        # Extract JSON from response (handle markdown code blocks)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        result = json.loads(response_text.strip())

        # Add metadata
        result["move"] = move
        result["concept"] = concept
        result["confidence"] = 0.85
        result["provider"] = self.active_provider.name

        # Ensure required fields
        if "related_concepts" not in result:
            result["related_concepts"] = self._extract_related_concepts(result)

        return result

    def _extract_related_concepts(self, result: dict) -> list[str]:
        """Extract related concepts from the analysis result."""
        related = []

        if "elements" in result:
            elements = result["elements"]
            if isinstance(elements.get("parts"), list):
                related.extend(elements["parts"])
            if elements.get("whole"):
                related.append(elements["whole"])
            if isinstance(elements.get("reactions"), list):
                related.extend(elements["reactions"])
            if isinstance(elements.get("perspectives"), list):
                for p in elements["perspectives"]:
                    if isinstance(p, dict) and p.get("point"):
                        related.append(p["point"])

        return list(set(related))[:10]

    async def extract_concepts_from_text(
        self,
        text: str,
        max_concepts: int = 10,
        source_name: str | None = None,
    ) -> dict:
        """
        Extract key concepts from a text document (PDF, transcript, etc.)

        Args:
            text: The extracted text content
            max_concepts: Maximum number of concepts to extract
            source_name: Optional name of the source document

        Returns:
            Dictionary with extracted concepts and their suggested moves
        """
        if not self.active_provider:
            raise RuntimeError("No AI provider available.")

        # Truncate text if too long (keep first ~8000 chars for context)
        if len(text) > 8000:
            text = text[:8000] + "\n\n[Text truncated...]"

        source_context = f" from '{source_name}'" if source_name else ""

        user_prompt = f"""Analyze this text{source_context} and extract the {max_concepts} most important concepts for DSRP analysis.

For each concept, suggest:
1. The concept name (2-4 words, clear and specific)
2. A brief description (1 sentence)
3. The best DSRP move to start analyzing it (is-is-not, zoom-in, zoom-out, part-party, rds-barbell, or p-circle)
4. Why this concept is important in the text

TEXT TO ANALYZE:
\"\"\"
{text}
\"\"\"

Respond in JSON format:
{{
  "source_summary": "Brief 1-2 sentence summary of what this text is about",
  "concepts": [
    {{
      "name": "Concept Name",
      "description": "Brief description",
      "suggested_move": "is-is-not",
      "importance": "Why this concept matters in the text"
    }}
  ],
  "main_theme": "The overarching theme or subject"
}}"""

        response_text = await self.active_provider.generate(DSRP_SYSTEM_PROMPT, user_prompt)

        # Extract JSON from response
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        result = json.loads(response_text.strip())
        result["provider"] = self.active_provider.name

        return result
