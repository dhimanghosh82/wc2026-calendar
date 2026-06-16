"""
FIFA World Cup 2026 - Live ICS Generator
Fetches scores from football-data.org (free tier) and generates ICS.
Run manually or via GitHub Actions on a schedule.

API: https://www.football-data.org/
Competition ID for World Cup: WC
Season: 2026
"""

import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
import pytz

# ── Config ────────────────────────────────────────────────────────────────────
API_KEY   = os.environ.get("FOOTBALL_DATA_API_KEY", "")
API_BASE  = "https://api.football-data.org/v4"
WC_CODE   = "WC"
OUTPUT    = "FIFA_WorldCup2026.ics"

# ── Flag map ──────────────────────────────────────────────────────────────────
FLAGS = {
    "Mexico": "🇲🇽", "South Africa": "🇿🇦", "Korea Republic": "🇰🇷",
    "Czechia": "🇨🇿", "Canada": "🇨🇦", "Bosnia and Herzegovina": "🇧🇦",
    "Bosnia & Herzegovina": "🇧🇦", "United States": "🇺🇸", "USA": "🇺🇸",
    "Paraguay": "🇵🇾", "Qatar": "🇶🇦", "Switzerland": "🇨🇭",
    "Brazil": "🇧🇷", "Morocco": "🇲🇦", "Haiti": "🇭🇹", "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "Australia": "🇦🇺", "Türkiye": "🇹🇷", "Turkey": "🇹🇷",
    "Germany": "🇩🇪", "Curaçao": "🇨🇼", "Curacao": "🇨🇼",
    "Netherlands": "🇳🇱", "Japan": "🇯🇵", "Côte d'Ivoire": "🇨🇮",
    "Ivory Coast": "🇨🇮", "Ecuador": "🇪🇨", "Sweden": "🇸🇪",
    "Tunisia": "🇹🇳", "Spain": "🇪🇸", "Cabo Verde": "🇨🇻",
    "Cape Verde": "🇨🇻", "Belgium": "🇧🇪", "Egypt": "🇪🇬",
    "Saudi Arabia": "🇸🇦", "Uruguay": "🇺🇾", "Iran": "🇮🇷",
    "New Zealand": "🇳🇿", "France": "🇫🇷", "Senegal": "🇸🇳",
    "Iraq": "🇮🇶", "Norway": "🇳🇴", "Argentina": "🇦🇷",
    "Algeria": "🇩🇿", "Austria": "🇦🇹", "Jordan": "🇯🇴",
    "Portugal": "🇵🇹", "DR Congo": "🇨🇩", "Congo DR": "🇨🇩",
    "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "Croatia": "🇭🇷", "Ghana": "🇬🇭",
    "Panama": "🇵🇦", "Uzbekistan": "🇺🇿", "Colombia": "🇨🇴",
}

STATUS_EMOJI = {
    "FINISHED":  "✅",
    "IN_PLAY":   "🔴",
    "PAUSED":    "⏸️",
    "SUSPENDED": "⚠️",
    "POSTPONED": "📅",
    "CANCELLED": "❌",
    "TIMED":     "",
    "SCHEDULED": "",
}

def flag(name):
    return FLAGS.get(name, "🏳️")

def team_str(name):
    return f"{flag(name)} {name}"

def fetch(path):
    url = f"{API_BASE}{path}"
    req = urllib.request.Request(url, headers={"X-Auth-Token": API_KEY})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def build_summary(match):
    home   = match["homeTeam"]["name"]
    away   = match["awayTeam"]["name"]
    status = match["status"]
    score  = match.get("score", {})
    ft     = score.get("fullTime", {})
    h_g    = ft.get("home")
    a_g    = ft.get("away")
    emoji  = STATUS_EMOJI.get(status, "")

    if status == "FINISHED" and h_g is not None:
        return f"{emoji} {team_str(home)} {h_g}–{a_g} {team_str(away)}"
    elif status in ("IN_PLAY", "PAUSED"):
        curr = score.get("halfTime", ft)
        hg   = curr.get("home", "?")
        ag   = curr.get("away", "?")
        return f"{emoji} {team_str(home)} {hg}–{ag} {team_str(away)} LIVE"
    else:
        return f"⚽️ {team_str(home)} vs {team_str(away)}"

def build_description(match):
    stage  = match.get("stage", "").replace("_", " ").title()
    group  = match.get("group", "")
    venue  = match.get("venue", "")
    status = match["status"]
    lines  = [f"Stage: {stage}"]
    if group:
        lines.append(f"Group: {group}")
    if venue:
        lines.append(f"Venue: {venue}")
    lines.append(f"Status: {status}")
    score = match.get("score", {})
    ft    = score.get("fullTime", {})
    if ft.get("home") is not None:
        lines.append(f"Score: {ft['home']}–{ft['away']}")
    return "\\n".join(lines)

def ics_fold(line):
    """Fold lines >75 octets per RFC 5545."""
    encoded = line.encode("utf-8")
    if len(encoded) <= 75:
        return line + "\r\n"
    result = b""
    while len(encoded) > 75:
        chunk = encoded[:75]
        # walk back past continuation bytes
        while len(chunk) > 0 and (chunk[-1] & 0xC0) == 0x80:
            chunk = chunk[:-1]
        # walk back past leading byte of multi-byte sequence
        while len(chunk) > 0 and (chunk[-1] & 0xC0) == 0xC0:
            chunk = chunk[:-1]
        if not chunk:
            chunk = encoded[:1]
        result += chunk + b"\r\n "
        encoded = encoded[len(chunk):]
    result += encoded + b"\r\n"
    return result.decode("utf-8")

def make_event(match):
    uid     = f"wc2026-{match['id']}@fifawc2026"
    summary = build_summary(match)
    desc    = build_description(match)
    venue   = match.get("venue", "")
    if not venue:
        venue = match.get("area", {}).get("name", "")

    dt_utc  = datetime.strptime(match["utcDate"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc)
    dt_end  = dt_utc + timedelta(hours=2)
    dtstamp = datetime.now(pytz.utc).strftime("%Y%m%dT%H%M%SZ")

    block  = "BEGIN:VEVENT\r\n"
    block += ics_fold(f"UID:{uid}")
    block += ics_fold(f"SUMMARY:{summary}")
    block += f"DTSTART:{dt_utc.strftime('%Y%m%dT%H%M%SZ')}\r\n"
    block += f"DTEND:{dt_end.strftime('%Y%m%dT%H%M%SZ')}\r\n"
    block += f"DTSTAMP:{dtstamp}\r\n"
    block += ics_fold(f"LOCATION:{venue}")
    block += ics_fold(f"DESCRIPTION:{desc}")
    block += "END:VEVENT\r\n"
    return block

def main():
    if not API_KEY:
        print("❌  Set FOOTBALL_DATA_API_KEY environment variable.")
        return

    print(f"⏳  Fetching all WC 2026 matches...")
    try:
        data = fetch(f"/competitions/{WC_CODE}/matches?season=2026&dateFrom=2026-06-11&dateTo=2026-07-20")
    except urllib.error.HTTPError as e:
        print(f"❌  API error {e.code}: {e.reason}")
        return

    matches = data.get("matches", [])
    print(f"✅  Got {len(matches)} matches from API.")

    cal  = "BEGIN:VCALENDAR\r\n"
    cal += "VERSION:2.0\r\n"
    cal += "PRODID:-//FIFA World Cup 2026 Live//EN\r\n"
    cal += "CALSCALE:GREGORIAN\r\n"
    cal += "METHOD:PUBLISH\r\n"
    cal += ics_fold("X-WR-CALNAME:🏆 FIFA World Cup 2026")
    cal += "X-WR-TIMEZONE:America/New_York\r\n"
    cal += "REFRESH-INTERVAL;VALUE=DURATION:PT3H\r\n"
    cal += "X-PUBLISHED-TTL:PT3H\r\n"

    for m in matches:
        cal += make_event(m)

    cal += "END:VCALENDAR\r\n"

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(cal)

    finished = sum(1 for m in matches if m["status"] == "FINISHED")
    live     = sum(1 for m in matches if m["status"] in ("IN_PLAY", "PAUSED"))
    upcoming = len(matches) - finished - live
    print(f"📅  Written {len(matches)} events → {OUTPUT}")
    print(f"    ✅ Finished: {finished}  🔴 Live: {live}  ⏳ Upcoming: {upcoming}")

if __name__ == "__main__":
    main()
