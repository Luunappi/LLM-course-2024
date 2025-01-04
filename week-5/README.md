# Retrieval Augmented Generation (RAG)
This week is focusing on practical introduction of a RAG concept: Retrieval Augmented Generation.

There are two main building blocks that you will work with:
1. [Jupyter notebook](00_simple_local_rag.ipynb)
2. [Streamlit UI](RAG-GUI.py), which implements the same functionality in a form of an interactive UI

This notebook and code were tested with Python 3.12

# Week's tasks
You are expected to submit one task (if you like, by all means do and submit more!) from the list below.
We will discuss these tasks in class, and you can ask your questions to better understand each of them.

1. Task 1: Change the notebook or streamlit UI to support pdf documents in a language other than English: Finnish, Swedish, German etc. Things to consider:
   * Would the same embedding and LLM work for Finnish?
   * What about extracting sentences and chunking: is there any change in terms of token length / chunk size?
   * Can you assess the final quality?
2. Task 2: Research and implement alternative algorithm for chunking. For example, you can take a look at semantic chunking technique. Things to consider:
   * Does this chunker apply to any language?
   * Can you assess the quality of chunker on a handful of pages in your pdf document?
   * What is the impact on quality of the overall RAG system pipeline?
3. Task 3(*):
   * Research agentic RAG. Pick a task, like checking stock price of a company, detect the respectful intent and pull the price.
   * You can also come up with your own task / tool to use and implement that instead. 
4. Task 4(**):
   * Research GraphRAG: https://www.youtube.com/watch?v=knDDGYHnnSI
   * Take a look at Neo4j demo: https://neo4j.com/labs/genai-ecosystem/rag-demo/
   * Come up with a KG for your domain of choice (it can be financial documents or research papers from arxiv)

# Jupyter notebook setup
Create virtual environment in this directory.

Install packages:
```
pip install -U "huggingface_hub[cli]"
pip install -U torch
pip install stqdm
pip install tqdm
pip install -U sentence-transformers
pip install PyMuPDF
```
# Streamlit UI setup
Download models from Hugging Face:
```
huggingface-cli download sentence-transformers/all-mpnet-base-v2
huggingface-cli download google/gemma-2b-it
```

Download spacy's English model:
```
python -m spacy download en_core_web_sm
```

# PDF RAG UI
The PDF RAG Demo is a UI application, implemented using streamlit. The core code of RAG is otherwise the same as in the
jupyter notebook.

Here is how the UI looks like during the Preprocessing phase, triggered by uploading a pdf file.
![PDF RAG Demo](img/pdf_rag_ui_preprocessing.png)

Here are two examples of answers we get from the vanilla LLM (Gemma) and from RAG-enhanced LLM (enhancement or
grounding is done using the original RAG paper: "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks".

![vanilla LLM answer](img/vanilla_llm_summarize_paper.png)

![RAG LLM answer](img/rag_summarize_paper.png)

Comparing these two outputs, we can see that RAG-enhanced LLM produces a much more nuanced answer about 
the key contributions of the paper, while vanilla LLM talks about more generic concepts.