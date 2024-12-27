# In-Context Learning
#
# In-context learning is a generalisation of few-shot learning where the LLM is provided
# a context as part of the prompt and asked to respond by utilising the information in the context.
#
# * Example: "Summarize this research article into one paragraph highlighting its strengths and weaknesses: [insert article text]"
# * Example: "Extract all the quotes from this text and organize them in alphabetical order: [insert text]"
#
# A very popular technique that you will learn in week 5 called Retrieval-Augmented Generation (RAG)
# is a form of in-context learning, where:
# * a search engine is used to retrieve some relevant information
# * that information is then provided to the LLM as context

import os  # Käyttöjärjestelmätason operaatioita varten (esim. ympäristömuuttujien käsittely)
import requests  # HTTP-pyyntöjen tekemiseen verkkosivuille
from bs4 import BeautifulSoup  # HTML/XML-parsintaan ja käsittelyyn
import ollama  # Mistral mallin käyttöön
from urllib.request import (
    urlopen,
    urlretrieve,
)  # URL:ien avaamiseen ja tiedostojen lataamiseen
from IPython.display import (
    Markdown,
    display,
)  # Markdown-muotoilun näyttämiseen Jupyter-ympäristössä
from pypdf import PdfReader  # PDF-tiedostojen lukemiseen ja tekstin erottamiseen
from datetime import date  # Päivämäärien käsittelyyn
from tqdm import tqdm  # Edistymispalkin näyttämiseen silmukoissa
from pathlib import Path
from typing import Dict, List
import json
import hashlib
from datetime import datetime, timedelta
import time
import subprocess
import signal
import atexit
import psutil
from contextlib import contextmanager

# Määritä hakemistot
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
PAPERS_DIR = DATA_DIR / "papers"
TEMP_DIR = DATA_DIR / "temp"
OUTPUT_DIR = DATA_DIR / "output"

# Luo hakemistot
for dir_path in [PAPERS_DIR, TEMP_DIR, OUTPUT_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


def extract_pdf(url: str) -> str:
    """Lataa ja lue PDF tiedosto"""
    pdf_path = TEMP_DIR / "temp.pdf"
    try:
        print(f"\nDownloading PDF from {url}")
        urlretrieve(url, pdf_path)

        with open(pdf_path, "rb") as f:
            reader = PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error extracting PDF: {str(e)}")
        return None
    finally:
        if pdf_path.exists():
            pdf_path.unlink()


def fetch_papers() -> List[Dict]:
    """Hae paperit Hugging Face:n sivulta"""
    BASE_URL = "https://huggingface.co/papers"

    response = requests.get(BASE_URL)
    soup = BeautifulSoup(response.content, "html.parser")
    h3s = soup.find_all("h3")

    papers = []
    for h3 in h3s:
        a = h3.find("a")
        title = a.text
        link = a["href"].replace("/papers", "")
        papers.append({"title": title, "url": f"https://arxiv.org/pdf{link}"})
    return papers


def get_cache_path(url: str) -> Path:
    """Luo yksilöllinen tiedostopolku URL:n perusteella"""
    # Luo hash URL:sta tiedostonimeksi
    filename = hashlib.md5(url.encode()).hexdigest() + ".json"
    return PAPERS_DIR / filename


def is_cache_valid(cache_path: Path, max_age_days: int = 7) -> bool:
    """Tarkista onko välimuisti vielä voimassa"""
    if not cache_path.exists():
        return False

    # Tarkista tiedoston ikä
    file_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
    age = datetime.now() - file_time
    return age.days < max_age_days


def load_from_cache(url: str) -> Dict:
    """Lataa paperin tiedot välimuistista"""
    cache_path = get_cache_path(url)
    if is_cache_valid(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading cache: {str(e)}")
    return None


def save_to_cache(url: str, data: Dict):
    """Tallenna paperin tiedot välimuistiin"""
    cache_path = get_cache_path(url)
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving to cache: {str(e)}")


def truncate_text(text: str, max_length: int = 2000) -> str:
    """Lyhennä teksti järkevästi"""
    if len(text) <= max_length:
        return text

    # Jaa kappaleisiin ja valitse tärkeimmät
    paragraphs = text.split("\n\n")
    # Ota alku, keskiosa ja loppu
    selected = (
        paragraphs[:2]
        + paragraphs[len(paragraphs) // 2 : len(paragraphs) // 2 + 2]
        + paragraphs[-2:]
    )
    return "\n\n".join(selected)[:max_length]


def analyze_paper(url: str, text: str = None) -> Dict:
    """Analysoi paperi käyttäen välimuistia ja Mistral mallia"""
    start_time = time.time()

    # Tarkista välimuisti (< 1ms)
    cached_data = load_from_cache(url)
    if cached_data:
        cache_time = time.time() - start_time
        print(f"Cache hit! Loaded in {cache_time*1000:.1f}ms")
        return cached_data

    # Mallin suoritus (tyypillisesti 1-5s)
    model_start = time.time()
    # Jos ei välimuistissa, analysoi teksti
    if text is None:
        text = extract_pdf(url)
        if not text:
            return {
                "summary": "PDF extraction failed",
                "strengths": ["N/A"],
                "weaknesses": ["N/A"],
            }

    # Lyhennä teksti ennen analyysiä
    if text:
        text = truncate_text(text)

    # Muokataan promptia selkeämmäksi
    prompt = (
        """Analyze this research article and provide a structured analysis in exactly this format:

SUMMARY: Write a 1-2 sentence summary here.

STRENGTHS:
- [Strength 1]: Explanation here
- [Strength 2]: Explanation here

WEAKNESSES:
- [Weakness 1]: Explanation here
- [Weakness 2]: Explanation here

Article text: """
        + text
    )

    response = ollama.chat(
        model="mistral", messages=[{"role": "user", "content": prompt}]
    )

    content = response["message"]["content"]

    # Debug tulostus
    print("\nDEBUG - Raw Mistral response:")
    print("---START OF RESPONSE---")
    print(content)
    print("---END OF RESPONSE---\n")

    # Uusi parsintalogiikka
    sections = content.split("\n")
    summary = ""
    strengths = []
    weaknesses = []

    current_section = None
    for line in sections:
        line = line.strip()
        if not line:
            continue

        # Debug tulostus
        print(f"Processing line: '{line}' (current_section: {current_section})")

        if "SUMMARY:" in line.upper():
            current_section = "summary"
            summary = line.split(":", 1)[1].strip() if ":" in line else ""
        elif "STRENGTHS:" in line.upper():
            current_section = "strengths"
        elif "WEAKNESSES:" in line.upper():
            current_section = "weaknesses"
        elif line.startswith("-") or line.startswith("*"):
            if current_section == "strengths":
                strengths.append(line.lstrip("- *").strip())
            elif current_section == "weaknesses":
                weaknesses.append(line.lstrip("- *").strip())
        elif current_section == "summary" and not summary:
            summary = line.strip()
        elif (
            current_section == "strengths"
            and line
            and not line.upper().startswith("WEAKNESS")
        ):
            # Kerää myös rivit jotka eivät ala viivalla
            if not any(
                line.upper().startswith(x)
                for x in ["SUMMARY:", "STRENGTH:", "WEAKNESS:"]
            ):
                strengths.append(line.strip())
        elif current_section == "weaknesses" and line:
            # Kerää myös rivit jotka eivät ala viivalla
            if not any(
                line.upper().startswith(x)
                for x in ["SUMMARY:", "STRENGTH:", "WEAKNESS:"]
            ):
                weaknesses.append(line.strip())

    # Debug tulostus lopputuloksesta
    print("\nParsed results:")
    print(f"Summary: {summary}")
    print(f"Strengths: {strengths}")
    print(f"Weaknesses: {weaknesses}\n")

    result = {
        "summary": summary,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "cached_at": datetime.now().isoformat(),
    }

    # Tallenna välimuistiin
    save_to_cache(url, result)

    model_time = time.time() - model_start
    print(f"Model inference took {model_time:.1f}s")

    print("DEBUG - Mistral response:", content)

    return result


def write_html_report(papers: List[Dict], model_name: str):
    """Kirjoita tulokset HTML-tiedostoon"""
    output_file = OUTPUT_DIR / "papers.html"

    html_content = [
        "<html>",
        "<head>",
        "<meta charset='utf-8'>",
        f"<title>Daily Dose of AI Research - {date.today()}</title>",
        "<style>",
        "body { max-width: 1200px; margin: 0 auto; padding: 20px; font-family: Arial; }",
        "table { width: 100%; border-collapse: collapse; }",
        "th, td { border: 1px solid #ddd; padding: 12px; }",
        "th { background-color: #f5f5f5; }",
        "</style>",
        "</head>",
        "<body>",
        "<h1>Daily Dose of AI Research</h1>",
        f"<h4>{date.today()}</h4>",
        f"<p><i>Analysis by: {model_name}</i></p>",
        "<table>",
        "<tr><th>Paper</th><th>Summary</th><th>Strengths</th><th>Weaknesses</th></tr>",
    ]

    for paper in papers:
        html_content.append(
            f"""<tr>
                <td><a href="{paper['url']}">{paper['title']}</a></td>
                <td>{paper.get('summary', 'N/A')}</td>
                <td><ul>{"".join(f"<li>{s}</li>" for s in paper.get('strengths', []))}</ul></td>
                <td><ul>{"".join(f"<li>{w}</li>" for w in paper.get('weaknesses', []))}</ul></td>
            </tr>"""
        )

    html_content.extend(["</table>", "</body>", "</html>"])

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(html_content))
    print(f"\nReport saved to {output_file}")


class OllamaService:
    def __init__(self):
        self.process = None
        self.ready = False
        atexit.register(self.stop)  # Varmista että palvelu suljetaan

    def start(self):
        """Käynnistä Ollama-palvelu ja odota kunnes se on valmis"""
        print("Starting Ollama service...")

        # Tarkista onko jo käynnissä
        if self.is_running():
            print("Ollama service already running")
            self.ready = True
            return

        try:
            # Käynnistä palvelu
            self.process = subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )

            # Odota kunnes palvelu on valmis
            start_time = time.time()
            while time.time() - start_time < 30:  # Timeout 30s
                if self.is_ready():
                    self.ready = True
                    print("Ollama service ready")
                    return
                time.sleep(0.5)

            raise TimeoutError("Ollama service failed to start")

        except Exception as e:
            print(f"Error starting Ollama: {str(e)}")
            self.stop()
            raise

    def stop(self):
        """Pysäytä Ollama-palvelu"""
        if self.process:
            print("Stopping Ollama service...")
            self.process.terminate()
            self.process.wait(timeout=5)
            self.process = None
            self.ready = False

        # Varmista että kaikki Ollama prosessit suljetaan
        for proc in psutil.process_iter(["name"]):
            if proc.info["name"] == "ollama":
                proc.kill()

    def is_running(self) -> bool:
        """Tarkista onko palvelu käynnissä"""
        return any(proc.name() == "ollama" for proc in psutil.process_iter(["name"]))

    def is_ready(self) -> bool:
        """Tarkista onko palvelu valmis vastaanottamaan pyyntöjä"""
        try:
            response = requests.get("http://localhost:11434/api/tags")
            return response.status_code == 200
        except:
            return False


@contextmanager
def ollama_service():
    """Context manager Ollama-palvelun hallintaan"""
    service = OllamaService()
    try:
        service.start()
        yield service
    finally:
        service.stop()


class PerformanceMonitor:
    def __init__(self):
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "model_calls": 0,
            "total_time": 0,
            "model_time": 0,
        }
        self.start_time = time.time()

    def update(self, event: str, duration: float = 0):
        if event == "cache_hit":
            self.stats["cache_hits"] += 1
        elif event == "cache_miss":
            self.stats["cache_misses"] += 1
        elif event == "model_call":
            self.stats["model_calls"] += 1
            self.stats["model_time"] += duration

    def report(self):
        self.stats["total_time"] = time.time() - self.start_time
        print("\nPerformance Report:")
        print(f"Total time: {self.stats['total_time']:.1f}s")
        print(f"Cache hits: {self.stats['cache_hits']}")
        print(f"Cache misses: {self.stats['cache_misses']}")
        print(f"Model calls: {self.stats['model_calls']}")
        if self.stats["model_calls"] > 0:
            print(
                f"Average model time: {self.stats['model_time']/self.stats['model_calls']:.1f}s"
            )
        return self.stats


def clear_cache():
    """Tyhjennä välimuisti"""
    for file in PAPERS_DIR.glob("*.json"):
        file.unlink()
    print("Cache cleared")


def main():
    monitor = PerformanceMonitor()

    # Tyhjennä välimuisti ennen ajoa
    clear_cache()

    # Käynnistä Ollama automaattisesti
    with ollama_service():
        try:
            # Hae paperit
            papers = fetch_papers()

            # Analysoi paperit
            for paper in tqdm(papers, desc="Processing papers"):
                # Yritä ensin ladata välimuistista
                results = load_from_cache(paper["url"])
                if results:
                    monitor.update("cache_hit")
                else:
                    monitor.update("cache_miss")
                    text = extract_pdf(paper["url"])
                    if text:
                        start_time = time.time()
                        results = analyze_paper(paper["url"], text)
                        monitor.update("model_call", time.time() - start_time)
                    else:
                        results = {
                            "summary": "PDF extraction failed",
                            "strengths": ["N/A"],
                            "weaknesses": ["N/A"],
                        }
                paper.update(results)

            # Tallenna tulokset
            write_html_report(papers, "Mistral 7B")

            # Tulosta suorituskykyraportti
            stats = monitor.report()

            # Tallenna tilastot
            stats_path = OUTPUT_DIR / "performance_stats.json"
            with open(stats_path, "w") as f:
                json.dump(stats, f, indent=2)

        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
        except Exception as e:
            print(f"\nError during execution: {str(e)}")
            raise


if __name__ == "__main__":
    main()
