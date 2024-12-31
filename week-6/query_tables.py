from llmsherpa.readers import LayoutPDFReader
from llama_index.llms.ollama import Ollama

# Initialize LLM
llm = Ollama(model="llama3", request_timeout=60.0)

# We read from the local NLM Ingestor or whichever PDF reading API
llmsherpa_api_url = "http://localhost:5010/api/parseDocument?renderFormat=all"
pdf_url = "https://abc.xyz/assets/91/b3/3f9213d14ce3ae27e1038e01a0e0/2024q1-alphabet-earnings-release-pdf.pdf"


def main():
    pdf_reader = LayoutPDFReader(llmsherpa_api_url)
    doc = pdf_reader.read_pdf(pdf_url)

    # Combine all sections into one HTML context
    full_context = ""
    for section in doc.sections():
        full_context += section.to_html(include_children=True, recurse=True)

    # Sample questions
    questions = [
        "What is Google's operating margin for 2024?",
        "What percentage of revenue is net income?",
        "Sum all segments revenue if available.",
    ]

    for q in questions:
        prompt = f"Read these tables below and answer:\nQuestion: {q}\n\nTable Data:\n{full_context}"
        response = llm.complete(prompt)
        print("----------------------------------------")
        print(f"Q: {q}")
        print(f"A: {response.text}")


if __name__ == "__main__":
    main()
