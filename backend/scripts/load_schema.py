#!/usr/bin/env python3
"""
Load DSRP 4-8-3 schema into TypeDB 3.x.
"""

import sys
from pathlib import Path

from typedb.driver import TypeDB, Credentials, TransactionType, DriverOptions

# Configuration
TYPEDB_HOST = "typedb"
TYPEDB_PORT = 1729
DATABASE_NAME = "dsrp_483"
USERNAME = "admin"
PASSWORD = "password"

SCHEMA_FILE = Path("/app/typedb/schema/dsrp-schema.tql")
SEED_DATA_FILE = Path("/app/typedb/schema/dsrp-seed-data.tql")


def main():
    print(f"Connecting to TypeDB at {TYPEDB_HOST}:{TYPEDB_PORT}...")

    try:
        # Connect to TypeDB 3.x with credentials (TLS disabled for local Docker)
        credentials = Credentials(USERNAME, PASSWORD)
        options = DriverOptions(is_tls_enabled=False)
        driver = TypeDB.driver(f"{TYPEDB_HOST}:{TYPEDB_PORT}", credentials, options)
        print("Connected to TypeDB!")

        # Check if database exists
        databases = driver.databases
        db_names = [db.name for db in databases.all()]
        print(f"Existing databases: {db_names}")

        # Create database if it doesn't exist
        if DATABASE_NAME in db_names:
            print(f"Database '{DATABASE_NAME}' already exists. Deleting and recreating...")
            databases.get(DATABASE_NAME).delete()

        print(f"Creating database '{DATABASE_NAME}'...")
        databases.create(DATABASE_NAME)
        print(f"Database '{DATABASE_NAME}' created!")

        # Load schema
        print(f"Loading schema from {SCHEMA_FILE}...")
        schema_content = SCHEMA_FILE.read_text()

        with driver.transaction(DATABASE_NAME, TransactionType.SCHEMA) as tx:
            tx.query(schema_content).resolve()
            tx.commit()
            print("Schema loaded successfully!")

        # Load seed data
        if SEED_DATA_FILE.exists():
            print(f"Loading seed data from {SEED_DATA_FILE}...")
            seed_content = SEED_DATA_FILE.read_text()

            # Remove comments and get just the insert statement
            lines = []
            for line in seed_content.split('\n'):
                if not line.strip().startswith('#'):
                    lines.append(line)
            seed_query = '\n'.join(lines).strip()

            with driver.transaction(DATABASE_NAME, TransactionType.WRITE) as tx:
                tx.query(seed_query).resolve()
                tx.commit()
                print("Seed data loaded successfully!")

        # Verify by querying the 6 moves
        print("\nVerifying data...")
        with driver.transaction(DATABASE_NAME, TransactionType.READ) as tx:
            # Query the moves we inserted
            result = list(tx.query("match $m isa dsrp_move, has move_name $n; select $n;").resolve())
            print(f"DSRP Moves loaded: {len(result)}")
            for row in result:
                print(f"  - {row.get('n').as_attribute().get_value()}")

        print("\n✓ DSRP 4-8-3 schema loaded successfully!")
        driver.close()
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
