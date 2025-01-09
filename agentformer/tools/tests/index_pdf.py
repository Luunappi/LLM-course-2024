import logging
import sys
from agentformer.tools.rag_tool import RAGTool
from agentformer.memory.backends.faiss_backend import FaissMemoryBackend
import os

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def index_pdf(filename: str):
    """Index a PDF file with detailed logging."""
    try:
        logger.info(f"Starting indexing process for {filename}")

        # Initialize tools
        rag = RAGTool()
        backend = FaissMemoryBackend()

        # Check if file exists
        file_path = os.path.join("agentformer/saved_files", filename)
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False

        logger.info(f"Loading file: {file_path}")
        file_content = backend.load_file(filename)

        if not file_content:
            logger.error("Failed to load file content")
            return False

        logger.info(f"File loaded successfully, size: {len(file_content)} bytes")
        logger.info("Adding document to index...")

        # Add document with metadata
        rag.add_document(
            document=file_content,
            doc_id=f"saved-{filename}",
            file_type="pdf",
            extra_meta={"filename": filename},
        )

        logger.info("Document indexed successfully")

        # Verify indexing
        logger.info("Verifying index...")
        if backend.index:
            logger.info(f"FAISS index contains {backend.index.ntotal} vectors")
        else:
            logger.warning("FAISS index not initialized")

        if backend.metadata:
            logger.info(f"Metadata contains {len(backend.metadata)} records")
        else:
            logger.warning("No metadata records found")

        return True

    except Exception as e:
        logger.error(f"Error during indexing: {str(e)}", exc_info=True)
        return False


if __name__ == "__main__":
    success = index_pdf("Meta-prompting.pdf")
    sys.exit(0 if success else 1)
