from io import StringIO
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.layout import LAParams
from pdfminer.high_level import extract_text_to_fp
import logging

from .base import BaseExtractionStrategy, ExtractionResult
from ..exceptions import TextExtractionError

logger = logging.getLogger(__name__)

class PdfNativeStrategy(BaseExtractionStrategy):
    """Extracts text from PDFs using pdfminer.six (native extraction)."""

    def extract(self, file_stream, language: str = 'eng') -> ExtractionResult:
        logger.info("Starting PDF native extraction.")
        try:
            # pdfminer.six works best with file paths or seekable streams.
            # reset stream just in case
            file_stream.seek(0)
            
            # Iterate pages and extract text
            # Optimizing to single-pass extraction
             
             
            laparams = LAParams()

            rsrcmgr = PDFResourceManager()
            pages_text = []
            
            for page in PDFPage.get_pages(file_stream, check_extractable=True):
                 page_retstr = StringIO()
                 page_device = TextConverter(rsrcmgr, page_retstr, laparams=laparams)
                 page_interpreter = PDFPageInterpreter(rsrcmgr, page_device)
                 page_interpreter.process_page(page)
                 
                 text = page_retstr.getvalue()
                 pages_text.append(text)
                 
                 # clean up
                 page_device.close()
                 page_retstr.close()
            
            full_text = "\n\n".join(pages_text) # Reconstruct full text from pages to be consistent
            
            logger.info(f"PDF extraction successful. Extracted {len(pages_text)} pages.")
            return ExtractionResult(
                full_text=full_text,
                pages=pages_text,
                metadata={"method": "native_pdf", "page_count": len(pages_text)}
            )

        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            raise TextExtractionError(f"Failed to extract text from PDF: {str(e)}")
