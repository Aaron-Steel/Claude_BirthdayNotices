"""
Birthday & Work Anniversary Email Notifier
Reads start dates and birthdays.csv and sends email via Outlook
when today matches a birthday or work anniversary.
"""

import csv
import os
import sys
from datetime import datetime, date
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

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
    """Send email via Office 365 SMTP."""
    smtp_user = os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")

    if not smtp_user or not smtp_password:
        print("ERROR: SMTP_USER and SMTP_PASSWORD environment variables must be set")
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = "; ".join(recipients)
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL("smtp.office365.com", 465) as server:
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, recipients, msg.as_string())

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
