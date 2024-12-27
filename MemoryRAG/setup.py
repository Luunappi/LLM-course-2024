from setuptools import setup, find_namespace_packages

setup(
    name="memoryrag",
    version="0.1",
    package_dir={"": "src"},
    packages=find_namespace_packages(where="src"),
    install_requires=[
        "tiktoken",
        "pytest",
        "openai",
        "python-dotenv",
        "numpy",
    ],
)
