"""Analyzer Tool - Analysointityökalu

Tämä työkalu analysoi järjestelmän toimintaa ja antaa palautetta:
1. Seuraa keskusteluja ja arvioi vastausten laatua
2. Analysoi orkestraattorin päätöksiä ja työkaluvalintoja
3. Ehdottaa parannuksia järjestelmän toimintaan
4. Ylläpitää analyysihistoriaa kehitystä varten
"""

import logging
import json
from typing import Dict, Optional
from ..core_tools.model_tool import ModelTool

logger = logging.getLogger(__name__)


class AnalyzerTool:
    """Seuraa ja analysoi kysymys-vastaus ketjuja järjestelmän parantamiseksi"""

    def __init__(self):
        self.model_tool = ModelTool()
        self.analysis_history = []
        self.pending_guideline_update = None

    def analyze_interaction(self, query: str, analysis: Dict, response: Dict) -> Dict:
        """Analysoi vuorovaikutusta ja anna palautetta"""
        try:
            # Muodosta analyysi-viesti
            messages = [
                {
                    "role": "user",
                    "content": (
                        "You are an expert system analyst. Analyze the interaction and return a JSON object with:\n"
                        "{\n"
                        '    "was_appropriate": true/false,\n'
                        '    "tool_selection_optimal": true/false,\n'
                        '    "response_quality": 1-5,\n'
                        '    "feedback_message": "Clear feedback message",\n'
                        '    "suggested_improvements": ["improvement1", "improvement2"],\n'
                        '    "should_update_guidelines": true/false\n'
                        "}"
                    ),
                },
                {
                    "role": "user",
                    "content": f"Analyze this interaction: {json.dumps({'query': query, 'mode': analysis.get('mode', 'unknown'), 'orchestrator_analysis': analysis.get('explanation', ''), 'used_rag': analysis.get('should_use_rag', False), 'response_source': response.get('source', 'unknown'), 'found_in_docs': response.get('found_in_docs', False), 'response': response.get('response', '')}, indent=2)}",
                },
            ]

            # Käytä o1-mini mallia analyysiin
            result = self.model_tool.query(messages, model_name="gpt-4o-mini")

            try:
                # Poista mahdolliset markdown-koodiblokki merkinnät
                json_str = result
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1]
                if "```" in json_str:
                    json_str = json_str.split("```")[0]

                # Siisti merkkijono ja yritä parsia JSON
                json_str = json_str.strip()
                return json.loads(json_str)

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from model: {result}")
                return {
                    "feedback_message": "Error: Invalid analysis format",
                    "was_appropriate": False,
                    "response_quality": 1,
                }

        except Exception as e:
            logger.error(f"Error in interaction analysis: {str(e)}")
            return {
                "feedback_message": f"Error analyzing interaction: {str(e)}",
                "was_appropriate": False,
                "response_quality": 1,
            }

    def _generate_guideline_update(
        self, query: str, analysis: Dict, response: Dict, analysis_result: Dict
    ):
        """Luo ehdotus ohjeistuksen päivitykselle"""
        try:
            update_prompt = f"""Based on this interaction analysis, suggest specific improvements to the orchestrator's guidelines:

Query: {query}
Current Analysis: {analysis["explanation"]}
Analysis Result: {analysis_result}

Current Guidelines:
1. For document/file related queries:
   - These are ONLY queries about the documents themselves
   - Response: "Let's use RAG to check our document database"
   - Set should_use_rag: true

2. For document content queries:
   - Response: "We should search our document database"
   - Set should_use_rag: true

3. For general questions:
   - Response: "This is a general question - handle directly"
   - Set should_use_rag: false
   - Set model: "o1-mini"

4. For complex analysis:
   - Response: "This requires deeper analysis"
   - Set should_use_rag: false

Propose a specific improvement to these guidelines. Return as JSON:
{{
    "proposed_change": "Clear description of what to add/modify",
    "rationale": "Brief explanation why this change is needed",
    "example_queries": ["example1", "example2"],
    "guideline_section": "Which section to update (1-4)",
    "new_guideline_text": "Complete text for the updated guideline section"
}}"""

            result = self.model_tool.query(
                "gpt-4o",
                system_prompt="You are an expert system analyst. Propose clear, specific improvements.",
                user_message=update_prompt,
            )

            self.pending_guideline_update = json.loads(result)
            return self.pending_guideline_update
        except Exception as e:
            logger.error(f"Error generating guideline update: {str(e)}")
            return None

    def get_pending_update(self) -> Optional[Dict]:
        """Hae odottava ohjeistuksen päivitysehdotus"""
        return self.pending_guideline_update

    def clear_pending_update(self):
        """Tyhjennä odottava ohjeistuksen päivitys"""
        self.pending_guideline_update = None

    def apply_guideline_update(self, orchestrator_instance) -> bool:
        """Sovella odottava ohjeistuksen päivitys orkestraattoriin"""
        if not self.pending_guideline_update:
            return False

        try:
            update = self.pending_guideline_update
            section = update.get("guideline_section")
            new_text = update.get("new_guideline_text")

            # Update the orchestrator's analysis prompt
            current_prompt = orchestrator_instance.analyze_query.__defaults__[0]
            sections = current_prompt.split("\n\n")

            # Find and update the correct guideline section
            for i, section_text in enumerate(sections):
                if section_text.startswith(f"{section}."):
                    sections[i] = new_text
                    break

            # Combine updated sections
            updated_prompt = "\n\n".join(sections)

            # Update the orchestrator's prompt
            orchestrator_instance.analyze_query.__defaults__ = (updated_prompt,)

            self.clear_pending_update()
            return True
        except Exception as e:
            logger.error(f"Error applying guideline update: {str(e)}")
            return False

    def get_analysis_history(self) -> list:
        """Hae analysoitujen vuorovaikutusten historia"""
        return self.analysis_history
