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

# Test query
query = "What are the main concepts and findings discussed in the meta-prompting paper? Include specific details from the paper."
print(f"\nQuerying: {query}")

# Get results
result = rag.query(query)

print("\nResults:")
print(f"\nResponse: {result.get('response', 'No response available')}")
print(f"\nFound in documents: {result.get('found_in_docs', False)}")

if result.get("context"):
    print("\nRelevant context:")
    for i, ctx in enumerate(result["context"], 1):
        print(f"\n--- Context {i} ---")
        print(f"Content: {ctx.get('content', 'No content available')}")
        print(f"Source: {ctx.get('source', 'Unknown source')}")
        print(f"Relevance: {ctx.get('score', 'N/A')}")

if result.get("metadata"):
    print("\nMetadata:")
    for key, value in result["metadata"].items():
        print(f"{key}: {value}")
