import os
import datetime
import re
import json
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build

print("--- [DEBUG] Script process started ---")

# --- Configuration ---
WEBHOOK_URL = os.environ.get("MACRODROID_WEBHOOK_URL")
TARGET_CALENDAR_ID = os.environ.get("TARGET_CALENDAR_EMAIL")
TARGET_COLOR_ID = '1'  # Lavender
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


def get_calendar_service():
    """Authenticates using a Service Account."""
    print("--- [DEBUG] Connecting to Google Calendar with Service Account...")
    creds = None
    if os.path.exists('credentials.json'):
        try:
            creds = service_account.Credentials.from_service_account_file(
                'credentials.json', scopes=SCOPES)
            print("--- [DEBUG] Loaded credentials successfully.")
        except Exception as e:
            print(f"❌ ERROR loading credentials: {e}")
            return None
    else:
        print("❌ ERROR: credentials.json not found!")
        return None

    try:
        service = build('calendar', 'v3', credentials=creds)
        print("--- [DEBUG] Service built successfully.")
        return service
    except Exception as e:
        print(f"❌ ERROR building service: {e}")
        return None


def extract_phone_number(text):
    if not text:
        return None
    match = re.search(r'(05\d-?\d{3}-?\d{4})', text)
    if match:
        return match.group(1).replace('-', '')
    return None


def get_tomorrow_range():
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    israel_time = utc_now + datetime.timedelta(hours=2)
    today_date = israel_time.date()
    tomorrow = today_date + datetime.timedelta(days=1)

    time_min = f"{tomorrow}T00:00:00Z"
    time_max = f"{tomorrow}T23:59:59Z"

    print(
        f"--- [DEBUG] Calculation: Now(IL)={israel_time}, Search Target={tomorrow}")
    return time_min, time_max


def main():
    try:
        print(f"--- [DEBUG] Webhook configured: {bool(WEBHOOK_URL)}")
        if not WEBHOOK_URL:
            print("❌ ERROR: Webhook URL missing.")
            return

        if not TARGET_CALENDAR_ID:
            print("❌ ERROR: Target Calendar Email missing from secrets.")
            return

        service = get_calendar_service()
        if not service:
            print("❌ CRITICAL: Failed to connect to Calendar service. Exiting.")
            return

        time_min, time_max = get_tomorrow_range()
        print(
            f"--- [DEBUG] Querying range: {time_min} to {time_max} for calendar: {TARGET_CALENDAR_ID}")

        events_result = service.events().list(
            calendarId=TARGET_CALENDAR_ID, timeMin=time_min, timeMax=time_max,
            singleEvents=True, orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        print(f"--- [DEBUG] Events found count: {len(events)}")

        if not events:
            print("--- [INFO] No events found in range.")
            return

        for event in events:
            summary = event.get('summary', 'No Title')
            description = event.get('description', '')
            color_id = event.get('colorId', None)

            print(f"--- [DEBUG] Checking event: {summary} | Color: {color_id}")

            raw_start_time = event.get('start', {}).get('dateTime')
            if raw_start_time:
                dt_object = datetime.datetime.fromisoformat(raw_start_time)
                formatted_time = dt_object.strftime('%H:%M')
            else:
                formatted_time = "במהלך היום"

            if color_id and color_id != TARGET_COLOR_ID:
                print(f"    -> Skipped (Color mismatch)")
                continue

            phone = extract_phone_number(description)
            if phone:
                print(f"    -> MATCH! Found phone: {phone}")
                message_text = f"היי {summary},\nיש לך מחר תור ב {formatted_time} למספרה \nברח' העבודה 1 בית מספר 3 רמה\"ש, הכניסה למתחם הבתים מרח' העבודה 1 או מרח' המלאכה 18, אפשר לחנות ברח' המלאכה.\nנתראה, טליה אברך."
                try:
                    resp = requests.get(WEBHOOK_URL, params={
                                        "phone": phone, "msg": message_text})
                    print(f"    -> Webhook sent! Status: {resp.status_code}")
                except Exception as e:
                    print(f"❌ ERROR sending webhook: {e}")
            else:
                print(f"    -> Skipped (No phone number)")

    except Exception as e:
        print(f"❌ CRITICAL ERROR IN MAIN: {e}")


if __name__ == '__main__':
    main()
