"""Azure OpenAI mallien testaus"""

import asyncio
import aiohttp
import json
from memoryrag.model_manager import ModelManager, TaskType
import os
from pathlib import Path
from dotenv import load_dotenv


async def test_direct_api(model_name: str) -> None:
    """Testaa Azure API:a suoraan"""
    endpoint = os.getenv("AZURE_ENDPOINT").rstrip("/")
    api_key = os.getenv("AZURE_API_KEY")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")

    url = f"{endpoint}/openai/deployments/{model_name}/chat/completions"

    headers = {"api-key": api_key, "Content-Type": "application/json"}

    data = {"messages": [{"role": "user", "content": "Test"}], "max_tokens": 5}

    print(f"\nTestataan suoraan Azure API:a mallille {model_name}")
    print(f"URL: {url}")
    print(f"API version: {api_version}")

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{url}?api-version={api_version}", headers=headers, json=data
        ) as resp:
            print(f"Status: {resp.status}")
            response_text = await resp.text()
            print(f"Response: {response_text}")
            return resp.status == 200


async def list_deployments() -> None:
    """Listaa kaikki saatavilla olevat Azure OpenAI deploymentit"""
    endpoint = os.getenv("AZURE_ENDPOINT").rstrip("/")
    api_key = os.getenv("AZURE_API_KEY")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")

    url = f"{endpoint}/openai/deployments?api-version={api_version}"

    headers = {"api-key": api_key}

    print("\nHaetaan saatavilla olevat deploymentit:")
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            print(f"Status: {resp.status}")
            if resp.status == 200:
                data = await resp.json()
                print("\nSaatavilla olevat deploymentit:")
                for deployment in data["value"]:
                    print(f"- {deployment['id']}: {deployment['model']['name']}")
            else:
                print(f"Virhe: {await resp.text()}")


async def test_azure_models():
    """Testaa Azure OpenAI malleja"""
    # Näytä nykyinen hakemisto
    current_dir = Path.cwd()
    print(f"\nNykyinen hakemisto: {current_dir}")

    # Näytä tiedoston sijainti
    file_path = Path(__file__).resolve()
    print(f"Tämä tiedosto: {file_path}")

    # Näytä polku ylöspäin
    print("\nPolku ylöspäin:")
    for i, parent in enumerate(file_path.parents):
        print(f"{i}: {parent}")
        if i >= 3:  # Näytä 4 tasoa
            break

    # Hae .env tiedosto
    repo_root = (
        Path(__file__).resolve().parents[2]
    )  # 2 tasoa ylös examples/test_azure.py:stä
    env_path = repo_root / ".env"

    print(f"\nEtsitään .env tiedostoa: {env_path}")
    if env_path.exists():
        print("✓ .env tiedosto löytyi!")
    else:
        print("❌ .env tiedostoa ei löydy!")

    load_dotenv(dotenv_path=env_path)

    # Tarkista pakolliset ympäristömuuttujat
    required_vars = ["AZURE_API_KEY", "AZURE_ENDPOINT", "AZURE_OPENAI_API_VERSION"]

    print("\nYmpäristömuuttujat:")
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
            print(f"❌ {var}: Puuttuu")
        else:
            # Näytä vain osa API-avaimesta turvallisuussyistä
            if "KEY" in var:
                print(f"✓ {var}: {value[:6]}...{value[-4:]}")
            else:
                print(f"✓ {var}: {value}")

    if missing_vars:
        print(
            f"\nVIRHE: Seuraavat ympäristömuuttujat puuttuvat: {', '.join(missing_vars)}"
        )
        print("Varmista että .env tiedosto sisältää kaikki tarvittavat muuttujat:")
        print("""
        # Azure OpenAI
        AZURE_API_KEY=your-azure-key
        AZURE_ENDPOINT=https://your-resource.openai.azure.com
        AZURE_OPENAI_API_VERSION=2024-02-15-preview
        """)
        return

    # Jatka testeihin vain jos kaikki asetukset löytyvät
    print("\nKaikki asetukset OK, aloitetaan testit...")

    # Alusta model manager
    model_mgr = ModelManager()

    # Testaa ensin suoraan API:a
    print("\nTestataan Azure API:a suoraan:")
    for model_name in ["gpt-4o-mini", "o1-mini", "o1-preview"]:
        success = await test_direct_api(model_name)
        if not success:
            print(f"⚠️  Suora API testi epäonnistui mallille {model_name}")
            continue
        print(f"✓ Suora API testi onnistui mallille {model_name}")

    # Jatka OpenAI clientin testaukseen
    # Testaa jokaista Azure mallia
    test_prompts = {
        "gpt-4o-mini": "Tiivistä lyhyesti: Mikä on tekoäly?",
        "o1-preview": "Analysoi tarkasti: Miten neuroverkot oppivat?",
        "o1-mini": "Vertaile eri koneoppimismalleja.",
    }

    for model_name, prompt in test_prompts.items():
        print(f"\n=== Testataan mallia: {model_name} ===")
        try:
            # Kutsu mallia suoraan ilman fallbackia
            client = model_mgr.azure_clients[model_name]  # Hae oikea client
            response = await client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7,
            )
            print(f"Vastaus: {response.choices[0].message.content}")
            print("✓ Testi onnistui")

        except Exception as e:
            print(f"✗ Testi epäonnistui: {str(e)}")
            print(f"Virheviesti: {e.__class__.__name__}: {str(e)}")

            # Näytä lisätietoja virheestä
            print("\nDebug tiedot:")
            print(f"Model name: {model_name}")
            print(f"Available clients: {list(model_mgr.azure_clients.keys())}")

            # Käytä samaa URL:n muodostusta kuin alustuksessa
            endpoint = model_mgr.azure_endpoint.rstrip("/")
            deployment_path = f"openai/deployments/{model_name}"
            base_url = f"{endpoint}/{deployment_path}"
            print(f"Base URL: {base_url}")

    # Listaa ensin saatavilla olevat deploymentit
    await list_deployments()


if __name__ == "__main__":
    print("Aloitetaan Azure mallien testaus...")
    asyncio.run(test_azure_models())
