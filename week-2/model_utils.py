from typing import List, Optional, Union, Dict, Tuple
import google.generativeai as genai
import os
from dotenv import load_dotenv
import requests
import time


class LLMInterface:
    """Base interface for language models"""

    def generate_content(self, messages: Union[str, List[str]]) -> Tuple[str, Dict]:
        """Returns tuple of (response_text, metrics)"""
        raise NotImplementedError

    def is_local(self) -> bool:
        return False


class GeminiModel(LLMInterface):
    """Wrapper for Gemini API"""

    def __init__(self, model_name: str = "gemini-1.5-pro"):
        # Yritä ensin hakea avain .env tiedostosta
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")

        # Jos avainta ei löydy .env:stä, kokeile Colab secrets
        if not api_key:
            try:
                with open("/content/secrets/google_api_key.txt", "r") as f:
                    api_key = f.read().strip()
            except FileNotFoundError:
                pass

        if not api_key:
            raise ValueError(
                "Please set the GOOGLE_API_KEY either in .env file or Colab secrets"
            )

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def generate_content(self, messages: Union[str, List[str]]) -> Tuple[str, Dict]:
        # Vaihe 1: Syötteen käsittely
        process_start = time.time()
        if isinstance(messages, list):
            text = " ".join(messages)
        else:
            text = messages
        process_time = time.time() - process_start

        # Vaihe 2: Mallin inferenssi
        api_start = time.time()
        response = self.model.generate_content(messages)
        api_time = time.time() - api_start

        # Vaihe 3: Vastauksen jäsentäminen
        parse_start = time.time()
        estimated_prompt_tokens = len(text.split())
        estimated_completion_tokens = len(response.text.split())
        parse_time = time.time() - parse_start

        total_time = process_time + api_time + parse_time

        metrics = {
            "model_name": self.model_name,
            "duration": total_time,
            "prompt_tokens": estimated_prompt_tokens,
            "completion_tokens": estimated_completion_tokens,
            "total_tokens": estimated_prompt_tokens + estimated_completion_tokens,
            "cost": 0.0001 * (estimated_prompt_tokens + estimated_completion_tokens),
            "timing": {
                "prompt_processing": process_time,
                "model_inference": api_time,
                "response_parsing": parse_time,
            },
        }
        return response.text, metrics


class MistralModel(LLMInterface):
    """Wrapper for local Mistral API"""

    def __init__(self, model_name: str = "mistral", api_url: Optional[str] = None):
        self.model_name = model_name
        self.api_url = api_url or "http://localhost:11434/api/generate"

        # Määritellään agentin rooli ja ohjeet
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
        self.current_language = "en"

    def generate_content(self, messages: Union[str, List[str]]) -> Tuple[str, Dict]:
        # Add assessment context
        context = [
            self.system_prompts[self.current_language],
            "<|user|>Remember to follow the assessment matrix and provide detailed feedback.</|user|>",
            "<|assistant|>I will evaluate the submission carefully using all five categories.</|assistant|>",
        ]

        # Add user messages
        if isinstance(messages, list):
            for msg in messages:
                context.append(f"<|user|>{msg}</|user|>")
        else:
            context.append(f"<|user|>{messages}</|user|>")

        # Create final prompt
        prompt = "\n".join(context)

        # Vaihe 1: Viestin käsittely
        process_start = time.time()
        process_time = time.time() - process_start

        # Vaihe 2: API-kutsu
        api_start = time.time()
        try:
            response = requests.post(
                self.api_url,
                json={"model": self.model_name, "prompt": prompt, "stream": False},
                timeout=30,  # Lisätään timeout
            )
            response.raise_for_status()  # Nostaa virheen jos status ei ole 200
            response_json = response.json()
            if "error" in response_json:
                raise Exception(response_json["error"])
            response_text = response_json["response"]
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to connect to Ollama: {str(e)}")
        except Exception as e:
            raise Exception(f"Error generating response: {str(e)}")
        api_time = time.time() - api_start

        # Vaihe 3: Vastauksen käsittely
        parse_start = time.time()
        prompt_tokens = len(prompt.split())
        completion_tokens = len(response_text.split())
        parse_time = time.time() - parse_start

        total_time = process_time + api_time + parse_time

        metrics = {
            "model_name": self.model_name,
            "duration": total_time,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "cost": 0.0,  # Local models are free
            "timing": {
                "prompt_processing": process_time,
                "model_inference": api_time,
                "response_parsing": parse_time,
            },
        }
        return response_text, metrics


def get_model(model_type: str = "gemini", **kwargs) -> LLMInterface:
    """Factory function to get the appropriate model"""
    if model_type.lower() == "gemini":
        return GeminiModel(**kwargs)
    elif model_type.lower() == "mistral":
        return MistralModel(**kwargs)
    else:
        raise ValueError(f"Unknown model type: {model_type}")
