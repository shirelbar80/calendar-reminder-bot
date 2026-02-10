import os
import datetime
import re
import json # הוספנו לבדיקות
import sys  # הוספנו לבדיקות
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# הדפסה ראשונית מיידית - כדי לראות שהקוד בכלל רץ
print("--- [DEBUG] Script process started ---", flush=True)

# --- Configuration ---
WEBHOOK_URL = os.environ.get("MACRODROID_WEBHOOK_URL")
TARGET_COLOR_ID = '1'
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def check_files_integrity():
    """בודק האם הקבצים הסודיים קיימים והם בפורמט JSON תקין"""
    print("--- [DEBUG] Checking file integrity...", flush=True)
    
    files = ['token.json', 'credentials.json']
    for filename in files:
        if not os.path.exists(filename):
            print(f"❌ ERROR: {filename} does not exist!", flush=True)
            continue
            
        # בדיקת גודל הקובץ
        size = os.path.getsize(filename)
        if size == 0:
            print(f"❌ ERROR: {filename} is empty (0 bytes)!", flush=True)
            continue
            
        # בדיקת תקינות JSON
        try:
            with open(filename, 'r') as f:
                content = json.load(f)
                print(f"✅ {filename} is valid JSON. Keys found: {list(content.keys())}", flush=True)
        except json.JSONDecodeError as e:
            print(f"❌ ERROR: {filename} contains invalid JSON! Error: {e}", flush=True)
            print("Make sure you pasted the content correctly in GitHub Secrets without extra spaces.", flush=True)

def get_calendar_service():
    print("--- [DEBUG] Attempting to connect to Google Calendar...", flush=True)
    creds = None
    
    if os.path.exists('token.json'):
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            print("--- [DEBUG] Loaded credentials from token.json", flush=True)
        except Exception as e:
            print(f"❌ ERROR loading token.json: {e}", flush=True)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("--- [DEBUG] Token expired, refreshing...", flush=True)
            try:
                creds.refresh(Request())
                print("--- [DEBUG] Token refreshed successfully.", flush=True)
            except Exception as e:
                print(f"❌ ERROR refreshing token: {e}", flush=True)
                return None
        else:
            print("❌ ERROR: No valid token found and cannot refresh headless.", flush=True)
            return None
            
    try:
        service = build('calendar', 'v3', credentials=creds)
        print("--- [DEBUG] Service built successfully.", flush=True)
        return service
    except Exception as e:
        print(f"❌ ERROR building service: {e}", flush=True)
        return None

def extract_phone_number(text):
    if not text: return None
    match = re.search(r'(05\d-?\d{7})', text)
    return match.group(1) if match else None

def get_tomorrow_range():
    # חישוב זמן לפי UTC
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    israel_time = utc_now + datetime.timedelta(hours=2)
    
    today_date = israel_time.date()
    tomorrow = today_date + datetime.timedelta(days=1) # שנה ל- days=0 אם את רוצה לבדוק על היום
    
    time_min = f"{tomorrow}T00:00:00Z"
    time_max = f"{tomorrow}T23:59:59Z"
    
    print(f"--- [DEBUG] Calculation: Now(IL)={israel_time}, Search Target={tomorrow}", flush=True)
    return time_min, time_max

def main():
    try:
        print(f"--- [DEBUG] Webhook configured: {bool(WEBHOOK_URL)}", flush=True)
        if not WEBHOOK_URL:
            print("❌ ERROR: Webhook URL missing.", flush=True)
            return

        # הרצת בדיקת קבצים לפני הכל
        check_files_integrity()

        service = get_calendar_service()
        if not service:
            print("❌ CRITICAL: Failed to connect to Calendar service. Exiting.", flush=True)
            return

        time_min, time_max = get_tomorrow_range()
        print(f"--- [DEBUG] Querying range: {time_min} to {time_max}", flush=True)

        events_result = service.events().list(
            calendarId='primary', timeMin=time_min, timeMax=time_max,
            singleEvents=True, orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        print(f"--- [DEBUG] Events found count: {len(events)}", flush=True)
        
        if not events:
            print("--- [INFO] No events found in range.", flush=True)
            return

        for event in events:
            summary = event.get('summary', 'No Title')
            description = event.get('description', '')
            color_id = event.get('colorId', None)
            
            print(f"--- [DEBUG] Checking event: {summary} | Color: {color_id}", flush=True)

            raw_start_time = event.get('start', {}).get('dateTime')
            if raw_start_time:
                dt_object = datetime.datetime.fromisoformat(raw_start_time)
                formatted_time = dt_object.strftime('%H:%M')
            else:
                formatted_time = "במהלך היום"

            if color_id and color_id != TARGET_COLOR_ID:
                print(f"    -> Skipped (Color mismatch)", flush=True)
                continue

            phone = extract_phone_number(description)
            if phone:
                print(f"    -> MATCH! Found phone: {phone}", flush=True)
                message_text = f"היי {summary}, תזכורת לתור שלך מחר בשעה {formatted_time} לתספורת אצלי! נתראה :)"
                try:
                    resp = requests.get(WEBHOOK_URL, params={"phone": phone, "msg": message_text})
                    print(f"    -> Webhook sent! Status: {resp.status_code}", flush=True)
                except Exception as e:
                    print(f"❌ ERROR sending webhook: {e}", flush=True)
            else:
                print(f"    -> Skipped (No phone number)", flush=True)

    except Exception as e:
        print(f"❌ CRITICAL ERROR IN MAIN: {e}", flush=True)
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
