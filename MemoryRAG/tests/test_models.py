"""Testi eri mallien käytölle"""

import asyncio
from memoryrag.model_manager import ModelManager, TaskType


async def test_models():
    # Alusta model manager
    model_mgr = ModelManager()

    # 1. Testaa dokumentin prosessointia (GPT-4o-mini)
    test_text = """
    Retrieval-Augmented Generation (RAG) combines neural text generation with retrieval 
    of external documents. This paper presents experiments showing that RAG models 
    achieve state-of-the-art results while being more precise and factual.
    """

    process_result = await model_mgr.run_task(
        TaskType.PROCESS, f"Jäsentele tämä teksti avainkohtiin:\n\n{test_text}"
    )
    print("\nProsessoinnin tulos:")
    print(process_result["result"])

    # 2. Testaa faktojen tarkistusta (o1-mini)
    fact_result = await model_mgr.run_task(
        TaskType.FACTCHECK,
        "Tarkista seuraavat väitteet tekstistä:\n"
        "1. RAG yhdistää tekstin generoinnin ja tiedonhaun\n"
        "2. RAG-mallit saavuttivat parhaat tulokset\n"
        "3. RAG-mallit ovat tarkempia ja faktapohjaisempia",
    )
    print("\nFaktojen tarkistus:")
    print(fact_result["result"])

    # 3. Testaa teknistä analyysiä (o1-mini)
    technical_result = await model_mgr.run_task(
        TaskType.TECHNICAL, "Analysoi RAG-mallin tekninen toteutus ja sen komponentit."
    )
    print("\nTekninen analyysi:")
    print(technical_result["result"])

    # 4. Testaa syvällistä analyysiä (o1-preview)
    analysis_result = await model_mgr.run_task(
        TaskType.ANALYSIS,
        "Analysoi RAG-mallin merkitys ja vaikutukset tekoälyn kehitykselle.",
    )
    print("\nSyvällinen analyysi:")
    print(analysis_result["result"])

    # Näytä käyttötilastot
    stats = model_mgr.get_usage_stats()
    print("\nKäyttötilastot:")
    print(f"Kokonaiskustannus: ${stats['total_cost']:.4f}")
    for task_type, tokens in stats["token_usage"].items():
        print(
            f"{task_type.value}: {tokens} tokenia, " f"${stats['costs'][task_type]:.4f}"
        )


if __name__ == "__main__":
    asyncio.run(test_models())
