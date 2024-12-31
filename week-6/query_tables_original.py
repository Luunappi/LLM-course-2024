from llmsherpa.readers import LayoutPDFReader
from IPython.core.display import display, HTML
from llama_index.llms.ollama import Ollama
from llama_index.core import VectorStoreIndex
from llama_index.core import Document, ServiceContext, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings

# Source: https://medium.com/@jitsins/query-complex-pdfs-in-natural-language-with-llmsherpa-ollama-llama3-8b-13b4782243de
# To install:
# 1. run https://stackoverflow.com/questions/52805115/certificate-verify-failed-unable-to-get-local-issuer-certificate
# 2. install and run ollama:
# ollama pull llama3
# ollama run llama3
# 3. Install docker and run:
# docker pull ghcr.io/nlmatics/nlm-ingestor:latest
# docker run -p 5010:5001 ghcr.io/nlmatics/nlm-ingestor:latest
# This will expose the api link “http://localhost:5010/api/parseDocument?renderFormat=all” for you to utilize in your code.

# Initialize LLm
llm = Ollama(model="llama3", request_timeout=60.0)

llmsherpa_api_url = "http://localhost:5010/api/parseDocument?renderFormat=all"
pdf_url = "https://abc.xyz/assets/91/b3/3f9213d14ce3ae27e1038e01a0e0/2024q1-alphabet-earnings-release-pdf.pdf"
pdf_reader = LayoutPDFReader(llmsherpa_api_url)

# Read PDF
doc = pdf_reader.read_pdf(pdf_url)

# Get data from the Section by Title
selected_section = None
for section in doc.sections():
    if 'Q1 2024 Financial Highlights' in section.title:
        selected_section = section
        break

# Convert the output in HTML format
context = selected_section.to_html(include_children=True, recurse=True)
question = "What was Google's operating margin for 2024"
resp = llm.complete(
    f"read this table and answer question: {question}:\n{context}")
print(resp.text)

question = "What % Net income is of the Revenues?"
resp = llm.complete(
    f"read this table and answer question: {question}:\n{context}")
print(resp.text)