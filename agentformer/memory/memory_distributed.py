"""
Distributed Memory Module

This module implements a distributed, network-like memory structure where information
is stored in interconnected nodes that form an associative network.

Key Features:
- Memory consists of interconnected nodes
- Automatic formation of connections between related nodes
- Support for associative search and retrieval
- Active node tracking for recent/relevant information
- Automatic cleanup of old and weakly connected nodes

Memory Structure:
- Nodes: Store actual content with metadata
- Connections: Links between related nodes
- Active Set: Recently accessed or relevant nodes

This implementation is particularly suitable for:
- Dynamic knowledge association
- Flexible information retrieval
- Pattern recognition
- Contextual memory access

The distributed structure allows for organic growth of memory connections
and efficient retrieval of related information through node traversal.
"""

import time
from typing import Dict, List, Any, Optional
import logging
from .memory_base import BaseMemory

logger = logging.getLogger(__name__)


class DistributedMemory(BaseMemory):
    def __init__(self):
        self.nodes = {}  # Muistisolmut
        self.connections = {}  # Solmujen väliset yhteydet
        self.active_nodes = set()  # Aktiiviset solmut
        logger.debug("Initialized DistributedMemory")

    def store(self, content: Any, memory_type: str = "episodic", **kwargs) -> None:
        """Store content in distributed nodes"""
        node_id = time.time_ns()
        node = {
            "content": content,
            "type": memory_type,
            "timestamp": time.time(),
            "metadata": kwargs,
            "connections": set(),
        }

        # Lisää solmu ja yhdistä se relevantteihin solmuihin
        self.nodes[node_id] = node
        self._connect_related_nodes(node_id)
        self.active_nodes.add(node_id)

        logger.debug(f"Stored node {node_id}: {content}")

    def retrieve(self, query: str, memory_type: Optional[str] = None) -> List[Dict]:
        """Retrieve memories through node traversal"""
        results = []
        visited = set()

        # Aloita aktiivisista solmuista
        nodes_to_visit = self.active_nodes.copy()

        while nodes_to_visit:
            node_id = nodes_to_visit.pop()
            if node_id in visited:
                continue

            node = self.nodes[node_id]
            visited.add(node_id)

            # Tarkista vastaako solmu hakua
            if memory_type and node["type"] != memory_type:
                continue

            if query.lower() in str(node["content"]).lower():
                results.append(node)

            # Lisää yhdistetyt solmut käsittelyjonoon
            nodes_to_visit.update(node["connections"])

        return results

    def cleanup(self) -> None:
        """Remove old and weakly connected nodes"""
        current_time = time.time()
        max_age = 30 * 24 * 60 * 60  # 30 päivää

        nodes_to_remove = set()
        for node_id, node in self.nodes.items():
            # Poista vanhat solmut
            if current_time - node["timestamp"] > max_age:
                nodes_to_remove.add(node_id)
                continue

            # Poista heikosti yhdistetyt solmut
            if len(node["connections"]) < 2:
                nodes_to_remove.add(node_id)

        # Päivitä rakenteet
        for node_id in nodes_to_remove:
            self._remove_node(node_id)

        logger.info(f"Removed {len(nodes_to_remove)} nodes in cleanup")

    def get_state(self) -> Dict:
        """Get current memory state"""
        return {
            "total_nodes": len(self.nodes),
            "active_nodes": len(self.active_nodes),
            "avg_connections": self._get_avg_connections(),
            "memory_types": self._get_type_distribution(),
        }

    def _connect_related_nodes(self, node_id: int) -> None:
        """Connect node to related nodes based on content similarity"""
        new_node = self.nodes[node_id]

        for other_id, other_node in self.nodes.items():
            if other_id == node_id:
                continue

            # Tässä voisi olla kehittyneempi samankaltaisuuden laskenta
            if new_node["type"] == other_node["type"]:
                new_node["connections"].add(other_id)
                other_node["connections"].add(node_id)

    def _remove_node(self, node_id: int) -> None:
        """Remove node and its connections"""
        node = self.nodes[node_id]

        # Poista viittaukset muista solmuista
        for connected_id in node["connections"]:
            if connected_id in self.nodes:
                self.nodes[connected_id]["connections"].remove(node_id)

        # Poista solmu
        self.nodes.pop(node_id)
        self.active_nodes.discard(node_id)

    def _get_avg_connections(self) -> float:
        """Calculate average number of connections per node"""
        if not self.nodes:
            return 0.0
        total = sum(len(node["connections"]) for node in self.nodes.values())
        return total / len(self.nodes)

    def _get_type_distribution(self) -> Dict[str, int]:
        """Get distribution of memory types"""
        distribution = {}
        for node in self.nodes.values():
            mtype = node["type"]
            distribution[mtype] = distribution.get(mtype, 0) + 1
        return distribution
