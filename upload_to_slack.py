# upload_to_slack.py

import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
from datetime import datetime
import pytz

def send_db_to_slack(file_path="uw_received_offers.db", county=None, state=None, timestamp=None):
    # Load .env from config folder
    load_dotenv(dotenv_path='config/.env')
    SLACK_BOT_TOKEN = os.getenv("UW_TRACKER_SLACK_BOT_TOKEN")
    client = WebClient(token=SLACK_BOT_TOKEN)

    # List of users to send
    user_ids = [
        "U0704LPKTLH",
    ]

    # Use provided timestamp if available, else compute Central time
    if timestamp is None:
        tz = pytz.timezone("US/Central")
        now = datetime.now(tz)
        timestamp = now.strftime("%B %d, %Y at %I:%M %p %Z")

    for user_id in user_ids:
        try:
            response = client.conversations_open(users=user_id)
            channel_id = response["channel"]["id"]

            county_info = f"*{county}*" if county else ""
            state_info = f"*{state}*" if state else ""

            message_text = (
                f"Hello! This is an automated message from the UW Received Offers Tracker Bot.\n\n"
                f"Timestamp: {timestamp}\n\n"
                f"Attached is the latest database file: `uw_received_offers.db`. Added UW Offers for {county_info}, {state_info}."
            )

            client.files_upload_v2(
                channel=channel_id,
                file=file_path,
                title=os.path.basename(file_path),
                initial_comment=message_text
            )
            print(f"Message and file sent successfully to {user_id}!")

        except SlackApiError as e:
            print(f"Error sending message or uploading file to {user_id}: {e.response['error']}")

# Optional: allows standalone running
if __name__ == "__main__":
    send_db_to_slack()