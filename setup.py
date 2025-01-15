from setuptools import setup, find_packages

setup(
    name="agentformer",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "pytest",
        "sentence-transformers",
        "numpy",
        "pypdf",
    ],
)
