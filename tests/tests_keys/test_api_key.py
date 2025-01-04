"""
General API Key Validation Test

This test verifies the availability and validity of required API keys for the project.

Tests for:
1. OpenAI API key:
   - Tries to load from root .env file (OPENAI_API_KEY)
   - Tries to load from Colab secrets (/content/secrets/openai_api_key.txt)
   - Validates key format and length

2. Google Gemini API key:
   - Tries to load from root .env file (GOOGLE_API_KEY)
   - Tries to load from Colab secrets (/content/secrets/google_api_key.txt)
   - Validates key format and length

The test checks both local (.env) and Colab environments to ensure keys are
accessible in both development contexts.

Usage:
    pytest tests_jw/test_api_key_jw.py -v

Author: Jussi Wright
Date: March 2024
"""

# ... [rest of the code stays the same] ...
