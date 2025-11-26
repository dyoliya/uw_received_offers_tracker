import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
from datetime import datetime
import pytz

def load_ids_from_file(filename):
    """
    Loads IDs from a text file, stripping whitespace and ignoring empty lines.
    Returns an empty list if the file doesn't exist.
    """
    if not os.path.exists(filename):
        print(f"Warning: {filename} not found. No IDs loaded.")
        return []
    with open(filename, "r") as f:
        return [line.strip() for line in f if line.strip()]

def send_db_to_slack(file_path="uw_received_offers.db", county=None, state=None, timestamp=None, uploaded_by=None):
    # Load .env from config folder
    load_dotenv(dotenv_path='config/.env')
    SLACK_BOT_TOKEN = os.getenv("UW_TRACKER_SLACK_BOT_TOKEN")
    client = WebClient(token=SLACK_BOT_TOKEN)

    user_ids = load_ids_from_file("slack_user_ids.txt")     # direct messages
    channel_ids = load_ids_from_file("slack_channel_ids.txt")  # public/private channels

    if not user_ids and not channel_ids:
        print("No Slack user IDs or channel IDs found. Aborting.")
        return

    # Use provided timestamp if available, else compute Central time
    if timestamp is None:
        tz = pytz.timezone("US/Central")
        now = datetime.now(tz)
        timestamp = now.strftime("%B %d, %Y at %I:%M %p %Z")

    county_info = f"*{county}*" if county else ""
    state_info = f"*{state}*" if state else ""
    uploader_info = f"*{uploaded_by}*" if uploaded_by else ""

    message_text = (
        "Hello! This is an automated message from the UW Received Offers Tracker Bot.\n\n"
        f"Attached is the latest database file: `uw_received_offers.db`. "
        f"Added UW Offers for {county_info.upper()}, {state_info.upper()}.\n"
        f"Updated by: {uploader_info} [{timestamp}]"
    )

    # -------------------------
    # SEND TO USER DIRECT MESSAGES
    # -------------------------
    for user_id in user_ids:
        try:
            response = client.conversations_open(users=user_id)
            dm_channel = response["channel"]["id"]

            client.files_upload_v2(
                channel=dm_channel,
                file=file_path,
                title=os.path.basename(file_path),
                initial_comment=message_text
            )
            print(f"Message and file sent successfully to USER {user_id}!")

        except SlackApiError as e:
            print(f"Error sending DM/file to {user_id}: {e.response['error']}")

    # -------------------------
    # SEND TO CHANNELS (optional)
    # -------------------------
    if channel_ids:
        for ch_id in channel_ids:
            try:
                client.files_upload_v2(
                    channel=ch_id,
                    file=file_path,
                    title=os.path.basename(file_path),
                    initial_comment=message_text
                )
                print(f"Message and file sent successfully to CHANNEL {ch_id}!")
            except SlackApiError as e:
                print(f"Error sending message/file to channel {ch_id}: {e.response['error']}")

    else:
        print("No channel IDs found — skipping channel notifications.")

# Optional standalone run
if __name__ == "__main__":
    send_db_to_slack()