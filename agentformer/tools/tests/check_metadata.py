import json
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# Read metadata file
try:
    with open("faiss_metadata.json", "r") as f:
        metadata = json.load(f)

    print("\nMetadata file contents:")
    print(f"Total records: {len(metadata)}")

    # Display first few records
    for i, record in enumerate(metadata[:3], 1):
        print(f"\n--- Record {i} ---")
        if isinstance(record, dict):
            for key, value in record.items():
                if isinstance(value, dict):
                    print(f"{key}:")
                    for k, v in value.items():
                        print(f"  {k}: {v}")
                else:
                    print(f"{key}: {value}")
        else:
            print(f"Record format: {type(record)}")
            print(f"Content: {record}")

except FileNotFoundError:
    print("Metadata file not found")
except json.JSONDecodeError as e:
    print(f"Error decoding JSON: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
