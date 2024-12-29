import pytest
import asyncio
import json
import aiofiles
from pathlib import Path
import shutil
from agentic import MemoryManager, MemoryStorage


@pytest.fixture(autouse=True)
async def setup_teardown():
    """Setup and teardown for each test"""
    # Setup
    if Path("data/memories").exists():
        shutil.rmtree("data/memories")

    yield

    # Teardown
    if Path("data/memories").exists():
        shutil.rmtree("data/memories")


@pytest.mark.asyncio
async def test_memory_persistence():
    """Test that memories persist between sessions"""
    # First session: Store memory
    manager1 = MemoryManager()
    await manager1.initialize()
    test_content = "Test memory content"
    await manager1.store_memory("episodic", test_content, 1.0)

    # Second session: Verify memory exists
    manager2 = MemoryManager()
    await manager2.initialize()
    memories = await manager2.search_memories("Test", "episodic")

    assert len(memories) == 1
    assert memories[0]["content"] == test_content


@pytest.mark.asyncio
async def test_memory_file_structure():
    """Test that memory files are created correctly"""
    manager = MemoryManager()
    await manager.initialize()

    # Store memories of different types
    await manager.store_memory("core", "Core memory", 1.0)
    await manager.store_memory("semantic", "Semantic memory", 0.8)
    await manager.store_memory("episodic", "Episodic memory", 0.6)

    # Check that files exist
    memory_dir = Path("data/memories")
    assert (memory_dir / "core.json").exists()
    assert (memory_dir / "semantic.json").exists()
    assert (memory_dir / "episodic.json").exists()

    # Verify file contents
    async with aiofiles.open(memory_dir / "core.json") as f:
        content = await f.read()
        memory = json.loads(content.strip())
        assert memory["content"] == "Core memory"
