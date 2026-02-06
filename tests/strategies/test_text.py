"""Tests for RawTextStrategy."""
import pytest
from unittest.mock import MagicMock, patch
from io import BytesIO
from text_extractor.strategies.text import RawTextStrategy


def test_text_extract_simple():
    """Test basic text extraction."""
    strategy = RawTextStrategy()
    content = b"Hello, World!\nThis is a test."
    stream = BytesIO(content)
    
    result = strategy.extract(stream)
    
    assert result.full_text == "Hello, World!\nThis is a test."
    assert result.metadata['method'] == 'raw_text'
    assert result.metadata['page_count'] == 1
    assert len(result.pages) == 1


def test_text_extract_utf8():
    """Test UTF-8 encoded text extraction."""
    strategy = RawTextStrategy()
    content = "Здравствуй мир! 你好世界 مرحبا بالعالم".encode('utf-8')
    stream = BytesIO(content)
    
    result = strategy.extract(stream)
    
    assert "Здравствуй мир!" in result.full_text
    assert "你好世界" in result.full_text
    assert "مرحبا بالعالم" in result.full_text


def test_text_extract_latin1_fallback():
    """Test fallback to latin-1 for non-UTF8 content."""
    strategy = RawTextStrategy()
    # Create content with latin-1 specific characters
    content = b"\xc0\xe9\xf1"  # Characters that aren't valid UTF-8
    stream = BytesIO(content)
    
    # Should not raise an error
    result = strategy.extract(stream)
    
    # Should have some text (decoded as latin-1)
    assert len(result.full_text) > 0


def test_text_extract_large_file():
    """Test chunked reading for large files."""
    strategy = RawTextStrategy()
    
    # Create a large text content (2MB)
    chunk_size = 1024 * 1024  # 1MB
    large_content = b"A" * (chunk_size * 2)
    stream = BytesIO(large_content)
    
    result = strategy.extract(stream)
    
    # Verify all content was read
    assert len(result.full_text) == chunk_size * 2
    assert result.full_text == "A" * (chunk_size * 2)


def test_text_extract_from_bytes_directly():
    """Test extraction when stream is bytes directly."""
    strategy = RawTextStrategy()
    content = b"Direct bytes content"
    
    # Pass bytes directly (not BytesIO)
    result = strategy.extract(content)
    
    assert result.full_text == "Direct bytes content"


def test_text_extract_empty_file():
    """Test extraction from empty file."""
    strategy = RawTextStrategy()
    stream = BytesIO(b"")
    
    result = strategy.extract(stream)
    
    assert result.full_text == ""
    assert result.metadata['page_count'] == 1


def test_text_extract_with_special_characters():
    """Test extraction with various special characters."""
    strategy = RawTextStrategy()
    content = b"Line 1\r\nLine 2\tTabbed\nLine 3\x00Null"
    stream = BytesIO(content)
    
    result = strategy.extract(stream)
    
    assert "Line 1" in result.full_text
    assert "Line 2" in result.full_text
    assert "Tabbed" in result.full_text


def test_text_extract_multiple_chunks():
    """Test that chunked reading preserves content correctly."""
    strategy = RawTextStrategy()
    
    # Create content that spans multiple chunks
    # Each chunk is 1MB, so 3MB should be 3 chunks
    content = ("Chunk1-" * 200000 + "Chunk2-" * 200000 + "Chunk3-" * 200000).encode('utf-8')
    stream = BytesIO(content)
    
    result = strategy.extract(stream)
    
    # Verify all chunks are present
    assert "Chunk1-" in result.full_text
    assert "Chunk2-" in result.full_text
    assert "Chunk3-" in result.full_text


@patch('text_extractor.strategies.text.logger')
def test_text_extract_logs_large_file_warning(mock_logger):
    """Test that large files trigger a warning log."""
    strategy = RawTextStrategy()
    
    # Create a file larger than 500MB threshold (use mock to avoid actual large allocation)
    # We'll just verify the logging behavior with a smaller file
    large_content = b"X" * (600 * 1024 * 1024)  # 600MB
    stream = BytesIO(large_content)
    
    result = strategy.extract(stream)
    
    # The warning should be logged
    mock_logger.warning.assert_called()
    warning_calls = [call for call in mock_logger.warning.call_args_list 
                     if 'Large text file detected' in str(call)]
    assert len(warning_calls) > 0
