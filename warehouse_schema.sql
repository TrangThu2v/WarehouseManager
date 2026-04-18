PRAGMA foreign_keys = ON;

-- =============================================
-- WAREHOUSE MANAGER DATABASE SCHEMA (SQLite)
-- Bao phủ 8 chức năng chính + 20 chức năng chi tiết
-- =============================================

-- 1) Quản lý người dùng
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE,
    phone TEXT,
    role TEXT NOT NULL CHECK (role IN ('admin', 'staff')),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- 2) Quản lý danh mục
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT
);

-- 3) Quản lý nhà cung cấp
CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_code TEXT NOT NULL UNIQUE,
    supplier_name TEXT NOT NULL,
    contact_name TEXT,
    phone TEXT,
    email TEXT,
    address TEXT,
    tax_code TEXT,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_suppliers_name ON suppliers(supplier_name);

-- 4) Quản lý sản phẩm
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT NOT NULL UNIQUE,
    barcode TEXT UNIQUE,
    product_name TEXT NOT NULL,
    category_id INTEGER NOT NULL,
    supplier_id INTEGER,
    unit TEXT NOT NULL DEFAULT 'cái',
    cost_price REAL NOT NULL DEFAULT 0 CHECK (cost_price >= 0),
    sale_price REAL NOT NULL DEFAULT 0 CHECK (sale_price >= 0),
    min_stock_level INTEGER NOT NULL DEFAULT 0 CHECK (min_stock_level >= 0),
    max_stock_level INTEGER CHECK (max_stock_level IS NULL OR max_stock_level >= 0),
    description TEXT,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_products_name ON products(product_name);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_supplier ON products(supplier_id);

-- 5) Quản lý tồn kho (số lượng hiện tại)
CREATE TABLE IF NOT EXISTS inventory (
    product_id INTEGER PRIMARY KEY,
    quantity_on_hand INTEGER NOT NULL DEFAULT 0 CHECK (quantity_on_hand >= 0),
    last_updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (product_id) REFERENCES products(id) ON UPDATE CASCADE ON DELETE CASCADE
);

-- 6) Quản lý nhập kho
CREATE TABLE IF NOT EXISTS import_receipts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_no TEXT NOT NULL UNIQUE,
    supplier_id INTEGER NOT NULL,
    imported_by INTEGER NOT NULL,
    import_date TEXT NOT NULL DEFAULT (date('now')),
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'completed', 'cancelled')),
    note TEXT,
    total_amount REAL NOT NULL DEFAULT 0 CHECK (total_amount >= 0),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (imported_by) REFERENCES users(id) ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_import_receipts_date ON import_receipts(import_date);
CREATE INDEX IF NOT EXISTS idx_import_receipts_status ON import_receipts(status);

CREATE TABLE IF NOT EXISTS import_receipt_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_cost REAL NOT NULL CHECK (unit_cost >= 0),
    line_total REAL GENERATED ALWAYS AS (quantity * unit_cost) STORED,
    FOREIGN KEY (receipt_id) REFERENCES import_receipts(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    UNIQUE (receipt_id, product_id)
);

CREATE INDEX IF NOT EXISTS idx_import_items_receipt ON import_receipt_items(receipt_id);
CREATE INDEX IF NOT EXISTS idx_import_items_product ON import_receipt_items(product_id);

-- 7) Quản lý xuất kho
CREATE TABLE IF NOT EXISTS export_receipts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_no TEXT NOT NULL UNIQUE,
    exported_by INTEGER NOT NULL,
    customer_name TEXT,
    export_date TEXT NOT NULL DEFAULT (date('now')),
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'completed', 'cancelled')),
    note TEXT,
    total_amount REAL NOT NULL DEFAULT 0 CHECK (total_amount >= 0),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT,
    FOREIGN KEY (exported_by) REFERENCES users(id) ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_export_receipts_date ON export_receipts(export_date);
CREATE INDEX IF NOT EXISTS idx_export_receipts_status ON export_receipts(status);

CREATE TABLE IF NOT EXISTS export_receipt_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL CHECK (unit_price >= 0),
    line_total REAL GENERATED ALWAYS AS (quantity * unit_price) STORED,
    FOREIGN KEY (receipt_id) REFERENCES export_receipts(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    UNIQUE (receipt_id, product_id)
);

CREATE INDEX IF NOT EXISTS idx_export_items_receipt ON export_receipt_items(receipt_id);
CREATE INDEX IF NOT EXISTS idx_export_items_product ON export_receipt_items(product_id);

-- 8) Nhật ký nhập/xuất kho để báo cáo - thống kê
CREATE TABLE IF NOT EXISTS stock_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    movement_type TEXT NOT NULL CHECK (movement_type IN ('IN', 'OUT', 'ADJUST')),
    product_id INTEGER NOT NULL,
    reference_type TEXT NOT NULL CHECK (reference_type IN ('IMPORT', 'EXPORT', 'MANUAL')),
    reference_id INTEGER,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL DEFAULT 0 CHECK (unit_price >= 0),
    movement_date TEXT NOT NULL DEFAULT (datetime('now')),
    created_by INTEGER NOT NULL,
    note TEXT,
    FOREIGN KEY (product_id) REFERENCES products(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (created_by) REFERENCES users(id) ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_stock_movements_date ON stock_movements(movement_date);
CREATE INDEX IF NOT EXISTS idx_stock_movements_product ON stock_movements(product_id);
CREATE INDEX IF NOT EXISTS idx_stock_movements_type ON stock_movements(movement_type);

-- =============================================
-- Trigger: tự cập nhật tồn kho khi hoàn thành phiếu nhập
-- =============================================
CREATE TRIGGER IF NOT EXISTS trg_import_completed_update_inventory
AFTER UPDATE OF status ON import_receipts
FOR EACH ROW
WHEN OLD.status <> 'completed' AND NEW.status = 'completed'
BEGIN
    INSERT INTO inventory (product_id, quantity_on_hand, last_updated_at)
    SELECT iri.product_id, SUM(iri.quantity), datetime('now')
    FROM import_receipt_items iri
    WHERE iri.receipt_id = NEW.id
    GROUP BY iri.product_id
    ON CONFLICT(product_id) DO UPDATE SET
        quantity_on_hand = quantity_on_hand + excluded.quantity_on_hand,
        last_updated_at = datetime('now');

    INSERT INTO stock_movements (movement_type, product_id, reference_type, reference_id, quantity, unit_price, movement_date, created_by, note)
    SELECT 'IN', iri.product_id, 'IMPORT', NEW.id, iri.quantity, iri.unit_cost, datetime('now'), NEW.imported_by, NEW.note
    FROM import_receipt_items iri
    WHERE iri.receipt_id = NEW.id;
END;

-- =============================================
-- Trigger: chặn xuất kho khi không đủ tồn
-- =============================================
CREATE TRIGGER IF NOT EXISTS trg_export_check_inventory
BEFORE UPDATE OF status ON export_receipts
FOR EACH ROW
WHEN OLD.status <> 'completed' AND NEW.status = 'completed'
BEGIN
    SELECT
        CASE
            WHEN EXISTS (
                SELECT 1
                FROM export_receipt_items eri
                LEFT JOIN inventory i ON i.product_id = eri.product_id
                WHERE eri.receipt_id = NEW.id
                  AND COALESCE(i.quantity_on_hand, 0) < eri.quantity
            ) THEN RAISE(ABORT, 'Khong du ton kho de xuat')
        END;
END;

-- =============================================
-- Trigger: tự trừ tồn kho khi hoàn thành phiếu xuất
-- =============================================
CREATE TRIGGER IF NOT EXISTS trg_export_completed_update_inventory
AFTER UPDATE OF status ON export_receipts
FOR EACH ROW
WHEN OLD.status <> 'completed' AND NEW.status = 'completed'
BEGIN
    UPDATE inventory
    SET quantity_on_hand = quantity_on_hand - (
            SELECT eri.quantity
            FROM export_receipt_items eri
            WHERE eri.receipt_id = NEW.id
              AND eri.product_id = inventory.product_id
        ),
        last_updated_at = datetime('now')
    WHERE product_id IN (
        SELECT product_id
        FROM export_receipt_items
        WHERE receipt_id = NEW.id
    );

    INSERT INTO stock_movements (movement_type, product_id, reference_type, reference_id, quantity, unit_price, movement_date, created_by, note)
    SELECT 'OUT', eri.product_id, 'EXPORT', NEW.id, eri.quantity, eri.unit_price, datetime('now'), NEW.exported_by, NEW.note
    FROM export_receipt_items eri
    WHERE eri.receipt_id = NEW.id;
END;

-- =============================================
-- VIEW báo cáo nhập - xuất theo sản phẩm
-- =============================================
CREATE VIEW IF NOT EXISTS vw_product_inout_summary AS
SELECT
    p.id AS product_id,
    p.sku,
    p.product_name,
    COALESCE(SUM(CASE WHEN sm.movement_type = 'IN' THEN sm.quantity ELSE 0 END), 0) AS total_in,
    COALESCE(SUM(CASE WHEN sm.movement_type = 'OUT' THEN sm.quantity ELSE 0 END), 0) AS total_out,
    COALESCE(i.quantity_on_hand, 0) AS current_stock
FROM products p
LEFT JOIN stock_movements sm ON sm.product_id = p.id
LEFT JOIN inventory i ON i.product_id = p.id
GROUP BY p.id, p.sku, p.product_name, i.quantity_on_hand;

-- VIEW sản phẩm sắp hết hàng (thấp hơn hoặc bằng định mức tối thiểu)
CREATE VIEW IF NOT EXISTS vw_low_stock_products AS
SELECT
    p.id,
    p.sku,
    p.product_name,
    c.name AS category_name,
    COALESCE(i.quantity_on_hand, 0) AS current_stock,
    p.min_stock_level
FROM products p
JOIN categories c ON c.id = p.category_id
LEFT JOIN inventory i ON i.product_id = p.id
WHERE COALESCE(i.quantity_on_hand, 0) <= p.min_stock_level
ORDER BY current_stock ASC, p.product_name ASC;
