import pytest
from unittest.mock import patch, MagicMock
from io import StringIO
from text_extractor.strategies.pdf import PdfNativeStrategy

@patch('text_extractor.strategies.pdf.extract_text_to_fp')
@patch('text_extractor.strategies.pdf.PDFPage')
def test_pdf_extract_success(mock_pdf_page, mock_extract_to_fp):
    # Setup mocks
    mock_extract_to_fp.side_effect = lambda stream, out, **kwargs: out.write("Extracted Text")
    
    # Mock pages - just 1 page
    mock_pdf_page.get_pages.return_value = [MagicMock()]
    
    # We also need to mock the page iterators inside the method
    # Since the method instantiates TextConverter and PDFPageInterpreter locally,
    # we might need to patch those classes or just accept that the loop runs.
    # To keep it simple, let's patch the classes used inside the loop.
    
    with patch('text_extractor.strategies.pdf.TextConverter') as MockConverter, \
         patch('text_extractor.strategies.pdf.PDFPageInterpreter') as MockInterpreter:

        # Mock the TextConverter to write to the passed StringIO
        def mock_converter_init(rsrcmgr, retstr, **kwargs):
            # Write text to the retstr (StringIO) that was passed in
            retstr.write("Extracted Text from page")
            mock_instance = MagicMock()
            mock_instance.close = MagicMock()
            return mock_instance
        
        MockConverter.side_effect = mock_converter_init
        
        strategy = PdfNativeStrategy()
        stream = MagicMock()
        # Fix for pdfminer using .tell() and .seek()
        stream.tell.return_value = 0
        stream.read.return_value = b"" # Ensure read returns bytes if called
        
        result = strategy.extract(stream)
        
        assert "Extracted Text from page" in result.full_text
        assert result.metadata['method'] == 'native_pdf'
