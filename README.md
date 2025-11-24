# 📤 UW Received Offers Tracker


The **UW Received Offers Tracker** is a Python-based application that simplifies the management of Underwriter (UW) received offers.
It provides an intuitive GUI that allows the data team to upload Excel files, validate required fields, generate unique reference numbers, store each entry in a local SQLite database, and automatically back up the database to Dropbox.
The tool ensures consistent handling of UW submissions and keeps all processed data organized and accessible.

---

![Version](https://img.shields.io/badge/version-1.0.0-ffab4c?style=for-the-badge&logo=python&logoColor=white)
![Python](https://img.shields.io/badge/python-3.11%2B-273946?style=for-the-badge&logo=python&logoColor=ffab4c)
![Status](https://img.shields.io/badge/status-active-273946?style=for-the-badge&logo=github&logoColor=ffab4c)

---
## 🚧 Problem Statement / Motivation
Handling UW submissions through Slack introduced several recurring issues:
- Underwriters frequently send files named generically (e.g., “County List”), making it unclear which county or state they refer to once downloaded.
- Even when the Slack message includes county details, the information is lost after saving the file locally.
- Manually renaming files is time-consuming and prone to mistakes, especially when multiple submissions come in.
- Backtracking old offers requires searching Slack conversations again, which is slow and disrupts workflow.
- Local storage quickly becomes cluttered with multiple similarly named files, even after renaming.

The tracker was built to solve these frustrations by centralizing uploads, automating organization, and creating a consistent, searchable database for all UW received offers.

---

## ✨ Features

- **Excel File Processing**: Reads Excel files from Underwriters and validates all required columns before uploading.
- **Automatic Reference Number Generation**: Creates unique ref_no values based on the current year and sequential numbering.
- **SQLite Database Storage**: Automatically creates a local SQLite database and table, storing all uploaded records with ref_no as the primary key.
- **Data Normalization**: Cleans and formats ZIP codes, enforces proper casing for state/county fields, and prepares rows before insertion.
- **Progress Tracking**: Displays a real-time progress bar during data upload for clear user visibility.
- **Dropbox Backup**: Automatically uploads a timestamped copy of the database to a Dropbox folder using API integration.
- **Underwriter Auto-Save**: Detects new “Received From” entries and saves them to `underwriters.txt`, updating the dropdown list automatically.
- **User-Friendly GUI**: Modern CustomTkinter interface with file selection, form inputs, progress display, and error handling.
- **Threaded Upload Process**: Uses background threading to prevent the GUI from freezing during large uploads.
- **Column Validation**: Ensures that all required Excel columns are present, preventing incomplete or invalid data uploads.

---

## 📝 Requirements

- Python 3.11+
- `pandas`
- `pymysql`
- `sqlite3` (built-in)
- `customtkinter`
- `python-dotenv`
- `tkcalendar`
- `dropbox`

> Tip: You can install all dependencies via:
> ```bash
> pip install -r requirements.txt
> ```

---
## 🚀 Installation and Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/budb_upload_to_mysql.git
   cd budb_upload_to_mysql

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt

3. **Folder Structure**
    <pre>project/
    │
    ├── config/                        # Configuration files
    │   ├── .env                       # Environment variables
    │   └── dropbox_config.py          # Dropbox client configuration
    ├── uw_received_offers_tracker.py  # Main script
    ├── requirements.txt               # Dependencies
    └── underwriters.txt               # List of underwriters
    </pre>
    
    Before running the tool, you need to set up your Dropbox app credentials and generate a **refresh token** to allow the app to access your Dropbox account securely.

4. **Set Up Configuration**

    4.1. **Create a Dropbox App**

   - Go to the [Dropbox App Console](https://www.dropbox.com/developers/apps).
   - Click **Create App**.
   - Select **Scoped access** and **Full Dropbox** or **App folder** depending on your needs.
   - Give your app a unique name.
   - In the app settings, add this as your **Redirect URI**:  
     `http://localhost:8080`  
     *(Make sure it matches the `REDIRECT_URI` in your token generation script.)*
   - Save the app.

   4.2. **Get Your App Credentials**

   - Copy your **App Key** and **App Secret** from the app settings.
   - Paste these values into your `.env` file like so:

     ```env
      DROPBOX_UW_OFFERS_TRACKER_APP_KEY=your_dropbox_app_key
      DROPBOX_UW_OFFERS_TRACKER_APP_SECRET=your_dropbox_secret
     ```

   4.3. **Generate the Refresh Token**

   - Use the included script (`generate_refresh_token.py`) to perform the OAuth flow and obtain a refresh token.
   - Edit the script and fill in your app credentials at the top:
      ```python
     APP_KEY = "your_app_key_here"       # Dropbox App Key
     APP_SECRET = "your_app_secret_here" # Dropbox App Secret
     REDIRECT_URI = "http://localhost:8080"
     ```
   - Run the script locally (it will open a browser window and prompt for Dropbox login).
   - After successful login, it will output the **refresh token** in the **dropbox_tokens.json** file.
   - Copy the refresh token and add it to your `.env` file:

     ```env
     DROPBOX_UW_OFFERS_TRACKER_REFRESH_TOKEN=your_dropbox_refresh_token
     ```

   4.4. **Place the `.env` file inside the `config/` folder and ensure it contains the ffg variables**
     ```bash
      DROPBOX_UW_OFFERS_TRACKER_ACCESS_TOKEN=your_dropbox_access_token
      DROPBOX_UW_OFFERS_TRACKER_APP_KEY=your_dropbox_app_key
      DROPBOX_UW_OFFERS_TRACKER_APP_SECRET=your_dropbox_secret
      DROPBOX_UW_OFFERS_TRACKER_REFRESH_TOKEN=your_dropbox_refresh_token
      ```
   - The tool will automatically load these environment variables from `config/.env`.

5. **Compile the tool**
   ```bash
   pyinstaller --onefile uw_received_offers_tracker.py
---

## 🖥️ User Guide

1. **Launch the Application**
   * Run the .exe file and the GUI window will appear.

2. **Select the Excel File**
   * Click “Select Excel File”
   * Choose the UW file (.xlsx) to process
   * Required columns include:
      * Owner
      * Owner ID
      * First Name
      * Last Name
      * ATTN
      * Address
      * City
      * State
      * Zip Code
      * \# of Interests
      * PDP Value ($)
      * Total Value - Low ($)
      * Total Value - High ($)

3. **Fill Out Metadata**
   * Target County – required
   * Target State – required
   * Received From
      * Select from dropdown
      * Or type a new name (automatically saved)
   * Date Received – choose from calendar

4. **Upload**
   * Click UPLOAD.
   * The program will:
      * Insert records into the SQLite database
      * Generate unique ref_no values
      * Update the progress bar
      * Upload the database to Dropbox (timestamped) for backup

You will receive a pop-up message once the process completes.
     
> ⚠️ **Important Notes**
>
> * The tool only supports uploading one file at a time.
> * Do not close the app while an upload is in progress, as this may interrupt the process.
> * The tool will produce an error if the uploaded file is missing any required column(s).


---

## 👩‍💻 Credits
- **2025-11-20**: Project created by **Julia** ([@dyoliya](https://github.com/dyoliya))  
- 2025–present: Maintained by **Julia** for **Community Minerals II, LLC**
