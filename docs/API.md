# API Reference

## Overview

DocuExtract Pro provides three interfaces for text extraction:
1. **Python Module API** - For programmatic integration
2. **Command-Line Interface (CLI)** - For scripting and automation  
3. **Web UI** - For interactive use via browser

---

## Python Module API

### Installation

```bash
pip install -e .
```

### Quick Start

```python
from text_extractor import extract_text

# Extract from file path
result = extract_text("document.pdf")
print(result.full_text)
```

---

### Core Functions

#### `extract_text(input_data, filename=None, ocr_mode='auto', language='eng')`

Main entry point for text extraction.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `input_data` | `str | Path | bytes | BinaryIO` | *required* | File path, bytes, or file-like object |
| `filename` | `str | None` | `None` | Filename hint for type detection (required if `input_data` is bytes) |
| `ocr_mode` | `str` | `'auto'` | OCR mode: `'auto'`, `'force'`, or `'skip'` |
| `language` | `str` | `'eng'` | Tesseract language code (e.g., `'eng'`, `'fra'`, `'ara'`) |

**Returns:** `ExtractionResult`

**Example:**

```python
from text_extractor import extract_text

# From file path
result = extract_text("invoice.pdf")

# From bytes with OCR
with open("scanned.pdf", "rb") as f:
    result = extract_text(f.read(), filename="scanned.pdf", ocr_mode='force')

# French document
result = extract_text("rapport.pdf", language='fra')
```

---

### Data Structures

#### `ExtractionResult`

Object returned by all extraction methods.

**Attributes:**
| Attribute | Type | Description |
|-----------|------|-------------|
| `full_text` | `str` | Concatenated text from all pages |
| `pages` | `List[str]` | List of text content per page |
| `metadata` | `Dict[str, Any]` | Document metadata (author, title, page_count, etc.) |

**Example:**

```python
result = extract_text("document.pdf")

# Access full text
print(result.full_text)

# Access individual pages
for i, page_text in enumerate(result.pages, 1):
    print(f"Page {i}: {page_text[:100]}...")

# Check metadata
print(f"Pages: {result.metadata.get('page_count')}")
print(f"Fallback triggered: {result.metadata.get('fallback_triggered', False)}")
```

---

### Advanced Usage

#### `TextExtractor` Class

Low-level interface for custom workflows.

```python
from text_extractor import TextExtractor

extractor = TextExtractor()
result = extractor.extract(
    "document.pdf",
    ocr_mode='auto',
    language='eng'
)
```

#### Strategy Pattern (Expert Use)

```python
from text_extractor.registry import ExtractorRegistry

# Get specific strategy
strategy = ExtractorRegistry.get_strategy('pdf_native')

# Extract using strategy directly
with open("document.pdf", "rb") as stream:
    result = strategy.extract(stream, language='eng')
```

---

### Exception Handling

```python
from text_extractor import extract_text, TextExtractionError, OcrError

try:
    result = extract_text("malformed.pdf")
except TextExtractionError as e:
    print(f"Extraction failed: {e}")
except OcrError as e:
    print(f"OCR failed: {e}")
```

**Exception Hierarchy:**
- `TextExtractionError` (base exception)
  - `OcrError` (OCR-specific failures)
  - `UnsupportedFileTypeError` (unknown file format)

---

## Command-Line Interface (CLI)

### Installation

```bash
chmod +x extract
./extract --help
```

### Basic Usage

```bash
# Extract and print to stdout
./extract document.pdf

# Save to file
./extract document.pdf --output result.txt

# Force OCR extraction
./extract scanned.pdf --ocr

# Use different language
./extract french_doc.pdf --language fra
```

### CLI Reference

```
Usage: extract [OPTIONS] FILE

Options:
  -o, --output PATH       Output file path (default: stdout)
  --ocr                   Force OCR extraction (default: auto-detect)
  --language TEXT         Tesseract language code (default: eng)
  --format [text|json]    Output format (default: text)
  --help                  Show this message and exit
```

**Examples:**

```bash
# JSON output with metadata
./extract document.pdf --format json > output.json

# Batch processing
for file in *.pdf; do
    ./extract "$file" --output "${file%.pdf}.txt"
done

# Pipeline integration
./extract document.pdf | grep "invoice" | wc -l
```

---

## Web UI API

### Starting the Server

```bash
streamlit run app.py
```

Access at: `http://localhost:8501`

<img src="./images/ui_screenshot.png" width="800" alt="DocuExtract Pro Interface">
*Figure 1: Web interface showing PDF preview, extraction controls, and settings*

### Features

| Feature | Description |
|---------|-------------|
| **File Upload** | Drag-and-drop or browse for files |
| **Live Preview** | Real-time PDF rendering with page navigation |
| **Settings** | OCR toggle, language selection, output format |
| **Custom Filename** | Edit output filename before download |
| **Diagnostics** | Performance metrics and optimization tips |

### Supported Formats

| Format | Extensions | Strategy |
|--------|-----------|----------|
| PDF | `.pdf` | Native text or OCR |
| Images | `.jpg`, `.jpeg`, `.png` | OCR |
| Word Docs | `.docx` | python-docx parser |
| Text Files | `.txt`, `.md` | Direct read |
| Structured Data | `.csv`, `.json`, `.xml` | Format-specific parsers |

---

## Language Codes Reference

### Supported OCR Languages

| Language | Code |
|----------|------|
| English | `eng` |
| French | `fra` |
| Spanish | `spa` |
| Arabic | `ara` |
| German | `deu` |
| Chinese (Simplified) | `chi_sim` |
| Japanese | `jpn` |

**Full List**: See [Tesseract Language Data](https://github.com/tesseract-ocr/tessdata)

---

## Integration Examples

### FastAPI Integration

```python
from fastapi import FastAPI, UploadFile
from text_extractor import extract_text

app = FastAPI()

@app.post("/extract")
async def extract_endpoint(file: UploadFile):
    content = await file.read()
    result = extract_text(content, filename=file.filename)
    return {
        "text": result.full_text,
        "pages": len(result.pages),
        "metadata": result.metadata
    }
```

### Django Integration

```python
from django.http import JsonResponse
from text_extractor import extract_text

def extract_view(request):
    uploaded_file = request.FILES['document']
    result = extract_text(uploaded_file.read(), filename=uploaded_file.name)
    
    return JsonResponse({
        "text": result.full_text,
        "page_count": result.metadata.get('page_count')
    })
```

### AWS Lambda Integration

```python
import json
import base64
from text_extractor import extract_text

def lambda_handler(event, context):
    # Decode base64 file from API Gateway
    file_bytes = base64.b64decode(event['body'])
    
    result = extract_text(file_bytes, filename="upload.pdf")
    
    return {
        'statusCode': 200,
        'body': json.dumps({'text': result.full_text})
    }
```

---

## Rate Limits & Performance

### Recommended Limits (Production)

| Metric | Recommended Limit | Reasoning |
|--------|------------------|-----------|
| File Size | 100 MB | Memory efficiency |
| Concurrent Requests | 10 per instance | CPU saturation |
| OCR Pages | 200 per request | Processing time |
| Timeout | 5 minutes | Large scanned PDFs |

### Performance Tuning

```python
# Reduce preview DPI for faster rendering
from app import PDF_PREVIEW_DPI
PDF_PREVIEW_DPI = 72  # Faster, lower quality

# Adjust thread count for OCR
import os
os.environ['OMP_THREAD_LIMIT'] = '8'  # More parallelism
```

---

## Troubleshooting

### Common Issues

**"Tesseract not found"**
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Docker
RUN apt-get update && apt-get install -y tesseract-ocr
```

**"Poppler not found"**
```bash
# Ubuntu/Debian
sudo apt-get install poppler-utils

# macOS
brew install poppler
```

**"Memory Error on large files"**
```python
# Use file path instead of bytes
result = extract_text("large.pdf")  # ✅ Streams from disk

# Avoid
with open("large.pdf", "rb") as f:
    data = f.read()  # ❌ Loads entire file into RAM
    result = extract_text(data)
```

---

## Changelog

### v2.1.0 (Current)
- ✅ Real-time UI updates (dynamic filename, language selector)
- ✅ Performance diagnostics panel
- ✅ 6.7x faster PDF preview rendering
- ✅ 87% memory reduction for large files
- ✅ Deprecation warning suppression

### v2.0.0
- ✅ Smart OCR fallback (auto-detection)
- ✅ Multi-threaded preview generation
- ✅ Strategy pattern refactor

### v1.0.0
- ✅ Initial release
- ✅ PDF, DOCX, image support
- ✅ Basic OCR with Tesseract

---

## Support & Contributing

- **Issues**: [GitHub Issues](https://github.com/iradukunda-fils/document-text-extractor/issues)
- **Discussions**: [GitHub Discussions](https://github.com/iradukunda-fils/document-text-extractor/discussions)
- **Newsletter**: [Engineering Insights](https://iradukundafils.substack.com/)
