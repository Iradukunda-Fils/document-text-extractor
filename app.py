import streamlit as st
import os
import tempfile
import base64
import time
import warnings
from io import BytesIO
from typing import Tuple
from contextlib import contextmanager

# Import internal package
from text_extractor import TextExtractor

# ==============================================================================
# CONFIG & CONSTANTS
# ==============================================================================

PAGE_CONFIG = {
    "page_title": "DocuExtract Pro",
    "page_icon": "📑",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# Supported file types
SUPPORTED_EXTENSIONS = {
    "pdf": "application/pdf",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png", 
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "txt": "text/plain",
    "md": "text/markdown"
}

# Limits
MAX_PDF_PREVIEW_SIZE_MB = 100.0
PDF_PREVIEW_DPI = 100  # Optimized for performance

# Links
AUTHOR_LINK = "https://github.com/iradukunda-fils"
NEWSLETTER_LINK = "https://iradukundafils.substack.com/"

# ==============================================================================
# STYLING (CSS)
# ==============================================================================

CUSTOM_CSS = """
<style>
    /* Global Styles */
    .main {
        background-color: #f8f9fa;
    }
    
    /* Typography */
    h1, h2, h3 {
        color: #1a1f36;
        font-family: 'Inter', sans-serif;
    }
    
    /* Buttons */
    .stDownloadButton button, .stButton button {
        width: 100%;
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    /* Primary Action Button */
    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #FF6719 0%, #ff8c42 100%);
        border: none;
        box-shadow: 0 4px 14px rgba(255, 103, 25, 0.3);
    }
    .stButton button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(255, 103, 25, 0.4);
    }
    
    /* PDF Viewer Container */
    .pdf-viewer-container {
        max-height: 600px;
        overflow-y: auto;
        overflow-x: hidden;
        border: 1px solid #e1e4e8;
        border-radius: 12px;
        padding: 24px;
        background-color: #f3f4f6;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Scrollbar Styling */
    .pdf-viewer-container::-webkit-scrollbar {
        width: 10px;
    }
    .pdf-viewer-container::-webkit-scrollbar-track {
        background: #f1f3f4;
        border-radius: 10px;
    }
    .pdf-viewer-container::-webkit-scrollbar-thumb {
        background: #bdc1c6;
        border-radius: 10px;
        border: 2px solid #f1f3f4;
    }
    .pdf-viewer-container::-webkit-scrollbar-thumb:hover {
        background: #9aa0a6;
    }
    
    /* PDF Page Card */
    .page-wrapper {
        margin-bottom: 24px;
        background: white;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06);
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    
    .page-wrapper:last-child {
        margin-bottom: 0;
    }
    
    /* Page Label */
    .page-label {
        align-self: flex-start;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #5f6368;
        font-weight: 700;
        margin-bottom: 12px;
        padding: 4px 8px;
        background: #f1f3f4;
        border-radius: 4px;
    }
    
    /* Hide Streamlit Boilerplate */
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
</style>
"""

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

@contextmanager
def performance_timer(label: str, metrics: dict):
    """Context manager to measure execution time."""
    start = time.perf_counter()
    yield
    end = time.perf_counter()
    metrics[label] = f"{end - start:.2f}s"

@st.cache_data(show_spinner=False)
def _get_pdf_images(file_bytes: bytes, dpi: int = 100) -> list:
    """
    Convert PDF bytes to images with caching and parallel processing.
    """
    from pdf2image import convert_from_bytes
    
    cpu_count = os.cpu_count() or 2
    threads = min(4, cpu_count)
    
    images = convert_from_bytes(
        file_bytes, 
        dpi=dpi,
        fmt='jpeg',
        thread_count=threads,
        use_pdftocairo=True
    )
    return images

def setup_app():
    """Initialize page config and styles."""
    st.set_page_config(**PAGE_CONFIG)
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    if 'text' not in st.session_state:
        st.session_state['text'] = ""
    if 'filename' not in st.session_state:
        st.session_state['filename'] = "document"

def render_sidebar() -> Tuple[str, bool, str, str]:
    """Render the application sidebar and return settings."""
    with st.sidebar:
        st.image("https://cdn.simpleicons.org/substack/ff6719", width=50)
        st.title("DocuExtract Pro")
        st.caption("v2.1 | Distributed Engine")
        
        st.divider()
        
        st.subheader("⚙️ Settings")
        output_format = st.radio(
            "Output Format",
            ('One text file (.txt)', 'Text per page (ZIP)'),
            help="Choose how you want to save your results."
        )
        
        enable_ocr = st.toggle(
            'High-Accuracy OCR', 
            help="Enable for scanned PDFs or images. Uses Tesseract engine."
        )
        
        # Language selector - dynamically visible when OCR is enabled
        lang = 'eng'  # Default
        if enable_ocr:
            languages = {
                'English': 'eng', 
                'French': 'fra', 
                'Arabic': 'ara', 
                'Spanish': 'spa'
            }
            selected_lang = st.selectbox(
                'OCR Language',
                list(languages.keys()),
                help="Language for OCR text recognition"
            )
            lang = languages[selected_lang]
        
        # Output filename editor - uses uploaded filename from session state
        default_name = st.session_state.get('filename', 'document')
        base_name = os.path.splitext(default_name)[0]
        
        # Use unique key based on filename to force refresh when file changes
        output_filename = st.text_input(
            "Output Filename (without extension)",
            value=base_name,
            help="Customize the name of the downloaded file",
            key=f"output_filename_{base_name}"  # Dynamic key forces update
        )
        
        st.divider()
        
        st.markdown("### 👨‍💻 Developed by")
        st.markdown(f"[Iradukunda Fils]({AUTHOR_LINK})")
        
        st.markdown(f"""
            <a href="{NEWSLETTER_LINK}" target="_blank">
                <img src="https://img.shields.io/badge/Newsletter-Subscribe-FF6719?style=for-the-badge&logo=substack&logoColor=white" width="100%">
            </a>
            <p style="font-size: 0.8rem; margin-top: 0.5rem; color: #666;">📬 Join for engineering insights.</p>
        """, unsafe_allow_html=True)
        
    return output_format, enable_ocr, output_filename, lang

    
def render_pdf_viewer(uploaded_file, file_size_mb: float) -> int:
    """Render a professional scrollable PDF viewer. Returns page count."""
    if file_size_mb > MAX_PDF_PREVIEW_SIZE_MB:
        st.warning(f"⚠️ PDF is too large ({file_size_mb:.1f} MB) for live preview. Extraction will still work.")
        return 1

    try:
        from pdf2image import pdfinfo_from_path
        
        pdf_data = uploaded_file.read()
        uploaded_file.seek(0)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(pdf_data)
            tmp_path = tmp_file.name
        
        try:
            info = pdfinfo_from_path(tmp_path)
            total_pages = info.get("Pages", 1)
            
            st.caption(f"📄 Document: {uploaded_file.name} • {total_pages} Pages • {file_size_mb:.1f} MB")
            
            with st.spinner(f"Rendering preview ({total_pages} pages)..."):
                images = _get_pdf_images(pdf_data, dpi=PDF_PREVIEW_DPI)
                _render_scrollable_images(images)
            
            return total_pages
                
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except ImportError:
        st.error("❌ `pdf2image` or `poppler` is missing. Please check server configuration.")
        return 1
    except Exception as e:
        st.warning(f"⚠️ Preview unavailable: {str(e)}")
        st.info("You can still proceed with extraction.")
        return 1

def _render_scrollable_images(images: list):
    """Internal helper to render list of images in custom scroll container."""
    pages_html = '<div class="pdf-viewer-container">'
    
    for idx, img in enumerate(images, 1):
        buffered = BytesIO()
        img.save(buffered, format="JPEG", quality=85)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        # Properly escape the HTML and ensure no line breaks in img tag
        pages_html += f'<div class="page-wrapper"><div class="page-label">Page {idx}</div>'
        pages_html += f'<img src="data:image/jpeg;base64,{img_str}" style="width: 100%; border-radius: 4px; box-shadow: 0 0 4px rgba(0,0,0,0.1);" alt="Page {idx}">'
        pages_html += '</div>'
        
    pages_html += '</div>'
    st.markdown(pages_html, unsafe_allow_html=True)

def render_results_column(text: str, output_format: str, output_filename: str = "document"):
    """Render the results column."""
    st.success("✅ Extraction Complete!")
    
    file_ext = "txt" if output_format.startswith('One') else "zip"
    mime = "text/plain" if file_ext == "txt" else "application/zip"
    
    st.download_button(
        label=f"📥 Download Results ({file_ext.upper()})",
        data=text.encode('utf-8'),
        file_name=f"{output_filename}_extracted.{file_ext}",
        mime=mime,
        type="primary"
    )
    
    st.text_area("Extracted Text", text, height=500)

def render_diagnostics(metrics: dict, file_size_mb: float, total_pages: int, ocr_enabled: bool):
    """Display performance insights based on execution metrics."""
    st.divider()
    with st.expander("⚡ Performance Stats & Diagnostics", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Execution Times**")
            if not metrics:
                st.write("No metrics available yet.")
            for label, duration in metrics.items():
                st.write(f"- {label}: `{duration}`")
        
        with col2:
            st.markdown("**Context**")
            st.write(f"- File Size: `{file_size_mb:.2f} MB`")
            st.write(f"- Pages: `{total_pages}`")
            st.write(f"- OCR Mode: `{'Enabled' if ocr_enabled else 'Auto/Disabled'}`")

        if ocr_enabled:
            st.info("💡 **Note**: OCR is enabled. This significantly increases processing time (approx. 1-2s per page). Disable it for native PDFs to extract text instantly.")
        elif total_pages > 20:
             st.info("💡 **Tip**: For large documents, preview generation is cached. The second time you view this file, it will load instantly.")

# ==============================================================================
# MAIN
# ==============================================================================

def main():
    setup_app()
    output_format, enable_ocr, output_filename, lang = render_sidebar()
    
    # Header
    st.markdown("## 📑 Document Text Extractor")
    st.markdown("Convert PDF, Images, and Docs to clean, structured text.")
    
    # Top Section: File Upload
    uploaded_file = st.file_uploader(
        "Upload Document", 
        type=list(SUPPORTED_EXTENSIONS.keys()),
        help="Supported: PDF, JPG, PNG, DOCX, TXT"
    )
    
    st.divider()
    
    # Bottom Section: Two Columns (Preview | Results)
    col1, col2 = st.columns([1, 1], gap="large")
    
    metrics = {}
    total_pages = 1
    
    with col1:
        st.markdown("### 🔍 Preview")
        
        if uploaded_file:
            file_mb = uploaded_file.size / (1024 * 1024)
            is_pdf = uploaded_file.type == "application/pdf"
            
            # Update filename in session state immediately (realtime sync)
            if st.session_state.get('filename') != uploaded_file.name:
                st.session_state['filename'] = uploaded_file.name
            
            # Show Preview
            if is_pdf:
                with performance_timer("Preview Generation", metrics):
                    total_pages = render_pdf_viewer(uploaded_file, file_mb)
            elif uploaded_file.type.startswith('image'):
                # Show file info for images too
                st.caption(f"🖼️ Image: {uploaded_file.name} • {file_mb:.1f} MB")
                with st.spinner("Loading image..."):
                    st.image(uploaded_file, caption="Image Preview", use_container_width=True)
            else:
                # Show file info for other types
                st.caption(f"📄 File: {uploaded_file.name} • {file_mb:.1f} MB")
                st.info("📄 Text file uploaded. Preview available after extraction.")
            
            uploaded_file.seek(0)
        else:
            st.info("👈 Upload a file to see the live preview here.")
    
    with col2:
        st.markdown("### 📝 Extraction")
        
        if uploaded_file:
            # Extract Action
            if st.button("🚀 Run Extraction", type="primary", use_container_width=True):
                try:
                    extractor = TextExtractor()
                    
                    with st.spinner("Processing document..."):
                        with performance_timer("Text Extraction", metrics):
                            suffix = f".{uploaded_file.name.split('.')[-1]}"
                            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                                tmp_file.write(uploaded_file.getbuffer())
                                tmp_path = tmp_file.name
                                
                            # Fixed API call: use ocr_mode and language (singular)
                            results = extractor.extract(
                                tmp_path, 
                                ocr_mode='force' if enable_ocr else 'auto',
                                language=lang
                            )
                            
                            if os.path.exists(tmp_path):
                                os.unlink(tmp_path)
                            
                        st.session_state['text'] = results.full_text
                        st.session_state['filename'] = uploaded_file.name
                    
                    render_diagnostics(metrics, file_mb, total_pages, enable_ocr)
                        
                except Exception as e:
                    st.error(f"❌ Extraction failed: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
            
            # Show results if available
            if st.session_state['text']:
                st.divider()
                render_results_column(st.session_state['text'], output_format, output_filename)
        else:
            st.info("👈 Upload a file to extract text.")
            st.markdown("""
                ### Why use this tool?
                - **Privacy First**: Files are processed locally/in-memory.
                - **Smart OCR**: Automatically detects scanned pages.
                - **Format Retention**: Tries to keep layout structure.
            """)

if __name__ == "__main__":
    main()
