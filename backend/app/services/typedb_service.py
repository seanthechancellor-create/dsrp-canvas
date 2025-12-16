"""
TypeDB Service Layer

Provides database operations for the DSRP knowledge graph using TypeDB 3.x.
Handles connections, queries, and CRUD operations for all entity types.
"""

import os
import logging
from datetime import datetime
from typing import Any, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# TypeDB connection settings
TYPEDB_HOST = os.getenv("TYPEDB_HOST", "127.0.0.1")
TYPEDB_PORT = os.getenv("TYPEDB_PORT", "1729")
TYPEDB_ADDRESS = f"{TYPEDB_HOST}:{TYPEDB_PORT}"
TYPEDB_DATABASE = os.getenv("TYPEDB_DATABASE", "dsrp_canvas")
TYPEDB_USERNAME = os.getenv("TYPEDB_USERNAME", "admin")
TYPEDB_PASSWORD = os.getenv("TYPEDB_PASSWORD", "password")


class TypeDBService:
    """Service for TypeDB 3.x database operations."""

    def __init__(self):
        self._driver = None

    @property
    def driver(self):
        """Lazy-load the TypeDB driver."""
        if self._driver is None:
            self._driver = self._create_driver()
        return self._driver

    def _create_driver(self):
        """Create a TypeDB driver connection."""
        try:
            from typedb.driver import TypeDB, Credentials, DriverOptions

            creds = Credentials(TYPEDB_USERNAME, TYPEDB_PASSWORD)
            opts = DriverOptions(is_tls_enabled=False)
            driver = TypeDB.driver(TYPEDB_ADDRESS, creds, opts)
            logger.info(f"Connected to TypeDB at {TYPEDB_ADDRESS}")
            return driver
        except ImportError:
            logger.error("TypeDB driver not installed. Run: pip install typedb-driver")
            return None
        except Exception as e:
            logger.error(f"Failed to connect to TypeDB: {e}")
            return None

    @contextmanager
    def read_transaction(self):
        """Context manager for read transactions."""
        if not self.driver:
            raise RuntimeError("TypeDB driver not available")

        from typedb.driver import TransactionType

        tx = self.driver.transaction(TYPEDB_DATABASE, TransactionType.READ)
        try:
            yield tx
        finally:
            tx.close()

    @contextmanager
    def write_transaction(self):
        """Context manager for write transactions."""
        if not self.driver:
            raise RuntimeError("TypeDB driver not available")

        from typedb.driver import TransactionType

        tx = self.driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE)
        try:
            yield tx
            tx.commit()
        except Exception:
            # Transaction auto-rolls back on close without commit
            raise
        finally:
            tx.close()

    def close(self):
        """Close the driver connection."""
        if self._driver:
            self._driver.close()
            self._driver = None

    # =========================================================================
    # Source Operations
    # =========================================================================

    async def create_source(
        self,
        source_id: str,
        source_type: str,
        file_path: str,
        original_filename: str,
    ) -> dict:
        """Create a new source entity in TypeDB."""
        now = datetime.utcnow().isoformat()

        # TypeDB 3.x insert query (using underscored attribute names to match schema)
        query = f"""
            insert
            $s isa source,
                has source_id "{source_id}",
                has source_type "{source_type}",
                has file_path "{file_path}",
                has original_filename "{original_filename}",
                has created_at {now};
        """

        with self.write_transaction() as tx:
            tx.query(query).resolve()

        return {
            "id": source_id,
            "source_type": source_type,
            "file_path": file_path,
            "original_filename": original_filename,
            "created_at": now,
        }

    async def update_source_text(self, source_id: str, extracted_text: str) -> bool:
        """Update a source with extracted text."""
        # Escape quotes in text
        escaped_text = extracted_text.replace('"', '\\"').replace("\n", "\\n")

        query = f"""
            match
            $s isa source, has source_id "{source_id}";
            insert
            $s has extracted_text "{escaped_text}";
        """

        try:
            with self.write_transaction() as tx:
                tx.query(query).resolve()
            return True
        except Exception as e:
            logger.error(f"Failed to update source text: {e}")
            return False

    async def get_source(self, source_id: str) -> Optional[dict]:
        """Get a source by ID."""
        # TypeDB 3.x fetch query for JSON output
        query = f"""
            match
            $s isa source, has source_id "{source_id}";
            $s has source_type $type,
               has file_path $path,
               has original_filename $filename,
               has created_at $created;
            fetch {{
                "id": $s.source_id,
                "source_type": $type,
                "file_path": $path,
                "original_filename": $filename,
                "created_at": $created
            }};
        """

        try:
            with self.read_transaction() as tx:
                answer = tx.query(query).resolve()
                for doc in answer.as_concept_documents():
                    return doc
        except Exception as e:
            logger.error(f"Failed to get source: {e}")

        return None

    async def get_source_text(self, source_id: str) -> Optional[str]:
        """Get extracted text for a source."""
        query = f"""
            match
            $s isa source, has source_id "{source_id}",
               has extracted_text $text;
            fetch {{ "text": $text }};
        """

        try:
            with self.read_transaction() as tx:
                answer = tx.query(query).resolve()
                for doc in answer.as_concept_documents():
                    return doc.get("text")
        except Exception as e:
            logger.debug(f"No extracted text for source {source_id}: {e}")

        return None

    async def list_sources(self, limit: int = 50) -> list[dict]:
        """List all sources."""
        query = f"""
            match
            $s isa source,
               has source_id $id,
               has source_type $type,
               has original_filename $filename,
               has created_at $created;
            fetch {{
                "id": $id,
                "source_type": $type,
                "original_filename": $filename,
                "created_at": $created
            }};
            limit {limit};
        """

        sources = []
        try:
            with self.read_transaction() as tx:
                answer = tx.query(query).resolve()
                for doc in answer.as_concept_documents():
                    sources.append(doc)
        except Exception as e:
            logger.error(f"Failed to list sources: {e}")

        return sources

    # =========================================================================
    # Concept Operations
    # =========================================================================

    async def create_concept(
        self,
        concept_id: str,
        name: str,
        description: Optional[str] = None,
    ) -> dict:
        """Create a new concept entity."""
        now = datetime.utcnow().isoformat()

        desc_clause = f', has description "{description}"' if description else ""

        query = f"""
            insert
            $c isa dsrp_concept,
                has concept_id "{concept_id}",
                has name "{name}"{desc_clause},
                has created_at {now},
                has updated_at {now};
        """

        with self.write_transaction() as tx:
            tx.query(query).resolve()

        return {
            "id": concept_id,
            "name": name,
            "description": description,
            "created_at": now,
            "updated_at": now,
        }

    async def get_concept(self, concept_id: str) -> Optional[dict]:
        """Get a concept by ID."""
        query = f"""
            match
            $c isa dsrp_concept, has concept_id "{concept_id}";
            $c has name $name, has created_at $created, has updated_at $updated;
            fetch {{
                "id": $c.concept_id,
                "name": $name,
                "created_at": $created,
                "updated_at": $updated
            }};
        """

        try:
            with self.read_transaction() as tx:
                answer = tx.query(query).resolve()
                for doc in answer.as_concept_documents():
                    # Try to get optional description
                    doc["description"] = await self._get_concept_description(concept_id)
                    return doc
        except Exception as e:
            logger.error(f"Failed to get concept: {e}")

        return None

    async def _get_concept_description(self, concept_id: str) -> Optional[str]:
        """Get concept description (optional attribute)."""
        query = f"""
            match
            $c isa dsrp_concept, has concept_id "{concept_id}", has description $desc;
            fetch {{ "description": $desc }};
        """

        try:
            with self.read_transaction() as tx:
                answer = tx.query(query).resolve()
                for doc in answer.as_concept_documents():
                    return doc.get("description")
        except Exception:
            pass
        return None

    async def get_concept_by_name(self, name: str) -> Optional[dict]:
        """Get a concept by name."""
        query = f"""
            match
            $c isa dsrp_concept, has name "{name}";
            $c has concept_id $id, has created_at $created, has updated_at $updated;
            fetch {{
                "id": $id,
                "name": $c.name,
                "created_at": $created,
                "updated_at": $updated
            }};
        """

        try:
            with self.read_transaction() as tx:
                answer = tx.query(query).resolve()
                for doc in answer.as_concept_documents():
                    return doc
        except Exception as e:
            logger.debug(f"Concept not found by name '{name}': {e}")

        return None

    async def list_concepts(self, limit: int = 50, offset: int = 0) -> list[dict]:
        """List all concepts with pagination."""
        query = f"""
            match
            $c isa dsrp_concept,
               has concept_id $id,
               has name $name,
               has created_at $created,
               has updated_at $updated;
            fetch {{
                "id": $id,
                "name": $name,
                "created_at": $created,
                "updated_at": $updated
            }};
            offset {offset};
            limit {limit};
        """

        concepts = []
        try:
            with self.read_transaction() as tx:
                answer = tx.query(query).resolve()
                for doc in answer.as_concept_documents():
                    concepts.append(doc)
        except Exception as e:
            logger.error(f"Failed to list concepts: {e}")

        return concepts

    async def delete_concept(self, concept_id: str) -> bool:
        """Delete a concept by ID."""
        query = f"""
            match
            $c isa dsrp_concept, has concept_id "{concept_id}";
            delete
            $c isa dsrp_concept;
        """

        try:
            with self.write_transaction() as tx:
                tx.query(query).resolve()
            return True
        except Exception as e:
            logger.error(f"Failed to delete concept: {e}")
            return False

    # =========================================================================
    # DSRP Analysis Operations
    # =========================================================================

    async def create_analysis(
        self,
        analysis_id: str,
        concept_id: str,
        pattern_type: str,
        move_type: str,
        reasoning: str,
        confidence_score: float,
        source_id: Optional[str] = None,
    ) -> dict:
        """Create a DSRP analysis and link it to a concept."""
        now = datetime.utcnow().isoformat()
        escaped_reasoning = reasoning.replace('"', '\\"')

        # Insert the analysis entity
        insert_query = f"""
            insert
            $a isa dsrp_analysis,
                has analysis_id "{analysis_id}",
                has pattern_type "{pattern_type}",
                has move_type "{move_type}",
                has reasoning "{escaped_reasoning}",
                has confidence_score {confidence_score},
                has created_at {now};
        """

        with self.write_transaction() as tx:
            tx.query(insert_query).resolve()

        # Link analysis to concept
        link_query = f"""
            match
            $c isa dsrp_concept, has concept_id "{concept_id}";
            $a isa dsrp_analysis, has analysis_id "{analysis_id}";
            insert
            (subject: $c, result: $a) isa analysis_rel,
                has analysis_link_id "{analysis_id}_link";
        """

        try:
            with self.write_transaction() as tx:
                tx.query(link_query).resolve()
        except Exception as e:
            logger.warning(f"Failed to link analysis to concept: {e}")

        return {
            "id": analysis_id,
            "concept_id": concept_id,
            "pattern_type": pattern_type,
            "move_type": move_type,
            "reasoning": reasoning,
            "confidence_score": confidence_score,
            "created_at": now,
        }

    async def get_analyses_for_concept(self, concept_id: str) -> list[dict]:
        """Get all analyses for a concept."""
        query = f"""
            match
            $c isa dsrp_concept, has concept_id "{concept_id}";
            (subject: $c, result: $a) isa analysis_rel;
            $a has analysis_id $aid,
               has pattern_type $pattern,
               has move_type $move,
               has reasoning $reason,
               has confidence_score $conf,
               has created_at $created;
            fetch {{
                "id": $aid,
                "pattern": $pattern,
                "move": $move,
                "reasoning": $reason,
                "confidence": $conf,
                "created_at": $created
            }};
        """

        analyses = []
        try:
            with self.read_transaction() as tx:
                answer = tx.query(query).resolve()
                for doc in answer.as_concept_documents():
                    analyses.append(doc)
        except Exception as e:
            logger.error(f"Failed to get analyses for concept: {e}")

        return analyses

    # =========================================================================
    # DSRP Relation Operations
    # =========================================================================

    async def create_distinction(
        self,
        distinction_id: str,
        identity_concept_id: str,
        other_concept_id: str,
        label: Optional[str] = None,
    ) -> dict:
        """Create a distinction relation between two concepts."""
        label_clause = f', has distinction_label "{label}"' if label else ""

        query = f"""
            match
            $i isa dsrp_concept, has concept_id "{identity_concept_id}";
            $o isa dsrp_concept, has concept_id "{other_concept_id}";
            insert
            (identity: $i, other: $o) isa distinction,
                has distinction_id "{distinction_id}"{label_clause};
        """

        with self.write_transaction() as tx:
            tx.query(query).resolve()

        return {
            "id": distinction_id,
            "identity": identity_concept_id,
            "other": other_concept_id,
            "label": label,
        }

    async def create_system_structure(
        self,
        system_id: str,
        whole_concept_id: str,
        part_concept_id: str,
        label: Optional[str] = None,
    ) -> dict:
        """Create a system_structure relation (part/whole)."""
        label_clause = f', has system_label "{label}"' if label else ""

        query = f"""
            match
            $w isa dsrp_concept, has concept_id "{whole_concept_id}";
            $p isa dsrp_concept, has concept_id "{part_concept_id}";
            insert
            (whole: $w, part: $p) isa system_structure,
                has system_id "{system_id}"{label_clause};
        """

        with self.write_transaction() as tx:
            tx.query(query).resolve()

        return {
            "id": system_id,
            "whole": whole_concept_id,
            "part": part_concept_id,
            "label": label,
        }

    async def create_relationship_link(
        self,
        relationship_id: str,
        action_concept_id: str,
        reaction_concept_id: str,
        relationship_type: Optional[str] = None,
        label: Optional[str] = None,
    ) -> dict:
        """Create a relationship_link relation (action/reaction)."""
        type_clause = f', has relationship_type "{relationship_type}"' if relationship_type else ""
        label_clause = f', has relationship_label "{label}"' if label else ""

        query = f"""
            match
            $a isa dsrp_concept, has concept_id "{action_concept_id}";
            $r isa dsrp_concept, has concept_id "{reaction_concept_id}";
            insert
            (action: $a, reaction: $r) isa relationship_link,
                has relationship_id "{relationship_id}"{type_clause}{label_clause};
        """

        with self.write_transaction() as tx:
            tx.query(query).resolve()

        return {
            "id": relationship_id,
            "action": action_concept_id,
            "reaction": reaction_concept_id,
            "relationship_type": relationship_type,
            "label": label,
        }

    async def create_perspective_view(
        self,
        perspective_id: str,
        point_concept_id: str,
        view_concept_id: str,
        label: Optional[str] = None,
    ) -> dict:
        """Create a perspective_view relation (point/view)."""
        label_clause = f', has perspective_label "{label}"' if label else ""

        query = f"""
            match
            $p isa dsrp_concept, has concept_id "{point_concept_id}";
            $v isa dsrp_concept, has concept_id "{view_concept_id}";
            insert
            (point: $p, view: $v) isa perspective_view,
                has perspective_id "{perspective_id}"{label_clause};
        """

        with self.write_transaction() as tx:
            tx.query(query).resolve()

        return {
            "id": perspective_id,
            "point": point_concept_id,
            "view": view_concept_id,
            "label": label,
        }

    async def get_concept_relations(self, concept_id: str) -> dict:
        """Get all DSRP relations for a concept."""
        relations = {
            "distinctions": [],
            "systems": [],
            "relationships": [],
            "perspectives": [],
        }

        # Get distinctions where concept is identity
        dist_query = f"""
            match
            $c isa dsrp_concept, has concept_id "{concept_id}";
            (identity: $c, other: $o) isa distinction, has distinction_id $did;
            $o has name $oname;
            fetch {{
                "id": $did,
                "role": "identity",
                "other_name": $oname
            }};
        """

        try:
            with self.read_transaction() as tx:
                answer = tx.query(dist_query).resolve()
                for doc in answer.as_concept_documents():
                    relations["distinctions"].append(doc)
        except Exception as e:
            logger.debug(f"Error getting distinctions: {e}")

        # Get system structures where concept is whole
        sys_query = f"""
            match
            $c isa dsrp_concept, has concept_id "{concept_id}";
            (whole: $c, part: $p) isa system_structure, has system_id $sid;
            $p has name $pname;
            fetch {{
                "id": $sid,
                "role": "whole",
                "part_name": $pname
            }};
        """

        try:
            with self.read_transaction() as tx:
                answer = tx.query(sys_query).resolve()
                for doc in answer.as_concept_documents():
                    relations["systems"].append(doc)
        except Exception as e:
            logger.debug(f"Error getting systems: {e}")

        # Get relationships where concept is action
        rel_query = f"""
            match
            $c isa dsrp_concept, has concept_id "{concept_id}";
            (action: $c, reaction: $r) isa relationship_link, has relationship_id $rid;
            $r has name $rname;
            fetch {{
                "id": $rid,
                "role": "action",
                "reaction_name": $rname
            }};
        """

        try:
            with self.read_transaction() as tx:
                answer = tx.query(rel_query).resolve()
                for doc in answer.as_concept_documents():
                    relations["relationships"].append(doc)
        except Exception as e:
            logger.debug(f"Error getting relationships: {e}")

        # Get perspectives where concept is point
        persp_query = f"""
            match
            $c isa dsrp_concept, has concept_id "{concept_id}";
            (point: $c, view: $v) isa perspective_view, has perspective_id $pid;
            $v has name $vname;
            fetch {{
                "id": $pid,
                "role": "point",
                "view_name": $vname
            }};
        """

        try:
            with self.read_transaction() as tx:
                answer = tx.query(persp_query).resolve()
                for doc in answer.as_concept_documents():
                    relations["perspectives"].append(doc)
        except Exception as e:
            logger.debug(f"Error getting perspectives: {e}")

        return relations


    def is_connected(self) -> bool:
        """Check if TypeDB connection is available."""
        try:
            if self.driver is None:
                return False
            # Try to list databases to verify connection
            databases = self.driver.databases.all()
            return True
        except Exception as e:
            logger.debug(f"TypeDB connection check failed: {e}")
            return False

    async def get_graph_stats(self) -> dict:
        """Get statistics about the knowledge graph."""
        stats = {
            "concepts": 0,
            "analyses": 0,
            "distinctions": 0,
            "systems": 0,
            "relationships": 0,
            "perspectives": 0,
            "sources": 0,
        }

        queries = {
            "concepts": "match $c isa dsrp_concept; reduce $count = count;",
            "analyses": "match $a isa dsrp_analysis; reduce $count = count;",
            "distinctions": "match $d isa distinction; reduce $count = count;",
            "systems": "match $s isa system_structure; reduce $count = count;",
            "relationships": "match $r isa relationship_link; reduce $count = count;",
            "perspectives": "match $p isa perspective_view; reduce $count = count;",
            "sources": "match $s isa source; reduce $count = count;",
        }

        for key, query in queries.items():
            try:
                with self.read_transaction() as tx:
                    answer = tx.query(query).resolve()
                    # TypeDB 3.x returns aggregates differently
                    for row in answer.as_concept_rows():
                        stats[key] = row.get("count") or 0
                        break
            except Exception as e:
                logger.debug(f"Error getting {key} count: {e}")

        return stats

    async def export_concept_graph(self, limit: int = 100) -> dict:
        """Export the concept graph for visualization."""
        nodes = []
        edges = []

        # Get all concepts with their IDs and names
        concept_query = f"""
            match
            $c isa dsrp_concept,
               has concept_id $id,
               has name $name;
            fetch {{
                "id": $id,
                "name": $name
            }};
            limit {limit};
        """

        concept_ids = set()
        try:
            with self.read_transaction() as tx:
                answer = tx.query(concept_query).resolve()
                for doc in answer.as_concept_documents():
                    nodes.append({
                        "id": doc["id"],
                        "label": doc["name"],
                        "type": "concept",
                    })
                    concept_ids.add(doc["id"])
        except Exception as e:
            logger.error(f"Error exporting concepts: {e}")

        # Get distinctions
        dist_query = """
            match
            (identity: $i, other: $o) isa distinction, has distinction_id $did;
            $i has concept_id $iid;
            $o has concept_id $oid;
            fetch {
                "id": $did,
                "source": $iid,
                "target": $oid,
                "type": "distinction"
            };
        """
        try:
            with self.read_transaction() as tx:
                answer = tx.query(dist_query).resolve()
                for doc in answer.as_concept_documents():
                    edges.append({
                        "id": doc["id"],
                        "source": doc["source"],
                        "target": doc["target"],
                        "type": "D",
                        "label": "identity/other",
                    })
        except Exception as e:
            logger.debug(f"Error exporting distinctions: {e}")

        # Get system structures
        sys_query = """
            match
            (whole: $w, part: $p) isa system_structure, has system_id $sid;
            $w has concept_id $wid;
            $p has concept_id $pid;
            fetch {
                "id": $sid,
                "source": $wid,
                "target": $pid,
                "type": "system"
            };
        """
        try:
            with self.read_transaction() as tx:
                answer = tx.query(sys_query).resolve()
                for doc in answer.as_concept_documents():
                    edges.append({
                        "id": doc["id"],
                        "source": doc["source"],
                        "target": doc["target"],
                        "type": "S",
                        "label": "part/whole",
                    })
        except Exception as e:
            logger.debug(f"Error exporting systems: {e}")

        # Get relationships
        rel_query = """
            match
            (action: $a, reaction: $r) isa relationship_link, has relationship_id $rid;
            $a has concept_id $aid;
            $r has concept_id $rid2;
            fetch {
                "id": $rid,
                "source": $aid,
                "target": $rid2,
                "type": "relationship"
            };
        """
        try:
            with self.read_transaction() as tx:
                answer = tx.query(rel_query).resolve()
                for doc in answer.as_concept_documents():
                    edges.append({
                        "id": doc["id"],
                        "source": doc["source"],
                        "target": doc["target"],
                        "type": "R",
                        "label": "action/reaction",
                    })
        except Exception as e:
            logger.debug(f"Error exporting relationships: {e}")

        # Get perspectives
        persp_query = """
            match
            (point: $p, view: $v) isa perspective_view, has perspective_id $pid;
            $p has concept_id $pid2;
            $v has concept_id $vid;
            fetch {
                "id": $pid,
                "source": $pid2,
                "target": $vid,
                "type": "perspective"
            };
        """
        try:
            with self.read_transaction() as tx:
                answer = tx.query(persp_query).resolve()
                for doc in answer.as_concept_documents():
                    edges.append({
                        "id": doc["id"],
                        "source": doc["source"],
                        "target": doc["target"],
                        "type": "P",
                        "label": "point/view",
                    })
        except Exception as e:
            logger.debug(f"Error exporting perspectives: {e}")

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "node_count": len(nodes),
                "edge_count": len(edges),
            },
        }


# Singleton instance
_typedb_service: Optional[TypeDBService] = None


def get_typedb_service() -> TypeDBService:
    """Get the singleton TypeDB service instance."""
    global _typedb_service
    if _typedb_service is None:
        _typedb_service = TypeDBService()
    return _typedb_service
