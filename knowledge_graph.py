"""
R1X Platform - Memory Graph System
Persistent Knowledge Graph for Cyber Intelligence
Version: 2.0.0

نظام الذاكرة الذكي:
- Knowledge Graph للمعرفة المُستفادة
- Session Memory للجلسة الحالية
- Threat Intelligence للتهديدات
- Pattern Store للأنماط المُكتشفة
"""

import asyncio
import sqlite3
import json
import time
import hashlib
import networkx as nx
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import deque
from datetime import datetime
import threading
from pathlib import Path


# ═══════════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class KnowledgeNode:
    """Node in the knowledge graph"""
    node_id: str
    node_type: str  # target, vulnerability, technique, waf, endpoint
    label: str
    properties: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    confidence: float = 1.0
    tags: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "label": self.label,
            "properties": self.properties,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "confidence": self.confidence,
            "tags": list(self.tags)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeNode':
        data["tags"] = set(data.get("tags", []))
        return cls(**data)


@dataclass
class KnowledgeEdge:
    """Edge in the knowledge graph"""
    edge_id: str
    source_id: str
    target_id: str
    relation_type: str  # has_vulnerability, bypasses, targets, etc.
    properties: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type,
            "properties": self.properties,
            "weight": self.weight,
            "created_at": self.created_at
        }


@dataclass
class ThreatIntel:
    """Threat intelligence record"""
    threat_id: str
    threat_type: str  # waf, malware, bot, attacker
    signature: str
    severity: str
    description: str
    mitigation: str
    effectiveness_score: float = 0.5
    use_count: int = 0
    success_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    @property
    def success_rate(self) -> float:
        return self.success_count / max(self.use_count, 1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "threat_id": self.threat_id,
            "threat_type": self.threat_type,
            "signature": self.signature,
            "severity": self.severity,
            "description": self.description,
            "mitigation": self.mitigation,
            "effectiveness_score": self.effectiveness_score,
            "use_count": self.use_count,
            "success_count": self.success_count,
            "success_rate": self.success_rate,
            "metadata": self.metadata,
            "created_at": self.created_at
        }


@dataclass
class PatternRecord:
    """Learned pattern record"""
    pattern_id: str
    pattern_type: str  # response, behavior, payload
    pattern_data: str
    context: str
    target_type: Optional[str] = None
    success_count: int = 0
    failure_count: int = 0
    last_used: Optional[float] = None
    created_at: float = field(default_factory=time.time)

    @property
    def effectiveness(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / max(total, 1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type,
            "pattern_data": self.pattern_data,
            "context": self.context,
            "target_type": self.target_type,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "effectiveness": self.effectiveness,
            "last_used": self.last_used,
            "created_at": self.created_at
        }


@dataclass
class SessionMemory:
    """Session-scoped memory"""
    session_id: str
    target: str
    scan_type: str
    data: Dict[str, Any] = field(default_factory=dict)
    endpoints: List[str] = field(default_factory=list)
    files_found: List[str] = field(default_factory=list)
    vulnerabilities: List[Dict[str, Any]] = field(default_factory=list)
    bypass_attempts: List[Dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def update(self, key: str, value: Any) -> None:
        self.data[key] = value
        self.updated_at = time.time()


# ═══════════════════════════════════════════════════════════════════════════════
# KNOWLEDGE GRAPH ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class KnowledgeGraph:
    """
    Persistent Knowledge Graph for Cyber Intelligence

    الميزات:
    - NetworkX graph for in-memory operations
    - SQLite for persistence
    - Incremental learning from scan results
    - Pattern correlation and analysis
    - Query optimization
    """

    def __init__(self, db_path: str = "data/r1x_knowledge.db"):
        self.db_path = db_path
        self._graph = nx.MultiDiGraph()  # In-memory graph
        self._nodes: Dict[str, KnowledgeNode] = {}
        self._edges: Dict[str, KnowledgeEdge] = {}
        self._lock = asyncio.Lock()
        self._db_lock = threading.Lock()

        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

    def _init_database(self) -> None:
        """Initialize SQLite database"""
        with self._db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Nodes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS nodes (
                    node_id TEXT PRIMARY KEY,
                    node_type TEXT NOT NULL,
                    label TEXT NOT NULL,
                    properties TEXT,
                    metadata TEXT,
                    created_at REAL,
                    updated_at REAL,
                    confidence REAL,
                    tags TEXT
                )
            """)

            # Edges table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS edges (
                    edge_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relation_type TEXT NOT NULL,
                    properties TEXT,
                    weight REAL,
                    created_at REAL,
                    FOREIGN KEY (source_id) REFERENCES nodes(node_id),
                    FOREIGN KEY (target_id) REFERENCES nodes(node_id)
                )
            """)

            # Threat Intel table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS threat_intel (
                    threat_id TEXT PRIMARY KEY,
                    threat_type TEXT NOT NULL,
                    signature TEXT NOT NULL,
                    severity TEXT,
                    description TEXT,
                    mitigation TEXT,
                    effectiveness_score REAL,
                    use_count INTEGER,
                    success_count INTEGER,
                    metadata TEXT,
                    created_at REAL
                )
            """)

            # Patterns table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patterns (
                    pattern_id TEXT PRIMARY KEY,
                    pattern_type TEXT NOT NULL,
                    pattern_data TEXT NOT NULL,
                    context TEXT,
                    target_type TEXT,
                    success_count INTEGER,
                    failure_count INTEGER,
                    last_used REAL,
                    created_at REAL
                )
            """)

            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    target TEXT NOT NULL,
                    scan_type TEXT,
                    data TEXT,
                    endpoints TEXT,
                    files_found TEXT,
                    vulnerabilities TEXT,
                    bypass_attempts TEXT,
                    created_at REAL,
                    updated_at REAL
                )
            """)

            # Indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(node_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_nodes_label ON nodes(label)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_relation ON edges(relation_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_threat_type ON threat_intel(threat_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_patterns_type ON patterns(pattern_type)")

            conn.commit()
            conn.close()

    # ═══════════════════════════════════════════════════════════════════════
    # NODE OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════

    async def add_node(
        self,
        node_type: str,
        label: str,
        properties: Optional[Dict[str, Any]] = None,
        tags: Optional[Set[str]] = None,
        node_id: Optional[str] = None
    ) -> KnowledgeNode:
        """Add a node to the knowledge graph"""
        async with self._lock:
            node_id = node_id or self._generate_node_id(node_type, label)

            if node_id in self._nodes:
                return self._nodes[node_id]

            node = KnowledgeNode(
                node_id=node_id,
                node_type=node_type,
                label=label,
                properties=properties or {},
                tags=tags or set()
            )

            # Add to in-memory graph
            self._graph.add_node(node_id, **node.properties)
            self._nodes[node_id] = node

            # Persist to database
            await self._save_node(node)

            return node

    async def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """Get a node by ID"""
        if node_id in self._nodes:
            return self._nodes[node_id]

        # Load from database
        with self._db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM nodes WHERE node_id = ?",
                (node_id,)
            )
            row = cursor.fetchone()
            conn.close()

        if row:
            data = {
                "node_id": row[0],
                "node_type": row[1],
                "label": row[2],
                "properties": json.loads(row[3]) if row[3] else {},
                "metadata": json.loads(row[4]) if row[4] else {},
                "created_at": row[5],
                "updated_at": row[6],
                "confidence": row[7],
                "tags": set(json.loads(row[8])) if row[8] else set()
            }
            node = KnowledgeNode.from_dict(data)
            self._nodes[node_id] = node
            return node

        return None

    async def find_nodes(
        self,
        node_type: Optional[str] = None,
        label_contains: Optional[str] = None,
        tags: Optional[Set[str]] = None,
        limit: int = 100
    ) -> List[KnowledgeNode]:
        """Find nodes matching criteria"""
        results = []

        for node in self._nodes.values():
            if node_type and node.node_type != node_type:
                continue
            if label_contains and label_contains.lower() not in node.label.lower():
                continue
            if tags and not any(t in node.tags for t in tags):
                continue
            results.append(node)

        return results[:limit]

    async def update_node(self, node_id: str, **updates) -> Optional[KnowledgeNode]:
        """Update a node's properties"""
        async with self._lock:
            if node_id not in self._nodes:
                return None

            node = self._nodes[node_id]
            for key, value in updates.items():
                if hasattr(node, key):
                    setattr(node, key, value)

            node.updated_at = time.time()

            # Update in-memory graph
            if node_id in self._graph:
                self._graph.nodes[node_id].update(updates)

            # Persist
            await self._save_node(node)

            return node

    async def delete_node(self, node_id: str) -> bool:
        """Delete a node and its edges"""
        async with self._lock:
            if node_id not in self._nodes:
                return False

            self._graph.remove_node(node_id)
            del self._nodes[node_id]

            with self._db_lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM nodes WHERE node_id = ?", (node_id,))
                cursor.execute(
                    "DELETE FROM edges WHERE source_id = ? OR target_id = ?",
                    (node_id, node_id)
                )
                conn.commit()
                conn.close()

            return True

    # ═══════════════════════════════════════════════════════════════════════
    # EDGE OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════

    async def add_edge(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        properties: Optional[Dict[str, Any]] = None,
        weight: float = 1.0
    ) -> KnowledgeEdge:
        """Add an edge between nodes"""
        async with self._lock:
            edge_id = self._generate_edge_id(source_id, target_id, relation_type)

            if edge_id in self._edges:
                return self._edges[edge_id]

            # Ensure nodes exist
            if source_id not in self._nodes:
                await self.get_node(source_id)
            if target_id not in self._nodes:
                await self.get_node(target_id)

            edge = KnowledgeEdge(
                edge_id=edge_id,
                source_id=source_id,
                target_id=target_id,
                relation_type=relation_type,
                properties=properties or {},
                weight=weight
            )

            # Add to graph
            self._graph.add_edge(source_id, target_id, relation_type=relation_type, **edge.properties)
            self._edges[edge_id] = edge

            # Persist
            await self._save_edge(edge)

            return edge

    async def get_related_nodes(
        self,
        node_id: str,
        relation_type: Optional[str] = None,
        direction: str = "out"  # out, in, both
    ) -> List[Tuple[KnowledgeNode, str]]:
        """Get nodes related to the given node"""
        results = []

        if node_id not in self._nodes:
            return results

        related_ids = set()

        if direction in ("out", "both"):
            for _, target, data in self._graph.out_edges(node_id, data=True):
                if relation_type is None or data.get("relation_type") == relation_type:
                    related_ids.add((target, data.get("relation_type", "")))

        if direction in ("in", "both"):
            for source, _, data in self._graph.in_edges(node_id, data=True):
                if relation_type is None or data.get("relation_type") == relation_type:
                    related_ids.add((source, data.get("relation_type", "")))

        for rel_id, rel_type in related_ids:
            node = await self.get_node(rel_id)
            if node:
                results.append((node, rel_type))

        return results

    # ═══════════════════════════════════════════════════════════════════════
    # THREAT INTELLIGENCE
    # ═══════════════════════════════════════════════════════════════════════

    async def add_threat_intel(self, threat: ThreatIntel) -> None:
        """Add threat intelligence"""
        with self._db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO threat_intel
                (threat_id, threat_type, signature, severity, description,
                 mitigation, effectiveness_score, use_count, success_count,
                 metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                threat.threat_id,
                threat.threat_type,
                threat.signature,
                threat.severity,
                threat.description,
                threat.mitigation,
                threat.effectiveness_score,
                threat.use_count,
                threat.success_count,
                json.dumps(threat.metadata),
                threat.created_at
            ))
            conn.commit()
            conn.close()

    async def find_threats(
        self,
        threat_type: Optional[str] = None,
        signature: Optional[str] = None,
        min_effectiveness: float = 0.0
    ) -> List[ThreatIntel]:
        """Find threat intelligence matching criteria"""
        results = []

        with self._db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            query = "SELECT * FROM threat_intel WHERE 1=1"
            params = []

            if threat_type:
                query += " AND threat_type = ?"
                params.append(threat_type)

            if signature:
                query += " AND signature LIKE ?"
                params.append(f"%{signature}%")

            query += " AND effectiveness_score >= ?"
            params.append(min_effectiveness)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

        for row in rows:
            results.append(ThreatIntel(
                threat_id=row[0],
                threat_type=row[1],
                signature=row[2],
                severity=row[3],
                description=row[4],
                mitigation=row[5],
                effectiveness_score=row[6],
                use_count=row[7],
                success_count=row[8],
                metadata=json.loads(row[9]) if row[9] else {},
                created_at=row[10]
            ))

        return results

    async def record_threat_usage(self, threat_id: str, success: bool) -> None:
        """Record usage of a threat intel (for learning)"""
        with self._db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "UPDATE threat_intel SET use_count = use_count + 1 WHERE threat_id = ?",
                (threat_id,)
            )

            if success:
                cursor.execute(
                    "UPDATE threat_intel SET success_count = success_count + 1 WHERE threat_id = ?",
                    (threat_id,)
                )

            # Recalculate effectiveness
            cursor.execute("""
                UPDATE threat_intel
                SET effectiveness_score = CAST(success_count AS REAL) / use_count
                WHERE threat_id = ?
            """, (threat_id,))

            conn.commit()
            conn.close()

    # ═══════════════════════════════════════════════════════════════════════
    # PATTERN LEARNING
    # ═══════════════════════════════════════════════════════════════════════

    async def learn_pattern(
        self,
        pattern_type: str,
        pattern_data: str,
        context: str,
        success: bool,
        target_type: Optional[str] = None
    ) -> PatternRecord:
        """Learn a new pattern from scan results"""
        pattern_id = hashlib.sha256(
            f"{pattern_type}:{pattern_data}:{context}".encode()
        ).hexdigest()[:16]

        with self._db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if pattern exists
            cursor.execute(
                "SELECT * FROM patterns WHERE pattern_id = ?",
                (pattern_id,)
            )
            row = cursor.fetchone()

            if row:
                # Update existing pattern
                success_count = row[5] + (1 if success else 0)
                failure_count = row[6] + (0 if success else 1)

                cursor.execute("""
                    UPDATE patterns
                    SET success_count = ?, failure_count = ?, last_used = ?
                    WHERE pattern_id = ?
                """, (success_count, failure_count, time.time(), pattern_id))
            else:
                # Insert new pattern
                cursor.execute("""
                    INSERT INTO patterns
                    (pattern_id, pattern_type, pattern_data, context,
                     target_type, success_count, failure_count, last_used, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pattern_id,
                    pattern_type,
                    pattern_data,
                    context,
                    target_type,
                    1 if success else 0,
                    0 if success else 1,
                    time.time(),
                    time.time()
                ))

            conn.commit()
            conn.close()

        return await self.get_pattern(pattern_id)

    async def get_pattern(self, pattern_id: str) -> Optional[PatternRecord]:
        """Get a pattern by ID"""
        with self._db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM patterns WHERE pattern_id = ?",
                (pattern_id,)
            )
            row = cursor.fetchone()
            conn.close()

        if row:
            return PatternRecord(
                pattern_id=row[0],
                pattern_type=row[1],
                pattern_data=row[2],
                context=row[3],
                target_type=row[4],
                success_count=row[5],
                failure_count=row[6],
                last_used=row[7],
                created_at=row[8]
            )
        return None

    async def find_patterns(
        self,
        pattern_type: Optional[str] = None,
        min_effectiveness: float = 0.0,
        limit: int = 100
    ) -> List[PatternRecord]:
        """Find patterns matching criteria"""
        results = []

        with self._db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            query = "SELECT * FROM patterns WHERE 1=1"
            params = []

            if pattern_type:
                query += " AND pattern_type = ?"
                params.append(pattern_type)

            # Calculate effectiveness on-the-fly
            query += " AND (CAST(success_count AS REAL) / NULLIF(success_count + failure_count, 0)) >= ?"
            params.append(min_effectiveness)

            query += " ORDER BY last_used DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

        for row in rows:
            results.append(PatternRecord(
                pattern_id=row[0],
                pattern_type=row[1],
                pattern_data=row[2],
                context=row[3],
                target_type=row[4],
                success_count=row[5],
                failure_count=row[6],
                last_used=row[7],
                created_at=row[8]
            ))

        return results

    # ═══════════════════════════════════════════════════════════════════════
    # SESSION MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════

    async def create_session(
        self,
        session_id: str,
        target: str,
        scan_type: str
    ) -> SessionMemory:
        """Create a new session"""
        session = SessionMemory(
            session_id=session_id,
            target=target,
            scan_type=scan_type
        )

        with self._db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sessions
                (session_id, target, scan_type, data, endpoints,
                 files_found, vulnerabilities, bypass_attempts, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session.session_id,
                session.target,
                session.scan_type,
                json.dumps(session.data),
                json.dumps(session.endpoints),
                json.dumps(session.files_found),
                json.dumps(session.vulnerabilities),
                json.dumps(session.bypass_attempts),
                session.created_at,
                session.updated_at
            ))
            conn.commit()
            conn.close()

        return session

    async def update_session(self, session: SessionMemory) -> None:
        """Update session data"""
        session.updated_at = time.time()

        with self._db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE sessions
                SET data = ?, endpoints = ?, files_found = ?,
                    vulnerabilities = ?, bypass_attempts = ?, updated_at = ?
                WHERE session_id = ?
            """, (
                json.dumps(session.data),
                json.dumps(session.endpoints),
                json.dumps(session.files_found),
                json.dumps(session.vulnerabilities),
                json.dumps(session.bypass_attempts),
                session.updated_at,
                session.session_id
            ))
            conn.commit()
            conn.close()

    async def get_session(self, session_id: str) -> Optional[SessionMemory]:
        """Get session by ID"""
        with self._db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM sessions WHERE session_id = ?",
                (session_id,)
            )
            row = cursor.fetchone()
            conn.close()

        if row:
            return SessionMemory(
                session_id=row[0],
                target=row[1],
                scan_type=row[2],
                data=json.loads(row[3]) if row[3] else {},
                endpoints=json.loads(row[4]) if row[4] else [],
                files_found=json.loads(row[5]) if row[5] else [],
                vulnerabilities=json.loads(row[6]) if row[6] else [],
                bypass_attempts=json.loads(row[7]) if row[7] else [],
                created_at=row[8],
                updated_at=row[9]
            )
        return None

    # ═══════════════════════════════════════════════════════════════════════
    # GRAPH ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════

    async def find_shortest_path(
        self,
        source_id: str,
        target_id: str
    ) -> Optional[List[str]]:
        """Find shortest path between two nodes"""
        try:
            path = nx.shortest_path(self._graph, source_id, target_id)
            return path
        except nx.NetworkXNoPath:
            return None

    async def get_central_nodes(self, limit: int = 10) -> List[Tuple[str, float]]:
        """Get most central nodes (by betweenness centrality)"""
        centrality = nx.betweenness_centrality(self._graph)
        sorted_cent = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        return sorted_cent[:limit]

    async def get_subgraph(
        self,
        node_ids: List[str],
        depth: int = 1
    ) -> nx.MultiDiGraph:
        """Get subgraph around given nodes"""
        subgraph_nodes = set(node_ids)

        for node_id in node_ids:
            # Add nodes within specified depth
            for _ in range(depth):
                neighbors = list(self._graph.predecessors(node_id)) + \
                           list(self._graph.successors(node_id))
                subgraph_nodes.update(neighbors)

        return self._graph.subgraph(subgraph_nodes).copy()

    # ═══════════════════════════════════════════════════════════════════════
    # UTILITY METHODS
    # ═══════════════════════════════════════════════════════════════════════

    def _generate_node_id(self, node_type: str, label: str) -> str:
        """Generate unique node ID"""
        content = f"{node_type}:{label}:{time.time()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _generate_edge_id(
        self,
        source_id: str,
        target_id: str,
        relation_type: str
    ) -> str:
        """Generate unique edge ID"""
        content = f"{source_id}:{target_id}:{relation_type}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    async def _save_node(self, node: KnowledgeNode) -> None:
        """Persist node to database"""
        with self._db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO nodes
                (node_id, node_type, label, properties, metadata,
                 created_at, updated_at, confidence, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                node.node_id,
                node.node_type,
                node.label,
                json.dumps(node.properties),
                json.dumps(node.metadata),
                node.created_at,
                node.updated_at,
                node.confidence,
                json.dumps(list(node.tags))
            ))
            conn.commit()
            conn.close()

    async def _save_edge(self, edge: KnowledgeEdge) -> None:
        """Persist edge to database"""
        with self._db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO edges
                (edge_id, source_id, target_id, relation_type,
                 properties, weight, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                edge.edge_id,
                edge.source_id,
                edge.target_id,
                edge.relation_type,
                json.dumps(edge.properties),
                edge.weight,
                edge.created_at
            ))
            conn.commit()
            conn.close()

    async def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge graph statistics"""
        with self._db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            node_count = cursor.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
            edge_count = cursor.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
            threat_count = cursor.execute("SELECT COUNT(*) FROM threat_intel").fetchone()[0]
            pattern_count = cursor.execute("SELECT COUNT(*) FROM patterns").fetchone()[0]
            session_count = cursor.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]

            # Node types distribution
            cursor.execute("SELECT node_type, COUNT(*) FROM nodes GROUP BY node_type")
            type_distribution = dict(cursor.fetchall())

            # Most effective threats
            cursor.execute("""
                SELECT signature, effectiveness_score
                FROM threat_intel
                ORDER BY effectiveness_score DESC
                LIMIT 5
            """)
            top_threats = [{"signature": r[0], "score": r[1]} for r in cursor.fetchall()]

            conn.close()

        return {
            "nodes": node_count,
            "edges": edge_count,
            "threats": threat_count,
            "patterns": pattern_count,
            "sessions": session_count,
            "type_distribution": type_distribution,
            "top_threats": top_threats
        }

    async def cleanup(self) -> None:
        """Cleanup resources"""
        self._nodes.clear()
        self._edges.clear()
        self._graph.clear()
