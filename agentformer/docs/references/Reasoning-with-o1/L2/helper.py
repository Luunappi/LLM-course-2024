import os
from pathlib import Path
from dotenv import load_dotenv


def get_openai_api_key():
    """
    Get OpenAI API key from environment variable.
    Returns the API key as string.
    """
    # Get the repository root directory by going up from current file
    repo_root = Path(__file__).parent.parent.parent
    env_path = repo_root / ".env"

    # Load environment variables from .env file if it exists
    if env_path.exists():
        load_dotenv(env_path)
    else:
        raise FileNotFoundError(
            f"No .env file found at {env_path}. Please create one with your OPENAI_API_KEY."
        )

    # Try to get API key from environment variable
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found in .env file. "
            "Please add OPENAI_API_KEY=your-key-here to your .env file."
        )

    # Validate key format
    if not api_key.startswith("sk-"):
        raise ValueError("Invalid OPENAI_API_KEY format. Key should start with 'sk-'")

    return api_key
