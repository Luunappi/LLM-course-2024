"""Yhteiset pytest-määritykset ja fixturet"""

import pytest
import pytest_asyncio
from memoryrag import MemoryRAG


@pytest_asyncio.fixture(scope="function")
async def rag():
    """Yhteinen MemoryRAG fixture kaikille testeille"""
    instance = await MemoryRAG.create()
    yield instance
    await instance.clear_memories()
