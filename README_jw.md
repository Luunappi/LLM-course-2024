# LLM Course 2024

This repository contains implementations and experiments from the LLM course, organized by week.

## Repository Structure

```
LLM-course-2024/
├── models/                    # Shared model files and logs
│   ├── finetuned/            # Finetuned model files
│   ├── logs/                 # Training and test logs
│   └── checkpoints/          # Training checkpoints
├── week-2/                   # In-context learning & prompting
├── week-4/                   # Model fine-tuning experiments
└── week-5/                   # RAG implementations
```

## Week 2: In-Context Learning & Prompting

Experiments with different prompting techniques and in-context learning:

* **Gemini Chatbot** (`gemini-chatbot/`)
  - Academic assessment assistant
  - System prompts in EN/FI
  - Structured evaluation matrix

* **In-Context Learning** (`in-context-learning/`)
  - Research paper analysis
  - HTML to Markdown conversion
  - Automated paper summaries

* **Prompting Examples** (`prompting-notebook/`)
  - Different prompting techniques
  - Model comparison tests
  - Performance evaluation

See [week-2/README.md](week-2/README.md) for details.

## Week 4: Model Fine-tuning

Fine-tuning experiments with Mistral-7B using LoRA:

* **DPO Fine-tuning** (`dpo_finetuning.py`)
  - Base: Mistral-7B-Instruct-v0.3
  - Dataset: Anthropic's HH-RLHF
  - LoRA adapters for efficiency
  - MPS optimization for M-series Macs

* **Model Testing** (`compare_models.py`)
  - Base vs Finetuned comparison
  - Gemini as evaluator
  - 5 different test prompts
  - Detailed performance logs

* **Results**
  - Finetuned model better in 4/5 tests
  - Improved: Analysis depth & coherence
  - Base better: Simple explanations
  - Full results in `models/logs/`

See [week-4/README.md](week-4/README.md) for implementation details.

## Week 5: Retrieval-Augmented Generation (RAG)

RAG implementations and experiments:

* **Simple Local RAG** (`00_simple_local_rag.ipynb`)
  - Local document processing
  - Vector embeddings
  - Similarity search
  - Context-aware responses

See [week-5/README.md](week-5/README.md) for details.

## Setup & Requirements

1. **Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. **Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **API Keys** (in `.env`)
   ```
   HUGGINGFACE_TOKEN=xxx
   GEMINI_API_KEY=xxx
   ```

## Hardware Requirements

* Python 3.11+
* M-series Mac (optimized) or GPU
* 16GB+ RAM recommended

## References

* [Course Materials](https://github.com/Helsinki-NLP/LLM-course-2024)
* [Hugging Face Documentation](https://huggingface.co/docs)
* [LoRA Paper](https://arxiv.org/abs/2106.09685)
* [Anthropic HH-RLHF Dataset](https://huggingface.co/datasets/Anthropic/hh-rlhf)
