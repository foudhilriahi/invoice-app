import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import ImageTk
import threading, queue, os, json, sqlite3, pandas as pd

from processor import process_invoice

# ─── Styling Helpers ────────────────────────────────────────────
def style_button(btn):
    btn.config(
        bg="#4CAF50", fg="white",
        font=("Arial", 12, "bold"),
        padx=12, pady=6,
        relief=tk.FLAT,
        activebackground="#45a049"
    )
    return btn

def style_label(lbl):
    lbl.config(font=("Arial", 14, "bold"), fg="#333")
    return lbl

def style_text(txt):
    txt.config(font=("Arial", 10), wrap=tk.WORD)
    return txt

# ─── Main App ───────────────────────────────────────────────────
class InvoiceApp:
    def __init__(self, root):
        self.root = root
        root.title("🧾 GOD MODE INVOICE AI")
        root.geometry("1000x800")
        root.configure(bg="#f0f0f0")

        self.results = []
        self.work_queue = queue.Queue()

        # Title
        style_label(
            tk.Label(root, text="INVOICE.AI ⚡")
        ).pack(pady=15)

        # Image Preview
        self.image_label = tk.Label(root, bg="#ddd", width=60, height=15, relief=tk.RIDGE)
        self.image_label.pack(pady=10)

        # Table of results
        cols = ["File","Field","Value","Confidence"]
        self.tree = ttk.Treeview(root, columns=cols, show="headings", height=12)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=200, anchor=tk.W)
        self.tree.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # Processing & Export Buttons Frame
        btn_frame = tk.Frame(root, bg="#f0f0f0")
        btn_frame.pack(pady=10)

        # Select Files
        self.btn_select = style_button(
            tk.Button(btn_frame, text="📂 Select Files", command=self.start_processing)
        )
        self.btn_select.grid(row=0, column=0, padx=8)

        # Export CSV
        self.btn_csv = style_button(
            tk.Button(btn_frame, text="💾 Export CSV", command=self.export_csv, state=tk.DISABLED)
        )
        self.btn_csv.grid(row=0, column=1, padx=8)

        # Export Excel
        self.btn_xlsx = style_button(
            tk.Button(btn_frame, text="📊 Export Excel", command=self.export_excel, state=tk.DISABLED)
        )
        self.btn_xlsx.grid(row=0, column=2, padx=8)

        # Save JSON + DB
        self.btn_json = style_button(
            tk.Button(btn_frame, text="💽 Save JSON/DB", command=self.save_json_db, state=tk.DISABLED)
        )
        self.btn_json.grid(row=0, column=3, padx=8)

        # Start polling queue
        root.after(100, self.check_queue)

    def start_processing(self):
        paths = filedialog.askopenfilenames(
            filetypes=[("PDF/Images","*.pdf *.jpg *.png *.jpeg")]
        )
        if not paths:
            return

        # Disable exports until done
        for btn in (self.btn_select, self.btn_csv, self.btn_xlsx, self.btn_json):
            btn.config(state=tk.DISABLED)

        # Clear old data
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.results.clear()

        # Launch worker thread
        threading.Thread(target=self.worker, args=(paths,), daemon=True).start()

    def worker(self, paths):
        for p in paths:
            try:
                img, rows = process_invoice(p)
                self.work_queue.put((img, rows, os.path.basename(p)))
            except Exception as e:
                self.work_queue.put(("__ERROR__", str(e), None))
        self.work_queue.put(None)

    def check_queue(self):
        try:
            item = self.work_queue.get_nowait()
        except queue.Empty:
            pass
        else:
            if item is None:
                messagebox.showinfo("✅ Done", "All files processed!")
                # Enable export buttons
                if self.results:
                    self.btn_csv.config(state=tk.NORMAL)
                    self.btn_xlsx.config(state=tk.NORMAL)
                    self.btn_json.config(state=tk.NORMAL)
                self.btn_select.config(state=tk.NORMAL)
            else:
                img, rows, fname = item
                if img == "__ERROR__":
                    messagebox.showerror("Error", rows)
                else:
                    self.display_image(img)
                    for r in rows:
                        val = r["value"]
                        if not isinstance(val, str):
                            val = json.dumps(val, ensure_ascii=False)
                        self.tree.insert("", tk.END,
                                         values=(fname, r["field"], val, r["confidence"]))
                        self.results.append({
                            "File": fname,
                            "field": r["field"],
                            "value": val,
                            "confidence": r["confidence"]
                        })
        finally:
            self.root.after(100, self.check_queue)

    def display_image(self, img):
        img.thumbnail((500,500))
        self.tk_img = ImageTk.PhotoImage(img)
        self.image_label.config(image=self.tk_img)

    def export_csv(self):
        if not self.results:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV","*.csv")],
            initialfile="output.csv"
        )
        if path:
            pd.DataFrame(self.results).to_csv(path, index=False, encoding="utf-8")
            messagebox.showinfo("✅ Saved", f"CSV saved to:\n{path}")

    def export_excel(self):
        if not self.results:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel","*.xlsx")],
            initialfile="output.xlsx"
        )
        if path:
            pd.DataFrame(self.results).to_excel(path, index=False)
            messagebox.showinfo("✅ Saved", f"Excel saved to:\n{path}")

    def save_json_db(self):
        if not self.results:
            return
        # JSON Save
        json_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON","*.json")],
            initialfile="output.json"
        )
        if json_path:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(self.results, f, indent=4, ensure_ascii=False)

        # DB Save
        db_path = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("SQLite DB","*.db")],
            initialfile="invoices.db"
        )
        if db_path:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS invoices (
                    filename TEXT, field TEXT, value TEXT, confidence TEXT
                )
            """)
            for i in self.results:
                c.execute(
                    "INSERT INTO invoices VALUES (?,?,?,?)",
                    (i["File"], i["field"], i["value"], i["confidence"])
                )
            conn.commit()
            conn.close()

        messagebox.showinfo("✅ Saved", f"JSON & DB saved to:\n{json_path}\n{db_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = InvoiceApp(root)
    root.mainloop()
