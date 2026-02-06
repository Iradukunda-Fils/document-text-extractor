import pytest
from unittest.mock import MagicMock, patch
from text_extractor.core import extract, TextExtractor
from text_extractor.strategies.base import ExtractionResult

@patch('text_extractor.core.ExtractorRegistry')
def test_extract_calls_strategy_correctly(mock_registry):
    # Setup mock strategy
    mock_strategy = MagicMock()
    mock_registry.auto_select_strategy.return_value = mock_strategy
    expected_result = ExtractionResult(full_text="Result", pages=["Result"], metadata={})
    mock_strategy.extract.return_value = expected_result

    # Call with simple byte input
    input_bytes = b"some data"
    result = extract(input_bytes, filename="test.pdf")

    # Verify Registry was asked for a strategy
    mock_registry.auto_select_strategy.assert_called_with("test.pdf", enable_ocr=False)
    
    # Verify strategy.extract was called
    mock_strategy.extract.assert_called()
    assert result == expected_result

@patch('text_extractor.core.ExtractorRegistry')
def test_extract_ocr_mode_force(mock_registry):
    mock_strategy = MagicMock()
    mock_registry.auto_select_strategy.return_value = mock_strategy
    mock_strategy.extract.return_value = ExtractionResult(full_text="", pages=[], metadata={})

    extract(b"", filename="test.pdf", ocr_mode='force')
    
    # Enable OCR should be True
    mock_registry.auto_select_strategy.assert_called_with("test.pdf", enable_ocr=True)

def test_extract_invalid_input_type():
    with pytest.raises(Exception):
        extract(12345) # Passing int instead of str/bytes/stream

@patch('text_extractor.core.ExtractorRegistry')
def test_smart_fallback_to_ocr(mock_registry):
    """Test that core automatically falls back to OCR for scanned PDFs."""
    # Setup: Native PDF extraction returns very little text
    mock_pdf_strategy = MagicMock()
    mock_pdf_strategy.__class__.__name__ = 'PdfNativeStrategy'
    
    # Simulate a scanned PDF (native extraction yields almost nothing)
    scanned_result = ExtractionResult(
        full_text="   ",  # Only whitespace
        pages=[""],
        metadata={"method": "native_pdf", "page_count": 1}
    )
    mock_pdf_strategy.extract.return_value = scanned_result
    
    # Setup OCR strategy mock
    mock_ocr_strategy = MagicMock()
    ocr_result = ExtractionResult(
        full_text="Scanned document content",
        pages=["Scanned document content"],
        metadata={"method": "ocr", "page_count": 1}
    )
    mock_ocr_strategy.extract.return_value = ocr_result
    
    # Configure registry
    mock_registry.auto_select_strategy.return_value = mock_pdf_strategy
    mock_registry.get_strategy.return_value = mock_ocr_strategy
    
    # Execute
    result = extract(b"fake pdf", filename="scanned.pdf", ocr_mode='auto')
    
    # Verify fallback occurred
    mock_registry.get_strategy.assert_called_once_with('ocr')
    assert result.metadata.get('fallback_triggered') == True
    assert result.full_text == "Scanned document content"
