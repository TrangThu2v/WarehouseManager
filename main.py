import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import sqlite3

import database


class WarehouseApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Quản lý kho hàng")
        self.root.geometry("900x520")

        self.selected_id: int | None = None

        self._build_form()
        self._build_tools()
        self._build_table()
        self.load_products()

    def _build_form(self) -> None:
        frame = ttk.LabelFrame(self.root, text="Thông tin sản phẩm")
        frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(frame, text="Tên sản phẩm").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.name_var, width=28).grid(row=0, column=1, padx=8, pady=8)

        ttk.Label(frame, text="SKU").grid(row=0, column=2, padx=8, pady=8, sticky="w")
        self.sku_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.sku_var, width=20).grid(row=0, column=3, padx=8, pady=8)

        ttk.Label(frame, text="Số lượng").grid(row=1, column=0, padx=8, pady=8, sticky="w")
        self.qty_var = tk.StringVar(value="0")
        ttk.Entry(frame, textvariable=self.qty_var, width=28).grid(row=1, column=1, padx=8, pady=8)

        ttk.Label(frame, text="Đơn giá").grid(row=1, column=2, padx=8, pady=8, sticky="w")
        self.price_var = tk.StringVar(value="0")
        ttk.Entry(frame, textvariable=self.price_var, width=20).grid(row=1, column=3, padx=8, pady=8)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=4, pady=8)

        ttk.Button(btn_frame, text="Thêm", command=self.add_product).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Cập nhật", command=self.update_product).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Xóa", command=self.delete_product).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Làm mới", command=self.clear_form).pack(side="left", padx=4)

    def _build_tools(self) -> None:
        frame = ttk.LabelFrame(self.root, text="Tìm kiếm / Sắp xếp / Nhập - Xuất hàng")
        frame.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Label(frame, text="Từ khóa").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.search_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.search_var, width=22).grid(row=0, column=1, padx=8, pady=8)
        ttk.Button(frame, text="Tìm kiếm", command=self.search_products).grid(row=0, column=2, padx=4, pady=8)
        ttk.Button(frame, text="Xóa lọc", command=self.reset_filters).grid(row=0, column=3, padx=4, pady=8)

        ttk.Label(frame, text="Sắp xếp theo").grid(row=0, column=4, padx=(20, 8), pady=8, sticky="w")
        self.sort_field_var = tk.StringVar(value="id")
        sort_field_combo = ttk.Combobox(
            frame,
            textvariable=self.sort_field_var,
            values=["id", "name", "sku", "quantity", "price"],
            width=12,
            state="readonly",
        )
        sort_field_combo.grid(row=0, column=5, padx=8, pady=8)

        self.sort_order_var = tk.StringVar(value="DESC")
        sort_order_combo = ttk.Combobox(
            frame,
            textvariable=self.sort_order_var,
            values=["DESC", "ASC"],
            width=7,
            state="readonly",
        )
        sort_order_combo.grid(row=0, column=6, padx=8, pady=8)
        ttk.Button(frame, text="Sắp xếp", command=self.sort_products).grid(row=0, column=7, padx=4, pady=8)

        ttk.Button(frame, text="Nhập hàng", command=self.import_stock).grid(row=1, column=1, padx=8, pady=(0, 8))
        ttk.Button(frame, text="Xuất hàng", command=self.export_stock).grid(row=1, column=2, padx=8, pady=(0, 8))

    def _build_table(self) -> None:
        table_frame = ttk.Frame(self.root)
        table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        columns = ("id", "name", "sku", "quantity", "price")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Tên sản phẩm")
        self.tree.heading("sku", text="SKU")
        self.tree.heading("quantity", text="Số lượng")
        self.tree.heading("price", text="Đơn giá")

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("name", width=280)
        self.tree.column("sku", width=150, anchor="center")
        self.tree.column("quantity", width=120, anchor="center")
        self.tree.column("price", width=140, anchor="e")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_select_row)

    def _render_products(self, products: list[sqlite3.Row]) -> None:
        for row_id in self.tree.get_children():
            self.tree.delete(row_id)

        for item in products:
            self.tree.insert(
                "",
                "end",
                values=(item["id"], item["name"], item["sku"], item["quantity"], f"{item['price']:.2f}"),
            )

    def load_products(self) -> None:
        self._render_products(database.get_all_products())

    def _parse_inputs(self) -> tuple[str, str, int, float] | None:
        name = self.name_var.get().strip()
        sku = self.sku_var.get().strip()

        if not name or not sku:
            messagebox.showwarning("Thiếu dữ liệu", "Tên sản phẩm và SKU là bắt buộc.")
            return None

        try:
            quantity = int(self.qty_var.get())
            price = float(self.price_var.get())
        except ValueError:
            messagebox.showwarning("Sai định dạng", "Số lượng phải là số nguyên, đơn giá phải là số.")
            return None

        if quantity < 0 or price < 0:
            messagebox.showwarning("Giá trị không hợp lệ", "Số lượng và đơn giá không được âm.")
            return None

        return name, sku, quantity, price

    def add_product(self) -> None:
        data = self._parse_inputs()
        if not data:
            return

        try:
            database.add_product(*data)
            self.load_products()
            self.clear_form()
            messagebox.showinfo("Thành công", "Đã thêm sản phẩm mới.")
        except sqlite3.IntegrityError:
            messagebox.showerror("Lỗi dữ liệu", "SKU đã tồn tại, vui lòng nhập SKU khác.")

    def update_product(self) -> None:
        if self.selected_id is None:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn một sản phẩm để cập nhật.")
            return

        data = self._parse_inputs()
        if not data:
            return

        try:
            database.update_product(self.selected_id, *data)
            self.load_products()
            self.clear_form()
            messagebox.showinfo("Thành công", "Đã cập nhật sản phẩm.")
        except sqlite3.IntegrityError:
            messagebox.showerror("Lỗi dữ liệu", "SKU đã tồn tại, vui lòng nhập SKU khác.")

    def delete_product(self) -> None:
        if self.selected_id is None:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn một sản phẩm để xóa.")
            return

        if not messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa sản phẩm này?"):
            return

        database.delete_product(self.selected_id)
        self.load_products()
        self.clear_form()
        messagebox.showinfo("Thành công", "Đã xóa sản phẩm.")

    def search_products(self) -> None:
        keyword = self.search_var.get()
        products = database.search_products(keyword)
        self._render_products(products)
        self.selected_id = None
        self.tree.selection_remove(self.tree.selection())

    def sort_products(self) -> None:
        sort_by = self.sort_field_var.get()
        descending = self.sort_order_var.get() == "DESC"
        products = database.sort_products(sort_by=sort_by, descending=descending)
        self._render_products(products)
        self.selected_id = None
        self.tree.selection_remove(self.tree.selection())

    def _ask_movement_quantity(self, title: str) -> int | None:
        qty = simpledialog.askinteger(title, "Nhập số lượng:", parent=self.root, minvalue=1)
        return qty

    def import_stock(self) -> None:
        if self.selected_id is None:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn sản phẩm để nhập hàng.")
            return

        qty = self._ask_movement_quantity("Nhập hàng")
        if qty is None:
            return

        note = simpledialog.askstring("Nhập hàng", "Ghi chú (không bắt buộc):", parent=self.root)
        try:
            database.import_stock(self.selected_id, qty, note)
        except ValueError as error:
            messagebox.showerror("Lỗi nhập hàng", str(error))
            return

        self.load_products()
        messagebox.showinfo("Thành công", f"Đã nhập {qty} sản phẩm vào kho.")

    def export_stock(self) -> None:
        if self.selected_id is None:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn sản phẩm để xuất hàng.")
            return

        qty = self._ask_movement_quantity("Xuất hàng")
        if qty is None:
            return

        note = simpledialog.askstring("Xuất hàng", "Ghi chú (không bắt buộc):", parent=self.root)
        try:
            database.export_stock(self.selected_id, qty, note)
        except ValueError as error:
            messagebox.showerror("Lỗi xuất hàng", str(error))
            return

        self.load_products()
        messagebox.showinfo("Thành công", f"Đã xuất {qty} sản phẩm khỏi kho.")

    def reset_filters(self) -> None:
        self.search_var.set("")
        self.sort_field_var.set("id")
        self.sort_order_var.set("DESC")
        self.load_products()

    def on_select_row(self, _event: tk.Event) -> None:
        selected = self.tree.selection()
        if not selected:
            return

        values = self.tree.item(selected[0], "values")
        self.selected_id = int(values[0])
        self.name_var.set(values[1])
        self.sku_var.set(values[2])
        self.qty_var.set(values[3])
        self.price_var.set(values[4])

    def clear_form(self) -> None:
        self.selected_id = None
        self.name_var.set("")
        self.sku_var.set("")
        self.qty_var.set("0")
        self.price_var.set("0")
        self.search_var.set("")
        self.sort_field_var.set("id")
        self.sort_order_var.set("DESC")
        self.tree.selection_remove(self.tree.selection())
        self.load_products()


def main() -> None:
    database.init_db()
    seed_sample_products = getattr(database, "seed_sample_products", None)
    if callable(seed_sample_products):
        seed_sample_products(25)
    root = tk.Tk()
    app = WarehouseApp(root)
    _ = app
    root.mainloop()


if __name__ == "__main__":
    main()
