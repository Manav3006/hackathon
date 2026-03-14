from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path


DATABASE_PATH = Path(__file__).with_name("inventory.db")

ROLE_OPTIONS = ("Inventory Manager", "Warehouse Staff")
STATUS_OPTIONS = ("Draft", "Waiting", "Ready", "Done", "Canceled")
DOCUMENT_TYPES = ("Receipt", "Delivery", "Internal Transfer", "Adjustment")
PASSWORD_MIN_LENGTH = 6
OTP_VALIDITY_MINUTES = 10
PBKDF2_ITERATIONS = 120_000

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


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return f"{salt.hex()}${password_hash.hex()}"


def verify_password(password: str, stored_password_hash: str) -> bool:
    try:
        salt_hex, hash_hex = stored_password_hash.split("$", maxsplit=1)
    except ValueError:
        return False

    salt = bytes.fromhex(salt_hex)
    expected_hash = bytes.fromhex(hash_hex)
    candidate_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return hmac.compare_digest(expected_hash, candidate_hash)


def get_user_by_email(email: str) -> sqlite3.Row | None:
    normalized_email = _normalize_email(email)

    with get_connection() as connection:
        return connection.execute(
            """
            SELECT id, full_name, email, password_hash, role, created_at
            FROM users
            WHERE email = ?
            """,
            (normalized_email,),
        ).fetchone()


def create_user(full_name: str, email: str, password: str, role: str) -> tuple[bool, str]:
    clean_name = full_name.strip()
    normalized_email = _normalize_email(email)

    if not clean_name:
        return False, "Full name is required."
    if "@" not in normalized_email:
        return False, "Please enter a valid email address."
    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {PASSWORD_MIN_LENGTH} characters long."
    if role not in ROLE_OPTIONS:
        return False, "Please select a valid role."

    password_hash = hash_password(password)

    try:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO users (full_name, email, password_hash, role)
                VALUES (?, ?, ?, ?)
                """,
                (clean_name, normalized_email, password_hash, role),
            )
            connection.commit()
    except sqlite3.IntegrityError:
        return False, "An account with this email already exists."

    return True, "Account created. You can now log in."


def authenticate_user(email: str, password: str) -> sqlite3.Row | None:
    user = get_user_by_email(email)
    if user is None:
        return None

    if not verify_password(password, user["password_hash"]):
        return None

    return user


def generate_password_reset_otp(
    email: str,
    *,
    valid_minutes: int = OTP_VALIDITY_MINUTES,
) -> tuple[bool, str]:
    user = get_user_by_email(email)
    if user is None:
        return False, "No account found with this email."

    otp_code = f"{secrets.randbelow(1_000_000):06d}"
    expires_at = (_utc_now() + timedelta(minutes=valid_minutes)).isoformat()

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO password_reset_otps (user_id, otp_code, expires_at)
            VALUES (?, ?, ?)
            """,
            (user["id"], otp_code, expires_at),
        )
        connection.commit()

    # Demo mode: OTP is returned so the UI can display it without SMS/email integration.
    return True, otp_code


def reset_password_with_otp(
    email: str,
    otp_code: str,
    new_password: str,
) -> tuple[bool, str]:
    if len(new_password) < PASSWORD_MIN_LENGTH:
        return False, f"New password must be at least {PASSWORD_MIN_LENGTH} characters long."

    user = get_user_by_email(email)
    if user is None:
        return False, "No account found with this email."

    with get_connection() as connection:
        otp_row = connection.execute(
            """
            SELECT id, expires_at
            FROM password_reset_otps
            WHERE user_id = ?
              AND otp_code = ?
              AND used_at IS NULL
            ORDER BY id DESC
            LIMIT 1
            """,
            (user["id"], otp_code.strip()),
        ).fetchone()

        if otp_row is None:
            return False, "Invalid OTP. Please check the code and try again."

        expires_at = datetime.fromisoformat(otp_row["expires_at"])
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < _utc_now():
            return False, "This OTP has expired. Please request a new one."

        connection.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (hash_password(new_password), user["id"]),
        )
        connection.execute(
            "UPDATE password_reset_otps SET used_at = ? WHERE id = ?",
            (_utc_now().isoformat(), otp_row["id"]),
        )
        connection.commit()

    return True, "Password reset successful. Please log in with your new password."


def list_categories() -> list[sqlite3.Row]:
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT id, name, description
            FROM categories
            ORDER BY name
            """
        ).fetchall()


def list_locations() -> list[sqlite3.Row]:
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT
                locations.id,
                locations.name,
                locations.code,
                locations.warehouse_id,
                warehouses.name AS warehouse_name,
                warehouses.code AS warehouse_code
            FROM locations
            JOIN warehouses ON warehouses.id = locations.warehouse_id
            ORDER BY warehouses.name, locations.name
            """
        ).fetchall()


def create_product(
    name: str,
    sku: str,
    category_id: int | None,
    unit_of_measure: str,
    reorder_level: float,
    initial_stock: float,
    initial_location_id: int | None,
) -> tuple[bool, str]:
    clean_name = name.strip()
    clean_sku = sku.strip().upper()
    clean_unit = unit_of_measure.strip()

    if not clean_name:
        return False, "Product name is required."
    if not clean_sku:
        return False, "SKU / Code is required."
    if not clean_unit:
        return False, "Unit of measure is required."
    if reorder_level < 0:
        return False, "Reorder level cannot be negative."
    if initial_stock < 0:
        return False, "Initial stock cannot be negative."

    normalized_category_id = category_id if category_id else None

    with get_connection() as connection:
        selected_location: sqlite3.Row | None = None

        if initial_stock > 0:
            if initial_location_id is None:
                return False, "Select an initial stock location when initial stock is greater than 0."

            selected_location = connection.execute(
                """
                SELECT id, warehouse_id
                FROM locations
                WHERE id = ?
                """,
                (initial_location_id,),
            ).fetchone()
            if selected_location is None:
                return False, "Please select a valid initial stock location."

        try:
            cursor = connection.execute(
                """
                INSERT INTO products (name, sku, category_id, unit_of_measure, reorder_level)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    clean_name,
                    clean_sku,
                    normalized_category_id,
                    clean_unit,
                    float(reorder_level),
                ),
            )

            if initial_stock > 0 and selected_location is not None:
                connection.execute(
                    """
                    INSERT INTO stock_balances (
                        product_id,
                        warehouse_id,
                        location_id,
                        quantity,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT (product_id, warehouse_id, location_id)
                    DO UPDATE SET
                        quantity = stock_balances.quantity + excluded.quantity,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (
                        cursor.lastrowid,
                        selected_location["warehouse_id"],
                        selected_location["id"],
                        float(initial_stock),
                    ),
                )

            connection.commit()
        except sqlite3.IntegrityError as error:
            if "products.sku" in str(error).lower():
                return False, "This SKU already exists. Please use a unique SKU."
            return False, "Could not save product. Please try again."

    return True, "Product saved successfully."


def list_products(
    *,
    search_query: str = "",
    category_id: int | None = None,
) -> list[sqlite3.Row]:
    filters: list[str] = []
    params: list[object] = []

    cleaned_search = search_query.strip().lower()
    if cleaned_search:
        filters.append("(LOWER(products.sku) LIKE ? OR LOWER(products.name) LIKE ?)")
        like_pattern = f"%{cleaned_search}%"
        params.extend([like_pattern, like_pattern])

    if category_id is not None:
        filters.append("products.category_id = ?")
        params.append(category_id)

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    query = f"""
        SELECT
            products.id,
            products.name,
            products.sku,
            COALESCE(categories.name, 'Uncategorized') AS category,
            products.unit_of_measure AS unit,
            products.reorder_level,
            ROUND(COALESCE(SUM(stock_balances.quantity), 0), 2) AS total_stock,
            CASE
                WHEN COALESCE(SUM(stock_balances.quantity), 0) <= products.reorder_level THEN 'Yes'
                ELSE 'No'
            END AS low_stock
        FROM products
        LEFT JOIN categories ON categories.id = products.category_id
        LEFT JOIN stock_balances ON stock_balances.product_id = products.id
        {where_clause}
        GROUP BY
            products.id,
            products.name,
            products.sku,
            categories.name,
            products.unit_of_measure,
            products.reorder_level
        ORDER BY products.id DESC
    """

    with get_connection() as connection:
        return connection.execute(query, params).fetchall()