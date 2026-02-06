from text_extractor import extract_text
import io

def test_raw_text():
    print("Testing Raw Text Strategy...")
    content = b"Hello from a text file!"
    # Using .txt extension
    result = extract_text(content, filename="dummy.txt")
    print(f"TXT Result: {result.full_text}")
    assert "Hello from a text file!" in result.full_text
    assert result.metadata['method'] == 'raw_text'

    # Using .json extension
    content_json = b'{"key": "value"}'
    result = extract_text(content_json, filename="data.json")
    print(f"JSON Result: {result.full_text}")
    assert '{"key": "value"}' in result.full_text

def test_docx_mock():
    # Since we can't easily create a valid binary docx without the lib installed in this script runner 
    # (if we run before install), we will skip creating a real docx file here unless we are sure.
    # But checking if the registry picks the strategy is enough for "logic" verification.
    # The actual extraction depends on python-docx library correctness.
    
    print("\nTesting Registry Selection for Docx...")
    from text_extractor.registry import ExtractorRegistry
    strategy = ExtractorRegistry.auto_select_strategy("test.docx")
    print(f"Selected Strategy: {type(strategy).__name__}")
    assert "DocxStrategy" in type(strategy).__name__

if __name__ == "__main__":
    try:
        test_raw_text()
        test_docx_mock()
        print("\nSUCCESS: All new type tests passed!")
    except Exception as e:
        print(f"\nFAILURE: {e}")
        exit(1)
