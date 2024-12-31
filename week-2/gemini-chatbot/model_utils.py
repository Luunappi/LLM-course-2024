from typing import List, Optional, Union, Dict, Tuple
import google.generativeai as genai
import os
from dotenv import load_dotenv
import time
import requests


class LLMInterface:
    """Base interface for language models"""

    def generate_content(self, messages: Union[str, List[str]]) -> Tuple[str, Dict]:
        """Returns tuple of (response_text, metrics)"""
        raise NotImplementedError


class GeminiModel(LLMInterface):
    """Wrapper for Gemini API"""

    def __init__(self, model_name: str = "gemini-1.5-pro"):
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Please set GOOGLE_API_KEY in .env file")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.model_name = model_name
        self.current_language = "en"

        self.system_prompts = {
            "en": """<|system|>
                    You are an Academic Assessment Assistant specialized in Digital Humanities and Cognitive Science.

                    GENERAL STYLE GUIDELINES:
                    - Be thorough and objective in your assessments
                    - Use clear and polite language
                    - Justify grades using the assessment matrix
                    - Provide constructive feedback for student development
                    - Keep focus on course objectives and requirements

                    ASSESSMENT MATRIX (0-5 scale for each):
                    1. Topic Understanding & Connections
                       - Understanding of key concepts
                       - Links to cognitive science and digital humanities
                       - Integration of AI considerations

                    2. Analysis & Argumentation
                       - Logical and justified arguments
                       - Critical thinking and deep analysis
                       - Use of relevant sources

                    3. Structure & Coherence
                       - Clear intro, body, conclusion
                       - Smooth transitions
                       - Consistent and followable content

                    4. Language & Style
                       - Fluent and error-free language
                       - Academic writing style
                       - Clear expressions

                    5. Source Usage & References
                       - Diverse and reliable sources
                       - Consistent citation style
                       - Proper bibliography

                    RESPONSE FORMAT:
                    For each category:
                    - State score (X/5)
                    - Provide specific examples
                    - Give improvement suggestions

                    End with general feedback highlighting:
                    - Key strengths
                    - Areas for improvement
                    </|system|>

                    <|assistant|>
                    I understand my role as an Academic Assessment Assistant. I will:
                    1. Evaluate submissions using the 5-category matrix
                    2. Provide detailed feedback with examples
                    3. Maintain academic tone and objectivity
                    4. Focus on constructive improvement suggestions
                    </|assistant|>""",
            "fi": """<|system|>
                    [Sama sisältö suomeksi, mutta koska Mistral vastaa paremmin englanniksi, 
                    käytetään ensisijaisesti englanninkielistä versiota]
                    </|system|>""",
        }

    def set_language(self, language: str):
        if language not in self.system_prompts:
            raise ValueError(f"Unsupported language: {language}")
        self.current_language = language

    def generate_content(self, messages: Union[str, List[str]]) -> Tuple[str, Dict]:
        start_time = time.time()

        if isinstance(messages, list):
            text = " ".join(messages)
        else:
            text = messages

        prompt = f"{self.system_prompts[self.current_language]}\n\nUser: {text}"
        response = self.model.generate_content(prompt)

        duration = time.time() - start_time
        metrics = {
            "model_name": self.model_name,
            "duration": duration,
            "prompt_tokens": len(prompt.split()),
            "completion_tokens": len(response.text.split()),
            "total_tokens": len(prompt.split()) + len(response.text.split()),
            "cost": 0.0001 * (len(prompt.split()) + len(response.text.split())),
        }

        return response.text, metrics


class MistralModel(LLMInterface):
    """Wrapper for Mistral (commented out but ready to use)"""

    def __init__(self):
        self.current_language = "fi"
        self.model_name = "mistral-fi"

        # Käytetään samaa system promptia kuin GeminiModelissa
        self.system_prompts = {
            "en": """<|system|>
                    You are an Academic Assessment Assistant specialized in Digital Humanities and Cognitive Science.

                    GENERAL STYLE GUIDELINES:
                    - Be thorough and objective in your assessments
                    - Use clear and polite language
                    - Justify grades using the assessment matrix
                    - Provide constructive feedback for student development
                    - Keep focus on course objectives and requirements

                    ASSESSMENT MATRIX (0-5 scale for each):
                    1. Topic Understanding & Connections
                       - Understanding of key concepts
                       - Links to cognitive science and digital humanities
                       - Integration of AI considerations

                    2. Analysis & Argumentation
                       - Logical and justified arguments
                       - Critical thinking and deep analysis
                       - Use of relevant sources

                    3. Structure & Coherence
                       - Clear intro, body, conclusion
                       - Smooth transitions
                       - Consistent and followable content

                    4. Language & Style
                       - Fluent and error-free language
                       - Academic writing style
                       - Clear expressions

                    5. Source Usage & References
                       - Diverse and reliable sources
                       - Consistent citation style
                       - Proper bibliography

                    RESPONSE FORMAT:
                    For each category:
                    - State score (X/5)
                    - Provide specific examples
                    - Give improvement suggestions

                    End with general feedback highlighting:
                    - Key strengths
                    - Areas for improvement
                    </|system|>

                    <|assistant|>
                    I understand my role as an Academic Assessment Assistant. I will:
                    1. Evaluate submissions using the 5-category matrix
                    2. Provide detailed feedback with examples
                    3. Maintain academic tone and objectivity
                    4. Focus on constructive improvement suggestions
                    </|assistant|>""",
            "fi": """<|system|>
                    [Sama sisältö suomeksi, mutta koska Mistral vastaa paremmin englanniksi, 
                    käytetään ensisijaisesti englanninkielistä versiota]
                    </|system|>""",
        }

    def set_language(self, language: str):
        if language not in self.system_prompts:
            raise ValueError(f"Unsupported language: {language}")
        self.current_language = language

    def generate_content(self, messages: Union[str, List[str]]) -> Tuple[str, Dict]:
        start_time = time.time()

        if isinstance(messages, list):
            text = " ".join(messages)
        else:
            text = messages

        prompt = f"{self.system_prompts[self.current_language]}\n\nUser: {text}"

        try:
            # Debug print
            print(f"Sending to Mistral API: {prompt[:100]}...")

            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "mistral",
                    "prompt": prompt,
                },  # Käytä "mistral", ei "mistral-fi"
                timeout=30,
            )
            response.raise_for_status()
            response_text = response.json()["response"]

            duration = time.time() - start_time
            metrics = {
                "model_name": self.model_name,
                "duration": duration,
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": len(response_text.split()),
                "total_tokens": len(prompt.split()) + len(response_text.split()),
                "cost": 0.0,  # Local model, no cost
            }

            return response_text, metrics

        except Exception as e:
            raise Exception(f"Error calling Mistral API: {str(e)}")


def get_model(model_type: str) -> LLMInterface:
    """Factory function to get the right model"""
    if model_type.lower() == "gemini":
        return GeminiModel()
    elif model_type.lower() == "mistral":
        return MistralModel()
    else:
        raise ValueError(f"Unknown model type: {model_type}")
