#!/usr/bin/env python3
"""
NBA Player Stats Scraper — Contract Dashboard
=============================================
Pulls Advanced & Per-Game stats from Basketball-Reference,
saves to players.csv, and patches src/App.jsx.

Contract AAV is hardcoded from Spotrac data (JS-rendered site,
not reliably scrapable without a headless browser).

Season mapping (sign_year = summer the deal was inked):
  T   = season ending in sign_year  (the "contract year")
  T-1 = season ending in sign_year - 1
  T+1 = season ending in sign_year + 1

Usage:
    pip install requests beautifulsoup4 pandas lxml
    python fetch_stats.py
"""

import re
import sys
import time
import subprocess
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup, Comment

# ── Config ──────────────────────────────────────────────────────────────────

BBREF_BASE = "https://www.basketball-reference.com"
DELAY      = 4   # seconds between requests — BBRef asks for ≥3 s

# ── Player definitions ───────────────────────────────────────────────────────
#
# AAV figures from Spotrac (hardcoded — site requires JS rendering):
#   Westbrook  OKC   5 yr / $205.0 M   Aug 2017  → $41 M/yr
#   Harden     HOU   4 yr / $171.1 M   Jul 2019  → $43 M/yr
#   Lillard    POR   4 yr / $176.3 M   Aug 2021  → $44 M/yr
#   Young      ATL   5 yr / $207.5 M   Aug 2021  → $42 M/yr
#   LaVine     CHI   5 yr / $215.2 M   Jul 2022  → $43 M/yr
#   Towns      MIN   4 yr / $224.0 M   Oct 2022  → $56 M/yr
#   Booker     PHX   4 yr / $214.0 M   Jul 2022  → $54 M/yr
#   Brown      BOS   5 yr / $304.0 M   Jul 2023  → $61 M/yr
#
# Age = player's age in the summer of sign_year.

PLAYERS = [
    {
        "id": 1,  "name": "R. Westbrook", "bbref_id": "westbru01",
        "pos": "PG", "age": 28, "tier": "Max", "salary": 41, "contractYear": 2017,
    },
    {
        "id": 2,  "name": "J. Harden",    "bbref_id": "hardeja01",
        "pos": "PG", "age": 29, "tier": "Max", "salary": 43, "contractYear": 2019,
    },
    {
        "id": 3,  "name": "D. Lillard",   "bbref_id": "lillada01",
        "pos": "PG", "age": 31, "tier": "Max", "salary": 44, "contractYear": 2021,
    },
    {
        "id": 4,  "name": "T. Young",     "bbref_id": "youngtr01",
        "pos": "PG", "age": 22, "tier": "Max", "salary": 42, "contractYear": 2021,
    },
    {
        "id": 5,  "name": "Z. LaVine",    "bbref_id": "lavinza01",
        "pos": "SG", "age": 27, "tier": "Max", "salary": 43, "contractYear": 2022,
    },
    {
        "id": 6,  "name": "K. Towns",     "bbref_id": "townska01",
        "pos": "C",  "age": 26, "tier": "Max", "salary": 56, "contractYear": 2022,
    },
    {
        "id": 7,  "name": "D. Booker",    "bbref_id": "bookede01",
        "pos": "SG", "age": 25, "tier": "Max", "salary": 54, "contractYear": 2022,
    },
    {
        "id": 8,  "name": "J. Brown",     "bbref_id": "brownja02",
        "pos": "SF", "age": 26, "tier": "Max", "salary": 61, "contractYear": 2023,
    },
]

# BBRef data-stat column → output key
ADV_COLS  = {"per": "PER", "ts_pct": "TS", "ws": "WS", "vorp": "VORP"}
PERG_COLS = {"pts_per_g": "PTS", "ast_per_g": "AST",
             "trb_per_g": "TRB", "tov_per_g": "TOV"}

# BBRef table IDs and column names (as of 2024 site redesign)
SEASON_COL = "year_id"         # was "season" in old layout
TEAM_COL   = "team_name_abbr"  # was "team_id"; multi-team totals row = "2TM"/"3TM"
PG_TABLE   = "per_game_stats"  # was "per_game"
ADV_TABLE  = "advanced"        # unchanged (visible in main HTML, not a comment)

# ── Scraping helpers ─────────────────────────────────────────────────────────

def fetch_page(bbref_id: str) -> str:
    """Fetch a BBRef player page via curl.

    curl bypasses Cloudflare's bot-detection that blocks Python's requests
    library; BBRef returns 200 to curl with standard browser headers.
    """
    url = f"{BBREF_BASE}/players/{bbref_id[0]}/{bbref_id}.html"
    print(f"    GET {url}")
    result = subprocess.run(
        [
            "curl", "-s", "--compressed",
            "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "-H", "Accept-Language: en-US,en;q=0.9",
            "-H", "Connection: keep-alive",
            "-H", "Upgrade-Insecure-Requests: 1",
            url,
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl failed (exit {result.returncode}): {result.stderr[:200]}")
    if len(result.stdout) < 1000:
        raise RuntimeError(f"Response suspiciously short ({len(result.stdout)} chars) — may be blocked")
    time.sleep(DELAY)
    return result.stdout


def get_table(html: str, table_id: str):
    """Return the BS4 <table> element, searching HTML comments too.

    BBRef wraps some stat tables (e.g. advanced) in HTML comments for
    performance; we have to pull them out manually.
    """
    soup = BeautifulSoup(html, "lxml")

    # Direct hit (tables visible in initial HTML)
    tbl = soup.find("table", {"id": table_id})
    if tbl:
        return tbl

    # Search HTML comment nodes
    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        if table_id in comment:
            inner = BeautifulSoup(comment, "lxml")
            tbl = inner.find("table", {"id": table_id})
            if tbl:
                return tbl

    return None


def table_to_df(tbl) -> pd.DataFrame:
    """Convert a BBRef <table> element to a tidy DataFrame using data-stat attrs."""
    rows = []
    for tr in tbl.select("tbody tr"):
        # BBRef injects sub-header rows with class "thead" — skip them
        if "thead" in tr.get("class", []):
            continue
        row = {
            td.get("data-stat"): td.get_text(strip=True)
            for td in tr.find_all(["td", "th"])
            if td.get("data-stat")
        }
        if row:
            rows.append(row)
    return pd.DataFrame(rows)


def season_end_year(s: str):
    """Parse a BBRef year_id string to the ending calendar year.

    Examples: '2016-17' → 2017, '2019-20' → 2020.
    Returns None for career totals or unrecognised strings.
    """
    if not isinstance(s, str):
        return None
    m = re.match(r"(\d{4})-(\d{2})", s.strip())
    return int(m.group(1)) + 1 if m else None


def pick_row(df: pd.DataFrame, year: int):
    """Return the stat Series for a given season end-year.

    When a player was traded mid-season BBRef adds one row per team plus a
    combined-totals row whose team_name_abbr is '2TM', '3TM', etc.
    We prefer that totals row so stats reflect the full season.
    """
    if SEASON_COL not in df.columns:
        return None

    tmp = df.copy()
    tmp["_yr"] = tmp[SEASON_COL].apply(season_end_year)
    sub = tmp[tmp["_yr"] == year]
    if sub.empty:
        return None

    if TEAM_COL in sub.columns:
        # Multi-team totals row ends in "TM" (e.g. "2TM", "3TM")
        tot = sub[sub[TEAM_COL].str.endswith("TM", na=False)]
        return (tot if not tot.empty else sub).iloc[0]

    return sub.iloc[0]


def safe_float(val, scale: float = 1.0) -> float:
    """Parse a stat cell value to float, applying an optional multiplier.
    Returns 0.0 on any parse failure (empty cell, 'Did Not Play', etc.).
    """
    try:
        v = float(str(val).replace(",", "").strip())
        return round(v * scale, 1)
    except (ValueError, TypeError):
        return 0.0


def extract_season(adv_df: pd.DataFrame, pg_df: pd.DataFrame, year: int) -> dict:
    """Build the stat dict for one season from advanced + per-game tables."""
    adv = pick_row(adv_df, year)
    pg  = pick_row(pg_df,  year)

    out = {}

    # Advanced stats
    if adv is not None:
        for col, key in ADV_COLS.items():
            # BBRef stores TS% as a decimal (e.g. .621); multiply → 62.1
            scale = 100.0 if key == "TS" else 1.0
            out[key] = safe_float(adv.get(col), scale)
    else:
        out.update({key: 0.0 for key in ADV_COLS.values()})

    # Per-game stats
    if pg is not None:
        for col, key in PERG_COLS.items():
            out[key] = safe_float(pg.get(col))
    else:
        out.update({key: 0.0 for key in PERG_COLS.values()})

    return out


# ── JavaScript / CSV formatting ──────────────────────────────────────────────

def fmt_stat_block(s: dict) -> str:
    return (
        f"{{ PER: {s['PER']}, WS: {s['WS']}, VORP: {s['VORP']}, "
        f"PTS: {s['PTS']}, AST: {s['AST']}, TRB: {s['TRB']}, "
        f"TS: {s['TS']}, TOV: {s['TOV']} }}"
    )


def fmt_player_js(p: dict, t1: dict, t: dict, t2: dict) -> str:
    return (
        f"  {{ id: {p['id']},  name: \"{p['name']}\",     pos: \"{p['pos']}\", "
        f"age: {p['age']}, tier: \"{p['tier']}\", "
        f"salary: {p['salary']}, contractYear: {p['contractYear']},\n"
        f"    T1: {fmt_stat_block(t1)},\n"
        f"    T:  {fmt_stat_block(t)},\n"
        f"    T2: {fmt_stat_block(t2)} }}"
    )


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    csv_rows   = []
    js_entries = []
    errors     = []

    for p in PLAYERS:
        sy = p["contractYear"]
        t_label = f"{sy - 1}-{str(sy)[2:]}"   # e.g. "2016-17"
        print(f"\n[{p['id']}/{len(PLAYERS)}]  {p['name']}  (T = {t_label}, sign_year = {sy})")

        try:
            html    = fetch_page(p["bbref_id"])
            adv_tbl = get_table(html, ADV_TABLE)
            pg_tbl  = get_table(html, PG_TABLE)

            if adv_tbl is None:
                raise ValueError(f"'{ADV_TABLE}' table not found in page HTML")
            if pg_tbl is None:
                raise ValueError(f"'{PG_TABLE}' table not found in page HTML")

            adv_df = table_to_df(adv_tbl)
            pg_df  = table_to_df(pg_tbl)

            t1 = extract_season(adv_df, pg_df, sy - 1)
            t  = extract_season(adv_df, pg_df, sy)
            t2 = extract_season(adv_df, pg_df, sy + 1)

            for label, s in [("T-1", t1), ("T  ", t), ("T+1", t2)]:
                print(
                    f"    {label}  PER={s['PER']:5.1f}  WS={s['WS']:5.1f}  "
                    f"VORP={s['VORP']:5.1f}  PTS={s['PTS']:5.1f}  "
                    f"AST={s['AST']:4.1f}  TRB={s['TRB']:4.1f}  "
                    f"TS={s['TS']:5.1f}  TOV={s['TOV']:4.1f}"
                )

            js_entries.append(fmt_player_js(p, t1, t, t2))

            # Build flat CSV row
            row = {k: v for k, v in p.items() if k != "bbref_id"}
            for period, stats in [("T1", t1), ("T", t), ("T2", t2)]:
                for sk, sv in stats.items():
                    row[f"{period}_{sk}"] = sv
            csv_rows.append(row)

        except Exception as exc:
            msg = f"{p['name']}: {exc}"
            errors.append(msg)
            print(f"    ERROR: {exc}")

    # ── Save players.csv ─────────────────────────────────────────────────────
    if csv_rows:
        pd.DataFrame(csv_rows).to_csv("players.csv", index=False)
        print(f"\n✓  Saved {len(csv_rows)} players → players.csv")

    # ── Patch src/App.jsx ────────────────────────────────────────────────────
    if js_entries:
        new_block = "const PLAYERS = [\n" + ",\n".join(js_entries) + "\n];"
        jsx_path  = Path("src/App.jsx")

        if jsx_path.exists():
            original = jsx_path.read_text()
            # Match the entire const PLAYERS = [...]; block (multi-line)
            patched = re.sub(
                r"const PLAYERS\s*=\s*\[[\s\S]*?\];",
                new_block,
                original,
                count=1,
            )
            if patched != original:
                jsx_path.write_text(patched)
                print(f"✓  Patched src/App.jsx  ({len(js_entries)} players)")
            else:
                print("⚠   PLAYERS pattern not matched in App.jsx — printing new array below:")
                print(new_block)
        else:
            print("⚠   src/App.jsx not found — printing new array below:")
            print(new_block)

    # ── Summary ──────────────────────────────────────────────────────────────
    if errors:
        print(f"\n⚠   {len(errors)} error(s) during scrape:")
        for e in errors:
            print(f"    {e}")
    else:
        print(f"\n✓  All {len(PLAYERS)} players scraped successfully.")


if __name__ == "__main__":
    main()
