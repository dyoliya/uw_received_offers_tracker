import os
import sqlite3
import pandas as pd
import tkinter as tk
import customtkinter as ctk
import threading
import dropbox
import pytz
from datetime import datetime
from tkinter import filedialog, simpledialog, messagebox
from tkcalendar import DateEntry
from config.dropbox_config import get_dropbox_client
from upload_to_slack import send_db_to_slack

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

DB_FILE = "uw_received_offers.db"
TABLE_NAME = "uw_received_offers"

# ---------------- Database Functions ----------------
def create_db_if_not_exists():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            ref_no TEXT PRIMARY KEY NOT NULL,
            target_county TEXT NOT NULL,
            target_state TEXT NOT NULL,
            received_from TEXT NOT NULL,
            date_received TEXT NOT NULL,
            owner TEXT,
            owner_id TEXT,
            first_name TEXT,
            middle_name TEXT,
            last_name TEXT,
            attn TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            zip_code TEXT,
            num_of_interests INTEGER,
            pdp_value REAL,
            total_value_low REAL,
            total_value_high REAL,
            list TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_rows(df, target_county, target_state, received_from, date_received, progress_callback=None):
    create_db_if_not_exists()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    total = len(df)
    year = datetime.now().year

    # Get latest ref_no for this year
    c.execute(f"""
        SELECT ref_no FROM {TABLE_NAME}
        WHERE ref_no LIKE 'UW-{year}-%'
        ORDER BY ref_no DESC
        LIMIT 1
    """)
    last_ref = c.fetchone()

    if last_ref:
        # Extract numeric part after year (e.g., UW-2026-0000123 → 123)
        last_id = int(last_ref[0].split("-")[-1])
    else:
        last_id = 0

    next_id = last_id + 1

    # Ensure Zip Code is string, keep empty if missing
    def format_zip(x):
        if pd.isna(x):
            return None          # store as NULL
        if isinstance(x, (int, float)):
            return str(int(x))   # numeric, remove .0
        val = str(x).strip()
        return val if val else None  # blank strings become NULL

    for idx, row in df.iterrows():
        next_id = last_id + idx + 1
        ref_no = f"UW-{year}-{next_id:07d}"
        target_county = target_county.upper()
        target_state = target_state.upper()
        received_from = received_from.title()
        zip_code = format_zip(row.get('Zip Code'))  # <-- call inside loop per row

        c.execute(f"""
            INSERT OR IGNORE INTO {TABLE_NAME} (
                ref_no, target_county, target_state, received_from, date_received,
                owner, owner_id, first_name, middle_name, last_name, attn, address, city, state, zip_code,
                num_of_interests, pdp_value, total_value_low, total_value_high, list
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            ref_no,
            target_county,
            target_state,
            received_from,
            date_received,
            row.get('Owner'),
            row.get('Owner ID'),
            row.get('First Name'),
            row.get('Middle Name'),
            row.get('Last Name'),
            row.get('ATTN'),
            row.get('Address'),
            row.get('City'),
            row.get('State'),
            zip_code,  # use formatted ZIP
            row.get('# of Interests'),
            row.get('PDP Value ($)'),
            row.get('Total Value - Low ($)'),
            row.get('Total Value - High ($)'),
            row.get('List')
        ))

        if progress_callback:
            progress_callback((idx+1)/total)

    conn.commit()
    conn.close()

# ---------------- DROPBOX UPLOAD ----------------
def upload_db_to_dropbox(local_db_path, dropbox_folder="/uw_received_offers_tracker", timestamp=None):
    """
    Uploads the local SQLite database to Dropbox.
    """

    dbx = get_dropbox_client()
    
    # Use provided timestamp, else generate now
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Keep the original filename, just add timestamp at the beginning
    filename = os.path.basename(local_db_path)
    timestamped_filename = f"{timestamp}_{filename}"

    dropbox_path = os.path.join(dropbox_folder, timestamped_filename).replace("\\", "/")

    with open(local_db_path, "rb") as f:
        dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode.overwrite)


# ---------------- GUI ----------------
class UWUploadUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("UW Received Offers Tracker v1.1.0")
        self.geometry("420x420")
        self.configure(fg_color="#273946")

        # ---------------- Title ----------------
        ctk.CTkLabel(
            self,
            text="UW Received Offers Tracker",
            text_color="#fff6de",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold")
        ).pack(pady=(30, 20))

        # ---------------- Frame for form ----------------
        self.form_frame = ctk.CTkFrame(self, fg_color="#273946")
        self.form_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Configure columns for spacing
        self.form_frame.grid_columnconfigure(0, weight=0, minsize=160)  # label column
        self.form_frame.grid_columnconfigure(1, weight=1)                # input column (expands)

        row = 0
        PADDING_Y = 5

        # ---------------- File selection ----------------
        ctk.CTkLabel(self.form_frame, text="Select file from Underwriter:", text_color="#fff6de")\
            .grid(row=row, column=0, sticky="e", pady=PADDING_Y, padx=(0,10))
        self.file_label = ctk.CTkLabel(self.form_frame, text="No file selected", text_color="#fff6de")
        self.file_label.grid(row=row, column=1, sticky="w", pady=PADDING_Y)
        row += 1

        self.select_file_btn = ctk.CTkButton(
            self.form_frame, text="Select Excel File", fg_color="#CB1F47",
            hover_color="#ffab4c", command=self.select_file
        )
        self.select_file_btn.grid(row=row, column=1, sticky="we", pady=(0,10))
        row += 1

        # ---------------- Target County ----------------
        ctk.CTkLabel(self.form_frame, text="Target County:", text_color="#fff6de")\
            .grid(row=row, column=0, sticky="w", pady=PADDING_Y, padx=(0,10))
        self.county_entry = ctk.CTkEntry(self.form_frame, placeholder_text="Enter county...")
        self.county_entry.grid(row=row, column=1, sticky="we", pady=PADDING_Y)
        row += 1

        # ---------------- Target State ----------------
        ctk.CTkLabel(self.form_frame, text="Target State:", text_color="#fff6de")\
            .grid(row=row, column=0, sticky="w", pady=PADDING_Y, padx=(0,10))
        self.state_entry = ctk.CTkEntry(self.form_frame, placeholder_text="Enter state...")
        self.state_entry.grid(row=row, column=1, sticky="we", pady=PADDING_Y)
        row += 1

        # ---------------- Received from ----------------
        ctk.CTkLabel(self.form_frame, text="Received from (Underwriter):", text_color="#fff6de")\
            .grid(row=row, column=0, sticky="w", pady=PADDING_Y, padx=(0,10))
        self.underwriters = self.load_underwriters()
        self.received_from_combo = ctk.CTkComboBox(self.form_frame, values=self.underwriters)
        self.received_from_combo.grid(row=row, column=1, sticky="we", pady=PADDING_Y)
        self.received_from_combo.set("Select or type...")
        self.received_from_combo.configure(state="normal")
        row += 1

        # ---------------- Date received ----------------
        ctk.CTkLabel(self.form_frame, text="Date received:", text_color="#fff6de")\
            .grid(row=row, column=0, sticky="w", pady=PADDING_Y, padx=(0,10))
        self.date_received_entry = DateEntry(
            self.form_frame, date_pattern='yyyy-mm-dd',
            background='darkblue', foreground='white', borderwidth=2, font=("Arial", 12)
        )
        self.date_received_entry.grid(row=row, column=1, sticky="we", pady=PADDING_Y)
        row += 1

        # ---------------- Progress bar ----------------
        self.progress = ctk.CTkProgressBar(self.form_frame, fg_color="#444444", progress_color="#CB1F47")
        self.progress.set(0)
        self.progress.grid(row=row, column=0, columnspan=2, sticky="we", pady=15)
        row += 1

        # ---------------- Upload button ----------------
        self.upload_btn = ctk.CTkButton(self.form_frame, text="UPLOAD", fg_color="#CB1F47",
                                        hover_color="#ffab4c", command=self.start_upload)
        self.upload_btn.grid(row=row, column=0, columnspan=2, sticky="we", pady=15)

                # github link (hihi)
        self.credit_label = ctk.CTkLabel(
        self,
        text="© dyoliya • GitHub",
        text_color="#484949",
        font=ctk.CTkFont(size=8, underline=False),
        cursor="hand2"
        )
        self.credit_label.place(relx=1.0, x=-10, y=1, anchor="ne") 
        self.credit_label.bind("<Button-1>", lambda e: self.open_url("https://github.com/dyoliya"))

    # Helper function
    def open_url(self, url):
        import webbrowser
        webbrowser.open(url)

    def load_underwriters(self):
        # Read underwriters from txt file, one per line
        file_path = "underwriters.txt"
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                underwriters = [line.strip() for line in f if line.strip()]
                underwriters.sort()  # alphabetically
                return underwriters
        return []

    def save_underwriter(self, name):
        file_path = "underwriters.txt"
        # Read existing names
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                existing = {line.strip() for line in f if line.strip()}
        else:
            existing = set()

        # Add name only if not present
        if name not in existing:
            existing.add(name.title())
            with open(file_path, "w", encoding="utf-8") as f:
                for w in sorted(existing):     # keep alphabetical
                    f.write(w + "\n")

        # Update combobox values
        self.received_from_combo.configure(values=sorted(existing))

    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if file_path:
            self.file_path = file_path
            self.file_label.configure(text=os.path.basename(file_path))

    def start_upload(self):
        if not hasattr(self, "file_path"):
            messagebox.showerror("Error", "Please select an Excel file first.")
            return
        county = self.county_entry.get()
        state = self.state_entry.get()
        received_from = self.received_from_combo.get()
        # NEW: Save typed underwriter if not already in the list
        if received_from and received_from != "Select or type...":
            self.save_underwriter(received_from)
        date_received = self.date_received_entry.get_date().strftime("%Y-%m-%d")

        if not all([county, state, received_from, date_received]):
            messagebox.showerror("Error", "All metadata fields are required.")
            return

        threading.Thread(target=self.upload_file, args=(county, state, received_from, date_received), daemon=True).start()

    def upload_file(self, county, state, received_from, date_received):
        self.upload_btn.configure(state="disabled")
        df = pd.read_excel(self.file_path)
        # Optional: ensure expected columns exist
        required_cols = ['Owner','Owner ID','First Name','Last Name','ATTN','Address','City','State','Zip Code',
                         '# of Interests','PDP Value ($)','Total Value - Low ($)','Total Value - High ($)']
        optional_cols = ['Middle Name', 'List']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            messagebox.showerror("Error", f"Missing required columns in Excel: {missing}")
            self.upload_btn.configure(state="normal")
            return

        def progress_callback(fraction):
            self.progress.set(fraction)

        insert_rows(df, county, state, received_from, date_received, progress_callback)

        # at the start of upload_file
        central_tz = pytz.timezone("US/Central")
        now_central = datetime.now(central_tz)
        # for Dropbox filename (compact)
        timestamp_for_dropbox = now_central.strftime("%Y%m%d_%H%M%S")

        # for Slack message (readable)
        timestamp_for_slack = now_central.strftime("%B %d, %Y at %H:%M:%S %Z")

        # --- Upload DB to Dropbox ---
        try:
            upload_db_to_dropbox(DB_FILE, dropbox_folder="/uw_received_offers_tracker", timestamp=timestamp_for_dropbox)
        except Exception as e:
            messagebox.showwarning("Dropbox Upload Failed", f"Could not upload to Dropbox:\n{e}")
        # --- Upload DB to Slack ---
        try:
            send_db_to_slack(DB_FILE, county=county, state=state, timestamp=timestamp_for_slack)
        except Exception as e:
            messagebox.showwarning("Slack Upload Failed", f"Could not send to Slack:\n{e}")

        self.progress.set(1.0)
        messagebox.showinfo("Success", "Upload complete!")
        self.progress.set(0)
        self.upload_btn.configure(state="normal")

if __name__ == "__main__":
    create_db_if_not_exists()
    app = UWUploadUI()
    app.mainloop()
