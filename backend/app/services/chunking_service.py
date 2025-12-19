"""
Semantic Chunking Service

Provides intelligent text chunking that respects:
- Sentence boundaries
- Paragraph structure
- Section headers
- Semantic coherence

Better chunking leads to better RAG retrieval quality.
"""

import re
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """A text chunk with metadata."""
    text: str
    index: int
    start_char: int
    end_char: int
    metadata: dict


class SemanticChunker:
    """
    Intelligent text chunker that respects semantic boundaries.

    Unlike character-based chunking, this chunker:
    1. Splits on sentence boundaries
    2. Respects paragraph breaks
    3. Keeps related sentences together
    4. Maintains configurable overlap
    """

    # Sentence-ending patterns
    SENTENCE_ENDINGS = re.compile(r'(?<=[.!?])\s+(?=[A-Z])')

    # Paragraph patterns
    PARAGRAPH_BREAK = re.compile(r'\n\s*\n')

    # Section header patterns
    SECTION_HEADER = re.compile(r'^(?:#{1,6}\s|(?:\d+\.)+\s|[A-Z][A-Z\s]+:)', re.MULTILINE)

    def __init__(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 150,
        min_chunk_size: int = 100,
        respect_sentences: bool = True,
        respect_paragraphs: bool = True,
    ):
        """
        Initialize the chunker.

        Args:
            chunk_size: Target size for each chunk (characters)
            chunk_overlap: Overlap between consecutive chunks
            min_chunk_size: Minimum chunk size to keep
            respect_sentences: Try not to split mid-sentence
            respect_paragraphs: Prefer splitting at paragraph boundaries
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.respect_sentences = respect_sentences
        self.respect_paragraphs = respect_paragraphs

    def _split_into_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        # First split by sentence-ending punctuation
        sentences = self.SENTENCE_ENDINGS.split(text)

        # Clean up and filter empty sentences
        result = []
        for s in sentences:
            s = s.strip()
            if s:
                result.append(s)

        return result

    def _split_into_paragraphs(self, text: str) -> list[str]:
        """Split text into paragraphs."""
        paragraphs = self.PARAGRAPH_BREAK.split(text)
        return [p.strip() for p in paragraphs if p.strip()]

    def _find_split_point(self, text: str, target_pos: int) -> int:
        """
        Find the best position to split text near target_pos.

        Prefers splitting at:
        1. Paragraph breaks
        2. Sentence endings
        3. Word boundaries
        """
        search_range = min(200, len(text) - target_pos, target_pos)

        # Look for paragraph break
        if self.respect_paragraphs:
            for offset in range(search_range):
                # Search forward
                pos = target_pos + offset
                if pos < len(text) - 1 and text[pos:pos+2] == '\n\n':
                    return pos + 2
                # Search backward
                pos = target_pos - offset
                if pos > 0 and text[pos-2:pos] == '\n\n':
                    return pos

        # Look for sentence ending
        if self.respect_sentences:
            for offset in range(search_range):
                # Search forward
                pos = target_pos + offset
                if pos < len(text) and text[pos] in '.!?' and pos + 1 < len(text) and text[pos + 1] == ' ':
                    return pos + 2
                # Search backward
                pos = target_pos - offset
                if pos > 0 and text[pos - 1] in '.!?' and text[pos] == ' ':
                    return pos

        # Fall back to word boundary
        for offset in range(min(50, search_range)):
            pos = target_pos + offset
            if pos < len(text) and text[pos] == ' ':
                return pos + 1
            pos = target_pos - offset
            if pos > 0 and text[pos] == ' ':
                return pos + 1

        return target_pos

    def chunk(self, text: str, metadata: Optional[dict] = None) -> list[Chunk]:
        """
        Split text into semantic chunks.

        Args:
            text: The text to chunk
            metadata: Optional metadata to include with each chunk

        Returns:
            List of Chunk objects
        """
        if not text or not text.strip():
            return []

        text = text.strip()
        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            # Determine end position
            end = start + self.chunk_size

            if end >= len(text):
                # Last chunk - take everything remaining
                end = len(text)
            else:
                # Find best split point
                end = self._find_split_point(text, end)

            # Extract chunk text
            chunk_text = text[start:end].strip()

            # Only keep chunks above minimum size
            if len(chunk_text) >= self.min_chunk_size:
                chunks.append(Chunk(
                    text=chunk_text,
                    index=chunk_index,
                    start_char=start,
                    end_char=end,
                    metadata={
                        **(metadata or {}),
                        "chunk_method": "semantic",
                    }
                ))
                chunk_index += 1

            # Move start position with overlap
            if end >= len(text):
                break

            # Calculate overlap start
            overlap_start = end - self.chunk_overlap
            if overlap_start <= start:
                # Prevent infinite loop
                start = end
            else:
                start = self._find_split_point(text, overlap_start)

        logger.debug(f"Created {len(chunks)} semantic chunks from {len(text)} chars")
        return chunks

    def chunk_by_paragraphs(self, text: str, metadata: Optional[dict] = None) -> list[Chunk]:
        """
        Chunk text by paragraphs, merging small ones.

        Args:
            text: The text to chunk
            metadata: Optional metadata

        Returns:
            List of Chunk objects
        """
        paragraphs = self._split_into_paragraphs(text)

        chunks = []
        current_chunk = ""
        chunk_index = 0
        start_char = 0

        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 <= self.chunk_size:
                # Add to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
            else:
                # Save current chunk and start new one
                if current_chunk and len(current_chunk) >= self.min_chunk_size:
                    chunks.append(Chunk(
                        text=current_chunk,
                        index=chunk_index,
                        start_char=start_char,
                        end_char=start_char + len(current_chunk),
                        metadata={
                            **(metadata or {}),
                            "chunk_method": "paragraph",
                        }
                    ))
                    chunk_index += 1
                    start_char += len(current_chunk) + 2

                current_chunk = para

        # Don't forget the last chunk
        if current_chunk and len(current_chunk) >= self.min_chunk_size:
            chunks.append(Chunk(
                text=current_chunk,
                index=chunk_index,
                start_char=start_char,
                end_char=start_char + len(current_chunk),
                metadata={
                    **(metadata or {}),
                    "chunk_method": "paragraph",
                }
            ))

        return chunks


# Singleton instance
_chunker: Optional[SemanticChunker] = None


def get_chunker(
    chunk_size: int = 800,
    chunk_overlap: int = 150,
) -> SemanticChunker:
    """Get a chunker instance with specified settings."""
    global _chunker
    if _chunker is None or _chunker.chunk_size != chunk_size or _chunker.chunk_overlap != chunk_overlap:
        _chunker = SemanticChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
    return _chunker
