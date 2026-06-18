# Birthday & Work Anniversary Notifier

Sends daily email notifications when an employee has a birthday or work anniversary.

## How it works

A cloud agent (Claude Code Routine) runs every day at **7:00 AM AEST**. It clones this repo, reads the CSV files, and sends emails via Microsoft Graph API. No local machine required.

## Maintaining the employee list

Edit `start dates and birthdays.csv` and push to GitHub — the cloud routine reads this file fresh each run.

### CSV columns

| Column | Format | Example |
|--------|--------|---------|
| Name | Text | Aaron Steel |
| Start Date | DD/MM/YYYY | 21/10/2019 |
| Birthday | DD-Mon | 30-Apr |
| Country | Text | Australia |
| Department | Text | Operations |

Leave Birthday or Start Date blank if unknown — the notifier skips blank fields.

### Notification recipients

Edit `recipients.csv` — one email address per row under the `Email` header.

## Cloud routine

- **Routine ID:** trig_01Mp3dSXeTmacPePDw36cGGU
- **Schedule:** Daily 7:00 AM AEST (21:00 UTC)
- **Manage at:** https://claude.ai/code/routines/trig_01Mp3dSXeTmacPePDw36cGGU

## Email sending

Emails are sent from `feeds@macgeargroup.com` via the **Macgear Claude Agent** Azure app (client credentials flow, no user login).

- **Azure app:** Macgear Claude Agent
- **Tenant ID:** 9370e6f0-7dde-4255-9bbe-6af58d8e0dd4
- **Client ID:** 738bbae7-fdfc-4536-b8e1-607093efe671
- **Permission:** Mail.Send (Application, admin consented)
- **Client secret:** Stored in the cloud routine prompt. If it expires, generate a new secret in Azure portal → App registrations → Macgear Claude Agent → Certificates & secrets, then update the routine prompt at the link above.

## Running locally (for testing)

```powershell
$env:TENANT_ID   = "9370e6f0-7dde-4255-9bbe-6af58d8e0dd4"
$env:CLIENT_ID   = "738bbae7-fdfc-4536-b8e1-607093efe671"
$env:CLIENT_SECRET = "<secret-value>"
$env:SENDER_EMAIL  = "feeds@macgeargroup.com"
python birthday_notifier.py
```

To test on a specific date, temporarily add a row to the CSV with today's date as birthday or start date, run, then remove the row.
