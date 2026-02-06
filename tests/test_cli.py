"""Tests for the CLI (__main__.py)."""
import pytest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
from text_extractor.__main__ import main
from text_extractor.strategies.base import ExtractionResult


@patch('text_extractor.__main__.extract_text')
@patch('sys.argv', ['text_extractor', 'test.pdf'])
def test_cli_basic_extraction(mock_extract):
    """Test basic CLI extraction."""
    mock_extract.return_value = ExtractionResult(
        full_text="Extracted content",
        pages=["Extracted content"],
        metadata={"method": "pdf"}
    )
    
    with patch('text_extractor.__main__.Path.exists', return_value=True):
        with patch('builtins.print') as mock_print:
            main()
    
    mock_extract.assert_called_once()
    mock_print.assert_called_with("Extracted content")


@patch('text_extractor.__main__.extract_text')
@patch('sys.argv', ['text_extractor', 'test.pdf', '--ocr'])
def test_cli_with_ocr_flag(mock_extract):
    """Test CLI with OCR flag."""
    mock_extract.return_value = ExtractionResult(
        full_text="OCR content",
        pages=["OCR content"],
        metadata={"method": "ocr"}
    )
    
    with patch('text_extractor.__main__.Path.exists', return_value=True):
        with patch('builtins.print'):
            main()
    
    # Verify ocr_mode='force' was passed
    call_args = mock_extract.call_args
    assert call_args[1]['ocr_mode'] == 'force'


@patch('text_extractor.__main__.extract_text')
@patch('sys.argv', ['text_extractor', 'test.pdf', '--language', 'fra'])
def test_cli_with_language(mock_extract):
    """Test CLI with custom language."""
    mock_extract.return_value = ExtractionResult(
        full_text="French content",
        pages=["French content"],
        metadata={"method": "pdf"}
    )
    
    with patch('text_extractor.__main__.Path.exists', return_value=True):
        with patch('builtins.print'):
            main()
    
    # Verify language='fra' was passed
    call_args = mock_extract.call_args
    assert call_args[1]['language'] == 'fra'


@patch('text_extractor.__main__.extract_text')
@patch('sys.argv', ['text_extractor', 'test.pdf', '--output', 'output.txt'])
def test_cli_with_output_file(mock_extract):
    """Test CLI with output file."""
    mock_extract.return_value = ExtractionResult(
        full_text="Content to save",
        pages=["Content to save"],
        metadata={"method": "pdf"}
    )
    
    with patch('text_extractor.__main__.Path.exists', return_value=True):
        m = mock_open()
        with patch('builtins.open', m):
            main()
    
    # Verify file was written
    m.assert_called_once_with(Path('output.txt'), 'w', encoding='utf-8')
    handle = m()
    handle.write.assert_called_once_with("Content to save")


@patch('sys.argv', ['text_extractor', 'nonexistent.pdf'])
def test_cli_file_not_found():
    """Test CLI with non-existent file."""
    with pytest.raises(SystemExit) as exc_info:
        main()
    
    assert exc_info.value.code == 1


@patch('text_extractor.__main__.extract_text')
@patch('sys.argv', ['text_extractor', 'test.pdf'])
def test_cli_extraction_error(mock_extract):
    """Test CLI handles extraction errors."""
    from text_extractor import TextExtractionError
    mock_extract.side_effect = TextExtractionError("Extraction failed")
    
    with patch('text_extractor.__main__.Path.exists', return_value=True):
        with pytest.raises(SystemExit) as exc_info:
            main()
    
    assert exc_info.value.code == 1


@patch('text_extractor.__main__.extract_text')
@patch('sys.argv', ['text_extractor', 'test.pdf', '-v'])
def test_cli_verbose_logging(mock_extract):
    """Test CLI with verbose flag."""
    import logging
    
    mock_extract.return_value = ExtractionResult(
        full_text="Content",
        pages=["Content"],
        metadata={}
    )
    
    with patch('text_extractor.__main__.Path.exists', return_value=True):
        with patch('builtins.print'):
            with patch('logging.basicConfig') as mock_logging:
                main()
    
    # Verify logging was configured with INFO level
    call_args = mock_logging.call_args
    assert call_args[1]['level'] == logging.INFO
