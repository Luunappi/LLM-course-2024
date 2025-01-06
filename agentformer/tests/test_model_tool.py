from tools.model_tool import ModelTool


def test_model_tool_singleton():
    model_tool1 = ModelTool()
    model_tool2 = ModelTool()
    assert model_tool1 is model_tool2  # Sama instanssi


def test_get_model_for_task():
    model_tool = ModelTool()
    assert model_tool.get_model_for_task("rag_retrieval") == "o1-mini"
    assert model_tool.get_model_for_task("chat") == "gpt-4o-mini"


def test_tool_specific_configs():
    model_tool = ModelTool()

    # Tarkista RAG-työkalun omat konfiguraatiot
    rag_config = model_tool.get_model_config("o1-mini", tool_name="rag_tool")
    assert rag_config["temperature"] == 0.1  # RAG-spesifi asetus

    # Tarkista että perusasetukset säilyvät muille työkaluille
    default_config = model_tool.get_model_config("o1-mini")
    assert default_config["temperature"] == 0.7  # Alkuperäinen asetus

    # Testaa konfiguraation päivitystä
    model_tool.update_tool_config("rag_tool", "o1-mini", {"max_tokens": 6000})
    updated_config = model_tool.get_model_config("o1-mini", tool_name="rag_tool")
    assert updated_config["max_tokens"] == 6000
