from enum import Enum
import streamlit as st
import os
import json
import hashlib
import torch
from pathlib import Path
import pandas as pd


class SESSION_VARS(Enum):
    LOADED_MODELS = (1,)
    CUR_PDF_FILENAME = (2,)
    PROCESSED_DATA = (3,)
    NLP = (4,)
    EMBEDDING_MODEL_CPU = (5,)
    TOKENIZER = (6,)
    MODEL = (7,)
    EMBEDDINGS_FILENAME = (8,)
    CACHE_HASH = 9


def put_to_session(st: st, key: SESSION_VARS, value):
    """
    Update the Streamlit session state with the given key-value pair.

    Parameters:
    st_session_state (dict): The st.session_state object.
    key (str): The key to update or add in session state.
    value: The value to assign to the key.
    """
    if key not in st.session_state:
        st.session_state[key.name] = value


# Getter function
def get_from_session(st: st, key: SESSION_VARS, default=None):
    """
    Retrieve a value from Streamlit session state by key.

    Parameters:
    st_session_state (dict): The st.session_state object.
    key (str): The key to retrieve from session state.
    default: The default value to return if the key does not exist.

    Returns:
    The value associated with the key or the default value.
    """
    return st.session_state.get(key.name, default)


def print_session(st):
    print(st.session_state)


def get_cache_path(filename: str) -> Path:
    """Luo polku välimuistitiedostolle"""
    cache_dir = Path("memory/cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / filename


def save_processed_data(uploaded_file, embeddings_tensor, filtered_df, st):
    """Tallentaa prosessoidun datan välimuistiin.

    Args:
        uploaded_file: Ladattu PDF-tiedosto
        embeddings_tensor: Embeddings tensori
        filtered_df: DataFrame chunkeista
        st: Streamlit context
    """
    # Luo hash PDF:stä tunnistusta varten
    pdf_content = uploaded_file.read()
    uploaded_file.seek(0)  # Palauta osoitin alkuun
    file_hash = hashlib.md5(pdf_content).hexdigest()

    # Tallenna embeddings
    embeddings_file = get_cache_path(f"embeddings_{file_hash}.pt")
    torch.save(embeddings_tensor, embeddings_file)

    # Tallenna DataFrame
    df_file = get_cache_path(f"chunks_{file_hash}.json")
    filtered_df.to_json(df_file)

    # Tallenna metadata
    metadata = {
        "filename": uploaded_file.name,
        "hash": file_hash,
        "num_chunks": len(filtered_df),
        "embedding_dim": embeddings_tensor.shape[1],
    }
    metadata_file = get_cache_path(f"metadata_{file_hash}.json")
    with open(metadata_file, "w") as f:
        json.dump(metadata, f)

    # Tallenna tiedot sessioon käyttäen SESSION_VARS enumia
    put_to_session(st, SESSION_VARS.CACHE_HASH, file_hash)


def load_processed_data(uploaded_file, st):
    """Lataa prosessoidun datan välimuistista jos saatavilla."""
    # Tarkista onko tiedosto jo prosessoitu
    pdf_content = uploaded_file.read()
    uploaded_file.seek(0)
    file_hash = hashlib.md5(pdf_content).hexdigest()

    # Tarkista tiedostojen olemassaolo
    embeddings_file = get_cache_path(f"embeddings_{file_hash}.pt")
    df_file = get_cache_path(f"chunks_{file_hash}.json")
    metadata_file = get_cache_path(f"metadata_{file_hash}.json")

    if not all(f.exists() for f in [embeddings_file, df_file, metadata_file]):
        return None

    # Lataa data
    embeddings_tensor = torch.load(embeddings_file)
    filtered_df = pd.read_json(df_file)

    # Tallenna hash sessioon käyttäen SESSION_VARS enumia
    put_to_session(st, SESSION_VARS.CACHE_HASH, file_hash)

    return embeddings_tensor, filtered_df
