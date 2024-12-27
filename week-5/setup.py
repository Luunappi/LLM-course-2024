from setuptools import setup, find_packages

setup(
    name="rag_project",
    version="0.1",
    packages=find_packages(),
    package_dir={"": "."},  # Kertoo että paketit ovat juurikansiossa
    install_requires=[
        "streamlit",
        "torch",
        "transformers",
        "sentence-transformers",
        "spacy",
        "PyMuPDF",
        "python-dotenv",
        "pandas",
        "numpy",
        "stqdm",
    ],
)
