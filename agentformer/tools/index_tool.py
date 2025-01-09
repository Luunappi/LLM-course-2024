import logging
import sys
from typing import Optional
from agentformer.tools.rag_tool import RAGTool
from agentformer.memory.backends.faiss_backend import FaissMemoryBackend

logger = logging.getLogger(__name__)


def index_file(filename: str) -> bool:
    """Index a single file from the saved_files directory."""
    try:
        # Configure logging to only show INFO and above
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(message)s")  # Simplified format
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)  # Only show INFO and above

        logger.info(f"Starting indexing: {filename}")

        # Initialize tools
        rag = RAGTool()
        backend = FaissMemoryBackend()

        # Reset metadata if corrupted
        if not hasattr(backend, "metadata") or backend.metadata is None:
            backend.metadata = []

        # Load file
        content = backend.load_file(filename)
        if not content:
            logger.error(f"Could not load content for {filename}")
            return False

        # Index document
        rag.add_document(
            document=content,
            doc_id=f"saved-{filename}",
            file_type="pdf" if filename.lower().endswith(".pdf") else "text",
            extra_meta={"filename": filename},
        )

        logger.info(f"Successfully indexed: {filename}")
        return True

    except Exception as e:
        logger.error(f"Error indexing file: {str(e)}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        success = index_file(filename)
        sys.exit(0 if success else 1)
    else:
        print("Please provide a filename as argument")
        sys.exit(1)
