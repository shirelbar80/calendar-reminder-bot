# 💇‍♀️ Automated Hair Salon Appointment Reminder

A fully automated Python system designed to manage client reminders.
It scans a Google Calendar daily, filters relevant appointments, and sends personalized WhatsApp reminders using a webhook integration.

## 🚀 Key Features

- **Smart Filtering:** Detects appointments by specific color codes (Lavender).
- **Data Extraction:** Parses Israeli phone numbers (`05X-XXXXXXX`) from event descriptions.
- **Automation:** Deployed via **GitHub Actions** to run automatically every day at 12:00 PM.
- **Security:** Uses Environment Variables to protect sensitive API keys.

## 🛠️ Tech Stack

- Python 3.9
- Google Calendar API (OAuth 2.0)
- GitHub Actions (CI/CD)
- MacroDroid Webhooks

## ⚙️ Usage

The system is designed to run in a containerized environment or via cloud workflows, ensuring zero manual maintenance for the business owner.
