from .registry import ExtractorRegistry
from .exceptions import TextExtractionError, OcrError, UnsupportedFileTypeError
from .strategies.base import ExtractionResult
from .core import extract, TextExtractor

# Alias for backward compatibility or cleaner naming
extract_text = extract 

__all__ = [
    "ExtractorRegistry",
    "TextExtractionError",
    "OcrError",
    "UnsupportedFileTypeError",
    "ExtractionResult",
    "extract_text",
    "TextExtractor"
]
