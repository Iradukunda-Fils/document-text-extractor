import pytest
import io
from pathlib import Path

@pytest.fixture
def dummy_pdf_bytes():
    """Returns the bytes of a specialized 'Hello World' PDF."""
    # This is a minimal PDF file content
    return b"%PDF-1.4\r\n%...dummy content..."

@pytest.fixture
def dummy_image_bytes():
    """Returns dummy bytes simulating an image."""
    return b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR..."
