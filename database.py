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

SAMPLE_PRODUCTS: list[tuple[str, str, int, float]] = [
    ("Gạo ST25 5kg", "SP001", 120, 185000),
    ("Nước mắm 500ml", "SP002", 200, 42000),
    ("Đường trắng 1kg", "SP003", 180, 28000),
    ("Muối tinh 500g", "SP004", 250, 9000),
    ("Dầu ăn 1L", "SP005", 140, 52000),
    ("Mì gói tôm chua cay", "SP006", 500, 4500),
    ("Sữa tươi không đường 1L", "SP007", 110, 36000),
    ("Sữa đặc lon 380g", "SP008", 160, 29000),
    ("Trà xanh chai 455ml", "SP009", 320, 11000),
    ("Nước ngọt cola lon", "SP010", 290, 10500),
    ("Bánh quy bơ 300g", "SP011", 130, 47000),
    ("Kẹo bạc hà 100g", "SP012", 210, 18000),
    ("Cà phê hòa tan 20 gói", "SP013", 95, 78000),
    ("Nước rửa chén 750ml", "SP014", 125, 39000),
    ("Bột giặt 3kg", "SP015", 88, 129000),
    ("Nước lau sàn 1L", "SP016", 92, 65000),
    ("Giấy vệ sinh 10 cuộn", "SP017", 170, 86000),
    ("Khăn giấy hộp", "SP018", 190, 22000),
    ("Dầu gội 650g", "SP019", 105, 98000),
    ("Sữa tắm 900g", "SP020", 97, 112000),
    ("Bàn chải đánh răng", "SP021", 260, 17000),
    ("Kem đánh răng 180g", "SP022", 230, 32000),
    ("Nước rửa tay 500ml", "SP023", 150, 41000),
    ("Màng bọc thực phẩm 30m", "SP024", 90, 26000),
    ("Túi rác tự hủy 64x78", "SP025", 145, 34000),
]


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


def seed_sample_products(target_total: int = 25) -> int:
    """
    Thêm dữ liệu mẫu vào bảng products cho đủ số lượng target_total.
    Trả về số bản ghi mới được thêm.
    """
    with get_connection() as conn:
        current_total = conn.execute("SELECT COUNT(*) AS total FROM products").fetchone()["total"]
        missing = max(0, target_total - int(current_total))
        if missing == 0:
            return 0

        products_to_add = SAMPLE_PRODUCTS[:missing]
        conn.executemany(
            "INSERT OR IGNORE INTO products (name, sku, quantity, price) VALUES (?, ?, ?, ?)",
            [(name, sku, quantity, price) for name, sku, quantity, price in products_to_add],
        )
        conn.commit()
        return conn.total_changes
