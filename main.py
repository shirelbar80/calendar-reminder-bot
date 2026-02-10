import os
import datetime
import re
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# --- Configuration ---
# Retrieve the Webhook URL from environment variables.
# This ensures security when running in GitHub Actions.
WEBHOOK_URL = os.environ.get("MACRODROID_WEBHOOK_URL")

# Target color ID: Lavender is '1'
TARGET_COLOR_ID = '1'
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


def get_calendar_service():
    """Authenticates and returns the Google Calendar service object."""
    creds = None
    # Check for the token file (generated from GitHub Secrets in the workflow)
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing token: {e}")
                return None
        else:
            print("No valid token found and cannot refresh headless.")
            return None

    return build('calendar', 'v3', credentials=creds)


def extract_phone_number(text):
    """Extracts an Israeli phone number (05X-XXXXXXX) from the text."""
    if not text:
        return None
    match = re.search(r'(05\d-?\d{7})', text)
    return match.group(1) if match else None


def get_tomorrow_range():
    """Calculates the start and end time for tomorrow (UTC)."""
    # GitHub Actions servers run on UTC time.
    # We calculate 'tomorrow' based on the current UTC date.
    today = datetime.datetime.now(datetime.timezone.utc).date()
    tomorrow = today + datetime.timedelta(days=1)

    time_min = f"{tomorrow}T00:00:00Z"
    time_max = f"{tomorrow}T23:59:59Z"
