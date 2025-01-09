import pytest
import os
from flask import Flask
import io
from agentformer.web_gui import app


def test_rag_e2e(client):
    # 1) Lataa pieni teksti (dummy)
    dummy_text = b"Testataan RAG-hakua. Toinen lause. Kolmas lause."

    res_upload = client.post(
        "/api/rag/upload", data={"file": (io.BytesIO(dummy_text), "dummy.txt")}
    )
    assert res_upload.status_code == 200, f"Upload failure: {res_upload.data}"

    # 2) Kysy query
    payload = {"query": "Mitä testataan?"}
    res_query = client.post("/api/rag/query", json=payload)
    assert res_query.status_code == 200, f"Query failure: {res_query.data}"

    json_data = res_query.get_json()
    assert "result" in json_data, "Ei 'result'-avainta"
    assert "response" in json_data["result"], "Ei 'response'-avainta resultissa"
    assert len(json_data["result"]["response"]) > 0, "Tyhjä vastaus RAG-haulta"
    print("RAG e2e -testi suoritettu onnistuneesti")
