import hashlib
import sqlite3
from pathlib import Path
from typing import Iterable

DB_PATH = Path(__file__).resolve().parent / "warehouse.db"


# =========================
# Core helpers
# =========================
def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# =========================
# Database initialization
# =========================
def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'staff')),
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sku TEXT UNIQUE NOT NULL,
                category_id INTEGER,
                supplier_id INTEGER,
                unit TEXT NOT NULL DEFAULT 'pcs',
                cost_price REAL NOT NULL DEFAULT 0,
                sale_price REAL NOT NULL DEFAULT 0,
                reorder_level INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS inventory (
                product_id INTEGER PRIMARY KEY,
                quantity INTEGER NOT NULL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS import_receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_no TEXT UNIQUE NOT NULL,
                supplier_id INTEGER,
                imported_by INTEGER,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL,
                FOREIGN KEY (imported_by) REFERENCES users(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS import_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                unit_cost REAL NOT NULL CHECK(unit_cost >= 0),
                FOREIGN KEY (receipt_id) REFERENCES import_receipts(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS export_receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_no TEXT UNIQUE NOT NULL,
                customer_name TEXT,
                exported_by INTEGER,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (exported_by) REFERENCES users(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS export_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                unit_price REAL NOT NULL CHECK(unit_price >= 0),
                FOREIGN KEY (receipt_id) REFERENCES export_receipts(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            );
            """
        )
        _seed_default_admin(conn)
        conn.commit()


def _seed_default_admin(conn: sqlite3.Connection) -> None:
    exists = conn.execute("SELECT id FROM users WHERE username = ?", ("admin",)).fetchone()
    if exists:
        return
    conn.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'admin')",
        ("admin", _hash_password("admin123")),
    )


# =========================
# User management
# =========================
def authenticate(username: str, password: str) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT id, username, role, is_active
            FROM users
            WHERE username = ? AND password_hash = ? AND is_active = 1
            """,
            (username.strip(), _hash_password(password)),
        ).fetchone()


def create_user(username: str, password: str, role: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username.strip(), _hash_password(password), role),
        )
        conn.commit()


def get_users() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT id, username, role, is_active, created_at FROM users ORDER BY id DESC"
        ).fetchall()


# =========================
# Categories
# =========================
def add_category(name: str, description: str = "") -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO categories (name, description) VALUES (?, ?)",
            (name.strip(), description.strip()),
        )
        conn.commit()


def update_category(category_id: int, name: str, description: str = "") -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE categories SET name = ?, description = ? WHERE id = ?",
            (name.strip(), description.strip(), category_id),
        )
        conn.commit()


def delete_category(category_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        conn.commit()


def get_categories() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute("SELECT id, name, description FROM categories ORDER BY name").fetchall()


# =========================
# Suppliers
# =========================
def add_supplier(name: str, phone: str, email: str, address: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO suppliers (name, phone, email, address) VALUES (?, ?, ?, ?)",
            (name.strip(), phone.strip(), email.strip(), address.strip()),
        )
        conn.commit()


def update_supplier(supplier_id: int, name: str, phone: str, email: str, address: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE suppliers SET name = ?, phone = ?, email = ?, address = ? WHERE id = ?",
            (name.strip(), phone.strip(), email.strip(), address.strip(), supplier_id),
        )
        conn.commit()


def get_suppliers() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute("SELECT id, name, phone, email, address FROM suppliers ORDER BY id DESC").fetchall()


# =========================
# Products
# =========================
def add_product(
    name: str,
    sku: str,
    category_id: int | None,
    supplier_id: int | None,
    unit: str,
    cost_price: float,
    sale_price: float,
    reorder_level: int,
) -> None:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO products (name, sku, category_id, supplier_id, unit, cost_price, sale_price, reorder_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name.strip(),
                sku.strip().upper(),
                category_id,
                supplier_id,
                unit.strip() or "pcs",
                cost_price,
                sale_price,
                reorder_level,
            ),
        )
        conn.execute("INSERT INTO inventory (product_id, quantity) VALUES (?, 0)", (cursor.lastrowid,))
        conn.commit()


def update_product(
    product_id: int,
    name: str,
    sku: str,
    category_id: int | None,
    supplier_id: int | None,
    unit: str,
    cost_price: float,
    sale_price: float,
    reorder_level: int,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE products
            SET name = ?, sku = ?, category_id = ?, supplier_id = ?, unit = ?, cost_price = ?, sale_price = ?, reorder_level = ?
            WHERE id = ?
            """,
            (
                name.strip(),
                sku.strip().upper(),
                category_id,
                supplier_id,
                unit.strip() or "pcs",
                cost_price,
                sale_price,
                reorder_level,
                product_id,
            ),
        )
        conn.commit()


def delete_product(product_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()


def search_products(keyword: str = "") -> list[sqlite3.Row]:
    like = f"%{keyword.strip()}%"
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT p.id, p.name, p.sku, c.name AS category_name, s.name AS supplier_name,
                   p.unit, p.cost_price, p.sale_price, p.reorder_level, COALESCE(i.quantity, 0) AS quantity
            FROM products p
            LEFT JOIN categories c ON c.id = p.category_id
            LEFT JOIN suppliers s ON s.id = p.supplier_id
            LEFT JOIN inventory i ON i.product_id = p.id
            WHERE p.name LIKE ? OR p.sku LIKE ?
            ORDER BY p.id DESC
            """,
            (like, like),
        ).fetchall()


# =========================
# Import/Export receipts
# =========================
def create_import_receipt(receipt_no: str, supplier_id: int | None, imported_by: int, note: str = "") -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO import_receipts (receipt_no, supplier_id, imported_by, note) VALUES (?, ?, ?, ?)",
            (receipt_no.strip(), supplier_id, imported_by, note.strip()),
        )
        conn.commit()
        return int(cur.lastrowid)


def add_import_item(receipt_id: int, product_id: int, quantity: int, unit_cost: float) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO import_items (receipt_id, product_id, quantity, unit_cost) VALUES (?, ?, ?, ?)",
            (receipt_id, product_id, quantity, unit_cost),
        )
        conn.execute(
            """
            UPDATE inventory
            SET quantity = quantity + ?, updated_at = CURRENT_TIMESTAMP
            WHERE product_id = ?
            """,
            (quantity, product_id),
        )
        conn.commit()


def create_export_receipt(receipt_no: str, customer_name: str, exported_by: int, note: str = "") -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO export_receipts (receipt_no, customer_name, exported_by, note) VALUES (?, ?, ?, ?)",
            (receipt_no.strip(), customer_name.strip(), exported_by, note.strip()),
        )
        conn.commit()
        return int(cur.lastrowid)


def get_current_stock(product_id: int) -> int:
    with get_connection() as conn:
        row = conn.execute("SELECT quantity FROM inventory WHERE product_id = ?", (product_id,)).fetchone()
    return int(row["quantity"]) if row else 0


def add_export_item(receipt_id: int, product_id: int, quantity: int, unit_price: float) -> None:
    current_stock = get_current_stock(product_id)
    if quantity > current_stock:
        raise ValueError("Không đủ tồn kho để xuất.")

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO export_items (receipt_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
            (receipt_id, product_id, quantity, unit_price),
        )
        conn.execute(
            """
            UPDATE inventory
            SET quantity = quantity - ?, updated_at = CURRENT_TIMESTAMP
            WHERE product_id = ?
            """,
            (quantity, product_id),
        )
        conn.commit()


# =========================
# Inventory & reports
# =========================
def get_inventory_status() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT p.id, p.name, p.sku, COALESCE(i.quantity, 0) AS quantity, p.reorder_level,
                   CASE WHEN COALESCE(i.quantity, 0) <= p.reorder_level THEN 1 ELSE 0 END AS is_low_stock
            FROM products p
            LEFT JOIN inventory i ON i.product_id = p.id
            ORDER BY is_low_stock DESC, p.name ASC
            """
        ).fetchall()


def get_import_export_report() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT p.name, p.sku,
                   COALESCE(SUM(ii.quantity), 0) AS total_import,
                   COALESCE(SUM(ei.quantity), 0) AS total_export
            FROM products p
            LEFT JOIN import_items ii ON ii.product_id = p.id
            LEFT JOIN export_items ei ON ei.product_id = p.id
            GROUP BY p.id, p.name, p.sku
            ORDER BY p.name
            """
        ).fetchall()


def get_low_stock_report() -> list[sqlite3.Row]:
    return [row for row in get_inventory_status() if int(row["is_low_stock"]) == 1]


def get_lookup_map(rows: Iterable[sqlite3.Row], label_key: str = "name") -> dict[str, int]:
    return {str(row[label_key]): int(row["id"]) for row in rows}
