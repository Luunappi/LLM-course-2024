"""Path manager for memory storage"""

import os
import logging

logger = logging.getLogger(__name__)


class PathManager:
    """Manage paths for memory storage"""

    @staticmethod
    def get_project_root():
        """Get absolute path to project root"""
        return os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),  # memory/
                "..",  # storage/
                "..",  # agentformer/
            )
        )

    @staticmethod
    def get_storage_paths():
        """Get all storage related paths"""
        project_root = PathManager.get_project_root()

        paths = {
            "root": project_root,
            "storage": os.path.join(project_root, "storage"),
            "memory": os.path.join(project_root, "storage", "memory"),
            "saved_files": os.path.join(
                project_root, "storage", "memory", "saved_files"
            ),
            "vector_db": os.path.join(
                project_root, "storage", "memory", "vector_database"
            ),
        }

        # Create directories if they don't exist
        for path in paths.values():
            os.makedirs(path, exist_ok=True)

        logger.info("\n=== Storage Paths ===")
        for name, path in paths.items():
            logger.info(f"{name}: {path}")
        logger.info("===================\n")

        return paths
