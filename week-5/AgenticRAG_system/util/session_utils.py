from enum import Enum
import streamlit as st


class SESSION_VARS(Enum):
    """
    Enum luokka session muuttujien nimille.
    """

    NLP = "nlp"
    EMBEDDINGS = "embeddings"
    MODEL = "model"
    TOKENIZER = "tokenizer"


def get_from_session(st_session, var: SESSION_VARS):
    """
    Hakee muuttujan Streamlit-sessiosta.

    Args:
        st_session: Streamlit session_state objekti
        var: SESSION_VARS enum arvo

    Returns:
        Muuttujan arvo tai None jos ei löydy
    """
    return st_session.session_state.get(var.value)


def put_to_session(st_session, var: SESSION_VARS, value):
    """
    Tallentaa muuttujan Streamlit-sessioon.

    Args:
        st_session: Streamlit session_state objekti
        var: SESSION_VARS enum arvo
        value: Tallennettava arvo
    """
    st_session.session_state[var.value] = value
