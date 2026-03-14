from __future__ import annotations

import sqlite3
from pathlib import Path


DATABASE_PATH = Path(__file__).with_name("inventory.db")

ROLE_OPTIONS = ("Inventory Manager", "Warehouse Staff")
STATUS_OPTIONS = ("Draft", "Waiting", "Ready", "Done", "Canceled")
DOCUMENT_TYPES = ("Receipt", "Delivery", "Internal Transfer", "Adjustment")

SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK (role IN ('Inventory Manager', 'Warehouse Staff')),
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS password_reset_otps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        otp_code TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        used_at TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS warehouses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        code TEXT NOT NULL UNIQUE,
        address TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        warehouse_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        code TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (warehouse_id) REFERENCES warehouses (id),
        UNIQUE (warehouse_id, code)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        sku TEXT NOT NULL UNIQUE,
        category_id INTEGER,
        unit_of_measure TEXT NOT NULL,
        reorder_level REAL NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES categories (id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS stock_balances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        warehouse_id INTEGER NOT NULL,
        location_id INTEGER NOT NULL,
        quantity REAL NOT NULL DEFAULT 0 CHECK (quantity >= 0),
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products (id),
        FOREIGN KEY (warehouse_id) REFERENCES warehouses (id),
        FOREIGN KEY (location_id) REFERENCES locations (id),
        UNIQUE (product_id, warehouse_id, location_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS stock_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_type TEXT NOT NULL CHECK (
            document_type IN ('Receipt', 'Delivery', 'Internal Transfer', 'Adjustment')
        ),
        reference_number TEXT NOT NULL UNIQUE,
        status TEXT NOT NULL CHECK (
            status IN ('Draft', 'Waiting', 'Ready', 'Done', 'Canceled')
        ),
        partner_name TEXT,
        source_warehouse_id INTEGER,
        source_location_id INTEGER,
        destination_warehouse_id INTEGER,
        destination_location_id INTEGER,
        notes TEXT,
        created_by_user_id INTEGER,
        validated_by_user_id INTEGER,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        validated_at TEXT,
        FOREIGN KEY (source_warehouse_id) REFERENCES warehouses (id),
        FOREIGN KEY (source_location_id) REFERENCES locations (id),
        FOREIGN KEY (destination_warehouse_id) REFERENCES warehouses (id),
        FOREIGN KEY (destination_location_id) REFERENCES locations (id),
        FOREIGN KEY (created_by_user_id) REFERENCES users (id),
        FOREIGN KEY (validated_by_user_id) REFERENCES users (id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS stock_document_lines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity REAL NOT NULL CHECK (quantity > 0),
        counted_quantity REAL,
        line_note TEXT,
        FOREIGN KEY (document_id) REFERENCES stock_documents (id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS stock_ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        document_line_id INTEGER,
        product_id INTEGER NOT NULL,
        document_type TEXT NOT NULL CHECK (
            document_type IN ('Receipt', 'Delivery', 'Internal Transfer', 'Adjustment')
        ),
        warehouse_id INTEGER NOT NULL,
        location_id INTEGER NOT NULL,
        quantity_change REAL NOT NULL,
        balance_after REAL,
        reason TEXT,
        created_by_user_id INTEGER,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (document_id) REFERENCES stock_documents (id),
        FOREIGN KEY (document_line_id) REFERENCES stock_document_lines (id),
        FOREIGN KEY (product_id) REFERENCES products (id),
        FOREIGN KEY (warehouse_id) REFERENCES warehouses (id),
        FOREIGN KEY (location_id) REFERENCES locations (id),
        FOREIGN KEY (created_by_user_id) REFERENCES users (id)
    )
    """,
)

DEMO_WAREHOUSES = [
    ("Main Warehouse", "WH-MAIN", "Primary warehouse for demo data"),
]

DEMO_CATEGORIES = [
    ("Raw Materials", "Basic materials used for production"),
    ("Finished Goods", "Products ready for delivery"),
]

DEMO_LOCATIONS = [
    ("Receiving Zone", "LOC-RECV", "WH-MAIN"),
    ("Rack A", "LOC-RACK-A", "WH-MAIN"),
]


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db() -> None:
    with get_connection() as connection:
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)

        seed_reference_data(connection)
        connection.commit()


def seed_reference_data(connection: sqlite3.Connection) -> None:
    connection.executemany(
        "INSERT OR IGNORE INTO warehouses (name, code, address) VALUES (?, ?, ?)",
        DEMO_WAREHOUSES,
    )
    connection.executemany(
        "INSERT OR IGNORE INTO categories (name, description) VALUES (?, ?)",
        DEMO_CATEGORIES,
    )
    connection.executemany(
        """
        INSERT OR IGNORE INTO locations (warehouse_id, name, code)
        SELECT warehouses.id, ?, ?
        FROM warehouses
        WHERE warehouses.code = ?
        """,
        DEMO_LOCATIONS,
    )