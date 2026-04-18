import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "warehouse.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sku TEXT UNIQUE NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                price REAL NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def add_product(name: str, sku: str, quantity: int, price: float) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO products (name, sku, quantity, price) VALUES (?, ?, ?, ?)",
            (name.strip(), sku.strip().upper(), quantity, price),
        )
        conn.commit()


def update_product(product_id: int, name: str, sku: str, quantity: int, price: float) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE products
            SET name = ?, sku = ?, quantity = ?, price = ?
            WHERE id = ?
            """,
            (name.strip(), sku.strip().upper(), quantity, price, product_id),
        )
        conn.commit()


def delete_product(product_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()


def get_all_products() -> list[sqlite3.Row]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, name, sku, quantity, price FROM products ORDER BY id DESC"
        ).fetchall()
    return rows
