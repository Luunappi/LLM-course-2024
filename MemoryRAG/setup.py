from setuptools import setup, find_packages

setup(
    name="memoryrag",
    version="0.1",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "tiktoken",
        "pytest",
        "openai",
        "python-dotenv",
        "numpy",
        "pytest-asyncio",
        "aiofiles",
        "torch",
    ],
)
