"""Desktop GUI for the Mandi Crop Sales & Price Tracker.

The GUI deliberately reuses the same db, CRUD, seed, validation, and analytics
modules as the CLI so both interfaces always operate on the same live data.
"""

from datetime import datetime
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from typing import Any, Callable

from analytics import (
    avg_price_per_crop_per_mandi,
    district_wise_quantity,
    monthly_sales_trend,
    pending_payments_summary,
    revenue_per_farmer,
    top_n_farmers,
    wheat_price_distribution,
)
from crud import (
    add_facility,
    add_farmer,
    add_mandi,
    add_sale,
    delete_farmer,
    delete_sale,
    list_farmers,
    list_sales,
    mark_pending_as_paid,
    update_land,
    update_sale_rate,
)
from db import get_db
from seed_data import seed_all
from validation_demo import run_validation_tests


class MandiGUI:
    """Build and control the desktop application window."""

    def __init__(self, db: Any) -> None:
        """Create the window and connect its controls to MongoDB operations."""
        self.db = db
        self.root = tk.Tk()
        self.root.title("Mandi Crop Sales & Price Tracker")
        self.root.geometry("1250x760")
        self.root.minsize(980, 620)
        self.root.configure(bg="#eef5f0")
        self.status = tk.StringVar(value="Connected to mandi_db")
        self._configure_style()
        self._build_header()
        self._build_tabs()
        self.refresh_all()

    def _configure_style(self) -> None:
        """Configure a clean green-and-gold visual theme."""
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TNotebook", background="#eef5f0", borderwidth=0)
        style.configure("TNotebook.Tab", padding=(16, 8), font=("Segoe UI", 10, "bold"))
        style.configure("Treeview", rowheight=28, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        style.configure("Accent.TButton", foreground="white", background="#26734d",
                        font=("Segoe UI", 9, "bold"), padding=7)
        style.map("Accent.TButton", background=[("active", "#1b5639")])

    def _build_header(self) -> None:
        """Create the title, live collection counts, and status bar."""
        header = tk.Frame(self.root, bg="#1f5f43", padx=20, pady=15)
        header.pack(fill="x")
        tk.Label(header, text="MANDI CROP SALES & PRICE TRACKER",
                 fg="white", bg="#1f5f43", font=("Segoe UI", 20, "bold")).pack(anchor="w")
        tk.Label(header, text="A live farmer-friendly view of sales, prices, and payments",
                 fg="#d9f2df", bg="#1f5f43", font=("Segoe UI", 10)).pack(anchor="w")
        self.count_label = tk.Label(header, fg="#ffe8a3", bg="#1f5f43",
                                    font=("Segoe UI", 10, "bold"))
        self.count_label.pack(anchor="w", pady=(8, 0))

    def _build_tabs(self) -> None:
        """Create the operational tabs."""
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=14, pady=14)
        self.farmer_tab = ttk.Frame(self.tabs, padding=12)
        self.mandi_tab = ttk.Frame(self.tabs, padding=12)
        self.sales_tab = ttk.Frame(self.tabs, padding=12)
        self.analytics_tab = ttk.Frame(self.tabs, padding=12)
        self.tools_tab = ttk.Frame(self.tabs, padding=12)
        for tab, title in ((self.farmer_tab, "Farmers"), (self.mandi_tab, "Mandis"),
                           (self.sales_tab, "Sales"), (self.analytics_tab, "Analytics"),
                           (self.tools_tab, "Tools")):
            self.tabs.add(tab, text=title)
        self._build_farmers()
        self._build_mandis()
        self._build_sales()
        self._build_analytics()
        self._build_tools()
        ttk.Label(self.root, textvariable=self.status, anchor="w",
                  relief="sunken", padding=5).pack(fill="x", side="bottom")

    def _button_bar(self, parent: tk.Misc, buttons: list[tuple[str, Callable[[], None]]]) -> None:
        """Add a row of consistently styled action buttons."""
        bar = ttk.Frame(parent)
        bar.pack(fill="x", pady=(0, 10))
        for text, command in buttons:
            ttk.Button(bar, text=text, command=command, style="Accent.TButton").pack(side="left", padx=(0, 7))

    def _tree(self, parent: tk.Misc, columns: list[tuple[str, str]]) -> ttk.Treeview:
        """Create and return a stretchable tabular data view."""
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)
        tree = ttk.Treeview(frame, columns=[key for key, _ in columns], show="headings")
        for key, label in columns:
            tree.heading(key, text=label)
            tree.column(key, width=140, anchor="w")
        scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        return tree

    @staticmethod
    def _clear(tree: ttk.Treeview) -> None:
        """Remove all rows from a tree."""
        tree.delete(*tree.get_children())

    def _build_farmers(self) -> None:
        """Build farmer CRUD controls."""
        self._button_bar(self.farmer_tab, [
            ("Add Farmer", self.add_farmer_dialog), ("Update Land", self.update_farmer_dialog),
            ("Delete Farmer", self.delete_farmer_dialog), ("Refresh", self.refresh_farmers),
        ])
        self.farmer_tree = self._tree(self.farmer_tab, [
            ("name", "Name"), ("phone", "Phone"), ("land", "Land (acres)"),
            ("village", "Village"), ("district", "District"),
        ])

    def _build_mandis(self) -> None:
        """Build mandi CRUD controls."""
        self._button_bar(self.mandi_tab, [
            ("Add Mandi", self.add_mandi_dialog), ("Add Facility", self.facility_dialog),
            ("Add Commodity", self.commodity_dialog), ("Refresh", self.refresh_mandis),
        ])
        self.mandi_tree = self._tree(self.mandi_tab, [
            ("name", "Mandi"), ("district", "District"), ("commodities", "Commodities"),
            ("facilities", "Facilities"),
        ])

    def _build_sales(self) -> None:
        """Build sales CRUD controls."""
        self._button_bar(self.sales_tab, [
            ("Add Sale", self.add_sale_dialog), ("Update Rate", self.rate_dialog),
            ("Mark Mandi Paid", self.paid_dialog), ("Delete Sale", self.delete_sale_dialog),
            ("Refresh", self.refresh_sales),
        ])
        self.sales_tree = self._tree(self.sales_tab, [
            ("id", "Sale ID"), ("crop", "Crop"), ("qty", "Quintals"),
            ("rate", "Rate"), ("amount", "Total"), ("date", "Date"), ("status", "Status"),
        ])

    def _build_analytics(self) -> None:
        """Build the report selector and report table."""
        bar = ttk.Frame(self.analytics_tab)
        bar.pack(fill="x", pady=(0, 10))
        ttk.Label(bar, text="Choose report:").pack(side="left", padx=(0, 8))
        self.report_var = tk.StringVar(value="Revenue by Farmer")
        self.report_box = ttk.Combobox(bar, textvariable=self.report_var, state="readonly", width=30,
                                       values=["Revenue by Farmer", "Average Crop Prices", "Monthly Sales Trend",
                                               "Top Farmers", "District-wise Quantity", "Pending Payments",
                                               "Wheat Rate Distribution"])
        self.report_box.pack(side="left")
        ttk.Button(bar, text="Run Report", command=self.run_report, style="Accent.TButton").pack(side="left", padx=8)
        self.report_tree = self._tree(self.analytics_tab, [("data", "Report output")])

    def _build_tools(self) -> None:
        """Build reset, validation, and database utility controls."""
        self._button_bar(self.tools_tab, [
            ("Load Sample Data (reset)", self.load_seed),
            ("Run Validation Demo", self.run_validation),
            ("Refresh All", self.refresh_all),
        ])
        self.tool_text = tk.Text(self.tools_tab, height=20, wrap="word", font=("Consolas", 10))
        self.tool_text.pack(fill="both", expand=True)
        self.tool_text.insert("end", "Use this tab to reset the database, load demo data, or run validation tests.\n")
        self.tool_text.configure(state="disabled")

    def refresh_all(self) -> None:
        """Refresh every data view and the live record counters."""
        self.refresh_farmers()
        self.refresh_mandis()
        self.refresh_sales()
        self.count_label.configure(text=f"Farmers: {self.db.farmers.count_documents({})}   |   "
                                        f"Mandis: {self.db.mandis.count_documents({})}   |   "
                                        f"Sales: {self.db.sales.count_documents({})}")
        self.status.set("Data refreshed from MongoDB")

    def refresh_farmers(self) -> None:
        """Load farmers into the farmer table."""
        self._clear(self.farmer_tree)
        for row in list_farmers(self.db):
            address = row.get("address", {})
            self.farmer_tree.insert("", "end", values=(row["name"], row["phone"], row["land_acres"],
                                                       address.get("village", ""), address.get("district", "")))

    def refresh_mandis(self) -> None:
        """Load mandis into the mandi table."""
        self._clear(self.mandi_tree)
        for row in self.db.mandis.find().sort("name", 1):
            self.mandi_tree.insert("", "end", values=(row["name"], row["district"],
                                                      ", ".join(row.get("commodities", [])),
                                                      ", ".join(row.get("facilities", []))))

    def refresh_sales(self) -> None:
        """Load the 100 most recent sales into the sales table."""
        self._clear(self.sales_tree)
        for row in list_sales(self.db, limit=100):
            self.sales_tree.insert("", "end", iid=str(row["_id"]), values=(
                str(row["_id"]), row["crop"]["name"], row["quantity_quintals"],
                row["rate_per_quintal"], f"₹{row['total_amount']:,.2f}",
                row["sale_date"].strftime("%Y-%m-%d"), row.get("payment_status", "Pending")))

    @staticmethod
    def _prompt_fields(title: str, fields: list[tuple[str, str]]) -> dict[str, str] | None:
        """Collect a small form using a modal dialog."""
        dialog = tk.Toplevel()
        dialog.title(title)
        dialog.transient()
        dialog.grab_set()
        entries: dict[str, tk.Entry] = {}
        for index, (key, label) in enumerate(fields):
            ttk.Label(dialog, text=label).grid(row=index, column=0, padx=10, pady=6, sticky="w")
            entry = ttk.Entry(dialog, width=34)
            entry.grid(row=index, column=1, padx=10, pady=6)
            entries[key] = entry
        result: dict[str, str] | None = None

        def submit() -> None:
            nonlocal result
            result = {key: entry.get().strip() for key, entry in entries.items()}
            dialog.destroy()

        ttk.Button(dialog, text="Save", command=submit, style="Accent.TButton").grid(
            row=len(fields), column=0, columnspan=2, pady=10)
        dialog.wait_window()
        return result

    def _run(self, action: Callable[[], None]) -> None:
        """Run a GUI action and show database/input errors clearly."""
        try:
            action()
            self.refresh_all()
        except Exception as exc:
            messagebox.showerror("Operation failed", str(exc))

    def add_farmer_dialog(self) -> None:
        """Open the add-farmer form."""
        data = self._prompt_fields("Add Farmer", [
            ("name", "Full name"), ("phone", "10-digit phone"), ("land", "Land acres"),
            ("village", "Village"), ("district", "District"), ("pincode", "Pincode"),
            ("bank", "Bank name"), ("last4", "Account last 4 digits"),
        ])
        if data:
            self._run(lambda: add_farmer(self.db, data["name"], data["phone"], float(data["land"]),
                                         data["village"], data["district"], data["pincode"],
                                         data["bank"], data["last4"]))

    def update_farmer_dialog(self) -> None:
        """Open the update-land form."""
        data = self._prompt_fields("Update Farmer Land", [("phone", "Farmer phone"), ("land", "New acres")])
        if data:
            self._run(lambda: self._notify(update_land(self.db, data["phone"], float(data["land"])), "farmer"))

    def delete_farmer_dialog(self) -> None:
        """Delete a farmer and its referenced sales after confirmation."""
        phone = simpledialog.askstring("Delete Farmer", "Farmer phone:", parent=self.root)
        if phone and messagebox.askyesno("Confirm", "Delete this farmer and all linked sales?"):
            self._run(lambda: self._notify(delete_farmer(self.db, phone), "farmer"))

    def add_mandi_dialog(self) -> None:
        """Open the add-mandi form."""
        data = self._prompt_fields("Add Mandi", [
            ("name", "Mandi name"), ("district", "District"),
            ("crops", "Commodities (comma separated)"), ("facilities", "Facilities (comma separated)"),
        ])
        if data:
            self._run(lambda: add_mandi(self.db, data["name"], data["district"],
                                         [x.strip() for x in data["crops"].split(",") if x.strip()],
                                         [x.strip() for x in data["facilities"].split(",") if x.strip()]))

    def facility_dialog(self) -> None:
        """Add a facility to a mandi."""
        data = self._prompt_fields("Add Facility", [("mandi", "Mandi name"), ("facility", "Facility")])
        if data:
            self._run(lambda: self._notify(add_facility(self.db, data["mandi"], data["facility"]), "mandi"))

    def commodity_dialog(self) -> None:
        """Add a commodity to a mandi."""
        data = self._prompt_fields("Add Commodity", [("mandi", "Mandi name"), ("commodity", "Commodity")])
        if data:
            self._run(lambda: self._notify(self.db.mandis.update_one(
                {"name": data["mandi"]}, {"$addToSet": {"commodities": data["commodity"]}}).modified_count, "mandi"))

    def add_sale_dialog(self) -> None:
        """Open the add-sale form."""
        data = self._prompt_fields("Add Sale", [
            ("phone", "Farmer phone"), ("mandi", "Mandi name"), ("crop", "Crop"),
            ("variety", "Variety"), ("grade", "Grade A/B/C"), ("qty", "Quantity quintals"),
            ("rate", "Rate per quintal"), ("date", "Date YYYY-MM-DD"), ("status", "Paid/Pending"),
        ])
        if data:
            self._run(lambda: add_sale(self.db, data["phone"], data["mandi"], data["crop"], data["variety"],
                                        data["grade"], float(data["qty"]), float(data["rate"]),
                                        datetime.strptime(data["date"], "%Y-%m-%d"), data["status"]))

    def rate_dialog(self) -> None:
        """Update the selected sale's rate."""
        selected = self.sales_tree.selection()
        if not selected:
            messagebox.showinfo("Select a sale", "Select a sale row first.")
            return
        rate = simpledialog.askfloat("Update Rate", "New rate per quintal:", parent=self.root, minvalue=0.01)
        if rate is not None:
            self._run(lambda: update_sale_rate(self.db, selected[0], rate))

    def paid_dialog(self) -> None:
        """Mark all pending sales for a mandi as paid."""
        mandi = simpledialog.askstring("Mark Paid", "Mandi name:", parent=self.root)
        if mandi:
            self._run(lambda: self._notify(mark_pending_as_paid(self.db, mandi), "sales"))

    def delete_sale_dialog(self) -> None:
        """Delete the selected sale."""
        selected = self.sales_tree.selection()
        if not selected:
            messagebox.showinfo("Select a sale", "Select a sale row first.")
            return
        if messagebox.askyesno("Confirm", "Delete the selected sale?"):
            self._run(lambda: delete_sale(self.db, selected[0]))

    def _notify(self, count: int, label: str) -> None:
        """Raise a useful message when an update matched no records."""
        if count == 0:
            raise ValueError(f"No {label} record was changed or found.")

    def run_report(self) -> None:
        """Execute the selected aggregation and show one row per tree entry."""
        reports: dict[str, Callable[[], list[dict]]] = {
            "Revenue by Farmer": lambda: revenue_per_farmer(self.db),
            "Average Crop Prices": lambda: avg_price_per_crop_per_mandi(self.db),
            "Monthly Sales Trend": lambda: monthly_sales_trend(self.db),
            "Top Farmers": lambda: top_n_farmers(self.db, 5),
            "District-wise Quantity": lambda: district_wise_quantity(self.db),
            "Pending Payments": lambda: pending_payments_summary(self.db),
            "Wheat Rate Distribution": lambda: wheat_price_distribution(self.db),
        }
        self._clear(self.report_tree)
        for row in reports[self.report_var.get()]():
            self.report_tree.insert("", "end", values=(self._display(row),))
        self.status.set(f"Report complete: {self.report_var.get()}")

    @staticmethod
    def _display(row: dict) -> str:
        """Convert a report row into a readable compact string."""
        return " | ".join(f"{key}: {value:,.2f}" if isinstance(value, float) else f"{key}: {value}"
                          for key, value in row.items())

    def load_seed(self) -> None:
        """Reset the database and load repeatable demonstration data."""
        if messagebox.askyesno("Reset database", "This deletes current demo data. Continue?"):
            self._run(lambda: seed_all(self.db))

    def run_validation(self) -> None:
        """Run validation examples and display their output in the tools tab."""
        self.tool_text.configure(state="normal")
        self.tool_text.delete("1.0", "end")
        import contextlib
        import io
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            run_validation_tests(self.db)
        self.tool_text.insert("end", output.getvalue())
        self.tool_text.configure(state="disabled")
        self.status.set("Validation demonstration complete")

    def run(self) -> None:
        """Start the Tkinter event loop."""
        self.root.mainloop()


def launch_gui() -> None:
    """Connect to MongoDB and launch the desktop application."""
    try:
        MandiGUI(get_db()).run()
    except Exception as exc:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("MongoDB connection failed", str(exc))
        root.destroy()


if __name__ == "__main__":
    launch_gui()
