"""Text Tool - Tekstinkäsittelytyökalu

Tämä työkalu tarjoaa tekstinkäsittelyyn liittyviä toimintoja:
1. Tekstin generointi
2. Tekstin muokkaus
3. Tekstin analyysi
4. Tekstin validointi
"""

import logging
from typing import Dict, Any, Optional
from .model_tool import ModelTool

logger = logging.getLogger(__name__)


class TextTool:
    """Hoitaa tekstipohjaisten vastausten tuottamisen"""

    def __init__(self):
        self.model_tool = ModelTool()

    def process_direct_query(
        self, query: str, model_name: str = "gpt-4o"
    ) -> Dict[str, Any]:
        """Käsittele suora kysely ilman RAG-kontekstia"""
        try:
            response = self.model_tool.query(
                model_name,
                system_prompt="""Olet avulias tekoälyassistentti. 
                Vastaa kysymykseen suoraan käyttäen tietämystäsi.
                Ole aina avulias ja informatiivinen.
                Vastaa aina suomeksi.""",
                user_message=query,
            )

            return {
                "response": response,
                "source": "language_model",
                "model": model_name,
                "found_in_docs": False,
            }

        except Exception as e:
            logger.error(f"Error in direct query processing: {str(e)}")
            return {"error": str(e), "source": "error", "model": model_name}

    def process_rag_query(
        self, query: str, context: str, model_name: str = "gpt-4o-mini"
    ) -> Dict[str, Any]:
        """Käsittele kysely RAG-kontekstin kanssa"""
        try:
            response = self.model_tool.query(
                messages=[
                    {
                        "role": "system",
                        "content": """Olet avulias tekoälyassistentti. Tehtäväsi on vastata kysymyksiin annetun kontekstin perusteella.

TÄRKEÄT OHJEET VASTAUKSEN MUOTOILUUN:

1. Jos vastaus löytyy kontekstista:
   - Aloita vastaus kertomalla mistä dokumentista ja sivulta tieto löytyy
   - Näytä suorat lainaukset kontekstista muodossa:
     ```
     [Lainaus dokumentista X, sivu Y]
     "Tähän lainaus..."
     ```
   - Päätä vastaus merkinnällä "Lähde: RAG"

2. Jos vastausta ei löydy kontekstista:
   - Vastaa yleistietosi perusteella
   - Päätä vastaus merkinnällä "Lähde: LLM (perustuu kielimallin yleistietoon)"

HUOM: Jokaisen vastauksen TÄYTYY päättyä joko "Lähde: RAG" tai "Lähde: LLM" merkintään!""",
                    },
                    {
                        "role": "user",
                        "content": f"""Kysymys: {query}

Annettu konteksti:
{context}

Muista:
1. Mainitse dokumentti ja sivunumero
2. Näytä suorat lainaukset
3. Merkitse lähde (RAG/LLM)""",
                    },
                ],
                model_name=model_name,
            )

            # Tarkista löytyikö vastaus dokumenteista
            found_in_docs = "Lähde: RAG" in response

            # Jos lähdemerkintä puuttuu, lisää se
            if "Lähde:" not in response:
                response += "\n\nLähde: LLM (perustuu kielimallin yleistietoon)"
                found_in_docs = False

            return {
                "response": response,
                "found_in_docs": found_in_docs,
                "source": "rag" if found_in_docs else "llm",
                "model": model_name,
                "context_used": context if found_in_docs else None,
                "chunks_used": context.split("===") if found_in_docs else None,
            }

        except Exception as e:
            logger.error(f"Error in RAG query processing: {str(e)}")
            return str(e)

    def summarize_text(
        self, text: str, max_length: Optional[int] = None, model_name: str = "o1-mini"
    ) -> str:
        """Tiivistä teksti haluttuun pituuteen"""
        try:
            length_instruction = ""
            if max_length:
                length_instruction = f" Tiivistä noin {max_length} merkkiin."

            response = self.model_tool.query(
                model_name,
                system_prompt="""Olet taitava tekstin tiivistäjä. 
                Säilytä oleelliset tiedot ja merkitykset.
                Vastaa aina suomeksi.""",
                user_message=f"Tiivistä seuraava teksti.{length_instruction}\n\n{text}",
            )

            return response

        except Exception as e:
            logger.error(f"Error in text summarization: {str(e)}")
            return f"Error: {str(e)}"
