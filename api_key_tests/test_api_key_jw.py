"""
Test API key availability and validity.
Tests if required API keys (OpenAI, Google) can be found from:
1. .env file in repo root
2. Colab secrets folder
"""

import os
from pathlib import Path
from dotenv import load_dotenv


def test_api_keys():
    """Test that required API keys exist and are valid"""
    print("\n=== Testing API Keys ===")

    # 1. Try loading from .env
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Found .env at {env_path}")
    else:
        print("No .env file found")

    # 2. Check keys from both .env and Colab
    keys = {
        "OPENAI_API_KEY": {
            "env_var": "OPENAI_API_KEY",
            "colab_file": "/content/secrets/openai_api_key.txt",
            "prefix": "sk-",
        },
        "GOOGLE_API_KEY": {
            "env_var": "GOOGLE_API_KEY",
            "colab_file": "/content/secrets/google_api_key.txt",
            "prefix": "AI",
        },
    }

    for key_name, key_info in keys.items():
        print(f"\nChecking {key_name}:")
        print("-" * 30)

        # Try .env first
        key = os.getenv(key_info["env_var"])
        if key:
            print(f"✓ Found in .env: {key[:6]}...{key[-4:]}")
        else:
            print("✗ Not found in .env")

            # Try Colab if not in .env
            print("\nTrying Colab secrets:")
            try:
                colab_path = Path(key_info["colab_file"])
                if colab_path.exists():
                    key = colab_path.read_text().strip()
                    if key:
                        print(f"✓ Found in Colab: {key[:6]}...{key[-4:]}")
                    else:
                        print("✗ Empty file in Colab")
                else:
                    print(f"✗ No file at {colab_path}")
            except Exception as e:
                print(f"✗ Error reading Colab secret: {e}")

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

        if not key:
            raise AssertionError(f"{key_name} not found in .env or Colab")

    print("\n=== All API keys OK ===")
