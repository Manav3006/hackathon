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


def list_warehouses() -> list[sqlite3.Row]:
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT id, name, code, address
            FROM warehouses
            ORDER BY name
            """
        ).fetchall()


def create_warehouse(name: str, code: str, address: str) -> tuple[bool, str]:
    name = name.strip()
    code = code.strip().upper()
    address = address.strip()

    if not name:
        return False, "Warehouse name is required."
    if not code:
        return False, "Warehouse code is required."

    try:
        with get_connection() as connection:
            connection.execute(
                "INSERT INTO warehouses (name, code, address) VALUES (?, ?, ?)",
                (name, code, address),
            )
            connection.commit()
    except sqlite3.IntegrityError as error:
        lowered = str(error).lower()
        if "warehouses.name" in lowered or "unique" in lowered and "name" in lowered:
            return False, "A warehouse with that name already exists."
        if "warehouses.code" in lowered or "unique" in lowered and "code" in lowered:
            return False, "A warehouse with that code already exists."
        return False, "Could not save warehouse. Please try again."

    return True, f"Warehouse '{name}' created successfully."


def create_location(name: str, code: str, warehouse_id: int) -> tuple[bool, str]:
    name = name.strip()
    code = code.strip().upper()

    if not name:
        return False, "Location name is required."
    if not code:
        return False, "Location code is required."
    if not warehouse_id:
        return False, "Please select a warehouse."

    try:
        with get_connection() as connection:
            connection.execute(
                "INSERT INTO locations (name, code, warehouse_id) VALUES (?, ?, ?)",
                (name, code, warehouse_id),
            )
            connection.commit()
    except sqlite3.IntegrityError:
        return False, "A location with that code already exists in this warehouse."

    return True, f"Location '{name}' ({code}) created successfully."


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


# ── Stock posting engine ──────────────────────────────────────────────────────

def _generate_reference(prefix: str) -> str:
    """Return a unique reference number like REC-20260314-0001."""
    date_part = datetime.now(tz=timezone.utc).strftime("%Y%m%d")
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT COUNT(*) as cnt FROM stock_documents
            WHERE reference_number LIKE ?
            """,
            (f"{prefix}-{date_part}-%",),
        ).fetchone()
        sequence = (row["cnt"] if row else 0) + 1
    return f"{prefix}-{date_part}-{sequence:04d}"


def get_current_stock(product_id: int, location_id: int) -> float:
    """Return the current quantity for a product at a specific location."""
    with get_connection() as connection:
        row = connection.execute(
            "SELECT quantity FROM stock_balances WHERE product_id = ? AND location_id = ?",
            (product_id, location_id),
        ).fetchone()
    return float(row["quantity"]) if row else 0.0


def get_product_by_id(product_id: int) -> sqlite3.Row | None:
    with get_connection() as connection:
        return connection.execute(
            "SELECT id, name, sku, unit_of_measure, reorder_level FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()


def post_receipt(
    *,
    product_id: int,
    destination_location_id: int,
    quantity: float,
    partner_name: str,
    notes: str,
    created_by_user_id: int,
) -> tuple[bool, str]:
    """Increase stock at a location.  Writes document + line + ledger atomically."""
    if quantity <= 0:
        return False, "Quantity must be greater than zero."

    reference = _generate_reference("REC")
    now = datetime.now(tz=timezone.utc).isoformat()

    try:
        with get_connection() as connection:
            # 1) Document header
            location_row = connection.execute(
                "SELECT warehouse_id FROM locations WHERE id = ?",
                (destination_location_id,),
            ).fetchone()
            if not location_row:
                return False, "Selected location not found."
            warehouse_id = location_row["warehouse_id"]

            cur = connection.execute(
                """
                INSERT INTO stock_documents
                    (document_type, reference_number, status, partner_name,
                     destination_warehouse_id, destination_location_id,
                     notes, created_by_user_id, validated_at)
                VALUES ('Receipt', ?, 'Done', ?, ?, ?, ?, ?, ?)
                """,
                (reference, partner_name or None, warehouse_id,
                 destination_location_id, notes or None,
                 created_by_user_id, now),
            )
            document_id = cur.lastrowid

            # 2) Document line
            cur2 = connection.execute(
                "INSERT INTO stock_document_lines (document_id, product_id, quantity) VALUES (?, ?, ?)",
                (document_id, product_id, quantity),
            )
            line_id = cur2.lastrowid

            # 3) Update stock balance
            connection.execute(
                """
                INSERT INTO stock_balances (product_id, location_id, quantity)
                VALUES (?, ?, ?)
                ON CONFLICT (product_id, location_id) DO UPDATE
                    SET quantity = quantity + excluded.quantity
                """,
                (product_id, destination_location_id, quantity),
            )

            # 4) Ledger entry
            balance_after = get_current_stock(product_id, destination_location_id)
            connection.execute(
                """
                INSERT INTO stock_ledger
                    (document_id, document_line_id, product_id, document_type,
                     warehouse_id, location_id, quantity_change, balance_after,
                     created_by_user_id, created_at)
                VALUES (?, ?, ?, 'Receipt', ?, ?, ?, ?, ?, ?)
                """,
                (document_id, line_id, product_id,
                 warehouse_id, destination_location_id,
                 quantity, balance_after,
                 created_by_user_id, now),
            )
            connection.commit()
    except sqlite3.Error as error:
        return False, f"Database error: {error}"

    return True, f"Receipt {reference} validated. Stock increased by {quantity:g}."


def post_delivery(
    *,
    product_id: int,
    source_location_id: int,
    quantity: float,
    partner_name: str,
    notes: str,
    created_by_user_id: int,
) -> tuple[bool, str]:
    """Decrease stock at a location.  Blocks if stock would go negative."""
    if quantity <= 0:
        return False, "Quantity must be greater than zero."

    current = get_current_stock(product_id, source_location_id)
    if current < quantity:
        return False, (
            f"Not enough stock. Available: {current:g}, requested: {quantity:g}."
        )

    reference = _generate_reference("DEL")
    now = datetime.now(tz=timezone.utc).isoformat()

    try:
        with get_connection() as connection:
            location_row = connection.execute(
                "SELECT warehouse_id FROM locations WHERE id = ?",
                (source_location_id,),
            ).fetchone()
            if not location_row:
                return False, "Selected location not found."
            warehouse_id = location_row["warehouse_id"]

            cur = connection.execute(
                """
                INSERT INTO stock_documents
                    (document_type, reference_number, status, partner_name,
                     source_warehouse_id, source_location_id,
                     notes, created_by_user_id, validated_at)
                VALUES ('Delivery', ?, 'Done', ?, ?, ?, ?, ?, ?)
                """,
                (reference, partner_name or None, warehouse_id,
                 source_location_id, notes or None,
                 created_by_user_id, now),
            )
            document_id = cur.lastrowid

            cur2 = connection.execute(
                "INSERT INTO stock_document_lines (document_id, product_id, quantity) VALUES (?, ?, ?)",
                (document_id, product_id, quantity),
            )
            line_id = cur2.lastrowid

            connection.execute(
                """
                UPDATE stock_balances
                SET quantity = quantity - ?
                WHERE product_id = ? AND location_id = ?
                """,
                (quantity, product_id, source_location_id),
            )

            balance_after = current - quantity
            connection.execute(
                """
                INSERT INTO stock_ledger
                    (document_id, document_line_id, product_id, document_type,
                     warehouse_id, location_id, quantity_change, balance_after,
                     created_by_user_id, created_at)
                VALUES (?, ?, ?, 'Delivery', ?, ?, ?, ?, ?, ?)
                """,
                (document_id, line_id, product_id,
                 warehouse_id, source_location_id,
                 -quantity, balance_after,
                 created_by_user_id, now),
            )
            connection.commit()
    except sqlite3.Error as error:
        return False, f"Database error: {error}"

    return True, f"Delivery {reference} validated. Stock decreased by {quantity:g}."


def post_transfer(
    *,
    product_id: int,
    source_location_id: int,
    destination_location_id: int,
    quantity: float,
    notes: str,
    created_by_user_id: int,
) -> tuple[bool, str]:
    """Move stock between two locations.  Net total stock never changes."""
    if quantity <= 0:
        return False, "Quantity must be greater than zero."
    if source_location_id == destination_location_id:
        return False, "Source and destination locations must be different."

    current = get_current_stock(product_id, source_location_id)
    if current < quantity:
        return False, (
            f"Not enough stock at source. Available: {current:g}, requested: {quantity:g}."
        )

    reference = _generate_reference("TRF")
    now = datetime.now(tz=timezone.utc).isoformat()

    try:
        with get_connection() as connection:
            src_row = connection.execute(
                "SELECT warehouse_id FROM locations WHERE id = ?",
                (source_location_id,),
            ).fetchone()
            dst_row = connection.execute(
                "SELECT warehouse_id FROM locations WHERE id = ?",
                (destination_location_id,),
            ).fetchone()
            if not src_row or not dst_row:
                return False, "One or both locations not found."

            cur = connection.execute(
                """
                INSERT INTO stock_documents
                    (document_type, reference_number, status,
                     source_warehouse_id, source_location_id,
                     destination_warehouse_id, destination_location_id,
                     notes, created_by_user_id, validated_at)
                VALUES ('Internal Transfer', ?, 'Done', ?, ?, ?, ?, ?, ?, ?)
                """,
                (reference,
                 src_row["warehouse_id"], source_location_id,
                 dst_row["warehouse_id"], destination_location_id,
                 notes or None, created_by_user_id, now),
            )
            document_id = cur.lastrowid

            cur2 = connection.execute(
                "INSERT INTO stock_document_lines (document_id, product_id, quantity) VALUES (?, ?, ?)",
                (document_id, product_id, quantity),
            )
            line_id = cur2.lastrowid

            # Debit source
            connection.execute(
                "UPDATE stock_balances SET quantity = quantity - ? WHERE product_id = ? AND location_id = ?",
                (quantity, product_id, source_location_id),
            )

            # Credit destination
            connection.execute(
                """
                INSERT INTO stock_balances (product_id, location_id, quantity)
                VALUES (?, ?, ?)
                ON CONFLICT (product_id, location_id) DO UPDATE
                    SET quantity = quantity + excluded.quantity
                """,
                (product_id, destination_location_id, quantity),
            )

            src_balance = current - quantity
            dst_balance = get_current_stock(product_id, destination_location_id)

            # Two ledger entries — one debit, one credit
            connection.execute(
                """
                INSERT INTO stock_ledger
                    (document_id, document_line_id, product_id, document_type,
                     warehouse_id, location_id, quantity_change, balance_after,
                     reason, created_by_user_id, created_at)
                VALUES (?, ?, ?, 'Internal Transfer', ?, ?, ?, ?, 'Transfer out', ?, ?)
                """,
                (document_id, line_id, product_id,
                 src_row["warehouse_id"], source_location_id,
                 -quantity, src_balance,
                 created_by_user_id, now),
            )
            connection.execute(
                """
                INSERT INTO stock_ledger
                    (document_id, document_line_id, product_id, document_type,
                     warehouse_id, location_id, quantity_change, balance_after,
                     reason, created_by_user_id, created_at)
                VALUES (?, ?, ?, 'Internal Transfer', ?, ?, ?, ?, 'Transfer in', ?, ?)
                """,
                (document_id, line_id, product_id,
                 dst_row["warehouse_id"], destination_location_id,
                 quantity, dst_balance,
                 created_by_user_id, now),
            )
            connection.commit()
    except sqlite3.Error as error:
        return False, f"Database error: {error}"

    return True, f"Transfer {reference} validated. {quantity:g} units moved."


def post_adjustment(
    *,
    product_id: int,
    location_id: int,
    counted_quantity: float,
    reason: str,
    created_by_user_id: int,
) -> tuple[bool, str]:
    """Correct stock to the counted_quantity.  Positive or negative delta allowed."""
    if counted_quantity < 0:
        return False, "Counted quantity cannot be negative."
    if not reason.strip():
        return False, "A reason is required for adjustments."

    current = get_current_stock(product_id, location_id)
    delta = counted_quantity - current

    if delta == 0:
        return False, "Counted quantity matches current stock — no adjustment needed."

    reference = _generate_reference("ADJ")
    now = datetime.now(tz=timezone.utc).isoformat()

    try:
        with get_connection() as connection:
            loc_row = connection.execute(
                "SELECT warehouse_id FROM locations WHERE id = ?",
                (location_id,),
            ).fetchone()
            if not loc_row:
                return False, "Selected location not found."
            warehouse_id = loc_row["warehouse_id"]

            cur = connection.execute(
                """
                INSERT INTO stock_documents
                    (document_type, reference_number, status,
                     source_warehouse_id, source_location_id,
                     notes, created_by_user_id, validated_at)
                VALUES ('Adjustment', ?, 'Done', ?, ?, ?, ?, ?)
                """,
                (reference, warehouse_id, location_id,
                 reason.strip(), created_by_user_id, now),
            )
            document_id = cur.lastrowid

            cur2 = connection.execute(
                """
                INSERT INTO stock_document_lines
                    (document_id, product_id, quantity, counted_quantity, line_note)
                VALUES (?, ?, ?, ?, ?)
                """,
                (document_id, product_id, abs(delta), counted_quantity, reason.strip()),
            )
            line_id = cur2.lastrowid

            # Upsert balance to the counted quantity
            connection.execute(
                """
                INSERT INTO stock_balances (product_id, location_id, quantity)
                VALUES (?, ?, ?)
                ON CONFLICT (product_id, location_id) DO UPDATE
                    SET quantity = excluded.quantity
                """,
                (product_id, location_id, counted_quantity),
            )

            connection.execute(
                """
                INSERT INTO stock_ledger
                    (document_id, document_line_id, product_id, document_type,
                     warehouse_id, location_id, quantity_change, balance_after,
                     reason, created_by_user_id, created_at)
                VALUES (?, ?, ?, 'Adjustment', ?, ?, ?, ?, ?, ?, ?)
                """,
                (document_id, line_id, product_id,
                 warehouse_id, location_id,
                 delta, counted_quantity,
                 reason.strip(), created_by_user_id, now),
            )
            connection.commit()
    except sqlite3.Error as error:
        return False, f"Database error: {error}"

    direction = "increased" if delta > 0 else "decreased"
    return True, f"Adjustment {reference} applied. Stock {direction} by {abs(delta):g} to {counted_quantity:g}."


# ── Move History ──────────────────────────────────────────────────────────────

def list_ledger(
    *,
    search_sku: str = "",
    document_type: str | None = None,
    warehouse_id: int | None = None,
) -> list[sqlite3.Row]:
    """Return stock_ledger rows joined to documents, products, locations, warehouses.

    Filters:
      search_sku    – partial match on product SKU or name (case-insensitive)
      document_type – one of DOCUMENT_TYPES or None for all
      warehouse_id  – restrict to a specific warehouse or None for all
    """
    filters: list[str] = []
    params: list[object] = []

    cleaned = search_sku.strip().lower()
    if cleaned:
        filters.append(
            "(LOWER(products.sku) LIKE ? OR LOWER(products.name) LIKE ?)"
        )
        like = f"%{cleaned}%"
        params.extend([like, like])

    if document_type:
        filters.append("stock_ledger.document_type = ?")
        params.append(document_type)

    if warehouse_id is not None:
        filters.append("stock_ledger.warehouse_id = ?")
        params.append(warehouse_id)

    where = f"WHERE {' AND '.join(filters)}" if filters else ""

    query = f"""
        SELECT
            stock_ledger.id,
            stock_ledger.created_at                         AS timestamp,
            stock_ledger.document_type                      AS operation,
            stock_documents.reference_number                AS reference,
            products.sku,
            products.name                                   AS product_name,
            warehouses.name                                 AS warehouse,
            locations.name                                  AS location,
            ROUND(stock_ledger.quantity_change, 2)          AS qty_change,
            ROUND(stock_ledger.balance_after, 2)            AS balance_after,
            stock_documents.status,
            COALESCE(stock_ledger.reason, stock_documents.partner_name, '') AS note
        FROM stock_ledger
        JOIN stock_documents ON stock_documents.id = stock_ledger.document_id
        JOIN products        ON products.id         = stock_ledger.product_id
        JOIN locations       ON locations.id         = stock_ledger.location_id
        JOIN warehouses      ON warehouses.id         = stock_ledger.warehouse_id
        {where}
        ORDER BY stock_ledger.id DESC
    """

    with get_connection() as connection:
        return connection.execute(query, params).fetchall()


# ── Dashboard KPIs ────────────────────────────────────────────────────────────

def get_dashboard_kpis() -> dict[str, int | float]:
    """Return a dict of summary numbers used on the Dashboard."""
    with get_connection() as connection:
        total_products = connection.execute(
            "SELECT COUNT(*) AS cnt FROM products"
        ).fetchone()["cnt"]

        total_stock = connection.execute(
            "SELECT COALESCE(SUM(quantity), 0) AS total FROM stock_balances"
        ).fetchone()["total"]

        low_stock_rows = connection.execute(
            """
            SELECT products.id
            FROM products
            LEFT JOIN stock_balances ON stock_balances.product_id = products.id
            GROUP BY products.id, products.reorder_level
            HAVING COALESCE(SUM(stock_balances.quantity), 0) <= products.reorder_level
            """
        ).fetchall()
        low_stock = len(low_stock_rows)

        out_of_stock_rows = connection.execute(
            """
            SELECT products.id
            FROM products
            LEFT JOIN stock_balances ON stock_balances.product_id = products.id
            GROUP BY products.id
            HAVING COALESCE(SUM(stock_balances.quantity), 0) = 0
            """
        ).fetchall()
        out_of_stock_count = len(out_of_stock_rows)

        pending_receipts = connection.execute(
            "SELECT COUNT(*) AS cnt FROM stock_documents WHERE document_type = 'Receipt' AND status IN ('Draft', 'Waiting', 'Ready')"
        ).fetchone()["cnt"]

        pending_deliveries = connection.execute(
            "SELECT COUNT(*) AS cnt FROM stock_documents WHERE document_type = 'Delivery' AND status IN ('Draft', 'Waiting', 'Ready')"
        ).fetchone()["cnt"]

        today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        ops_today = connection.execute(
            "SELECT COUNT(*) AS cnt FROM stock_documents WHERE DATE(created_at) = ?",
            (today,),
        ).fetchone()["cnt"]

    return {
        "total_products": total_products,
        "total_stock": round(float(total_stock), 2),
        "low_stock": low_stock,
        "out_of_stock": out_of_stock_count,
        "pending_receipts": pending_receipts,
        "pending_deliveries": pending_deliveries,
        "ops_today": ops_today,
    }


def get_stock_by_product(limit: int = 15) -> list[sqlite3.Row]:
    """Return total stock per product, ordered descending, for the bar chart."""
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT
                products.name  AS product_name,
                products.sku,
                ROUND(COALESCE(SUM(stock_balances.quantity), 0), 2) AS total_stock
            FROM products
            LEFT JOIN stock_balances ON stock_balances.product_id = products.id
            GROUP BY products.id, products.name, products.sku
            ORDER BY total_stock DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()