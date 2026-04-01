# UW Received Offers Tracker — Release Notes (v2.1.0)

Compared to: **v2.0.2**

## New
- **Google Drive backup support added.** The tracker now creates database backups in a designated Google Drive folder.
- **County of Interest is now captured.** A new field from the UW file is now saved so teams can filter and report with more location detail.
- **Smarter backup behavior.** The app now keeps one daily backup checkpoint (Central Time) before the first update of the day, helping preserve a clean “start-of-day” snapshot.

## Updates
- **Upload file matching is now more forgiving.** Column names are normalized (for example, handling case differences), reducing avoidable upload failures when spreadsheets are formatted slightly differently.
- **Data validation and migration were improved.** Existing databases are automatically updated to support newer fields without manual database work.
- **Documentation refreshed.** Setup and process documentation were expanded to better explain flow and configuration.

## Fix
- **Reduced duplicate backup noise.** Backup tracking now prevents repeated same-day pre-update backups.
- **Improved field mapping reliability.** The uploader now consistently reads expected spreadsheet fields using normalized column names.

---

If you want, I can also provide a **one-paragraph announcement version** for Slack/email and a **short "What changed for users" version** for leadership.
