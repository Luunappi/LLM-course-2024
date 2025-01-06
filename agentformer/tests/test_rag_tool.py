from tools.rag_tool import RAGTool
from tools.model_tool import ModelTool


def test_rag_tool_uses_correct_models():
    rag_tool = RAGTool()
    model_tool = ModelTool()

    # Tarkista että RAG käyttää oikeita malleja
    test_doc = "Test document content"
    rag_tool.add_document(test_doc)

    result = rag_tool.query("test")

    assert result["models_used"] == ["o1-mini (retrieval)", "gpt-4o (generation)"]
    assert result["found_in_docs"] == True
