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

# ── Venue lookup by team pair (free tier API omits venue field) ────────────────
# Source: official FIFA WC 2026 schedule (NBCSports / FIFA.com)
# Key: frozenset of {home_team_name, away_team_name} as returned by the API
_V = {
    # Group A
    frozenset({"Mexico", "South Africa"}):            "Estadio Azteca, Mexico City, Mexico",
    frozenset({"Czechia", "South Africa"}):           "Mercedes-Benz Stadium, Atlanta, GA",
    frozenset({"Mexico", "Korea Republic"}):          "Estadio Akron, Guadalajara, Mexico",
    frozenset({"Czechia", "Mexico"}):                 "Estadio Azteca, Mexico City, Mexico",
    frozenset({"South Africa", "Korea Republic"}):    "Estadio BBVA, Monterrey, Mexico",
    # Group B
    frozenset({"Switzerland", "Bosnia and Herzegovina"}): "SoFi Stadium, Inglewood, CA",
    frozenset({"Canada", "Qatar"}):                   "BC Place, Vancouver, Canada",
    frozenset({"Switzerland", "Canada"}):             "BC Place, Vancouver, Canada",
    frozenset({"Bosnia and Herzegovina", "Qatar"}):   "Lumen Field, Seattle, WA",
    # Group C
    frozenset({"Haiti", "Scotland"}):                 "Gillette Stadium, Foxborough, MA",
    frozenset({"Scotland", "Morocco"}):               "Gillette Stadium, Foxborough, MA",
    frozenset({"Brazil", "Haiti"}):                   "Lincoln Financial Field, Philadelphia, PA",
    frozenset({"Scotland", "Brazil"}):                "Hard Rock Stadium, Miami Gardens, FL",
    frozenset({"Morocco", "Haiti"}):                  "Mercedes-Benz Stadium, Atlanta, GA",
    # Group D
    frozenset({"United States", "Australia"}):        "Lumen Field, Seattle, WA",
    frozenset({"Türkiye", "Paraguay"}):               "Levi's Stadium, Santa Clara, CA",
    frozenset({"Turkey", "Paraguay"}):                "Levi's Stadium, Santa Clara, CA",
    frozenset({"Türkiye", "United States"}):          "SoFi Stadium, Inglewood, CA",
    frozenset({"Turkey", "United States"}):           "SoFi Stadium, Inglewood, CA",
    frozenset({"Paraguay", "Australia"}):             "Levi's Stadium, Santa Clara, CA",
    # Group E
    frozenset({"Germany", "Côte d'Ivoire"}):          "BMO Field, Toronto, Canada",
    frozenset({"Germany", "Ivory Coast"}):            "BMO Field, Toronto, Canada",
    frozenset({"Ecuador", "Curaçao"}):                "Arrowhead Stadium, Kansas City, MO",
    frozenset({"Ecuador", "Curacao"}):                "Arrowhead Stadium, Kansas City, MO",
    frozenset({"Ecuador", "Germany"}):                "MetLife Stadium, East Rutherford, NJ",
    frozenset({"Curaçao", "Côte d'Ivoire"}):          "Lincoln Financial Field, Philadelphia, PA",
    frozenset({"Curacao", "Ivory Coast"}):            "Lincoln Financial Field, Philadelphia, PA",
    # Group F
    frozenset({"Netherlands", "Sweden"}):             "NRG Stadium, Houston, TX",
    frozenset({"Tunisia", "Japan"}):                  "Estadio BBVA, Monterrey, Mexico",
    frozenset({"Japan", "Sweden"}):                   "AT&T Stadium, Arlington, TX",
    frozenset({"Tunisia", "Netherlands"}):            "Arrowhead Stadium, Kansas City, MO",
    # Group G
    frozenset({"Belgium", "Iran"}):                   "SoFi Stadium, Inglewood, CA",
    frozenset({"New Zealand", "Egypt"}):              "BC Place, Vancouver, Canada",
    frozenset({"Egypt", "Iran"}):                     "Lumen Field, Seattle, WA",
    frozenset({"New Zealand", "Belgium"}):            "BC Place, Vancouver, Canada",
    # Group H
    frozenset({"Spain", "Saudi Arabia"}):             "Mercedes-Benz Stadium, Atlanta, GA",
    frozenset({"Uruguay", "Cabo Verde"}):             "Hard Rock Stadium, Miami Gardens, FL",
    frozenset({"Uruguay", "Cape Verde"}):             "Hard Rock Stadium, Miami Gardens, FL",
    frozenset({"Cabo Verde", "Saudi Arabia"}):        "NRG Stadium, Houston, TX",
    frozenset({"Cape Verde", "Saudi Arabia"}):        "NRG Stadium, Houston, TX",
    frozenset({"Uruguay", "Spain"}):                  "Estadio Akron, Guadalajara, Mexico",
    # Group I
    frozenset({"France", "Iraq"}):                    "Lincoln Financial Field, Philadelphia, PA",
    frozenset({"Norway", "Senegal"}):                 "MetLife Stadium, East Rutherford, NJ",
    frozenset({"Norway", "France"}):                  "Gillette Stadium, Foxborough, MA",
    frozenset({"Senegal", "Iraq"}):                   "BMO Field, Toronto, Canada",
    # Group J
    frozenset({"Argentina", "Austria"}):              "AT&T Stadium, Arlington, TX",
    frozenset({"Jordan", "Algeria"}):                 "Levi's Stadium, Santa Clara, CA",
    frozenset({"Algeria", "Austria"}):                "Arrowhead Stadium, Kansas City, MO",
    frozenset({"Jordan", "Argentina"}):               "AT&T Stadium, Arlington, TX",
    # Group K
    frozenset({"Uzbekistan", "Colombia"}):            "Estadio Azteca, Mexico City, Mexico",
    frozenset({"Portugal", "Uzbekistan"}):            "NRG Stadium, Houston, TX",
    frozenset({"Colombia", "DR Congo"}):              "Estadio Akron, Guadalajara, Mexico",
    frozenset({"Colombia", "Portugal"}):              "Hard Rock Stadium, Miami Gardens, FL",
    frozenset({"DR Congo", "Uzbekistan"}):            "Mercedes-Benz Stadium, Atlanta, GA",
    # Group L
    frozenset({"England", "Croatia"}):                "AT&T Stadium, Arlington, TX",
    frozenset({"Ghana", "Panama"}):                   "BMO Field, Toronto, Canada",
    frozenset({"England", "Ghana"}):                  "Gillette Stadium, Foxborough, MA",
    frozenset({"Panama", "Croatia"}):                 "BMO Field, Toronto, Canada",
    frozenset({"Panama", "England"}):                 "MetLife Stadium, East Rutherford, NJ",
    frozenset({"Croatia", "Ghana"}):                  "Lincoln Financial Field, Philadelphia, PA",
}

def _lookup_venue(match):
    home = match["homeTeam"]["name"]
    away = match["awayTeam"]["name"]
    return _V.get(frozenset({home, away}), "")

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
    venue  = match.get("venue", "") or _lookup_venue(match)
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
    venue = match.get("venue", "") or _lookup_venue(match)

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
