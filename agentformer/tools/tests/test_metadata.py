import logging
import sys
from agentformer.tools.rag_tool import RAGTool

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# Initialize RAG tool
print("Initializing RAG tool...")
rag = RAGTool()

# Get documents info
print("\nChecking indexed documents:")
docs = rag.get_documents_info()

if not docs:
    print("No documents found in the index")
else:
    for i, doc in enumerate(docs, 1):
        print(f"\n--- Document {i} ---")
        print(f"ID: {doc.get('id', 'No ID')}")
        print(f"Type: {doc.get('type', 'Unknown type')}")
        print(f"Chunks: {doc.get('chunks', 0)}")
        print(f"First chunk preview: {doc.get('first_chunk', 'No preview available')}")
        if "timestamp" in doc:
            from datetime import datetime

            timestamp = datetime.fromtimestamp(doc["timestamp"] / 1000)
            print(f"Indexed at: {timestamp}")
