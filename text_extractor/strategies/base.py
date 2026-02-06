from abc import ABC, abstractmethod
from typing import List, Tuple, Union
from dataclasses import dataclass

@dataclass
class ExtractionResult:
    """Encapsulates the result of a text extraction operation."""
    full_text: str
    pages: List[str]
    metadata: dict

class BaseExtractionStrategy(ABC):
    """Abstract base class for text extraction strategies."""

    @abstractmethod
    def extract(self, file_stream, language: str = 'eng') -> ExtractionResult:
        """
        Extracts text from the given file stream.

        Args:
            file_stream: A binary file stream (e.g. from open() or st.file_uploader)
            language: Language code for OCR or specific parsing (default: 'eng')

        Returns:
            ExtractionResult object containing the text and metadata.
        """
        pass
