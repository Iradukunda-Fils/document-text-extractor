"""Tests for DocxStrategy."""
import pytest
from unittest.mock import MagicMock, patch, Mock
from io import BytesIO
from text_extractor.strategies.docx import DocxStrategy


@patch('text_extractor.strategies.docx.Document')
def test_docx_extract_simple(mock_document_class):
    """Test basic DOCX extraction."""
    # Setup mock document
    mock_doc = MagicMock()
    mock_para1 = MagicMock()
    mock_para1.text = "First paragraph"
    mock_para2 = MagicMock()
    mock_para2.text = "Second paragraph"
    mock_doc.paragraphs = [mock_para1, mock_para2]
    
    mock_document_class.return_value = mock_doc
    
    strategy = DocxStrategy()
    stream = BytesIO(b"fake docx content")
    
    result = strategy.extract(stream)
    
    assert "First paragraph" in result.full_text
    assert "Second paragraph" in result.full_text
    assert result.metadata['method'] == 'docx'
    assert result.metadata['paragraph_count'] == 2


@patch('text_extractor.strategies.docx.Document')
def test_docx_extract_empty_document(mock_document_class):
    """Test extraction from empty DOCX."""
    mock_doc = MagicMock()
    mock_doc.paragraphs = []
    mock_document_class.return_value = mock_doc
    
    strategy = DocxStrategy()
    stream = BytesIO(b"fake docx")
    
    result = strategy.extract(stream)
    
    assert result.full_text == ""
    assert result.metadata['paragraph_count'] == 0


@patch('text_extractor.strategies.docx.Document')
def test_docx_extract_with_empty_paragraphs(mock_document_class):
    """Test extraction with some empty paragraphs."""
    mock_doc = MagicMock()
    mock_para1 = MagicMock()
    mock_para1.text = "Content"
    mock_para2 = MagicMock()
    mock_para2.text = ""  # Empty paragraph
    mock_para3 = MagicMock()
    mock_para3.text = "More content"
    mock_doc.paragraphs = [mock_para1, mock_para2, mock_para3]
    
    mock_document_class.return_value = mock_doc
    
    strategy = DocxStrategy()
    stream = BytesIO(b"fake docx")
    
    result = strategy.extract(stream)
    
    assert "Content" in result.full_text
    assert "More content" in result.full_text
    assert result.metadata['paragraph_count'] == 3


@patch('text_extractor.strategies.docx.logger')
@patch('text_extractor.strategies.docx.Document')
def test_docx_logs_warning_for_large_file(mock_document_class, mock_logger):
    """Test that large DOCX files trigger a warning."""
    mock_doc = MagicMock()
    mock_doc.paragraphs = []
    mock_document_class.return_value = mock_doc
    
    strategy = DocxStrategy()
    
    # Create a mock stream that reports large size
    stream = MagicMock()
    stream.seek = MagicMock()
    stream.tell = MagicMock(side_effect=[60 * 1024 * 1024, 0])  # 60MB, then reset
    
    result = strategy.extract(stream)
    
    # Verify warning was logged
    mock_logger.warning.assert_called()
    warning_msg = str(mock_logger.warning.call_args)
    assert "Large DOCX file detected" in warning_msg or "60" in warning_msg


@patch('text_extractor.strategies.docx.Document')
def test_docx_extract_unicode_content(mock_document_class):
    """Test extraction with Unicode characters."""
    mock_doc = MagicMock()
    mock_para = MagicMock()
    mock_para.text = "Unicode: 你好 мир 🌍"
    mock_doc.paragraphs = [mock_para]
    
    mock_document_class.return_value = mock_doc
    
    strategy = DocxStrategy()
    stream = BytesIO(b"fake docx")
    
    result = strategy.extract(stream)
    
    assert "你好" in result.full_text
    assert "мир" in result.full_text
    assert "🌍" in result.full_text


@patch('text_extractor.strategies.docx.Document')
def test_docx_extraction_failure(mock_document_class):
    """Test that extraction errors are properly raised."""
    mock_document_class.side_effect = Exception("Failed to open DOCX")
    
    strategy = DocxStrategy()
    stream = BytesIO(b"corrupt docx")
    
    with pytest.raises(Exception) as exc_info:
        strategy.extract(stream)
    
    assert "Failed to extract text from Docx" in str(exc_info.value)


@patch('text_extractor.strategies.docx.Document')
def test_docx_stream_seeking(mock_document_class):
    """Test that stream is properly seeked before processing."""
    mock_doc = MagicMock()
    mock_doc.paragraphs = []
    mock_document_class.return_value = mock_doc
    
    strategy = DocxStrategy()
    stream = MagicMock()
    stream.seek = MagicMock()
    stream.tell = MagicMock(return_value=1024)  # Return small size (1KB)
    
    strategy.extract(stream)
    
    # Verify seek(0) was called
    stream.seek.assert_called_with(0)


@patch('text_extractor.strategies.docx.Document')
def test_docx_preserves_paragraph_order(mock_document_class):
    """Test that paragraph order is preserved."""
    mock_doc = MagicMock()
    paragraphs = []
    for i in range(10):
        para = MagicMock()
        para.text = f"Paragraph {i}"
        paragraphs.append(para)
    mock_doc.paragraphs = paragraphs
    
    mock_document_class.return_value = mock_doc
    
    strategy = DocxStrategy()
    stream = BytesIO(b"fake docx")
    
    result = strategy.extract(stream)
    
    # Verify order
    for i in range(10):
        assert f"Paragraph {i}" in result.full_text
    
    # Verify they appear in order
    lines = result.full_text.split('\n')
    for i, line in enumerate(lines):
        if line:
            assert f"Paragraph {i}" == line
