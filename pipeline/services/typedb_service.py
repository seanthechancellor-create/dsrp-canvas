"""
TypeDB Service for DSRP Knowledge Pipeline

This service handles storing structured DSRP knowledge in TypeDB.
TypeDB is a strongly-typed database perfect for knowledge graphs.

The DSRP patterns map to TypeDB relations:
- Distinctions (D): distinction relation with identity/other roles
- Systems (S): system_structure relation with part/whole roles
- Relationships (R): relationship_link relation with action/reaction roles
- Perspectives (P): perspective_view relation with point/view roles
"""

import os
import logging
import uuid
from datetime import datetime
from typing import Optional
from typedb.driver import TypeDB, Credentials, TransactionType, DriverOptions

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TypeDBService:
    """
    Handles all TypeDB operations for storing DSRP semantic structure.

    This is the "Semantic Memory" - the structured knowledge graph that
    represents the logical relationships extracted from text.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        """
        Initialize connection to TypeDB.

        Args:
            host: TypeDB server host (default: TYPEDB_HOST env or localhost)
            port: TypeDB server port (default: TYPEDB_PORT env or 1729)
            database: Database name (default: TYPEDB_DATABASE env or dsrp_483)
            username: Username for auth (default: TYPEDB_USERNAME env or admin)
            password: Password for auth (default: TYPEDB_PASSWORD env or password)
        """
        self.host = host or os.getenv("TYPEDB_HOST", "localhost")
        self.port = port or int(os.getenv("TYPEDB_PORT", "1729"))
        self.database = database or os.getenv("TYPEDB_DATABASE", "dsrp_483")
        self.username = username or os.getenv("TYPEDB_USERNAME", "admin")
        self.password = password or os.getenv("TYPEDB_PASSWORD", "password")

        self.driver = None
        self._connect()

    def _connect(self):
        """Establish connection to TypeDB."""
        try:
            address = f"{self.host}:{self.port}"
            logger.info(f"Connecting to TypeDB at: {address}")

            # TypeDB 3.x uses credentials and options
            credentials = Credentials(self.username, self.password)
            options = DriverOptions(is_tls_enabled=False)

            self.driver = TypeDB.driver(address, credentials, options)
            logger.info(f"Connected to TypeDB, using database: {self.database}")

        except Exception as e:
            logger.error(f"Failed to connect to TypeDB: {e}")
            self.driver = None

    def _generate_id(self) -> str:
        """Generate a unique ID for entities."""
        return str(uuid.uuid4())

    def is_connected(self) -> bool:
        """Check if we have a valid connection."""
        return self.driver is not None

    def store_concept(
        self,
        name: str,
        description: Optional[str] = None,
        source_chunk_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Store a concept in TypeDB.

        A concept is a "thing" - any idea, entity, or notion extracted from text.

        Args:
            name: The name/label of the concept
            description: Optional description
            source_chunk_id: ID of the chunk this concept came from

        Returns:
            The concept's thing_id if successful, None otherwise
        """
        if not self.is_connected():
            logger.warning("TypeDB not connected, skipping concept storage")
            return None

        concept_id = self._generate_id()

        try:
            with self.driver.transaction(self.database, TransactionType.WRITE) as tx:
                # Check if concept with this name already exists
                check_query = f'''
                    match $c isa concept, has name "{self._escape(name)}";
                    get $c;
                '''
                results = list(tx.query(check_query).resolve().as_concept_rows())

                if results:
                    # Concept exists, return existing ID
                    existing = results[0]
                    existing_id = existing.get("c").get_has("thing_id")
                    for attr in existing_id:
                        logger.debug(f"Concept '{name}' already exists")
                        return attr.get_value()

                # Create new concept
                insert_query = f'''
                    insert $c isa concept,
                        has thing_id "{concept_id}",
                        has name "{self._escape(name)}",
                        has created_at {datetime.utcnow().isoformat()}Z;
                '''

                if description:
                    insert_query = f'''
                        insert $c isa concept,
                            has thing_id "{concept_id}",
                            has name "{self._escape(name)}",
                            has description "{self._escape(description)}",
                            has created_at {datetime.utcnow().isoformat()}Z;
                    '''

                tx.query(insert_query).resolve()
                tx.commit()

                logger.debug(f"Stored concept: {name} ({concept_id})")
                return concept_id

        except Exception as e:
            logger.error(f"Error storing concept '{name}': {e}")
            return None

    def get_concept_id_by_name(self, name: str) -> Optional[str]:
        """
        Get a concept's ID by its name.

        Args:
            name: The concept name to look up

        Returns:
            The concept's thing_id if found, None otherwise
        """
        if not self.is_connected():
            return None

        try:
            with self.driver.transaction(self.database, TransactionType.READ) as tx:
                query = f'''
                    match $c isa concept, has name "{self._escape(name)}", has thing_id $id;
                    get $id;
                '''
                results = list(tx.query(query).resolve().as_concept_rows())

                if results:
                    return results[0].get("id").get_value()
                return None

        except Exception as e:
            logger.error(f"Error looking up concept '{name}': {e}")
            return None

    def store_distinction(
        self,
        identity_name: str,
        other_name: str,
        boundary: Optional[str] = None,
        confidence: float = 0.85,
        source_chunk_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Store a Distinction (D) pattern in TypeDB.

        Distinctions define what something IS vs what it IS NOT.

        Args:
            identity_name: What the thing IS
            other_name: What it is NOT / what it's distinguished from
            boundary: The criteria separating identity from other
            confidence: Confidence score (0-1)
            source_chunk_id: Source chunk for traceability

        Returns:
            The distinction_id if successful
        """
        if not self.is_connected():
            logger.warning("TypeDB not connected")
            return None

        # Ensure both concepts exist
        identity_id = self.store_concept(identity_name)
        other_id = self.store_concept(other_name)

        if not identity_id or not other_id:
            logger.error("Failed to create concepts for distinction")
            return None

        distinction_id = self._generate_id()

        try:
            with self.driver.transaction(self.database, TransactionType.WRITE) as tx:
                query = f'''
                    match
                        $identity isa concept, has thing_id "{identity_id}";
                        $other isa concept, has thing_id "{other_id}";
                    insert
                        $d (identity: $identity, other: $other) isa distinction,
                            has distinction_id "{distinction_id}",
                            has confidence {confidence};
                '''

                tx.query(query).resolve()
                tx.commit()

                logger.info(f"Stored distinction: '{identity_name}' vs '{other_name}'")
                return distinction_id

        except Exception as e:
            logger.error(f"Error storing distinction: {e}")
            return None

    def store_system(
        self,
        whole_name: str,
        part_names: list[str],
        confidence: float = 0.85,
        source_chunk_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Store a System (S) pattern in TypeDB.

        Systems define part/whole relationships.

        Args:
            whole_name: The containing system
            part_names: List of parts that make up the whole
            confidence: Confidence score (0-1)
            source_chunk_id: Source chunk for traceability

        Returns:
            The system_id if successful
        """
        if not self.is_connected():
            logger.warning("TypeDB not connected")
            return None

        # Ensure whole concept exists
        whole_id = self.store_concept(whole_name)
        if not whole_id:
            logger.error(f"Failed to create whole concept: {whole_name}")
            return None

        system_id = self._generate_id()

        try:
            # Store each part relationship
            for part_name in part_names:
                part_id = self.store_concept(part_name)
                if not part_id:
                    continue

                with self.driver.transaction(self.database, TransactionType.WRITE) as tx:
                    query = f'''
                        match
                            $whole isa concept, has thing_id "{whole_id}";
                            $part isa concept, has thing_id "{part_id}";
                        insert
                            $s (whole: $whole, part: $part) isa system_structure,
                                has system_id "{self._generate_id()}",
                                has confidence {confidence};
                    '''
                    tx.query(query).resolve()
                    tx.commit()

            logger.info(f"Stored system: '{whole_name}' with {len(part_names)} parts")
            return system_id

        except Exception as e:
            logger.error(f"Error storing system: {e}")
            return None

    def store_relationship(
        self,
        action_name: str,
        reaction_name: str,
        relationship_type: str = "causal",
        strength: float = 0.75,
        confidence: float = 0.85,
        source_chunk_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Store a Relationship (R) pattern in TypeDB.

        Relationships define action/reaction connections.

        Args:
            action_name: The cause or initiating concept
            reaction_name: The effect or resulting concept
            relationship_type: Type (causal, correlative, structural, temporal)
            strength: How strong the relationship is (0-1)
            confidence: Confidence score (0-1)
            source_chunk_id: Source chunk for traceability

        Returns:
            The relationship_id if successful
        """
        if not self.is_connected():
            logger.warning("TypeDB not connected")
            return None

        # Ensure both concepts exist
        action_id = self.store_concept(action_name)
        reaction_id = self.store_concept(reaction_name)

        if not action_id or not reaction_id:
            logger.error("Failed to create concepts for relationship")
            return None

        relationship_id = self._generate_id()

        try:
            with self.driver.transaction(self.database, TransactionType.WRITE) as tx:
                query = f'''
                    match
                        $action isa concept, has thing_id "{action_id}";
                        $reaction isa concept, has thing_id "{reaction_id}";
                    insert
                        $r (action: $action, reaction: $reaction) isa relationship_link,
                            has relationship_id "{relationship_id}",
                            has confidence {confidence};
                '''
                tx.query(query).resolve()
                tx.commit()

                logger.info(f"Stored relationship: '{action_name}' -> '{reaction_name}'")
                return relationship_id

        except Exception as e:
            logger.error(f"Error storing relationship: {e}")
            return None

    def store_perspective(
        self,
        point_name: str,
        view_description: str,
        context: Optional[str] = None,
        confidence: float = 0.85,
        source_chunk_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Store a Perspective (P) pattern in TypeDB.

        Perspectives define point/view relationships - who sees what.

        Args:
            point_name: The observer (who is looking)
            view_description: What they see
            context: Additional context
            confidence: Confidence score (0-1)
            source_chunk_id: Source chunk for traceability

        Returns:
            The perspective_id if successful
        """
        if not self.is_connected():
            logger.warning("TypeDB not connected")
            return None

        # Create concepts for both point and view
        point_id = self.store_concept(point_name)
        view_id = self.store_concept(view_description)

        if not point_id or not view_id:
            logger.error("Failed to create concepts for perspective")
            return None

        perspective_id = self._generate_id()

        try:
            with self.driver.transaction(self.database, TransactionType.WRITE) as tx:
                query = f'''
                    match
                        $point isa concept, has thing_id "{point_id}";
                        $view isa concept, has thing_id "{view_id}";
                    insert
                        $p (point: $point, view: $view) isa perspective_view,
                            has perspective_id "{perspective_id}",
                            has confidence {confidence};
                '''
                tx.query(query).resolve()
                tx.commit()

                logger.info(f"Stored perspective: '{point_name}' sees '{view_description[:50]}...'")
                return perspective_id

        except Exception as e:
            logger.error(f"Error storing perspective: {e}")
            return None

    def store_dsrp_extraction(
        self,
        dsrp_data: dict,
        source_chunk_id: str
    ) -> dict:
        """
        Store a complete DSRP extraction from a text chunk.

        This is the main method called by the pipeline after LLM extraction.

        Args:
            dsrp_data: The JSON output from the LLM containing all patterns
            source_chunk_id: ID of the chunk this came from

        Returns:
            Summary of what was stored
        """
        results = {
            "distinctions": 0,
            "systems": 0,
            "relationships": 0,
            "perspectives": 0,
            "concepts": 0,
            "errors": []
        }

        # Store all unique concepts first
        concepts = dsrp_data.get("concepts", [])
        for concept_name in concepts:
            if concept_name and self.store_concept(concept_name, source_chunk_id=source_chunk_id):
                results["concepts"] += 1

        # Store Distinctions (D)
        for d in dsrp_data.get("distinctions", []):
            try:
                if self.store_distinction(
                    identity_name=d["identity"],
                    other_name=d["other"],
                    boundary=d.get("boundary"),
                    confidence=d.get("confidence", 0.85),
                    source_chunk_id=source_chunk_id
                ):
                    results["distinctions"] += 1
            except Exception as e:
                results["errors"].append(f"Distinction error: {e}")

        # Store Systems (S)
        for s in dsrp_data.get("systems", []):
            try:
                if self.store_system(
                    whole_name=s["whole"],
                    part_names=s["parts"],
                    confidence=s.get("confidence", 0.85),
                    source_chunk_id=source_chunk_id
                ):
                    results["systems"] += 1
            except Exception as e:
                results["errors"].append(f"System error: {e}")

        # Store Relationships (R)
        for r in dsrp_data.get("relationships", []):
            try:
                if self.store_relationship(
                    action_name=r["action"],
                    reaction_name=r["reaction"],
                    relationship_type=r.get("relationship_type", "causal"),
                    strength=r.get("strength", 0.75),
                    confidence=r.get("confidence", 0.85),
                    source_chunk_id=source_chunk_id
                ):
                    results["relationships"] += 1
            except Exception as e:
                results["errors"].append(f"Relationship error: {e}")

        # Store Perspectives (P)
        for p in dsrp_data.get("perspectives", []):
            try:
                if self.store_perspective(
                    point_name=p["point"],
                    view_description=p["view"],
                    context=p.get("context"),
                    confidence=p.get("confidence", 0.85),
                    source_chunk_id=source_chunk_id
                ):
                    results["perspectives"] += 1
            except Exception as e:
                results["errors"].append(f"Perspective error: {e}")

        logger.info(
            f"Stored DSRP extraction: {results['distinctions']}D, "
            f"{results['systems']}S, {results['relationships']}R, "
            f"{results['perspectives']}P, {results['concepts']} concepts"
        )

        return results

    def _escape(self, text: str) -> str:
        """Escape special characters for TypeQL strings."""
        if not text:
            return ""
        return text.replace('"', '\\"').replace("\n", " ").replace("\r", "")

    def close(self):
        """Close the TypeDB connection."""
        if self.driver:
            self.driver.close()
            logger.info("TypeDB connection closed")
