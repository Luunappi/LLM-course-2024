# Let's run Gemma on CPU, if GPU is not available
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import time


def load_tokenizer(model_name: str = "google/gemma-2b-it"):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    return tokenizer


def tokenize_with_chat(text: str, tokenizer) -> torch.Tensor:
    """Tokenize chat input for Gemma model.

    Args:
        text: Input text
        tokenizer: Tokenizer object

    Returns:
        torch.Tensor: Tokenized input
    """
    # Gemma ei tue system roolia, joten käytetään vain user viestiä
    prompt = f"<start_of_turn>user\n{text}<end_of_turn>\n<start_of_turn>model"
    return tokenizer(prompt, return_tensors="pt")["input_ids"]


def load_gemma(mobel_name: str = "google/gemma-2b-it"):
    llm_model = AutoModelForCausalLM.from_pretrained(
        mobel_name, torch_dtype=torch.bfloat16
    )
    return llm_model


def generate_answer(input_ids, model, tokenizer, max_new_tokens=512):
    """Generoi vastaus ja palauta myös token määrät"""
    start_time = time.time()

    # Laske input tokenit
    input_tokens = len(input_ids[0])

    # Generoi vastaus
    outputs = model.generate(
        input_ids,
        max_new_tokens=max_new_tokens,
        do_sample=True,
        temperature=0.7,
        top_p=0.95,
    )

    # Laske output tokenit
    output_tokens = len(outputs[0]) - input_tokens

    # Dekoodaa vastaus
    answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
    gen_time = time.time() - start_time

    return (
        answer,
        gen_time,
        {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
        },
    )


# rag
def rag_prompt_formatter(tokenizer, query: str, context_items: list[dict]) -> str:
    """
    Augments query with text-based context from context_items.
    """
    # Join context items into one dotted paragraph
    context = "- " + "\n- ".join([item["sentence_chunk"] for item in context_items])

    # Create a base prompt with examples to help the model
    # Note: this is very customizable, I've chosen to use 3 examples of the answer style we'd like.
    # We could also write this in a txt file and import it in if we wanted.
    base_prompt = """Based on the following context items, please answer the query.
Give yourself room to think by extracting relevant passages from the context before answering the query.
Don't return the thinking, only return the answer.
Make sure your answers are as explanatory as possible.
Use the following examples as reference for the ideal answer style.
\nExample 1:
Query: Who is Max Irwin?
Answer: Max is the CEO of Max.io, formerly he worked at OpenSource Connections delivering search improvements and running trainings.
\nExample 2:
Query: What is SolrCloud?
Answer: SolrCloud is a distributed search engine designed for improving the performance of full-text search over large datasets. It is built on top of Apache Solr, a powerful open-source search engine that provides functionality such as full-text search, faceted search, and more.
\nExample 3:
Query: What is a knowledge graph?
Answer: An instantiation of an Ontology that also contains the things that are related.
\nNow use the following context items to answer the user query:
{context}
\nRelevant passages: <extract relevant passages from the context here>
User query: {query}
Answer:"""

    # Update base prompt with context items and query
    base_prompt = base_prompt.format(context=context, query=query)

    # Create prompt template for instruction-tuned model
    dialogue_template = [{"role": "user", "content": base_prompt}]

    # Apply the chat template
    prompt = tokenizer.apply_chat_template(
        conversation=dialogue_template, tokenize=False, add_generation_prompt=True
    )
    return prompt


def tokenize_with_rag_prompt(
    query: str, context_items: list, tokenizer
) -> torch.Tensor:
    """Tokenize RAG prompt for Gemma model."""
    # Muodosta konteksti
    context_texts = [item["sentence_chunk"] for item in context_items]
    context = "\n\nContext:\n• " + "\n• ".join(context_texts)

    # Yksinkertaistettu prompt
    prompt = (
        f"<start_of_turn>user\n"
        f"Answer the question based on the following context. "
        f"If the context doesn't contain relevant information, say so clearly.\n"
        f"{context}\n\n"
        f"Question: {query}\n"
        f"<end_of_turn>\n"
        f"<start_of_turn>model\n"
        f"Based on the provided context, I will answer your question about {query}:"
    )

    return tokenizer(prompt, return_tensors="pt")["input_ids"]
