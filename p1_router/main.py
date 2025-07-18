import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import csv
import subprocess
from ui.dmx_visualizer import main as run_main_visualizer
from ui.tester import main as run_tester
from ui.unity_pong_listener import main as run_pong


CONFIG_PATH = "config/config.json"

class ConfigEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Config Editor")
        self.geometry("1000x500")
        self.config_data = []
        self.load_config()

        self.columns = ("universe", "from", "to", "ip")
        self.tree = ttk.Treeview(self, columns=self.columns, show="headings")
        for col in self.columns:
            self.tree.heading(col, text=col.capitalize())
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.populate_tree()

        self.tree.bind('<Double-1>', self.on_double_click)

        self.button_frame = tk.Frame(self)
        self.button_frame.pack(pady=10)

        tk.Button(self.button_frame, text="Add Line", command=self.add_line).pack(side=tk.LEFT, padx=5)
        tk.Button(self.button_frame, text="Delete Selected", command=self.delete_selected).pack(side=tk.LEFT, padx=5)
        tk.Button(self.button_frame, text="Import CSV", command=self.import_csv).pack(side=tk.LEFT, padx=5)
        tk.Button(self.button_frame, text="Export CSV", command=self.export_csv).pack(side=tk.LEFT, padx=5)
        tk.Button(self.button_frame, text="Save Config", command=self.save_config).pack(side=tk.LEFT, padx=5)
        tk.Button(self.button_frame, text="Run Visualizer", command=self.run_visualizer).pack(side=tk.LEFT, padx=5)
        tk.Button(self.button_frame, text="Run Tester", command=self.run_tester).pack(side=tk.LEFT, padx=5)
        tk.Button(self.button_frame, text="Run pong", command=self.run_pong).pack(side=tk.LEFT, padx=5)


    def load_config(self):
        try:
            with open(CONFIG_PATH, "r") as f:
                self.config_data = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config: {e}")
            self.destroy()

    def populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        for entry in self.config_data:
            self.tree.insert("", tk.END, values=(
                entry["universe"], entry["from"], entry["to"], entry["ip"]
            ))

    def on_double_click(self, event):
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        if not item or not column:
            return

        col_idx = int(column.replace('#', '')) - 1
        col_name = self.columns[col_idx]
        if col_name == "universe":
            return

        old_value = self.tree.item(item, "values")[col_idx]
        entry = tk.Entry(self)
        entry.insert(0, old_value)
        entry.place(x=event.x_root - self.winfo_rootx(), y=event.y_root - self.winfo_rooty())
        entry.focus()

        def save_edit(event=None):
            new_value = entry.get()
            values = list(self.tree.item(item, "values"))
            values[col_idx] = new_value
            self.tree.item(item, values=values)
            entry.destroy()
            # Update config_data
            universe_val = int(values[0])
            for c_entry in self.config_data:
                if c_entry["universe"] == universe_val:
                    if col_name in ["from", "to"]:
                        c_entry[col_name] = int(new_value)
                    else:
                        c_entry[col_name] = new_value
                    break

        entry.bind("<Return>", save_edit)
        entry.bind("<FocusOut>", lambda e: entry.destroy())

    def add_line(self):
        new_entry = {"universe": 0, "from": 0, "to": 0, "ip": "0.0.0.0"}
        self.config_data.append(new_entry)
        self.tree.insert("", tk.END, values=(0, 0, 0, "0.0.0.0"))

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Please select a row to delete.")
            return
        for item in selected:
            values = self.tree.item(item, "values")
            universe_val = int(values[0])
            self.config_data = [e for e in self.config_data if e["universe"] != universe_val]
            self.tree.delete(item)

    def import_csv(self):
        filepath = filedialog.askopenfilename(title="Select CSV file", filetypes=[("CSV files", "*.csv")])
        if not filepath:
            return
        try:
            with open(filepath, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                self.config_data = []
                for row in reader:
                    self.config_data.append({
                        "universe": int(row["universe"]),
                        "from": int(row["from"]),
                        "to": int(row["to"]),
                        "ip": row["ip"]
                    })
            self.populate_tree()
            messagebox.showinfo("Import", "CSV imported successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import CSV: {e}")

    def export_csv(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not filepath:
            return
        try:
            with open(filepath, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.columns)
                writer.writeheader()
                for entry in self.config_data:
                    writer.writerow({
                        "universe": entry["universe"],
                        "from": entry["from"],
                        "to": entry["to"],
                        "ip": entry["ip"]
                    })
            messagebox.showinfo("Export", "CSV exported successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export CSV: {e}")

    def save_config(self):
        try:
            with open(CONFIG_PATH, "w") as f:
                json.dump(self.config_data, f, indent=2)
            messagebox.showinfo("Success", "Config saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {e}")

    def run_visualizer(self):
        self.save_config()
        self.destroy()
        while not run_main_visualizer():
            continue
        self.__init__()

    def run_tester(self):
        self.save_config()
        self.destroy()
        while not run_tester():
            continue
        self.__init__()

    def run_pong(self):
        self.save_config()
        self.destroy()
        while not run_pong():
            continue
        self.__init__()

if __name__ == "__main__":
    app = ConfigEditor()
    app.mainloop()
