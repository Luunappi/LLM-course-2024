from setuptools import setup, find_packages

setup(
    name="AgenticRAG_system",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "torch",
        "transformers",
        "sentence-transformers",
        "pillow",
        "pandas",
        "streamlit",
        "pypdf",
    ],
)
