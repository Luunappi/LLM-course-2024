import os
import pytest
from dotenv import load_dotenv
from pathlib import Path


def test_api_key_loading():
    """Test API key loading from both .env and Colab secrets"""

    print("\n=== API Key Loading Test ===")
    api_key = None

    # 1. Yritä hakea avain projektin juuresta .env tiedostosta
    repo_root = Path(__file__).parent.parent  # Siirry tests-kansiosta ylös
    env_path = repo_root / ".env"

    print("\nTesting .env file loading:")
    print("-" * 30)
    if env_path.exists():
        print(f"✓ Found .env file at {env_path}")
        load_dotenv(env_path)
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            print("✓ Successfully loaded API key from .env file")
        else:
            print("✗ No API key found in .env file")
    else:
        print(f"✗ No .env file found at {env_path}")

    # 2. Jos .env ei toiminut, kokeile Colab secrets
    if not api_key:
        print("\nTesting Colab secrets loading:")
        print("-" * 30)
        colab_secret_path = Path("/content/secrets/google_api_key.txt")
        try:
            if colab_secret_path.exists():
                print(f"✓ Found secret file at {colab_secret_path}")
                with open(colab_secret_path, "r") as f:
                    api_key = f.read().strip()
                if api_key:
                    print("✓ Successfully loaded API key from Colab secrets")
                else:
                    print("✗ No API key found in Colab secrets file")
            else:
                print(f"✗ No secret file found at {colab_secret_path}")
        except Exception as e:
            print(f"✗ Error reading Colab secret: {e}")

    # 3. Tarkista että avain löytyi jostain
    print("\nValidating API key:")
    print("-" * 30)
    assert api_key is not None, "✗ API key not found in .env or Colab secrets"
    print("✓ API key found")

    # 4. Tarkista että avain on järkevän muotoinen
    assert len(api_key) > 20, "✗ API key seems too short"
    print("✓ API key length OK")
    assert api_key.startswith("AI"), "✗ API key should start with 'AI'"
    print("✓ API key format OK")

    print(f"\nFinal Result:")
    print("-" * 30)
    print(f"✓ Valid API key found: {api_key[:6]}...{api_key[-4:]}")
    print("=== Test Complete ===\n")
    return True
