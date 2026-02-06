from pdf2image import convert_from_bytes, convert_from_path, pdfinfo_from_path
import pytesseract
from PIL import Image
from .base import BaseExtractionStrategy, ExtractionResult
from ..exceptions import OcrError
import logging

logger = logging.getLogger(__name__)

class OcrStrategy(BaseExtractionStrategy):
    """Extracts text from PDFs/Images using OCR (Tesseract)."""

    def extract(self, file_stream, language: str = 'eng') -> ExtractionResult:
        logger.info(f"Starting OCR extraction with language={language}")
        try:
            # OCR Efficiency: Use temporary file to avoid loading full PDF into RAM for conversion
            import tempfile
            import os
            
            # Use .pdf as default suffix to help pdf2image, but internal content matters more
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                # Copy stream to temp file
                if hasattr(file_stream, 'seek'):
                    file_stream.seek(0)
                
                # Copy in chunks
                import shutil
                shutil.copyfileobj(file_stream, tmp_file)
                tmp_path = tmp_file.name
            
            try:
                # Use convert_from_path which is more memory efficient than bytes
                # We can also set thread_count
                
                logger.info(f"Processing via temp file: {tmp_path}")
                
                # Try treating as PDF first
                try:
                    info = pdfinfo_from_path(tmp_path)
                    total_pages = info["Pages"]
                    
                    pages_text = []
                    BATCH_SIZE = 5 # Process 5 pages at a time to keep RAM low
                    
                    for start_page in range(1, total_pages + 1, BATCH_SIZE):
                        end_page = min(start_page + BATCH_SIZE - 1, total_pages)
                        logger.info(f"Processing batch: Pages {start_page} to {end_page}")
                        
                        batch_images = convert_from_path(
                            tmp_path, 
                            first_page=start_page, 
                            last_page=end_page,
                            thread_count=2,
                            fmt='jpeg'
                        )
                        
                        # Parallelize OCR on the batch of images
                        from concurrent.futures import ThreadPoolExecutor, as_completed
                        
                        def process_image(img):
                            try:
                                txt = pytesseract.image_to_string(img, lang=language)
                                return txt
                            finally:
                                if hasattr(img, 'close'):
                                    img.close()

                        # Use max_workers=BATCH_SIZE or cpu_count
                        with ThreadPoolExecutor(max_workers=min(BATCH_SIZE, os.cpu_count() or 4)) as executor:
                             # We need to preserve order, so we map
                             results = list(executor.map(process_image, batch_images))
                             pages_text.extend(results)
                        
                        # Clear batch list
                        del batch_images
                
                except Exception as pdf_err:
                    logger.info(f"PDF processing failed ({pdf_err}), attempting fallback to standard image loader.")
                    # Fallback: Try opening as a single image using PIL
                    image = Image.open(tmp_path)
                    
                    # OCR the single image
                    text = pytesseract.image_to_string(image, lang=language)
                    pages_text = [text]
                    
                    if hasattr(image, 'close'):
                        image.close()
                
                full_text = "\n\n".join(pages_text)
                
            finally:
                # Clean up temp file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            
            logger.info(f"OCR extraction successful. Extracted {len(pages_text)} pages.")
            return ExtractionResult(
                full_text=full_text,
                pages=pages_text,
                metadata={"method": "ocr", "language": language, "page_count": len(pages_text)}
            )

        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            raise OcrError(f"OCR process failed: {str(e)}")
