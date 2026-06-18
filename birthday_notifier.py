"""
Birthday & Work Anniversary Email Notifier
Reads start dates and birthdays.csv and sends email via Outlook
when today matches a birthday or work anniversary.
"""

import csv
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# --- CONFIG ---
CSV_FILE = Path(__file__).parent / "start dates and birthdays.csv"
RECIPIENTS_FILE = Path(__file__).parent / "recipients.csv"
# --------------


def load_recipients():
    """Load email addresses from recipients.csv."""
    if not RECIPIENTS_FILE.exists():
        print(f"ERROR: Recipients file not found at {RECIPIENTS_FILE}")
        sys.exit(1)
    emails = []
    with open(RECIPIENTS_FILE, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get("Email", "").strip()
            if email:
                emails.append(email)
    if not emails:
        print("ERROR: No recipients found in recipients.csv")
        sys.exit(1)
    return emails


def parse_date(date_str):
    """Parse DD/MM/YYYY date string."""
    date_str = date_str.strip()
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").date()
    except ValueError:
        return None


def parse_birthday(date_str):
    """Parse DD-Mon birthday string (day and month only, no year)."""
    date_str = date_str.strip()
    if not date_str:
        return None
    try:
        d = datetime.strptime(date_str, "%d-%b")
        return d  # Only .month and .day are used
    except ValueError:
        return None


def send_outlook_email(subject, body, recipients):
    """Send email via Microsoft Graph API (client credentials flow)."""
    tenant_id = os.environ.get("TENANT_ID")
    client_id = os.environ.get("CLIENT_ID")
    client_secret = os.environ.get("CLIENT_SECRET")
    sender_email = os.environ.get("SENDER_EMAIL")

    if not all([tenant_id, client_id, client_secret, sender_email]):
        print("ERROR: TENANT_ID, CLIENT_ID, CLIENT_SECRET, SENDER_EMAIL must all be set")
        return False

    try:
        # Get access token (client credentials flow — no user login required)
        token_data = urllib.parse.urlencode({
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "https://graph.microsoft.com/.default",
        }).encode()
        token_req = urllib.request.Request(
            f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
            data=token_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(token_req) as resp:
            token = json.loads(resp.read())["access_token"]

        # Send via Graph API using the sender's mailbox
        payload = json.dumps({
            "message": {
                "subject": subject,
                "body": {"contentType": "Text", "content": body},
                "toRecipients": [{"emailAddress": {"address": r}} for r in recipients],
            }
        }).encode()
        send_req = urllib.request.Request(
            f"https://graph.microsoft.com/v1.0/users/{sender_email}/sendMail",
            data=payload,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(send_req):
            pass  # 202 Accepted = success

        print(f"Email sent: {subject}")
        return True
    except Exception as e:
        print(f"ERROR sending email: {e}")
        return False


def ordinal(n):
    """Return ordinal string for integer (1st, 2nd, 3rd, etc.)."""
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def main():
    today = date.today()
    emails_sent = 0
    recipients = load_recipients()
    print(f"Sending to: {', '.join(recipients)}")

    if not CSV_FILE.exists():
        print(f"ERROR: CSV file not found at {CSV_FILE}")
        sys.exit(1)

    with open(CSV_FILE, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("Name", "").strip()
            if not name:
                continue

            birthday = parse_birthday(row.get("Birthday ", "") or row.get("Birthday", ""))
            start_date = parse_date(row.get("Start Date", ""))
            country = row.get("Country", "").strip()
            department = row.get("Department", "").strip()

            location_line = f"Location: {country}" if country else ""
            dept_line = f"Department: {department}" if department else ""
            details = "\n".join(filter(None, [location_line, dept_line]))

            # Check birthday
            if birthday and birthday.month == today.month and birthday.day == today.day:
                subject = f"🎂 Birthday Today: {name}"
                body = (
                    f"Hi,\n\n"
                    f"Today is {name}'s birthday!\n\n"
                    f"Birthday: {birthday.strftime('%d %B')}\n"
                    + (f"{details}\n" if details else "")
                    + f"\nDon't forget to wish them a happy birthday!\n\n"
                    f"-- Birthday Notifier"
                )
                send_outlook_email(subject, body, recipients)
                emails_sent += 1

            # Check work anniversary
            if start_date and start_date.month == today.month and start_date.day == today.day:
                years = today.year - start_date.year
                if years > 0:
                    subject = f"🎉 Work Anniversary Today: {name} — {ordinal(years)} Year!"
                    body = (
                        f"Hi,\n\n"
                        f"Today marks {name}'s {ordinal(years)} work anniversary!\n\n"
                        f"Start date: {start_date.strftime('%d %B %Y')}\n"
                        f"Years with the company: {years}\n"
                        + (f"{details}\n" if details else "")
                        + f"\nTake a moment to recognise their dedication!\n\n"
                        f"-- Birthday Notifier"
                    )
                    send_outlook_email(subject, body, recipients)
                    emails_sent += 1

    print(f"Done. {emails_sent} notification(s) sent for {today.strftime('%d %B %Y')}.")


if __name__ == "__main__":
    main()
