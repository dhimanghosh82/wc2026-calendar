"""
FIFA World Cup 2026 - Live ICS Generator
Fetches scores from football-data.org (free tier) and generates ICS.
Run manually or via GitHub Actions on a schedule.

API: https://www.football-data.org/
Competition ID for World Cup: WC
Season: 2026
"""

import os
import re
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
    frozenset({"Mexico", "South Africa"}):                    "Estadio Azteca, Mexico City, Mexico",
    frozenset({"Korea Republic", "Czechia"}):                 "Estadio Akron, Guadalajara, Mexico",
    frozenset({"South Korea", "Czechia"}):                    "Estadio Akron, Guadalajara, Mexico",
    frozenset({"Czechia", "South Africa"}):                   "Mercedes-Benz Stadium, Atlanta, GA",
    frozenset({"Mexico", "Korea Republic"}):                  "Estadio Akron, Guadalajara, Mexico",
    frozenset({"Mexico", "South Korea"}):                     "Estadio Akron, Guadalajara, Mexico",
    frozenset({"Czechia", "Mexico"}):                         "Estadio Azteca, Mexico City, Mexico",
    frozenset({"South Africa", "Korea Republic"}):            "Estadio BBVA, Monterrey, Mexico",
    frozenset({"South Africa", "South Korea"}):               "Estadio BBVA, Monterrey, Mexico",
    # Group B
    frozenset({"Canada", "Bosnia and Herzegovina"}):          "BMO Field, Toronto, Canada",
    frozenset({"Canada", "Bosnia & Herzegovina"}):            "BMO Field, Toronto, Canada",
    frozenset({"Canada", "Bosnia-Herzegovina"}):              "BMO Field, Toronto, Canada",
    frozenset({"Qatar", "Switzerland"}):                      "Levi's Stadium, Santa Clara, CA",
    frozenset({"Switzerland", "Bosnia and Herzegovina"}):     "SoFi Stadium, Inglewood, CA",
    frozenset({"Switzerland", "Bosnia & Herzegovina"}):       "SoFi Stadium, Inglewood, CA",
    frozenset({"Switzerland", "Bosnia-Herzegovina"}):         "SoFi Stadium, Inglewood, CA",
    frozenset({"Canada", "Qatar"}):                           "BC Place, Vancouver, Canada",
    frozenset({"Switzerland", "Canada"}):                     "BC Place, Vancouver, Canada",
    frozenset({"Bosnia and Herzegovina", "Qatar"}):           "Lumen Field, Seattle, WA",
    frozenset({"Bosnia & Herzegovina", "Qatar"}):             "Lumen Field, Seattle, WA",
    frozenset({"Bosnia-Herzegovina", "Qatar"}):               "Lumen Field, Seattle, WA",
    # Group C
    frozenset({"Brazil", "Morocco"}):                         "MetLife Stadium, East Rutherford, NJ",
    frozenset({"Haiti", "Scotland"}):                         "Gillette Stadium, Foxborough, MA",
    frozenset({"Scotland", "Morocco"}):                       "Gillette Stadium, Foxborough, MA",
    frozenset({"Brazil", "Haiti"}):                           "Lincoln Financial Field, Philadelphia, PA",
    frozenset({"Scotland", "Brazil"}):                        "Hard Rock Stadium, Miami Gardens, FL",
    frozenset({"Morocco", "Haiti"}):                          "Mercedes-Benz Stadium, Atlanta, GA",
    # Group D
    frozenset({"United States", "Paraguay"}):                 "SoFi Stadium, Inglewood, CA",
    frozenset({"Australia", "Türkiye"}):                      "BC Place, Vancouver, Canada",
    frozenset({"Australia", "Turkey"}):                       "BC Place, Vancouver, Canada",
    frozenset({"United States", "Australia"}):                "Lumen Field, Seattle, WA",
    frozenset({"Türkiye", "Paraguay"}):                       "Levi's Stadium, Santa Clara, CA",
    frozenset({"Turkey", "Paraguay"}):                        "Levi's Stadium, Santa Clara, CA",
    frozenset({"Türkiye", "United States"}):                  "SoFi Stadium, Inglewood, CA",
    frozenset({"Turkey", "United States"}):                   "SoFi Stadium, Inglewood, CA",
    frozenset({"Paraguay", "Australia"}):                     "Levi's Stadium, Santa Clara, CA",
    # Group E
    frozenset({"Germany", "Curaçao"}):                        "NRG Stadium, Houston, TX",
    frozenset({"Germany", "Curacao"}):                        "NRG Stadium, Houston, TX",
    frozenset({"Côte d'Ivoire", "Ecuador"}):                  "Lincoln Financial Field, Philadelphia, PA",
    frozenset({"Ivory Coast", "Ecuador"}):                    "Lincoln Financial Field, Philadelphia, PA",
    frozenset({"Germany", "Côte d'Ivoire"}):                  "BMO Field, Toronto, Canada",
    frozenset({"Germany", "Ivory Coast"}):                    "BMO Field, Toronto, Canada",
    frozenset({"Ecuador", "Curaçao"}):                        "GEHA Field at Arrowhead, Kansas City, MO",
    frozenset({"Ecuador", "Curacao"}):                        "GEHA Field at Arrowhead, Kansas City, MO",
    frozenset({"Ecuador", "Germany"}):                        "MetLife Stadium, East Rutherford, NJ",
    frozenset({"Curaçao", "Côte d'Ivoire"}):                  "Lincoln Financial Field, Philadelphia, PA",
    frozenset({"Curacao", "Ivory Coast"}):                    "Lincoln Financial Field, Philadelphia, PA",
    # Group F
    frozenset({"Netherlands", "Japan"}):                      "AT&T Stadium, Arlington, TX",
    frozenset({"Sweden", "Tunisia"}):                         "Estadio BBVA, Monterrey, Mexico",
    frozenset({"Netherlands", "Sweden"}):                     "NRG Stadium, Houston, TX",
    frozenset({"Tunisia", "Japan"}):                          "Estadio BBVA, Monterrey, Mexico",
    frozenset({"Japan", "Sweden"}):                           "AT&T Stadium, Arlington, TX",
    frozenset({"Tunisia", "Netherlands"}):                    "GEHA Field at Arrowhead, Kansas City, MO",
    # Group G
    frozenset({"Iran", "New Zealand"}):                       "SoFi Stadium, Inglewood, CA",
    frozenset({"Belgium", "Egypt"}):                          "Lumen Field, Seattle, WA",
    frozenset({"Belgium", "Iran"}):                           "SoFi Stadium, Inglewood, CA",
    frozenset({"New Zealand", "Egypt"}):                      "BC Place, Vancouver, Canada",
    frozenset({"Egypt", "Iran"}):                             "Lumen Field, Seattle, WA",
    frozenset({"New Zealand", "Belgium"}):                    "BC Place, Vancouver, Canada",
    # Group H
    frozenset({"Spain", "Cabo Verde"}):                       "Mercedes-Benz Stadium, Atlanta, GA",
    frozenset({"Spain", "Cape Verde"}):                       "Mercedes-Benz Stadium, Atlanta, GA",
    frozenset({"Spain", "Cape Verde Islands"}):               "Mercedes-Benz Stadium, Atlanta, GA",
    frozenset({"Saudi Arabia", "Uruguay"}):                   "Hard Rock Stadium, Miami Gardens, FL",
    frozenset({"Spain", "Saudi Arabia"}):                     "Mercedes-Benz Stadium, Atlanta, GA",
    frozenset({"Uruguay", "Cabo Verde"}):                     "Hard Rock Stadium, Miami Gardens, FL",
    frozenset({"Uruguay", "Cape Verde"}):                     "Hard Rock Stadium, Miami Gardens, FL",
    frozenset({"Uruguay", "Cape Verde Islands"}):             "Hard Rock Stadium, Miami Gardens, FL",
    frozenset({"Cabo Verde", "Saudi Arabia"}):                "NRG Stadium, Houston, TX",
    frozenset({"Cape Verde", "Saudi Arabia"}):                "NRG Stadium, Houston, TX",
    frozenset({"Cape Verde Islands", "Saudi Arabia"}):        "NRG Stadium, Houston, TX",
    frozenset({"Uruguay", "Spain"}):                          "Estadio Akron, Guadalajara, Mexico",
    # Group I
    frozenset({"France", "Senegal"}):                         "MetLife Stadium, East Rutherford, NJ",
    frozenset({"Iraq", "Norway"}):                            "Gillette Stadium, Foxborough, MA",
    frozenset({"France", "Iraq"}):                            "Lincoln Financial Field, Philadelphia, PA",
    frozenset({"Norway", "Senegal"}):                         "MetLife Stadium, East Rutherford, NJ",
    frozenset({"Norway", "France"}):                          "Gillette Stadium, Foxborough, MA",
    frozenset({"Senegal", "Iraq"}):                           "BMO Field, Toronto, Canada",
    # Group J
    frozenset({"Argentina", "Algeria"}):                      "GEHA Field at Arrowhead, Kansas City, MO",
    frozenset({"Austria", "Jordan"}):                         "Levi's Stadium, Santa Clara, CA",
    frozenset({"Argentina", "Austria"}):                      "AT&T Stadium, Arlington, TX",
    frozenset({"Jordan", "Algeria"}):                         "Levi's Stadium, Santa Clara, CA",
    frozenset({"Algeria", "Austria"}):                        "GEHA Field at Arrowhead, Kansas City, MO",
    frozenset({"Jordan", "Argentina"}):                       "AT&T Stadium, Arlington, TX",
    # Group K
    frozenset({"Portugal", "DR Congo"}):                      "NRG Stadium, Houston, TX",
    frozenset({"Portugal", "Congo DR"}):                      "NRG Stadium, Houston, TX",
    frozenset({"Uzbekistan", "Colombia"}):                    "Estadio Azteca, Mexico City, Mexico",
    frozenset({"Portugal", "Uzbekistan"}):                    "NRG Stadium, Houston, TX",
    frozenset({"Colombia", "DR Congo"}):                      "Estadio Akron, Guadalajara, Mexico",
    frozenset({"Colombia", "Congo DR"}):                      "Estadio Akron, Guadalajara, Mexico",
    frozenset({"Colombia", "Portugal"}):                      "Hard Rock Stadium, Miami Gardens, FL",
    frozenset({"DR Congo", "Uzbekistan"}):                    "Mercedes-Benz Stadium, Atlanta, GA",
    frozenset({"Congo DR", "Uzbekistan"}):                    "Mercedes-Benz Stadium, Atlanta, GA",
    # Group L
    frozenset({"England", "Croatia"}):                        "AT&T Stadium, Arlington, TX",
    frozenset({"Ghana", "Panama"}):                           "BMO Field, Toronto, Canada",
    frozenset({"England", "Ghana"}):                          "Gillette Stadium, Foxborough, MA",
    frozenset({"Panama", "Croatia"}):                         "BMO Field, Toronto, Canada",
    frozenset({"Panama", "England"}):                         "MetLife Stadium, East Rutherford, NJ",
    frozenset({"Croatia", "Ghana"}):                          "Lincoln Financial Field, Philadelphia, PA",
}

import re as _re, unicodedata as _ud
def _norm(name):
    """Normalize team name for fuzzy matching."""
    # decompose unicode (ü→u+combining) then strip combining chars
    name = _ud.normalize("NFKD", name)
    name = "".join(c for c in name if _ud.category(c) != "Mn")
    name = name.lower()
    name = _re.sub(r"[^a-z]", "", name)  # strip non-alpha
    for src, dst in [("korearepublic","southkorea"),("cotedivoire","ivorycoast"),
                     ("democraticrepublicofcongo","drcongo"),("congord","drcongo"),("congodr","drcongo"),
                     ("capeverdeislands","capeverde"),("caboverde","capeverde"),
                     ("bosniaandherzegovina","bosniaherzegovina"),
                     ("bosnia","bosniaherzegovina"),("turkiye","turkey"),
                     ("unitedstates","usa"),]:
        name = name.replace(src, dst)
    return name

_V_NORM = {frozenset({_norm(a), _norm(b)}): v for fs, v in _V.items() for a, b in [list(fs)]}

# ── Knockout stage metadata ───────────────────────────────────────────────────
# Key = football-data.org match ID (int)
# short = compact bracket label shown when teams are TBD (e.g. "1C vs 2F")
# full  = verbose bracket description for the DESCRIPTION field
# ph/pa = home/away team. All 16 R32 matchups are FINAL — group winners,
#         runners-up, and the 8 best-third-place assignments are confirmed
#         (group stage complete, June 28 2026). Sources: kingdoggydog.github.io
#         group-winners.json + published R32 bracket (Sky Sports / Yahoo / CBS).
_KNOCKOUT = {
    # Round of 32 ── M73-M88
    537417: {"venue": "SoFi Stadium, Inglewood, CA",
              "short": "2A vs 2B", "full": "Runner-up Group A vs Runner-up Group B",
              "ph": "South Africa", "pa": "Canada"},
    537415: {"venue": "Gillette Stadium, Foxborough, MA",
              "short": "1E vs 3rd(A/B/C/D/F)", "full": "Winner Group E vs Best 3rd Place (A/B/C/D/F)",
              "ph": "Germany", "pa": "Paraguay"},
    537418: {"venue": "Estadio BBVA, Monterrey, Mexico",
              "short": "1F vs 2C", "full": "Winner Group F vs Runner-up Group C",
              "ph": "Netherlands", "pa": "Morocco"},
    537423: {"venue": "NRG Stadium, Houston, TX",
              "short": "1C vs 2F", "full": "Winner Group C vs Runner-up Group F",
              "ph": "Brazil", "pa": "Japan"},
    537416: {"venue": "MetLife Stadium, East Rutherford, NJ",
              "short": "1I vs 3rd(C/D/F/G/H)", "full": "Winner Group I vs Best 3rd Place (C/D/F/G/H)",
              "ph": "France", "pa": "Sweden"},
    537424: {"venue": "AT&T Stadium, Arlington, TX",
              "short": "2E vs 2I", "full": "Runner-up Group E vs Runner-up Group I",
              "ph": "Ivory Coast", "pa": "Norway"},
    537425: {"venue": "Estadio Azteca, Mexico City, Mexico",
              "short": "1A vs 3rd(C/E/F/H/I)", "full": "Winner Group A vs Best 3rd Place (C/E/F/H/I)",
              "ph": "Mexico", "pa": "Ecuador"},
    537426: {"venue": "Mercedes-Benz Stadium, Atlanta, GA",
              "short": "1L vs 3rd(E/H/I/J/K)", "full": "Winner Group L vs Best 3rd Place (E/H/I/J/K)",
              "ph": "England", "pa": "DR Congo"},
    537422: {"venue": "Lumen Field, Seattle, WA",
              "short": "1G vs 3rd(A/E/H/I/J)", "full": "Winner Group G vs Best 3rd Place (A/E/H/I/J)",
              "ph": "Belgium", "pa": "Senegal"},
    537421: {"venue": "Levi's Stadium, Santa Clara, CA",
              "short": "1D vs 3rd(B/E/F/I/J)", "full": "Winner Group D vs Best 3rd Place (B/E/F/I/J)",
              "ph": "United States", "pa": "Bosnia and Herzegovina"},
    537420: {"venue": "SoFi Stadium, Inglewood, CA",
              "short": "1H vs 2J", "full": "Winner Group H vs Runner-up Group J",
              "ph": "Spain", "pa": "Austria"},
    537419: {"venue": "BMO Field, Toronto, Canada",
              "short": "2K vs 2L", "full": "Runner-up Group K vs Runner-up Group L",
              "ph": "Portugal", "pa": "Croatia"},
    537429: {"venue": "BC Place, Vancouver, Canada",
              "short": "1B vs 3rd(E/F/G/I/J)", "full": "Winner Group B vs Best 3rd Place (E/F/G/I/J)",
              "ph": "Switzerland", "pa": "Algeria"},
    537428: {"venue": "AT&T Stadium, Arlington, TX",
              "short": "2D vs 2G", "full": "Runner-up Group D vs Runner-up Group G",
              "ph": "Australia", "pa": "Egypt"},
    537427: {"venue": "Hard Rock Stadium, Miami Gardens, FL",
              "short": "1J vs 2H", "full": "Winner Group J vs Runner-up Group H",
              "ph": "Argentina", "pa": "Cape Verde"},
    537430: {"venue": "GEHA Field at Arrowhead, Kansas City, MO",
              "short": "1K vs 3rd(D/E/I/J/L)", "full": "Winner Group K vs Best 3rd Place (D/E/I/J/L)",
              "ph": "Colombia", "pa": "Ghana"},
    # Round of 16 ── M89-M96
    537376: {"venue": "NRG Stadium, Houston, TX",
              "short": "W73 vs W75", "full": "Winner Match 73 vs Winner Match 75",
              "ph": None, "pa": None},
    537375: {"venue": "Lincoln Financial Field, Philadelphia, PA",
              "short": "W74 vs W77", "full": "Winner Match 74 vs Winner Match 77",
              "ph": None, "pa": None},
    537377: {"venue": "MetLife Stadium, East Rutherford, NJ",
              "short": "W76 vs W78", "full": "Winner Match 76 vs Winner Match 78",
              "ph": None, "pa": None},
    537378: {"venue": "Estadio Azteca, Mexico City, Mexico",
              "short": "W79 vs W80", "full": "Winner Match 79 vs Winner Match 80",
              "ph": None, "pa": None},
    537379: {"venue": "AT&T Stadium, Arlington, TX",
              "short": "W81 vs W82", "full": "Winner Match 81 vs Winner Match 82",
              "ph": None, "pa": None},
    537380: {"venue": "Lumen Field, Seattle, WA",
              "short": "W83 vs W84", "full": "Winner Match 83 vs Winner Match 84",
              "ph": None, "pa": None},
    537381: {"venue": "Mercedes-Benz Stadium, Atlanta, GA",
              "short": "W85 vs W86", "full": "Winner Match 85 vs Winner Match 86",
              "ph": None, "pa": None},
    537382: {"venue": "BC Place, Vancouver, Canada",
              "short": "W87 vs W88", "full": "Winner Match 87 vs Winner Match 88",
              "ph": None, "pa": None},
    # Quarterfinals ── M97-M100
    537383: {"venue": "Gillette Stadium, Foxborough, MA",
              "short": "W89 vs W90", "full": "Winner Match 89 vs Winner Match 90",
              "ph": None, "pa": None},
    537384: {"venue": "SoFi Stadium, Inglewood, CA",
              "short": "W93 vs W94", "full": "Winner Match 93 vs Winner Match 94",
              "ph": None, "pa": None},
    537385: {"venue": "Hard Rock Stadium, Miami Gardens, FL",
              "short": "W91 vs W92", "full": "Winner Match 91 vs Winner Match 92",
              "ph": None, "pa": None},
    537386: {"venue": "GEHA Field at Arrowhead, Kansas City, MO",
              "short": "W95 vs W96", "full": "Winner Match 95 vs Winner Match 96",
              "ph": None, "pa": None},
    # Semifinals ── M101-M102
    537387: {"venue": "AT&T Stadium, Arlington, TX",
              "short": "W97 vs W98", "full": "Winner Match 97 vs Winner Match 98",
              "ph": None, "pa": None},
    537388: {"venue": "Mercedes-Benz Stadium, Atlanta, GA",
              "short": "W99 vs W100", "full": "Winner Match 99 vs Winner Match 100",
              "ph": None, "pa": None},
    # Third Place Play-off ── M103
    537389: {"venue": "Hard Rock Stadium, Miami Gardens, FL",
              "short": "L101 vs L102", "full": "Loser Match 101 vs Loser Match 102",
              "ph": None, "pa": None},
    # Final ── M104
    537390: {"venue": "MetLife Stadium, East Rutherford, NJ",
              "short": "W101 vs W102", "full": "Winner Match 101 vs Winner Match 102",
              "ph": None, "pa": None},
}

# ── Bracket progression ───────────────────────────────────────────────────────
# FIFA match number (M73–M104) → football-data.org match id. Used to advance the
# bracket from results: the "short" labels above reference source matches by FIFA
# number (e.g. "W73 vs W75", "L101 vs L102"), and this map resolves those numbers
# to the API match objects that carry the actual results.
_M_TO_ID = {
    73: 537417, 74: 537415, 75: 537418, 76: 537423, 77: 537416, 78: 537424,
    79: 537425, 80: 537426, 81: 537421, 82: 537422, 83: 537419, 84: 537420,
    85: 537429, 86: 537427, 87: 537430, 88: 537428,
    89: 537376, 90: 537375, 91: 537377, 92: 537378, 93: 537379, 94: 537380,
    95: 537381, 96: 537382, 97: 537383, 98: 537384, 99: 537385, 100: 537386,
    101: 537387, 102: 537388, 103: 537389, 104: 537390,
}

def _winner_loser(m):
    """(winner_name, loser_name) for a FINISHED knockout match, else (None, None).
    Relies on football-data's score.winner, which already reflects extra time and
    penalty shootouts."""
    if not m or m.get("status") != "FINISHED":
        return None, None
    w    = (m.get("score") or {}).get("winner")
    home = (m.get("homeTeam") or {}).get("name")
    away = (m.get("awayTeam") or {}).get("name")
    if w == "HOME_TEAM":
        return home, away
    if w == "AWAY_TEAM":
        return away, home
    return None, None

def advance_bracket(matches):
    """Propagate winners/losers of finished knockout matches into the predictions
    (ph/pa) of the matches they feed, so the bracket advances from real results
    even before the API populates the next round's team slots. The display layer
    (_ko_slot) still prefers the API's own team names when present, so this only
    ever leads — never overrides — the official data."""
    by_id = {m.get("id"): m for m in matches}

    def resolve(token):
        # token like "W73" / "L101" → winner/loser name of that FIFA match, or None
        kind, num = token[0], int(token[1:])
        src = by_id.get(_M_TO_ID.get(num))
        win, lose = _winner_loser(src)
        return win if kind == "W" else lose

    for meta in _KNOCKOUT.values():
        parts = meta.get("short", "").split(" vs ", 1)
        if len(parts) != 2:
            continue
        for tok, key in ((parts[0].strip(), "ph"), (parts[1].strip(), "pa")):
            if re.fullmatch(r"[WL]\d+", tok):
                name = resolve(tok)
                if name:
                    meta[key] = name

def _lookup_venue(match):
    # Knockout metadata has venue for every non-group match (API omits it)
    ko = _KNOCKOUT.get(match.get("id"))
    if ko:
        return ko["venue"]
    home = (match.get("homeTeam") or {}).get("name") or ""
    away = (match.get("awayTeam") or {}).get("name") or ""
    if not home or not away:
        return ""
    key = frozenset({_norm(home), _norm(away)})
    return _V_NORM.get(key, "")

# ── Flag map ──────────────────────────────────────────────────────────────────
FLAGS = {
    "Mexico": "🇲🇽", "South Africa": "🇿🇦", "Korea Republic": "🇰🇷", "South Korea": "🇰🇷",
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

def fetch(path, retries=3):
    import time
    url = f"{API_BASE}{path}"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"X-Auth-Token": API_KEY})
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read())
        except Exception as e:
            if attempt == retries - 1:
                raise
            print(f"⚠️  Attempt {attempt + 1} failed ({e}), retrying...")
            time.sleep(3)

def _ko_slot(real_name, pred, bracket_label):
    """Display string for one team slot: real API name > prediction > bracket label."""
    if real_name and real_name != "TBD":
        return team_str(real_name)
    if pred:
        return f"{flag(pred)} {pred}"
    return f"🏆 {bracket_label}"

def build_summary(match):
    home   = (match.get("homeTeam") or {}).get("name") or "TBD"
    away   = (match.get("awayTeam") or {}).get("name") or "TBD"
    status = match["status"]
    score  = match.get("score", {})
    ft     = score.get("fullTime", {})
    h_g    = ft.get("home")
    a_g    = ft.get("away")
    emoji  = STATUS_EMOJI.get(status, "")

    if status == "FINISHED" and h_g is not None:
        return f"{emoji} {team_str(home)} {h_g}–{a_g} {team_str(away)}"
    elif status in ("IN_PLAY", "PAUSED"):
        hg = ft.get("home") if ft.get("home") is not None else "?"
        ag = ft.get("away") if ft.get("away") is not None else "?"
        return f"{emoji} {team_str(home)} {hg}–{ag} {team_str(away)} LIVE"

    ko = _KNOCKOUT.get(match.get("id"))
    if ko and (home == "TBD" or away == "TBD"):
        parts = ko["short"].split(" vs ", 1)
        h_label, a_label = parts[0], (parts[1] if len(parts) > 1 else "")
        hd = _ko_slot(home if home != "TBD" else "", ko.get("ph"), h_label)
        ad = _ko_slot(away if away != "TBD" else "", ko.get("pa"), a_label)
        return f"⚽️ {hd} vs {ad}"

    return f"⚽️ {team_str(home)} vs {team_str(away)}"

def build_description(match):
    home   = (match.get("homeTeam") or {}).get("name") or "TBD"
    away   = (match.get("awayTeam") or {}).get("name") or "TBD"
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
    ko = _KNOCKOUT.get(match.get("id"))
    if ko:
        lines.append(f"Bracket: {ko['full']}")
        if ko.get("ph") or ko.get("pa"):
            ph = ko.get("ph") or "TBD"
            pa = ko.get("pa") or "TBD"
            lines.append(f"Predicted: {ph} vs {pa}")
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

    # Advance knockout predictions from finished-match results
    advance_bracket(matches)

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
