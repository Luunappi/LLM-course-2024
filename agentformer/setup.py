from setuptools import setup, find_packages

setup(
    name="agentformer",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "flask",
        "numpy",
        "faiss-cpu",  # Käytetään CPU-versiota
        "pypdf",  # Huom: Varmista uusin pypdf
        "sentence-transformers>=2.0.0",
        "tiktoken",  # Token laskentaan
        "flask-session",  # Session hallintaan
        "flask-socketio",  # WebSocket tuki
    ],
)
