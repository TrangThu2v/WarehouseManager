import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "warehouse.db"


ALLOWED_SORT_FIELDS = {
    "id": "id",
    "name": "name",
    "sku": "sku",
    "quantity": "quantity",
    "price": "price",
}


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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS stock_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                movement_type TEXT NOT NULL CHECK(movement_type IN ('IMPORT', 'EXPORT')),
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(product_id) REFERENCES products(id)
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


def search_products(keyword: str) -> list[sqlite3.Row]:
    """Tìm kiếm sản phẩm theo tên hoặc SKU."""
    normalized_keyword = keyword.strip()
    if not normalized_keyword:
        return get_all_products()

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, name, sku, quantity, price
            FROM products
            WHERE name LIKE ? OR sku LIKE ?
            ORDER BY id DESC
            """,
            (f"%{normalized_keyword}%", f"%{normalized_keyword.upper()}%"),
        ).fetchall()
    return rows


def sort_products(sort_by: str = "id", descending: bool = True) -> list[sqlite3.Row]:
    """Sắp xếp danh sách sản phẩm theo cột được hỗ trợ."""
    column = ALLOWED_SORT_FIELDS.get(sort_by, "id")
    order = "DESC" if descending else "ASC"

    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT id, name, sku, quantity, price FROM products ORDER BY {column} {order}"
        ).fetchall()
    return rows


def import_stock(product_id: int, quantity: int, note: str | None = None) -> None:
    """Nhập hàng: tăng số lượng tồn kho và lưu lịch sử giao dịch."""
    if quantity <= 0:
        raise ValueError("Số lượng nhập phải lớn hơn 0.")

    with get_connection() as conn:
        updated = conn.execute(
            "UPDATE products SET quantity = quantity + ? WHERE id = ?",
            (quantity, product_id),
        )
        if updated.rowcount == 0:
            raise ValueError("Không tìm thấy sản phẩm để nhập hàng.")

        conn.execute(
            """
            INSERT INTO stock_movements (product_id, movement_type, quantity, note)
            VALUES (?, 'IMPORT', ?, ?)
            """,
            (product_id, quantity, (note or "").strip() or None),
        )
        conn.commit()


def export_stock(product_id: int, quantity: int, note: str | None = None) -> None:
    """Xuất hàng: trừ số lượng tồn kho và lưu lịch sử giao dịch."""
    if quantity <= 0:
        raise ValueError("Số lượng xuất phải lớn hơn 0.")

    with get_connection() as conn:
        product = conn.execute(
            "SELECT quantity FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()

        if product is None:
            raise ValueError("Không tìm thấy sản phẩm để xuất hàng.")

        current_quantity = int(product["quantity"])
        if current_quantity < quantity:
            raise ValueError("Không đủ tồn kho để xuất hàng.")

        conn.execute(
            "UPDATE products SET quantity = quantity - ? WHERE id = ?",
            (quantity, product_id),
        )
        conn.execute(
            """
            INSERT INTO stock_movements (product_id, movement_type, quantity, note)
            VALUES (?, 'EXPORT', ?, ?)
            """,
            (product_id, quantity, (note or "").strip() or None),
        )
        conn.commit()
