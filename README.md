# 📤 UW Received Offers Tracker


The **UW Received Offers Tracker** is a Python-based application that simplifies the management of Underwriter (UW) received offers.
It provides an intuitive GUI that allows the data team to upload Excel files, validate required fields, generate unique reference numbers, store each entry in a local SQLite database, and automatically back up the database to Dropbox.
The tool also sends notifications to designated Slack users and channels and manages underwriter entries dynamically, ensuring new names are saved and available for future uploads. 
Overall, it ensures consistent handling of UW submissions and keeps all processed data organized, accessible, and versioned.

---

![Version](https://img.shields.io/badge/version-2.0.2-ffab4c?style=for-the-badge&logo=python&logoColor=white)
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
- **Slack Notifications**: Automatically sends the uploaded SQLite database to designated Slack users and channels, with dynamic recipient lists and human-readable timestamps via UW Received Offers Tracker slack bot
- **Underwriter Management**: Automatically loads names of underwriters from `underwriters.txt` and ensures new names are saved for future use.
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
    ├── slack_channel_ids.txt          # List of slack channel ids to receive notifications  
    ├── slack_user_ids.txt             # List of slack individual user ids to receive notifications  
    └── underwriters.txt               # List of underwriters
       
    </pre>
    
    Before running the tool, you need to set up your Dropbox app credentials and generate a **refresh token** to allow the app to access your Dropbox account securely.


4. **Set Up Configuration**

   4.1. Dropbox Setup
   
   **Creating the App in Dropbox**:
   * Go to the [Dropbox App Console](https://www.dropbox.com/developers/apps) and click Create App.
   * Select Scoped access and Full Dropbox or App folder depending on your needs.
   * Give your app a unique name.
   * Under **Settings** tab:
      * Add this **Redirect URI** in app settings: `http://localhost:8080`
         * Must match REDIRECT_URI in the token generation script)
      * Copy the App Key and App Secret into the `.env` file
         ```env
         DROPBOX_UW_OFFERS_TRACKER_APP_KEY=your_dropbox_app_key
         DROPBOX_UW_OFFERS_TRACKER_APP_SECRET=your_dropbox_secret
         ```
   * Under **Permissions** tab:
      * Check the box for `files.metadata.write`
      * Check the box for `files.content.read`
      * Click **Submit**
     
   **Generate the refresh token:**
   * Run `generate_refresh_token.py` (edit with your App Key, App Secret, and Redirect URI)
   * Complete the OAuth flow in your browser
   * After a successful login, the script outputs the **refresh token** in the **dropbox_tokens.json** file.
   * Copy the refresh token to `.env`
      ```env
      DROPBOX_UW_OFFERS_TRACKER_REFRESH_TOKEN=your_dropbox_refresh_token
      ```
   4.2. **Slack Bot Setup**
   
   **Create a Slack app in your workspace:**
   * Go to [slack api](https://api.slack.com/apps)
   * Click **Create New App**
   * Choose **From scratch**
   * Enter a name for your app
   * Select a workspace from the dropdown menu
   * Click Create App
   * Under **OAuth & Permissions** tab:
      * Assign the following **Bot Token Scopes**:
         * chat:write (send messages)
         * files:write (upload files)
         * users:read (read user info, optional)
         * channels:history
         * channels:read (View basic information about public channels)
         * files:read (view files shared in channels and conversations)
         * groups:read (View basic information about private channels)
         * im:history
         * im:write
         * users:read
      * Install the app to your workspace and copy the **Bot User OAuth Token**.
      * Copy the Bot User OAuth Token and save it in `config/.env`
        ```env
        UW_TRACKER_SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
        ```
   * Create these files in the project root:
      * `slack_user_ids.txt` — list of individual user IDs (one per line)
      * `slack_channel_ids.txt` — list of channel IDs (one per line)
   
   ⚠️ Make sure the Slack bot is invited to all channels listed in `slack_channel_ids.txt`.
   
   4.3. Verify `.env` and File Placement
   
   * Place the .env file inside the config/ folder.
   * Required variables:
   ```env
   DROPBOX_UW_OFFERS_TRACKER_ACCESS_TOKEN=your_dropbox_access_token
   DROPBOX_UW_OFFERS_TRACKER_APP_KEY=your_dropbox_app_key
   DROPBOX_UW_OFFERS_TRACKER_APP_SECRET=your_dropbox_secret
   DROPBOX_UW_OFFERS_TRACKER_REFRESH_TOKEN=your_dropbox_refresh_token
   UW_TRACKER_SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
   ```

   The tool will automatically load these variables on startup.

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

3. **Metadata requirements**
   
   Before uploading, the following fields must be filled:
   * Your Name (Uploaded By) — stored as `uploaded_by`
   * Target County — required for tracking, stored as `target_county`
   * Target State — required for tracking, stored as `target_state`
   * Received From (Underwriter) — selectable from the dropdown or typed; stored as `received_from`
      * New names are automatically added to underwriters.txt and sorted alphabetically
   * Date Received — chosen from the calendar, stored as `date_received`
   
   Note: `date_uploaded` is automatically recorded as the current US/Central time when the upload happens. Users do not need to enter this.

4. **Upload**
   * Click UPLOAD.
   * The program will:
      * Insert records into the SQLite database
      * Generate unique ref_no values
      * Update the progress bar
      * Upload the database to Dropbox:
         * A timestamped copy is saved in the format: `YYYYMMDD_HHMMSS_<original_filename>.db`
         * Ensures versioning and prevents accidental overwrites
      * Send a notification via Slack:
         * Sent to individual users and channels defined in `slack_user_ids.txt` and `slack_channel_ids.txt`
         * Notification includes:
            * Target County
            * Target State
            * Uploader name
            * Upload timestamp (Central Time)
         * Handles empty or missing recipients; upload will continue without crashing

You will receive a pop-up message once the process completes.
     
> ⚠️ **Important Notes**
>
> * The tool only supports uploading one file at a time.
> * Do not close the app while an upload is in progress, as this may interrupt the process.
> * The tool will produce an error if the uploaded file is missing any required column(s).


---

## GUI / Screenshots
<p align="center">
   <img width="527" height="601" alt="image" src="https://github.com/user-attachments/assets/b97521ad-35e5-4529-a84a-9369045cd7ba" />
   <br>
   <em>Main interface for uploading UW offers. Fill out metadata fields and select the Excel file before uploading.</em>
</p>

:memo: Notes on message prompts:
* A success popup appears when the upload completes.
* An error popup appears if any required field is missing or a column is not found in the Excel file.
<br>
<br>
<p align="center">
   <img width="527" height="601" alt="image" src="https://github.com/user-attachments/assets/f8fc2231-ce50-429e-a75a-318ae2575c98" />
   <br>
   <em>Example of a Slack notification sent by the UW Received Offers Tracker. Shows Target County, Target State, Uploader, and Upload Timestamp.</em>
</p>

:memo: Note: The recipients are dynamically loaded from `slack_user_ids.txt` and `slack_channel_ids.txt`.

---

## 👩‍💻 Credits
- **2025-11-20**: Project created by **Julia** ([@dyoliya](https://github.com/dyoliya))  
- 2025–present: Maintained by **Julia** for **Community Minerals II, LLC**
