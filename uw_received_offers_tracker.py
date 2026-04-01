# -------------------------ABOUT --------------------------

# pyinstaller --onefile --windowed uw_received_offers_tracker.py
# Tool: UW Received Offers Tracker Tool
# Developer: dyoliya
# Created: 2025-11-20

# © 2025 dyoliya. All rights reserved.

# ---------------------------------------------------------

import os
import sqlite3
import pandas as pd
import tkinter as tk
import customtkinter as ctk
import threading
import pytz
from datetime import datetime
from tkinter import filedialog, simpledialog, messagebox
from tkcalendar import DateEntry
from upload_to_slack import send_db_to_slack
from googleapiclient.http import MediaFileUpload
from config.gdrive_config import get_drive_service

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

BACKUP_MARKER_FILE = "last_db_backup_run_date.txt"
DB_FILE = "uw_received_offers.db"
TABLE_NAME = "uw_received_offers"

GOOGLE_DRIVE_FOLDER_ID = "1I36aTRvd1QQpWm1fA_54JE2gl-kj_tz4"

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
            uploaded_by TEXT NOT NULL,
            date_uploaded TEXT NOT NULL,
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
            list TEXT,
            county_of_interest TEXT
        )
    """)

    # Check existing columns
    c.execute(f"PRAGMA table_info({TABLE_NAME})")
    existing_cols = {row[1].lower() for row in c.fetchall()}

    # Auto-add new columns for older DB versions
    if "county_of_interest" not in existing_cols:
        c.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN county_of_interest TEXT")

    conn.commit()
    conn.close()

def insert_rows(df, target_county, target_state, received_from, date_received, uploaded_by, date_uploaded, progress_callback=None):
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
        uploaded_by = uploaded_by.title()
        
        zip_code = format_zip(row.get('zip code'))  # <-- call inside loop per row

        c.execute(f"""
            INSERT OR IGNORE INTO {TABLE_NAME} (
                ref_no, target_county, target_state, received_from, date_received, uploaded_by, date_uploaded,
                owner, owner_id, first_name, middle_name, last_name, attn, address, city, state, zip_code,
                num_of_interests, pdp_value, total_value_low, total_value_high, list, county_of_interest
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            ref_no,
            target_county,
            target_state,
            received_from,
            date_received,
            uploaded_by,
            date_uploaded,
            row.get('owner'),
            row.get('owner id'),
            row.get('first name'),
            row.get('middle name'),
            row.get('last name'),
            row.get('attn'),
            row.get('address'),
            row.get('city'),
            row.get('state'),
            zip_code,  # use formatted ZIP
            row.get('# of interests'),
            row.get('pdp value ($)'),
            row.get('total value - low ($)'),
            row.get('total value - high ($)'),
            row.get('list'),
            row.get('county')
        ))

        if progress_callback:
            progress_callback((idx+1)/total)

    conn.commit()
    conn.close()

# ---------------- GDRIVE UPLOAD ----------------
def upload_db_to_gdrive(local_db_path, folder_id=GOOGLE_DRIVE_FOLDER_ID, timestamp=None):
    """
    Uploads the local SQLite database to Google Drive using OAuth.
    """

    service = get_drive_service()

    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    filename = os.path.basename(local_db_path)
    timestamped_filename = f"{timestamp}_backup_{filename}"

    file_metadata = {
        "name": timestamped_filename,
        "parents": [folder_id]
    }

    media = MediaFileUpload(
        local_db_path,
        mimetype="application/x-sqlite3",
        resumable=True
    )

    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, name, parents"
    ).execute()

    return uploaded_file

def get_today_central_date_str():
    central_tz = pytz.timezone("US/Central")
    now_central = datetime.now(central_tz)
    return now_central.strftime("%Y%m%d")

def get_db_snapshot_date(local_db_path):
    """
    Returns the DB file's last modified date in US/Central as YYYYMMDD.
    """
    if not os.path.exists(local_db_path):
        return None

    central_tz = pytz.timezone("US/Central")
    modified_ts = os.path.getmtime(local_db_path)
    modified_central = datetime.fromtimestamp(modified_ts, central_tz)
    return modified_central.strftime("%Y%m%d")


def read_last_backup_date():
    """
    Reads the last backed-up DB snapshot date from the marker file.
    Returns None if missing/blank.
    """
    if not os.path.exists(BACKUP_MARKER_FILE):
        return None

    with open(BACKUP_MARKER_FILE, "r", encoding="utf-8") as f:
        value = f.read().strip()
        return value or None


def write_last_backup_date(snapshot_date):
    """
    Writes the DB snapshot date that was successfully backed up.
    """
    with open(BACKUP_MARKER_FILE, "w", encoding="utf-8") as f:
        f.write(snapshot_date)

def backup_db_if_needed(local_db_path, folder_id=GOOGLE_DRIVE_FOLDER_ID):
    """
    Uploads at most one backup per US/Central day, before the first update of that day.
    The uploaded filename uses the DB snapshot date, but the marker tracks the run date.
    """
    if not os.path.exists(local_db_path):
        return False

    today_central = get_today_central_date_str()
    last_backup_run_date = read_last_backup_date()

    # already backed up once today
    if last_backup_run_date == today_central:
        return False

    # name the backup based on the DB snapshot date being preserved
    snapshot_date = get_db_snapshot_date(local_db_path)
    upload_db_to_gdrive(local_db_path, folder_id=folder_id, timestamp=snapshot_date)

    # mark that today's backup has already been done
    write_last_backup_date(today_central)
    return True

# ---------------- GUI ----------------
class UWUploadUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("UW Received Offers Tracker v2.0.2")
        self.geometry("420x450")
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

        # ---------------- Uploaded By ----------------
        ctk.CTkLabel(self.form_frame, text="Your Name:", text_color="#fff6de")\
            .grid(row=row, column=0, sticky="w", pady=PADDING_Y, padx=(0,10))
        self.uploader_entry = ctk.CTkEntry(self.form_frame, placeholder_text="Enter your name...")
        self.uploader_entry.grid(row=row, column=1, sticky="we", pady=PADDING_Y)
        row += 1

        # ---------------- File selection ----------------
        ctk.CTkLabel(self.form_frame, text="Select file from Underwriter:", text_color="#fff6de")\
            .grid(row=row, column=0, sticky="w", pady=PADDING_Y, padx=(0,10))
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
        central_tz = pytz.timezone("US/Central")
        now_central = datetime.now(central_tz)
        uploaded_by = self.uploader_entry.get()
        central_tz = pytz.timezone("US/Central")
        date_uploaded = datetime.now(central_tz).strftime("%Y-%m-%d")
        if not all([county, state, received_from, date_received, uploaded_by, date_uploaded]):
            messagebox.showerror("Error", "All metadata fields are required.")
            return

        threading.Thread(target=self.upload_file, args=(county, state, received_from, date_received, uploaded_by, date_uploaded), daemon=True).start()

    def upload_file(self, county, state, received_from, date_received, uploaded_by, date_uploaded):
        self.upload_btn.configure(state="disabled")
        df = pd.read_excel(self.file_path)

        # Normalize column names (case-insensitive, strip spaces)
        df.columns = [str(col).strip().lower() for col in df.columns]
        # Optional: ensure expected columns exist
        required_cols = [
            'owner','owner id','first name','last name','attn','address','city','state','zip code',
            '# of interests','pdp value ($)','total value - low ($)','total value - high ($)'
        ]

        optional_cols = ['middle name', 'list']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            messagebox.showerror("Error", f"Missing required columns in Excel: {missing}")
            self.upload_btn.configure(state="normal")
            return

        def progress_callback(fraction):
            self.progress.set(fraction)

        # --- Backup DB once per Central day, before today's first update ---
        try:
            backup_db_if_needed(DB_FILE, folder_id=GOOGLE_DRIVE_FOLDER_ID)
        except Exception as e:
            messagebox.showwarning("Google Drive Backup Failed", f"Could not back up database to Google Drive:\n{e}")

        insert_rows(df, county, state, received_from, date_received, uploaded_by, date_uploaded, progress_callback)

        # at the start of upload_file
        central_tz = pytz.timezone("US/Central")
        now_central = datetime.now(central_tz)

        # for Slack message (readable)
        timestamp_for_slack = now_central.strftime("%B %d, %Y at %H:%M:%S %Z")

        # --- Upload DB to Slack ---
        try:
            send_db_to_slack(DB_FILE, county=county, state=state, timestamp=timestamp_for_slack, uploaded_by=uploaded_by)
        except Exception as e:
            messagebox.showwarning("Slack Upload Failed", f"Could not send to Slack:\n{e}")

        self.progress.set(1.0)
        messagebox.showinfo("Success", "Upload complete!")
        self.progress.set(0)
        self.upload_btn.configure(state="normal")

if __name__ == "__main__":
    app = UWUploadUI()
    app.mainloop()
