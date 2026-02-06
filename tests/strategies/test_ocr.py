"""Tests for OcrStrategy."""
import pytest
from unittest.mock import MagicMock, patch, Mock
from io import BytesIO
from text_extractor.strategies.ocr import OcrStrategy
from text_extractor.exceptions import OcrError


@patch('text_extractor.strategies.ocr.pdfinfo_from_path')
@patch('text_extractor.strategies.ocr.convert_from_path')
@patch('text_extractor.strategies.ocr.pytesseract')
def test_ocr_pdf_chunked_processing(mock_tesseract, mock_convert, mock_pdfinfo):
    """Test that OCR processes PDF in chunks."""
    # Setup: Simulate a 12-page PDF (should process in 3 batches of 5, 5, 2)
    mock_pdfinfo.return_value = {"Pages": 12}
    
    # Mock images returned by convert_from_path - need different counts per call
    batch1 = [MagicMock() for _ in range(5)]
    batch2 = [MagicMock() for _ in range(5)]
    batch3 = [MagicMock() for _ in range(2)]  # Last batch is smaller
    
    for batch in [batch1, batch2, batch3]:
        for img in batch:
            img.close = MagicMock()
    
    # Mock returns different batches on successive calls
    mock_convert.side_effect = [batch1, batch2, batch3]
    mock_tesseract.image_to_string.return_value = "Page text"
    
    strategy = OcrStrategy()
    stream = BytesIO(b"fake pdf content")
    
    result = strategy.extract(stream, language='eng')
    
    # Verify chunking: convert_from_path should be called 3 times
    assert mock_convert.call_count == 3
    
    # Verify parallel execution setup (ThreadPoolExecutor was used)
    assert result.metadata['page_count'] == 12
    assert len(result.pages) == 12


@patch('text_extractor.strategies.ocr.pdfinfo_from_path')
@patch('text_extractor.strategies.ocr.Image')
def test_ocr_fallback_to_image(mock_image, mock_pdfinfo):
    """Test that OCR falls back to PIL for non-PDF images."""
    # Simulate pdfinfo_from_path failing (not a PDF)
    mock_pdfinfo.side_effect = Exception("Not a PDF")
    
    # Mock PIL Image.open
    mock_img = MagicMock()
    mock_img.close = MagicMock()
    mock_image.open.return_value = mock_img
    
    with patch('text_extractor.strategies.ocr.pytesseract.image_to_string') as mock_tesseract:
        mock_tesseract.return_value = "Image text content"
        
        strategy = OcrStrategy()
        stream = BytesIO(b"fake image content")
        
        result = strategy.extract(stream)
        
        # Verify fallback to PIL
        mock_image.open.assert_called_once()
        assert result.full_text == "Image text content"
        assert result.metadata['page_count'] == 1


@patch('text_extractor.strategies.ocr.pdfinfo_from_path')
def test_ocr_raises_error_on_failure(mock_pdfinfo):
    """Test that OCR raises OcrError on complete failure."""
    mock_pdfinfo.side_effect = Exception("Critical failure")
    
    with patch('text_extractor.strategies.ocr.Image.open') as mock_img_open:
        mock_img_open.side_effect = Exception("Image open failed")
        
        strategy = OcrStrategy()
        stream = BytesIO(b"invalid content")
        
        with pytest.raises(OcrError):
            strategy.extract(stream)


@patch('text_extractor.strategies.ocr.pdfinfo_from_path')
@patch('text_extractor.strategies.ocr.convert_from_path')
@patch('text_extractor.strategies.ocr.pytesseract')
def test_ocr_handles_different_languages(mock_tesseract, mock_convert, mock_pdfinfo):
    """Test OCR with different language codes."""
    mock_pdfinfo.return_value = {"Pages": 1}
    mock_images = [MagicMock()]
    mock_images[0].close = MagicMock()
    mock_convert.return_value = mock_images
    mock_tesseract.image_to_string.return_value = "Texte français"
    
    strategy = OcrStrategy()
    stream = BytesIO(b"fake pdf")
    
    result = strategy.extract(stream, language='fra')
    
    # Verify language was passed to tesseract
    mock_tesseract.image_to_string.assert_called_with(mock_images[0], lang='fra')
    assert result.metadata['language'] == 'fra'
