# 🏆 FIFA World Cup 2026 — Live Calendar

Auto-updating ICS calendar with **live scores** for all 104 matches.  
Powered by [football-data.org](https://www.football-data.org/) · Updated every 3 hours via GitHub Actions.

## 📅 Subscribe

Copy the raw URL below and add it as a **subscribed calendar** (not an import):

```
https://raw.githubusercontent.com/YOUR_USERNAME/wc2026-calendar/main/FIFA_WorldCup2026.ics
```

> Replace `YOUR_USERNAME` with your GitHub username.

### How to subscribe

|App                     |Steps                                                                         |
|------------------------|------------------------------------------------------------------------------|
|**Google Calendar**     |Other calendars → From URL → paste link                                       |
|**Apple Calendar (Mac)**|File → New Calendar Subscription → paste link                                 |
|**iPhone**              |Settings → Calendar → Accounts → Add Account → Other → Add Subscribed Calendar|
|**Outlook**             |Add calendar → From internet → paste link                                     |

## 📊 What you’ll see

- **Before kickoff:** `⚽ Group A · 🇲🇽 Mexico vs 🇿🇦 South Africa`
- **Live:** `🔴 🇲🇽 Mexico 1–0 🇿🇦 South Africa LIVE`
- **Final score:** `✅ 🇲🇽 Mexico 2–1 🇿🇦 South Africa`
- **Knockout TBD:** `🏆 Round of 32 · Winner Group A vs Runner-up Group B`

## ⚙️ Setup (fork this repo)

1. Fork this repository
1. Go to **Settings → Secrets → Actions**
1. Add a secret: `FOOTBALL_DATA_API_KEY` = your key from [football-data.org](https://www.football-data.org/client/register)  
   *(free registration, no credit card)*
1. GitHub Actions will auto-run every 3 hours

## 🔄 Update frequency

- GitHub Actions runs every **3 hours**
- Google Calendar refreshes subscriptions every **~24 hours**
- Apple Calendar refreshes every **1–6 hours** depending on your settings
- For faster refresh, open the calendar app and manually pull to refresh

## 📁 Files

|File                                   |Purpose                                 |
|---------------------------------------|----------------------------------------|
|`generate_ics.py`                      |Main script — fetches API, builds ICS   |
|`FIFA_WorldCup2026.ics`                |Generated calendar file (auto-committed)|
|`.github/workflows/update-calendar.yml`|GitHub Actions schedule                 |