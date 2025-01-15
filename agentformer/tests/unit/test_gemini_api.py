import os
import google.generativeai as genai
from dotenv import load_dotenv


def test_gemini_api():
    """Testaa Gemini API-avaimen toimivuuden"""
    try:
        # 1. Lataa .env tiedosto
        print("Loading .env file...")
        load_dotenv()

        # 2. Hae API-avain
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env file")
        print(f"API key found: {api_key[:6]}...{api_key[-4:]}")

        # 3. Konfiguroi Gemini
        print("\nConfiguring Gemini...")
        genai.configure(api_key=api_key)

        # 4. Listaa saatavilla olevat mallit
        print("\nListing available models:")
        for m in genai.list_models():
            print(f"- {m.name}")

        # 5. Testaa yksinkertaisella pyynnöllä
        print("\nTesting with simple generation...")
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content("Say 'Hello, World!'")
        print(f"Response: {response.text}")

        print("\n✅ API key works correctly!")
        return True

    except Exception as e:
        print(f"\n❌ Error testing API key: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Check that .env file exists in current directory")
        print("2. Verify GEMINI_API_KEY format in .env")
        print("3. Ensure API key is valid and not expired")
        print("4. Check your internet connection")
        print(f"\nCurrent working directory: {os.getcwd()}")
        return False


if __name__ == "__main__":
    print("=== Gemini API Key Test ===\n")
    success = test_gemini_api()
    exit(0 if success else 1)
