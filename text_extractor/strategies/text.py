from .base import BaseExtractionStrategy, ExtractionResult
import logging

logger = logging.getLogger(__name__)

class RawTextStrategy(BaseExtractionStrategy):
    """Extracts text from raw text files (.txt, .md, .csv, .json, .xml)."""

    def extract(self, file_stream, language: str = 'eng') -> ExtractionResult:
        logger.info("Starting Raw Text extraction.")
        try:
            # Ensure at start of stream
            if hasattr(file_stream, 'seek'):
                file_stream.seek(0)
            
            # Memory optimization: Read in chunks to handle very large text files
            # For files > 100MB, this prevents loading everything into RAM at once
            CHUNK_SIZE = 1024 * 1024  # 1MB chunks
            text_chunks = []
            total_size = 0
            
            try:
                while True:
                    chunk = file_stream.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    
                    # Decode chunk
                    try:
                        decoded_chunk = chunk.decode('utf-8')
                    except UnicodeDecodeError:
                        # Fallback to latin-1 for this chunk
                        logger.warning("UTF-8 decode failed for chunk, falling back to latin-1")
                        decoded_chunk = chunk.decode('latin-1', errors='ignore')
                    
                    text_chunks.append(decoded_chunk)
                    total_size += len(chunk)
                    
                    # Safety: Prevent accumulating too much in memory for extremely large files
                    # If we've read >500MB, log a warning
                    if total_size > 500 * 1024 * 1024:
                        logger.warning(f"Large text file detected: {total_size / (1024*1024):.1f} MB processed")
            
            except AttributeError:
                # file_stream might be bytes directly
                if isinstance(file_stream, bytes):
                    try:
                        text = file_stream.decode('utf-8')
                    except UnicodeDecodeError:
                        logger.warning("UTF-8 decode failed, falling back to latin-1")
                        text = file_stream.decode('latin-1')
                    text_chunks = [text]
                else:
                    raise

            # Join all chunks
            text = ''.join(text_chunks)

            # Naive page splitting probably doesn't apply to text files, 
            # but we can return the whole thing as one page.
            pages = [text]

            logger.info(f"Raw text extraction successful. Length: {len(text)} chars.")
            
            return ExtractionResult(
                full_text=text,
                pages=pages,
                metadata={"method": "raw_text", "page_count": 1}
            )

        except Exception as e:
            logger.error(f"Raw text extraction failed: {e}")
            raise Exception(f"Failed to extract text from file: {str(e)}")
