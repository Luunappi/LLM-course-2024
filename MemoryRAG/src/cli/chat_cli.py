import argparse
import asyncio
from pathlib import Path
from src.orchestrator import RAGOrchestrator


async def main():
    parser = argparse.ArgumentParser(description="MemoryRAG Chat CLI")
    parser.add_argument("--model", default="gpt-4o-mini", help="Käytettävä malli")
    args = parser.parse_args()

    # Luo orchestrator
    rag = await RAGOrchestrator.create(model_name=args.model)

    while True:
        query = input("Kysymys: ")
        if query.lower() in ["exit", "q"]:
            break
        response = await rag.process_query(query)
        print("Vastaus:", response)


if __name__ == "__main__":
    asyncio.run(main())
