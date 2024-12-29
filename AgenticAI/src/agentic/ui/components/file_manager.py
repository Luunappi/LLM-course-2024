"""File management component"""

from typing import List, Dict
import streamlit as st
from pathlib import Path
import json
import aiofiles


class FileManager:
    def __init__(self):
        self.storage_path = Path("data/files")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.file_index_path = self.storage_path / "file_index.json"
        self.files: Dict[str, Dict] = self._load_file_index()

    def _load_file_index(self) -> Dict:
        """Load file index from disk"""
        if self.file_index_path.exists():
            return json.loads(self.file_index_path.read_text())
        return {}

    async def save_file(self, file, metadata: Dict) -> str:
        """Save uploaded file and metadata"""
        file_path = self.storage_path / file.name
        file_path.write_bytes(await file.read())

        self.files[file.name] = {
            "path": str(file_path),
            "type": file.type,
            "size": file.size,
            **metadata,
        }
        await self._save_index()
        return file.name

    async def _save_index(self):
        """Save file index to disk"""
        async with aiofiles.open(self.file_index_path, "w") as f:
            await f.write(json.dumps(self.files, indent=2))

    def render_file_list(self):
        """Render file list with expander"""
        with st.expander("📁 Ladatut tiedostot", expanded=False):
            if not self.files:
                st.info("Ei ladattuja tiedostoja")
                return

            for name, info in self.files.items():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(f"{name} ({info['type']}, {info['size']} bytes)")
                with col2:
                    if st.button("🗑️", key=f"delete_{name}"):
                        self.delete_file(name)
