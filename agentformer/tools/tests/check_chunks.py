import json
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

# Read metadata file
try:
    with open("faiss_metadata.json", "r") as f:
        metadata = json.load(f)

    print("\nLooking for chunks from Meta-prompting.pdf:")
    meta_prompting_chunks = [
        record
        for record in metadata
        if isinstance(record, dict)
        and record.get("meta", {}).get("filename") == "Meta-prompting.pdf"
    ]

    if not meta_prompting_chunks:
        print("No chunks found from Meta-prompting.pdf")
    else:
        print(f"\nFound {len(meta_prompting_chunks)} chunks:")
        for i, chunk in enumerate(meta_prompting_chunks, 1):
            print(f"\n--- Chunk {i} ---")
            print(f"ID: {chunk.get('id', 'No ID')}")
            print(
                f"Content: {chunk.get('content', 'No content')[:500]}..."
            )  # Show first 500 chars
            if "meta" in chunk:
                print("\nMetadata:")
                for key, value in chunk["meta"].items():
                    print(f"{key}: {value}")

except FileNotFoundError:
    print("Metadata file not found")
except json.JSONDecodeError as e:
    print(f"Error decoding JSON: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
    raise
