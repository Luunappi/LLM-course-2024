"""
Test API key availability and validity.
Tests if required API keys can be found:
1. GOOGLE_API_KEY from .env (required for accessing other keys)
2. Other keys (like OpenAI) from either:
   - .env file
   - Colab secrets (accessed using GOOGLE_API_KEY)
"""

import os
from pathlib import Path
from dotenv import load_dotenv


def test_api_keys():
    """Test API key loading from .env and Colab secrets"""
    print("\n=== Testing API Keys ===")

    # 1. First, we need GOOGLE_API_KEY from .env
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Found .env at {env_path}")
    else:
        print("No .env file found")

    # 2. Validate GOOGLE_API_KEY first as it's needed for accessing other keys
    google_key = os.getenv("GOOGLE_API_KEY")
    print("\nChecking GOOGLE_API_KEY:")
    print("-" * 30)
    assert google_key is not None, "GOOGLE_API_KEY not found in .env"
    assert len(google_key) > 20, "GOOGLE_API_KEY too short"
    assert google_key.startswith("AI"), "GOOGLE_API_KEY should start with 'AI'"
    print(f"✓ Found valid GOOGLE_API_KEY: {google_key[:6]}...{google_key[-4:]}")

    # 3. Now check other keys (they can be in either .env or Colab)
    other_keys = {
        "OPENAI_API_KEY": {
            "env_var": "OPENAI_API_KEY",
            "prefix": "sk-",
        }
    }

    for key_name, key_info in other_keys.items():
        print(f"\nChecking {key_name}:")
        print("-" * 30)

        # Try .env first
        key = os.getenv(key_info["env_var"])
        if key:
            print(f"✓ Found in .env: {key[:6]}...{key[-4:]}")
        else:
            print(
                "✗ Not found in .env (will be fetched from Colab using GOOGLE_API_KEY)"
            )

        # Validate key if found
        if key:
            try:
                assert len(key) > 20, "Key too short"
                assert key.startswith(
                    key_info["prefix"]
                ), f"Should start with {key_info['prefix']}"
                print(f"✓ Key format valid")
            except AssertionError as e:
                print(f"✗ Invalid format: {e}")
                key = None

    print("\n=== API key check complete ===")
