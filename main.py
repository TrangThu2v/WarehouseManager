import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
from uuid import uuid4

import database


class LoginWindow:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Đăng nhập hệ thống kho")
        self.root.geometry("360x220")
        self.user: dict[str, str | int] | None = None

        frame = ttk.LabelFrame(root, text="Thông tin đăng nhập")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(frame, text="Tên đăng nhập").grid(row=0, column=0, padx=8, pady=10, sticky="w")
        self.username_var = tk.StringVar(value="admin")
        ttk.Entry(frame, textvariable=self.username_var, width=24).grid(row=0, column=1, padx=8, pady=10)

        ttk.Label(frame, text="Mật khẩu").grid(row=1, column=0, padx=8, pady=10, sticky="w")
        self.password_var = tk.StringVar(value="admin123")
        ttk.Entry(frame, textvariable=self.password_var, show="*", width=24).grid(row=1, column=1, padx=8, pady=10)

        ttk.Button(frame, text="Đăng nhập", command=self.login).grid(row=2, column=0, columnspan=2, pady=14)

    def login(self) -> None:
        user = database.authenticate(self.username_var.get(), self.password_var.get())
        if not user:
            messagebox.showerror("Đăng nhập thất bại", "Sai tài khoản/mật khẩu hoặc tài khoản bị khóa.")
            return

        self.user = {"id": int(user["id"]), "username": user["username"], "role": user["role"]}
        self.root.destroy()


class WarehouseApp:
    def __init__(self, root: tk.Tk, current_user: dict[str, str | int]) -> None:
        self.root = root
        self.current_user = current_user
        self.root.title(f"Warehouse Manager - Xin chào {current_user['username']} ({current_user['role']})")
        self.root.geometry("1260x760")

        self.selected_user_id: int | None = None
        self.selected_category_id: int | None = None
        self.selected_supplier_id: int | None = None
        self.selected_product_id: int | None = None

        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill="both", expand=True)

        self._build_user_tab()
        self._build_category_tab()
        self._build_product_tab()
        self._build_supplier_tab()
        self._build_import_tab()
        self._build_export_tab()
        self._build_inventory_tab()
        self._build_report_tab()

        self.refresh_all()
        self._apply_permissions()

    # 1) User management
    def _build_user_tab(self) -> None:
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="1. Người dùng")

        form = ttk.LabelFrame(tab, text="Quản lý tài khoản")
        form.pack(fill="x", padx=10, pady=10)

        self.user_username = tk.StringVar()
        self.user_password = tk.StringVar()
        self.user_role = tk.StringVar(value="staff")

        ttk.Label(form, text="Username").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        ttk.Entry(form, textvariable=self.user_username, width=24).grid(row=0, column=1, padx=8, pady=8)

        ttk.Label(form, text="Password").grid(row=0, column=2, padx=8, pady=8, sticky="w")
        ttk.Entry(form, textvariable=self.user_password, width=24, show="*").grid(row=0, column=3, padx=8, pady=8)

        ttk.Label(form, text="Role").grid(row=0, column=4, padx=8, pady=8, sticky="w")
        ttk.Combobox(form, textvariable=self.user_role, values=["admin", "staff"], width=10, state="readonly").grid(row=0, column=5, padx=8, pady=8)

        self.user_add_btn = ttk.Button(form, text="Tạo tài khoản", command=self.add_user)
        self.user_add_btn.grid(row=0, column=6, padx=8, pady=8)

        self.user_tree = ttk.Treeview(tab, columns=("id", "username", "role", "active", "created"), show="headings", height=14)
        for col, title, width in [
            ("id", "ID", 60),
            ("username", "Tên đăng nhập", 220),
            ("role", "Phân quyền", 120),
            ("active", "Hoạt động", 120),
            ("created", "Ngày tạo", 200),
        ]:
            self.user_tree.heading(col, text=title)
            self.user_tree.column(col, width=width, anchor="center")
        self.user_tree.pack(fill="both", expand=True, padx=10, pady=10)

    def add_user(self) -> None:
        username = self.user_username.get().strip()
        password = self.user_password.get().strip()
        role = self.user_role.get().strip()
        if not username or not password:
            messagebox.showwarning("Thiếu dữ liệu", "Username và password là bắt buộc.")
            return
        try:
            database.create_user(username, password, role)
            self.user_username.set("")
            self.user_password.set("")
            self.load_users()
            messagebox.showinfo("Thành công", "Đã tạo tài khoản.")
        except sqlite3.IntegrityError:
            messagebox.showerror("Lỗi", "Username đã tồn tại.")

    def load_users(self) -> None:
        self._clear_tree(self.user_tree)
        for row in database.get_users():
            self.user_tree.insert("", "end", values=(row["id"], row["username"], row["role"], "Yes" if row["is_active"] else "No", row["created_at"]))

    # 2) Category management
    def _build_category_tab(self) -> None:
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="2. Danh mục")

        form = ttk.LabelFrame(tab, text="Thêm/Sửa/Xóa danh mục")
        form.pack(fill="x", padx=10, pady=10)

        self.category_name = tk.StringVar()
        self.category_desc = tk.StringVar()
        ttk.Label(form, text="Tên danh mục").grid(row=0, column=0, padx=8, pady=8)
        ttk.Entry(form, textvariable=self.category_name, width=30).grid(row=0, column=1, padx=8, pady=8)
        ttk.Label(form, text="Mô tả").grid(row=0, column=2, padx=8, pady=8)
        ttk.Entry(form, textvariable=self.category_desc, width=40).grid(row=0, column=3, padx=8, pady=8)

        ttk.Button(form, text="Thêm", command=self.add_category).grid(row=0, column=4, padx=6)
        ttk.Button(form, text="Sửa", command=self.update_category).grid(row=0, column=5, padx=6)
        ttk.Button(form, text="Xóa", command=self.delete_category).grid(row=0, column=6, padx=6)

        self.category_tree = ttk.Treeview(tab, columns=("id", "name", "desc"), show="headings", height=14)
        for col, title, width in [("id", "ID", 80), ("name", "Tên danh mục", 280), ("desc", "Mô tả", 520)]:
            self.category_tree.heading(col, text=title)
            self.category_tree.column(col, width=width)
        self.category_tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.category_tree.bind("<<TreeviewSelect>>", self.on_category_select)

    def on_category_select(self, _event: tk.Event) -> None:
        selected = self.category_tree.selection()
        if not selected:
            return
        values = self.category_tree.item(selected[0], "values")
        self.selected_category_id = int(values[0])
        self.category_name.set(values[1])
        self.category_desc.set(values[2])

    def add_category(self) -> None:
        if not self.category_name.get().strip():
            messagebox.showwarning("Thiếu dữ liệu", "Tên danh mục là bắt buộc.")
            return
        try:
            database.add_category(self.category_name.get(), self.category_desc.get())
            self.category_name.set("")
            self.category_desc.set("")
            self.load_categories()
        except sqlite3.IntegrityError:
            messagebox.showerror("Lỗi", "Tên danh mục đã tồn tại.")

    def update_category(self) -> None:
        if self.selected_category_id is None:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn danh mục cần sửa.")
            return
        database.update_category(self.selected_category_id, self.category_name.get(), self.category_desc.get())
        self.load_categories()

    def delete_category(self) -> None:
        if self.selected_category_id is None:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn danh mục cần xóa.")
            return
        database.delete_category(self.selected_category_id)
        self.selected_category_id = None
        self.category_name.set("")
        self.category_desc.set("")
        self.load_categories()

    def load_categories(self) -> None:
        self._clear_tree(self.category_tree)
        rows = database.get_categories()
        for row in rows:
            self.category_tree.insert("", "end", values=(row["id"], row["name"], row["description"]))
        self.category_lookup = database.get_lookup_map(rows)

    # 3) Product management
    def _build_product_tab(self) -> None:
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="3. Sản phẩm")

        form = ttk.LabelFrame(tab, text="Thêm/Sửa/Xóa + Tìm kiếm sản phẩm")
        form.pack(fill="x", padx=10, pady=10)

        self.p_name = tk.StringVar()
        self.p_sku = tk.StringVar()
        self.p_category = tk.StringVar()
        self.p_supplier = tk.StringVar()
        self.p_unit = tk.StringVar(value="pcs")
        self.p_cost = tk.StringVar(value="0")
        self.p_sale = tk.StringVar(value="0")
        self.p_reorder = tk.StringVar(value="5")
        self.p_search = tk.StringVar()

        labels = ["Tên", "SKU", "Danh mục", "Nhà cung cấp", "ĐVT", "Giá nhập", "Giá bán", "Ngưỡng tồn thấp"]
        vars_ = [self.p_name, self.p_sku, self.p_category, self.p_supplier, self.p_unit, self.p_cost, self.p_sale, self.p_reorder]
        for i, (lb, var) in enumerate(zip(labels, vars_)):
            ttk.Label(form, text=lb).grid(row=i // 4, column=(i % 4) * 2, padx=6, pady=6, sticky="w")
            if lb in {"Danh mục", "Nhà cung cấp"}:
                box = ttk.Combobox(form, textvariable=var, width=20, state="readonly")
                if lb == "Danh mục":
                    self.category_combo = box
                else:
                    self.supplier_combo = box
                box.grid(row=i // 4, column=(i % 4) * 2 + 1, padx=6, pady=6)
            else:
                ttk.Entry(form, textvariable=var, width=22).grid(row=i // 4, column=(i % 4) * 2 + 1, padx=6, pady=6)

        btns = ttk.Frame(form)
        btns.grid(row=2, column=0, columnspan=8, pady=8)
        ttk.Button(btns, text="Thêm SP", command=self.add_product).pack(side="left", padx=5)
        ttk.Button(btns, text="Sửa SP", command=self.update_product).pack(side="left", padx=5)
        ttk.Button(btns, text="Xóa SP", command=self.delete_product).pack(side="left", padx=5)

        ttk.Label(btns, text="Tìm kiếm").pack(side="left", padx=(22, 6))
        ttk.Entry(btns, textvariable=self.p_search, width=24).pack(side="left")
        ttk.Button(btns, text="Tìm", command=self.load_products).pack(side="left", padx=5)

        columns = ("id", "name", "sku", "category", "supplier", "qty", "unit", "cost", "sale", "reorder")
        self.product_tree = ttk.Treeview(tab, columns=columns, show="headings", height=14)
        headers = ["ID", "Tên", "SKU", "Danh mục", "Nhà cung cấp", "Tồn", "ĐVT", "Giá nhập", "Giá bán", "Ngưỡng thấp"]
        widths = [60, 200, 110, 140, 140, 70, 60, 100, 100, 100]
        for col, header, width in zip(columns, headers, widths):
            self.product_tree.heading(col, text=header)
            self.product_tree.column(col, width=width, anchor="center")
        self.product_tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.product_tree.bind("<<TreeviewSelect>>", self.on_product_select)

    def on_product_select(self, _event: tk.Event) -> None:
        selected = self.product_tree.selection()
        if not selected:
            return
        values = self.product_tree.item(selected[0], "values")
        self.selected_product_id = int(values[0])
        self.p_name.set(values[1])
        self.p_sku.set(values[2])
        self.p_category.set(values[3])
        self.p_supplier.set(values[4])
        self.p_unit.set(values[6])
        self.p_cost.set(values[7])
        self.p_sale.set(values[8])
        self.p_reorder.set(values[9])

    def _parse_product_fields(self) -> tuple:
        if not self.p_name.get().strip() or not self.p_sku.get().strip():
            raise ValueError("Tên và SKU là bắt buộc.")
        category_id = self.category_lookup.get(self.p_category.get()) if self.p_category.get() else None
        supplier_id = self.supplier_lookup.get(self.p_supplier.get()) if self.p_supplier.get() else None
        return (
            self.p_name.get(),
            self.p_sku.get(),
            category_id,
            supplier_id,
            self.p_unit.get() or "pcs",
            float(self.p_cost.get()),
            float(self.p_sale.get()),
            int(self.p_reorder.get()),
        )

    def add_product(self) -> None:
        try:
            database.add_product(*self._parse_product_fields())
            self.load_products()
        except ValueError as err:
            messagebox.showwarning("Sai dữ liệu", str(err))
        except sqlite3.IntegrityError:
            messagebox.showerror("Lỗi", "SKU đã tồn tại.")

    def update_product(self) -> None:
        if self.selected_product_id is None:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn sản phẩm để sửa.")
            return
        try:
            database.update_product(self.selected_product_id, *self._parse_product_fields())
            self.load_products()
        except ValueError as err:
            messagebox.showwarning("Sai dữ liệu", str(err))
        except sqlite3.IntegrityError:
            messagebox.showerror("Lỗi", "SKU đã tồn tại.")

    def delete_product(self) -> None:
        if self.selected_product_id is None:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn sản phẩm để xóa.")
            return
        database.delete_product(self.selected_product_id)
        self.selected_product_id = None
        self.load_products()

    def load_products(self) -> None:
        self._clear_tree(self.product_tree)
        for row in database.search_products(self.p_search.get()):
            self.product_tree.insert(
                "",
                "end",
                values=(
                    row["id"],
                    row["name"],
                    row["sku"],
                    row["category_name"] or "",
                    row["supplier_name"] or "",
                    row["quantity"],
                    row["unit"],
                    f"{row['cost_price']:.2f}",
                    f"{row['sale_price']:.2f}",
                    row["reorder_level"],
                ),
            )

    # 4) Supplier management
    def _build_supplier_tab(self) -> None:
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="4. Nhà cung cấp")

        form = ttk.LabelFrame(tab, text="Thêm/Sửa nhà cung cấp")
        form.pack(fill="x", padx=10, pady=10)

        self.s_name = tk.StringVar()
        self.s_phone = tk.StringVar()
        self.s_email = tk.StringVar()
        self.s_address = tk.StringVar()

        for i, (title, var) in enumerate(
            [("Tên NCC", self.s_name), ("Điện thoại", self.s_phone), ("Email", self.s_email), ("Địa chỉ", self.s_address)]
        ):
            ttk.Label(form, text=title).grid(row=0, column=i * 2, padx=6, pady=8)
            ttk.Entry(form, textvariable=var, width=24).grid(row=0, column=i * 2 + 1, padx=6, pady=8)

        ttk.Button(form, text="Thêm", command=self.add_supplier).grid(row=1, column=0, pady=8)
        ttk.Button(form, text="Sửa", command=self.update_supplier).grid(row=1, column=1, pady=8)

        self.supplier_tree = ttk.Treeview(tab, columns=("id", "name", "phone", "email", "address"), show="headings", height=14)
        for col, title, width in [
            ("id", "ID", 60),
            ("name", "Tên NCC", 220),
            ("phone", "Điện thoại", 140),
            ("email", "Email", 200),
            ("address", "Địa chỉ", 320),
        ]:
            self.supplier_tree.heading(col, text=title)
            self.supplier_tree.column(col, width=width)
        self.supplier_tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.supplier_tree.bind("<<TreeviewSelect>>", self.on_supplier_select)

    def on_supplier_select(self, _event: tk.Event) -> None:
        selected = self.supplier_tree.selection()
        if not selected:
            return
        values = self.supplier_tree.item(selected[0], "values")
        self.selected_supplier_id = int(values[0])
        self.s_name.set(values[1])
        self.s_phone.set(values[2])
        self.s_email.set(values[3])
        self.s_address.set(values[4])

    def add_supplier(self) -> None:
        if not self.s_name.get().strip():
            messagebox.showwarning("Thiếu dữ liệu", "Tên nhà cung cấp là bắt buộc.")
            return
        database.add_supplier(self.s_name.get(), self.s_phone.get(), self.s_email.get(), self.s_address.get())
        self.load_suppliers()

    def update_supplier(self) -> None:
        if self.selected_supplier_id is None:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn nhà cung cấp để sửa.")
            return
        database.update_supplier(self.selected_supplier_id, self.s_name.get(), self.s_phone.get(), self.s_email.get(), self.s_address.get())
        self.load_suppliers()

    def load_suppliers(self) -> None:
        self._clear_tree(self.supplier_tree)
        rows = database.get_suppliers()
        for row in rows:
            self.supplier_tree.insert("", "end", values=(row["id"], row["name"], row["phone"], row["email"], row["address"]))
        self.supplier_lookup = database.get_lookup_map(rows)
        self.supplier_combo["values"] = list(self.supplier_lookup.keys())

    # 5) Import management
    def _build_import_tab(self) -> None:
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="5. Nhập kho")

        frame = ttk.LabelFrame(tab, text="Tạo phiếu nhập & thêm sản phẩm vào phiếu")
        frame.pack(fill="x", padx=10, pady=10)

        self.imp_receipt_no = tk.StringVar(value=f"PN-{uuid4().hex[:6].upper()}")
        self.imp_supplier = tk.StringVar()
        self.imp_note = tk.StringVar()
        self.imp_product = tk.StringVar()
        self.imp_qty = tk.StringVar(value="1")
        self.imp_cost = tk.StringVar(value="0")

        ttk.Label(frame, text="Mã phiếu").grid(row=0, column=0, padx=6, pady=6)
        ttk.Entry(frame, textvariable=self.imp_receipt_no, width=18).grid(row=0, column=1, padx=6, pady=6)
        ttk.Label(frame, text="NCC").grid(row=0, column=2, padx=6, pady=6)
        self.imp_supplier_combo = ttk.Combobox(frame, textvariable=self.imp_supplier, state="readonly", width=22)
        self.imp_supplier_combo.grid(row=0, column=3, padx=6, pady=6)
        ttk.Label(frame, text="Ghi chú").grid(row=0, column=4, padx=6, pady=6)
        ttk.Entry(frame, textvariable=self.imp_note, width=28).grid(row=0, column=5, padx=6, pady=6)

        ttk.Button(frame, text="Tạo phiếu nhập", command=self.create_import_receipt).grid(row=0, column=6, padx=8)

        ttk.Label(frame, text="Sản phẩm").grid(row=1, column=0, padx=6, pady=6)
        self.imp_product_combo = ttk.Combobox(frame, textvariable=self.imp_product, state="readonly", width=22)
        self.imp_product_combo.grid(row=1, column=1, padx=6, pady=6)
        ttk.Label(frame, text="SL").grid(row=1, column=2, padx=6, pady=6)
        ttk.Entry(frame, textvariable=self.imp_qty, width=10).grid(row=1, column=3, padx=6, pady=6)
        ttk.Label(frame, text="Giá nhập").grid(row=1, column=4, padx=6, pady=6)
        ttk.Entry(frame, textvariable=self.imp_cost, width=12).grid(row=1, column=5, padx=6, pady=6)
        ttk.Button(frame, text="Thêm vào phiếu", command=self.add_import_item).grid(row=1, column=6, padx=8)

        self.current_import_receipt_id: int | None = None

    def create_import_receipt(self) -> None:
        supplier_id = self.supplier_lookup.get(self.imp_supplier.get()) if self.imp_supplier.get() else None
        self.current_import_receipt_id = database.create_import_receipt(
            self.imp_receipt_no.get(), supplier_id, int(self.current_user["id"]), self.imp_note.get()
        )
        messagebox.showinfo("Thành công", f"Đã tạo phiếu nhập ID={self.current_import_receipt_id}")

    def add_import_item(self) -> None:
        if self.current_import_receipt_id is None:
            messagebox.showwarning("Chưa có phiếu", "Hãy tạo phiếu nhập trước.")
            return
        product_id = self.product_lookup.get(self.imp_product.get())
        if not product_id:
            messagebox.showwarning("Thiếu dữ liệu", "Vui lòng chọn sản phẩm.")
            return
        database.add_import_item(self.current_import_receipt_id, product_id, int(self.imp_qty.get()), float(self.imp_cost.get()))
        self.load_products()
        self.load_inventory()
        self.load_reports()
        messagebox.showinfo("Thành công", "Đã thêm sản phẩm vào phiếu nhập và cập nhật tồn kho.")

    # 6) Export management
    def _build_export_tab(self) -> None:
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="6. Xuất kho")

        frame = ttk.LabelFrame(tab, text="Tạo phiếu xuất + kiểm tra tồn trước khi xuất")
        frame.pack(fill="x", padx=10, pady=10)

        self.exp_receipt_no = tk.StringVar(value=f"PX-{uuid4().hex[:6].upper()}")
        self.exp_customer = tk.StringVar()
        self.exp_note = tk.StringVar()
        self.exp_product = tk.StringVar()
        self.exp_qty = tk.StringVar(value="1")
        self.exp_price = tk.StringVar(value="0")

        ttk.Label(frame, text="Mã phiếu").grid(row=0, column=0, padx=6, pady=6)
        ttk.Entry(frame, textvariable=self.exp_receipt_no, width=18).grid(row=0, column=1, padx=6, pady=6)
        ttk.Label(frame, text="Khách hàng").grid(row=0, column=2, padx=6, pady=6)
        ttk.Entry(frame, textvariable=self.exp_customer, width=22).grid(row=0, column=3, padx=6, pady=6)
        ttk.Label(frame, text="Ghi chú").grid(row=0, column=4, padx=6, pady=6)
        ttk.Entry(frame, textvariable=self.exp_note, width=28).grid(row=0, column=5, padx=6, pady=6)

        ttk.Button(frame, text="Tạo phiếu xuất", command=self.create_export_receipt).grid(row=0, column=6, padx=8)

        ttk.Label(frame, text="Sản phẩm").grid(row=1, column=0, padx=6, pady=6)
        self.exp_product_combo = ttk.Combobox(frame, textvariable=self.exp_product, state="readonly", width=22)
        self.exp_product_combo.grid(row=1, column=1, padx=6, pady=6)
        ttk.Label(frame, text="SL").grid(row=1, column=2, padx=6, pady=6)
        ttk.Entry(frame, textvariable=self.exp_qty, width=10).grid(row=1, column=3, padx=6, pady=6)
        ttk.Label(frame, text="Đơn giá xuất").grid(row=1, column=4, padx=6, pady=6)
        ttk.Entry(frame, textvariable=self.exp_price, width=12).grid(row=1, column=5, padx=6, pady=6)
        ttk.Button(frame, text="Xuất hàng", command=self.add_export_item).grid(row=1, column=6, padx=8)

        self.current_export_receipt_id: int | None = None

    def create_export_receipt(self) -> None:
        self.current_export_receipt_id = database.create_export_receipt(
            self.exp_receipt_no.get(), self.exp_customer.get(), int(self.current_user["id"]), self.exp_note.get()
        )
        messagebox.showinfo("Thành công", f"Đã tạo phiếu xuất ID={self.current_export_receipt_id}")

    def add_export_item(self) -> None:
        if self.current_export_receipt_id is None:
            messagebox.showwarning("Chưa có phiếu", "Hãy tạo phiếu xuất trước.")
            return
        product_id = self.product_lookup.get(self.exp_product.get())
        if not product_id:
            messagebox.showwarning("Thiếu dữ liệu", "Vui lòng chọn sản phẩm.")
            return
        try:
            database.add_export_item(self.current_export_receipt_id, product_id, int(self.exp_qty.get()), float(self.exp_price.get()))
            self.load_products()
            self.load_inventory()
            self.load_reports()
            messagebox.showinfo("Thành công", "Đã xuất kho và cập nhật tồn.")
        except ValueError as err:
            messagebox.showerror("Không thể xuất", str(err))

    # 7) Inventory management
    def _build_inventory_tab(self) -> None:
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="7. Tồn kho")

        self.inventory_tree = ttk.Treeview(tab, columns=("id", "name", "sku", "qty", "reorder", "status"), show="headings", height=18)
        headers = ["ID", "Tên", "SKU", "Tồn hiện tại", "Ngưỡng thấp", "Cảnh báo"]
        widths = [60, 250, 120, 130, 120, 140]
        for col, title, width in zip(("id", "name", "sku", "qty", "reorder", "status"), headers, widths):
            self.inventory_tree.heading(col, text=title)
            self.inventory_tree.column(col, width=width, anchor="center")
        self.inventory_tree.pack(fill="both", expand=True, padx=10, pady=12)

    def load_inventory(self) -> None:
        self._clear_tree(self.inventory_tree)
        for row in database.get_inventory_status():
            status = "⚠ Tồn thấp" if row["is_low_stock"] else "Ổn"
            self.inventory_tree.insert("", "end", values=(row["id"], row["name"], row["sku"], row["quantity"], row["reorder_level"], status))

    # 8) Reports
    def _build_report_tab(self) -> None:
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="8. Báo cáo")

        top = ttk.Frame(tab)
        top.pack(fill="x", padx=10, pady=8)
        ttk.Button(top, text="Làm mới báo cáo", command=self.load_reports).pack(side="left")

        self.report_tree = ttk.Treeview(tab, columns=("name", "sku", "import", "export"), show="headings", height=10)
        for col, title, width in [
            ("name", "Sản phẩm", 280),
            ("sku", "SKU", 120),
            ("import", "Tổng nhập", 120),
            ("export", "Tổng xuất", 120),
        ]:
            self.report_tree.heading(col, text=title)
            self.report_tree.column(col, width=width, anchor="center")
        self.report_tree.pack(fill="x", padx=10, pady=8)

        self.low_stock_tree = ttk.Treeview(tab, columns=("name", "sku", "qty", "reorder"), show="headings", height=8)
        for col, title, width in [
            ("name", "Sản phẩm tồn thấp", 280),
            ("sku", "SKU", 120),
            ("qty", "Tồn hiện tại", 120),
            ("reorder", "Ngưỡng thấp", 120),
        ]:
            self.low_stock_tree.heading(col, text=title)
            self.low_stock_tree.column(col, width=width, anchor="center")
        self.low_stock_tree.pack(fill="x", padx=10, pady=8)

    def load_reports(self) -> None:
        self._clear_tree(self.report_tree)
        for row in database.get_import_export_report():
            self.report_tree.insert("", "end", values=(row["name"], row["sku"], row["total_import"], row["total_export"]))

        self._clear_tree(self.low_stock_tree)
        for row in database.get_low_stock_report():
            self.low_stock_tree.insert("", "end", values=(row["name"], row["sku"], row["quantity"], row["reorder_level"]))

    # Common helpers
    def _clear_tree(self, tree: ttk.Treeview) -> None:
        for item in tree.get_children():
            tree.delete(item)

    def _load_lookups(self) -> None:
        categories = database.get_categories()
        suppliers = database.get_suppliers()
        products = database.search_products()

        self.category_lookup = database.get_lookup_map(categories)
        self.supplier_lookup = database.get_lookup_map(suppliers)
        self.product_lookup = {str(row["name"]): int(row["id"]) for row in products}

        self.category_combo["values"] = list(self.category_lookup.keys())
        self.supplier_combo["values"] = list(self.supplier_lookup.keys())
        self.imp_supplier_combo["values"] = list(self.supplier_lookup.keys())
        product_names = list(self.product_lookup.keys())
        self.imp_product_combo["values"] = product_names
        self.exp_product_combo["values"] = product_names

    def refresh_all(self) -> None:
        self.load_users()
        self.load_categories()
        self.load_suppliers()
        self.load_products()
        self.load_inventory()
        self.load_reports()
        self._load_lookups()

    def _apply_permissions(self) -> None:
        is_admin = self.current_user.get("role") == "admin"
        if is_admin:
            return

        self.user_add_btn.configure(state="disabled")
        self.tabs.tab(0, state="disabled")


def run_app() -> None:
    database.init_db()

    login_root = tk.Tk()
    login = LoginWindow(login_root)
    login_root.mainloop()

    if not login.user:
        return

    root = tk.Tk()
    app = WarehouseApp(root, login.user)
    _ = app
    root.mainloop()


if __name__ == "__main__":
    run_app()
