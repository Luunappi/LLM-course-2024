from pypdf import PdfReader
import pandas as pd
from llama_index.llms.ollama import Ollama
import requests
from io import BytesIO

# Initialize LLM
llm = Ollama(model="llama3", request_timeout=60.0)


def download_pdf(url):
    """Download PDF from URL"""
    response = requests.get(url)
    return BytesIO(response.content)


def extract_tables_from_pdf(pdf_file):
    """Extract text from PDF focusing on table-like content"""
    reader = PdfReader(pdf_file)
    tables_text = []

    for page in reader.pages:
        text = page.extract_text()
        # Simple heuristic: if line has multiple numbers, it might be tabular
        lines = text.split("\n")
        for line in lines:
            if sum(c.isdigit() for c in line) > 3:  # Line with multiple numbers
                tables_text.append(line)

    return "\n".join(tables_text)


def query_tables(question, context):
    """Query the tables using Ollama"""
    prompt = f"""Read this financial data and answer the question.
    
Question: {question}

Financial Data:
{context}

Answer the question based only on the provided financial data. 
If you can't find the exact information, say so.
"""
    response = llm.complete(prompt)
    return response.text


def main():
    # PDF URL (Alphabet's financial report)
    pdf_url = "https://abc.xyz/assets/91/b3/3f9213d14ce3ae27e1038e01a0e0/2024q1-alphabet-earnings-release-pdf.pdf"

    print("Downloading PDF...")
    pdf_file = download_pdf(pdf_url)

    print("Extracting tables...")
    tables_text = extract_tables_from_pdf(pdf_file)

    # Sample questions
    questions = [
        "What is Google's operating margin for 2024?",
        "What percentage of revenue is net income?",
        "What are the total revenues?",
    ]

    print("\nQuerying tables...\n")
    for question in questions:
        print(f"Q: {question}")
        answer = query_tables(question, tables_text)
        print(f"A: {answer}\n")
        print("-" * 80 + "\n")


if __name__ == "__main__":
    main()
