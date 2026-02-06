import pytest
from text_extractor.registry import ExtractorRegistry
from text_extractor.strategies.pdf import PdfNativeStrategy
from text_extractor.strategies.ocr import OcrStrategy

def test_registry_auto_select_pdf():
    strategy = ExtractorRegistry.auto_select_strategy("document.pdf")
    assert isinstance(strategy, PdfNativeStrategy)

def test_registry_auto_select_png():
    strategy = ExtractorRegistry.auto_select_strategy("screenshot.png")
    assert isinstance(strategy, OcrStrategy)

def test_registry_auto_select_jpg():
    strategy = ExtractorRegistry.auto_select_strategy("photo.jpg")
    assert isinstance(strategy, OcrStrategy)

def test_registry_force_ocr():
    # Even with a PDF extension, should return OCR if enabled
    strategy = ExtractorRegistry.auto_select_strategy("document.pdf", enable_ocr=True)
    assert isinstance(strategy, OcrStrategy)

def test_registry_unknown_extension_fallback():
    # Should fallback to PDF Native for unknown types
    strategy = ExtractorRegistry.auto_select_strategy("unknown_file.xyz")
    assert isinstance(strategy, PdfNativeStrategy)
