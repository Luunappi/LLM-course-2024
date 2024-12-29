from setuptools import setup, find_packages

setup(
    name="agentic",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "transformers>=4.35.2",
        "torch>=2.1.2",
        "openai>=1.6.1",
        "numpy>=1.26.2",
        "aiofiles>=23.2.1",
        "streamlit>=1.29.0",
        "python-dotenv>=1.0.0",
    ],
    python_requires=">=3.8",
)
