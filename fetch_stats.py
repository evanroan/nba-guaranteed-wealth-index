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
    python3 fetch_stats.py [--force]   # --force re-scrapes existing players
"""

import re
import sys
import time
import random
import subprocess
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup, Comment

# ── Config ──────────────────────────────────────────────────────────────────

BBREF_BASE     = "https://www.basketball-reference.com"
DELAY          = 4     # base seconds between requests — BBRef asks for ≥3 s
DELAY_JITTER   = 1.5   # extra random seconds added per request
SKIP_EXISTING  = "--force" not in sys.argv  # skip players already in players.csv
CSV_PATH       = Path("players.csv")
ERROR_LOG      = Path("scrape_errors.log")

# ── Player definitions ───────────────────────────────────────────────────────
#
# AAV figures from Spotrac (hardcoded — site requires JS rendering).
# Age = player's age in the summer of sign_year.
#
# ── MAX tier (~$28–61 M/yr) ────────────────────────────────────────────────
#   Westbrook  OKC   5 yr / $205.0 M   Aug 2017  → $41 M/yr
#   Harden     HOU   4 yr / $171.1 M   Jul 2019  → $43 M/yr
#   Lillard    POR   4 yr / $176.3 M   Aug 2021  → $44 M/yr
#   Young      ATL   5 yr / $207.5 M   Aug 2021  → $42 M/yr
#   LaVine     CHI   5 yr / $215.2 M   Jul 2022  → $43 M/yr
#   Towns      MIN   4 yr / $224.0 M   Oct 2022  → $56 M/yr
#   Booker     PHX   4 yr / $214.0 M   Jul 2022  → $54 M/yr
#   Brown      BOS   5 yr / $304.0 M   Jul 2023  → $61 M/yr
#   Hayward    BOS   4 yr / $128.0 M   Jul 2017  → $32 M/yr
#   Wall       WAS   4 yr / $170.0 M   Jul 2017  → $47 M/yr (super-max)
#   Griffin    DET   5 yr / $171.2 M   Jul 2018  → $34 M/yr
#   Wiggins    MIN   5 yr / $148.0 M   Oct 2017  → $30 M/yr (ext, kicks in 2018-19)
#   Conley     MEM   5 yr / $153.0 M   Jul 2016  → $31 M/yr
#   Simmons    PHI   5 yr / $170.0 M   Oct 2019  → $34 M/yr (ext, kicks in 2020-21)
#   T. Harris  PHI   5 yr / $180.0 M   Jul 2019  → $36 M/yr
#
# ── MID tier (~$13–27 M/yr) ────────────────────────────────────────────────
#   Noah       NYK   4 yr /  $72.0 M   Jul 2016  → $18 M/yr
#   Deng       LAL   4 yr /  $72.0 M   Jul 2016  → $18 M/yr
#   Parsons    MEM   4 yr /  $94.4 M   Jul 2016  → $24 M/yr
#   Fournier   NYK   4 yr /  $78.0 M   Aug 2021  → $20 M/yr
#   Mozgov     LAL   4 yr /  $64.0 M   Jul 2016  → $16 M/yr
#   Batum      CHA   5 yr / $120.0 M   Jul 2016  → $24 M/yr
#   R. Anderson HOU  4 yr /  $80.0 M   Jul 2016  → $20 M/yr
#   Biyombo    ORL   4 yr /  $72.0 M   Jul 2016  → $17 M/yr
#   E. Turner  POR   4 yr /  $70.0 M   Jul 2016  → $17.5 M/yr
#   O. Porter  WAS   4 yr / $106.0 M   Jul 2017  → $26.5 M/yr
#   Crabbe     BKN   4 yr /  $75.0 M   Jul 2016  → $18.75 M/yr
#
# ── LOW tier (~$5–12 M/yr) ──────────────────────────────────────────────────
#   Dellavedova MIL  4 yr /  $38.4 M   Jul 2016  →  $10 M/yr
#   Korver     ATL   4 yr /  $24.0 M   Jul 2014  →   $6 M/yr
#   Beverley   HOU   3 yr /  $21.0 M   Jul 2017  →   $7 M/yr
#   Belinelli  SAS   3 yr /  $19.5 M   Jul 2017  →   $7 M/yr
#   Sefolosha  ATL   3 yr /  $16.5 M   Jul 2014  →   $6 M/yr
#   MCW        MIL   4 yr /  $44.0 M   Oct 2015  →  $11 M/yr
#   C. Joseph  IND   4 yr /  $37.0 M   Jul 2016  →   $9 M/yr
#   J. Clarkson LAL  4 yr /  $50.0 M   Oct 2016  →  $12.5 M/yr
#   R. Hood    UTA   4 yr /  $48.0 M   Oct 2016  →  $12 M/yr

PLAYERS = [
    # ── Max ──────────────────────────────────────────────────────────────────
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
    {
        "id": 19, "name": "G. Hayward",   "bbref_id": "haywago01",
        "pos": "SF", "age": 27, "tier": "Max", "salary": 32, "contractYear": 2017,
    },
    {
        "id": 20, "name": "J. Wall",      "bbref_id": "walljo01",
        "pos": "PG", "age": 26, "tier": "Max", "salary": 47, "contractYear": 2017,
    },
    {
        "id": 21, "name": "B. Griffin",   "bbref_id": "griffbl01",
        "pos": "PF", "age": 28, "tier": "Max", "salary": 34, "contractYear": 2018,
    },
    {
        "id": 22, "name": "A. Wiggins",   "bbref_id": "wiggian01",
        "pos": "SF", "age": 22, "tier": "Max", "salary": 30, "contractYear": 2018,
    },
    {
        "id": 23, "name": "M. Conley",    "bbref_id": "conlemi01",
        "pos": "PG", "age": 28, "tier": "Max", "salary": 31, "contractYear": 2016,
    },
    {
        "id": 24, "name": "B. Simmons",   "bbref_id": "simmobe01",
        "pos": "PG", "age": 23, "tier": "Max", "salary": 34, "contractYear": 2020,
    },
    {
        "id": 25, "name": "T. Harris",    "bbref_id": "harrito02",
        "pos": "PF", "age": 26, "tier": "Max", "salary": 36, "contractYear": 2019,
    },
    # ── Mid ──────────────────────────────────────────────────────────────────
    {
        "id": 9,  "name": "J. Noah",      "bbref_id": "noahjo01",
        "pos": "C",  "age": 31, "tier": "Mid", "salary": 18, "contractYear": 2016,
    },
    {
        "id": 10, "name": "L. Deng",      "bbref_id": "denglu01",
        "pos": "SF", "age": 31, "tier": "Mid", "salary": 18, "contractYear": 2016,
    },
    {
        "id": 11, "name": "C. Parsons",   "bbref_id": "parsoch01",
        "pos": "SF", "age": 27, "tier": "Mid", "salary": 24, "contractYear": 2016,
    },
    {
        "id": 12, "name": "E. Fournier",  "bbref_id": "fournev01",
        "pos": "SG", "age": 28, "tier": "Mid", "salary": 20, "contractYear": 2021,
    },
    {
        "id": 13, "name": "T. Mozgov",    "bbref_id": "mozgoti01",
        "pos": "C",  "age": 30, "tier": "Mid", "salary": 16, "contractYear": 2016,
    },
    {
        "id": 26, "name": "N. Batum",     "bbref_id": "batumni01",
        "pos": "SF", "age": 27, "tier": "Mid", "salary": 24, "contractYear": 2016,
    },
    {
        "id": 27, "name": "R. Anderson",  "bbref_id": "anderry01",
        "pos": "PF", "age": 27, "tier": "Mid", "salary": 20, "contractYear": 2016,
    },
    {
        "id": 28, "name": "B. Biyombo",   "bbref_id": "biyombi01",
        "pos": "C",  "age": 23, "tier": "Mid", "salary": 17, "contractYear": 2016,
    },
    {
        "id": 29, "name": "E. Turner",    "bbref_id": "turneev01",
        "pos": "SG", "age": 27, "tier": "Mid", "salary": 18, "contractYear": 2016,
    },
    {
        "id": 30, "name": "O. Porter Jr.","bbref_id": "porteot01",
        "pos": "SF", "age": 23, "tier": "Mid", "salary": 27, "contractYear": 2017,
    },
    {
        "id": 31, "name": "A. Crabbe",    "bbref_id": "crabbal01",
        "pos": "SG", "age": 24, "tier": "Mid", "salary": 19, "contractYear": 2016,
    },
    # ── Low ──────────────────────────────────────────────────────────────────
    {
        "id": 14, "name": "M. Dellavedova", "bbref_id": "dellama01",
        "pos": "PG", "age": 25, "tier": "Low", "salary": 10, "contractYear": 2016,
    },
    {
        "id": 15, "name": "K. Korver",    "bbref_id": "korveky01",
        "pos": "SG", "age": 33, "tier": "Low", "salary":  6, "contractYear": 2014,
    },
    {
        "id": 16, "name": "P. Beverley",  "bbref_id": "beverpa01",
        "pos": "PG", "age": 29, "tier": "Low", "salary":  7, "contractYear": 2017,
    },
    {
        "id": 17, "name": "M. Belinelli", "bbref_id": "belinma01",
        "pos": "SG", "age": 31, "tier": "Low", "salary":  7, "contractYear": 2017,
    },
    {
        "id": 18, "name": "T. Sefolosha", "bbref_id": "sefolth01",
        "pos": "SF", "age": 30, "tier": "Low", "salary":  6, "contractYear": 2014,
    },
    {
        "id": 32, "name": "M. Carter-Williams", "bbref_id": "cartemi01",
        "pos": "PG", "age": 23, "tier": "Low", "salary": 11, "contractYear": 2015,
    },
    {
        "id": 33, "name": "C. Joseph",    "bbref_id": "josepco01",
        "pos": "PG", "age": 24, "tier": "Low", "salary":  9, "contractYear": 2016,
    },
    {
        "id": 34, "name": "J. Clarkson",  "bbref_id": "clarkjo01",
        "pos": "SG", "age": 24, "tier": "Low", "salary": 13, "contractYear": 2016,
    },
    {
        "id": 35, "name": "R. Hood",      "bbref_id": "hoodro01",
        "pos": "SG", "age": 23, "tier": "Low", "salary": 12, "contractYear": 2016,
    },
    # ── Max (batch 2) ─────────────────────────────────────────────────────────
    # LeBron - Heat 2010 (4yr/$96M, $24M/yr; was max for that cap era)
    {
        "id": 36, "name": "LeBron James",  "bbref_id": "jamesle01",
        "pos": "SF", "age": 25, "tier": "Max", "salary": 17, "contractYear": 2010,
    },
    # Chris Bosh - Heat 2010 (6yr/$110M)
    {
        "id": 37, "name": "C. Bosh",       "bbref_id": "boshch01",
        "pos": "C",  "age": 26, "tier": "Max", "salary": 18, "contractYear": 2010,
    },
    # Kevin Durant - Warriors 2016 (2yr/$54M, max for his service years)
    {
        "id": 38, "name": "K. Durant",     "bbref_id": "duranke01",
        "pos": "SF", "age": 27, "tier": "Max", "salary": 27, "contractYear": 2016,
    },
    # Chris Paul - Rockets 2017 (5yr/$207M supermax)
    {
        "id": 39, "name": "C. Paul",       "bbref_id": "paulch01",
        "pos": "PG", "age": 32, "tier": "Max", "salary": 35, "contractYear": 2017,
    },
    # Carmelo Anthony - Knicks 2014 re-sign (5yr/$124M)
    {
        "id": 40, "name": "C. Anthony",    "bbref_id": "anthoca01",
        "pos": "SF", "age": 30, "tier": "Max", "salary": 25, "contractYear": 2014,
    },
    # Paul George - OKC extension 2018 (4yr/$137M; kicks in 2018-19)
    {
        "id": 41, "name": "P. George",     "bbref_id": "georgpa01",
        "pos": "SF", "age": 28, "tier": "Max", "salary": 34, "contractYear": 2018,
    },
    # Kawhi Leonard - Clippers 2019 (4yr/$142M)
    {
        "id": 42, "name": "K. Leonard",    "bbref_id": "leonaka01",
        "pos": "SF", "age": 28, "tier": "Max", "salary": 36, "contractYear": 2019,
    },
    # Jimmy Butler - Heat 2019 (4yr/$142M)
    {
        "id": 43, "name": "J. Butler",     "bbref_id": "butleji01",
        "pos": "SF", "age": 29, "tier": "Max", "salary": 36, "contractYear": 2019,
    },
    # LaMarcus Aldridge - Spurs 2015 (4yr/$84M)
    {
        "id": 44, "name": "L. Aldridge",   "bbref_id": "aldrila01",
        "pos": "PF", "age": 30, "tier": "Max", "salary": 21, "contractYear": 2015,
    },
    # Kevin Love - Cavs extension 2015 (5yr/$110M)
    {
        "id": 45, "name": "K. Love",       "bbref_id": "loveke01",
        "pos": "PF", "age": 26, "tier": "Max", "salary": 22, "contractYear": 2015,
    },
    # Kyle Lowry - Raptors extension 2017 (3yr/$100M)
    {
        "id": 46, "name": "K. Lowry",      "bbref_id": "lowryky01",
        "pos": "PG", "age": 31, "tier": "Max", "salary": 33, "contractYear": 2017,
    },
    # Giannis Antetokounmpo - Bucks supermax 2020 (5yr/$228M)
    {
        "id": 47, "name": "Giannis",       "bbref_id": "antetgi01",
        "pos": "PF", "age": 25, "tier": "Max", "salary": 39, "contractYear": 2020,
    },
    # Anthony Davis - Lakers 2020 (3yr/$127M)
    {
        "id": 48, "name": "A. Davis",      "bbref_id": "davisan02",
        "pos": "PF", "age": 27, "tier": "Max", "salary": 42, "contractYear": 2020,
    },
    # ── Mid (batch 2) ─────────────────────────────────────────────────────────
    # Marc Gasol - Memphis extension 2015 (5yr/$113M)
    {
        "id": 49, "name": "M. Gasol",      "bbref_id": "gasolma01",
        "pos": "C",  "age": 30, "tier": "Mid", "salary": 23, "contractYear": 2015,
    },
    # DeAndre Jordan - Clippers 2015 (4yr/$88M)
    {
        "id": 50, "name": "D. Jordan",     "bbref_id": "jordade01",
        "pos": "C",  "age": 27, "tier": "Mid", "salary": 22, "contractYear": 2015,
    },
    # Hassan Whiteside - Heat 2016 (4yr/$98M)
    {
        "id": 51, "name": "H. Whiteside",  "bbref_id": "whiteha01",
        "pos": "C",  "age": 27, "tier": "Mid", "salary": 25, "contractYear": 2016,
    },
    # Enes Kanter - OKC 2015 (offer sheet matched; 4yr/$70M)
    {
        "id": 52, "name": "E. Kanter",     "bbref_id": "kanteen01",
        "pos": "C",  "age": 23, "tier": "Mid", "salary": 18, "contractYear": 2015,
    },
    # Khris Middleton - Bucks 2015 (5yr/$70M)
    {
        "id": 53, "name": "K. Middleton",  "bbref_id": "middlkh01",
        "pos": "SF", "age": 24, "tier": "Mid", "salary": 14, "contractYear": 2015,
    },
    # Al Horford - 76ers 2019 (4yr/$109M)
    {
        "id": 54, "name": "A. Horford",    "bbref_id": "horfoal01",
        "pos": "C",  "age": 33, "tier": "Mid", "salary": 27, "contractYear": 2019,
    },
    # Serge Ibaka - Raptors 2017 (3yr/$65M)
    {
        "id": 55, "name": "S. Ibaka",      "bbref_id": "ibakase01",
        "pos": "PF", "age": 27, "tier": "Mid", "salary": 22, "contractYear": 2017,
    },
    # Jeff Teague - Timberwolves 2017 (3yr/$57M)
    {
        "id": 56, "name": "J. Teague",     "bbref_id": "teaguje01",
        "pos": "PG", "age": 29, "tier": "Mid", "salary": 16, "contractYear": 2017,
    },
    # Solomon Hill - Pelicans 2016 (4yr/$52M)
    {
        "id": 57, "name": "S. Hill",       "bbref_id": "hillso01",
        "pos": "SF", "age": 24, "tier": "Mid", "salary": 13, "contractYear": 2016,
    },
    # Greg Monroe - Bucks 2015 (3yr/$50M)
    {
        "id": 58, "name": "G. Monroe",     "bbref_id": "monrogr01",
        "pos": "C",  "age": 25, "tier": "Mid", "salary": 17, "contractYear": 2015,
    },
    # Al Jefferson - Charlotte 2013 (3yr/$41M)
    {
        "id": 59, "name": "A. Jefferson",  "bbref_id": "jeffeal01",
        "pos": "C",  "age": 28, "tier": "Mid", "salary": 14, "contractYear": 2013,
    },
    # Tyreke Evans - Grizzlies 2017 (3yr/$55M)
    {
        "id": 60, "name": "T. Evans",      "bbref_id": "evansty01",
        "pos": "SG", "age": 27, "tier": "Mid", "salary": 16, "contractYear": 2017,
    },
    # Deron Williams - Nets 2012 (5yr/$99M)
    {
        "id": 61, "name": "D. Williams",   "bbref_id": "willide01",
        "pos": "PG", "age": 28, "tier": "Mid", "salary": 20, "contractYear": 2012,
    },
    # Tyson Chandler - Knicks 2011 (4yr/$58M) — won chip with Dallas in walk year
    {
        "id": 62, "name": "T. Chandler",   "bbref_id": "chandty01",
        "pos": "C",  "age": 28, "tier": "Mid", "salary": 15, "contractYear": 2011,
    },
    # Eric Bledsoe - Phoenix extension 2015 (5yr/$70M)
    {
        "id": 63, "name": "E. Bledsoe",    "bbref_id": "bledser01",
        "pos": "PG", "age": 25, "tier": "Mid", "salary": 14, "contractYear": 2015,
    },
    # David Lee - Warriors 2010 (6yr/$80M, $13M/yr)
    {
        "id": 64, "name": "D. Lee",        "bbref_id": "leeda02",
        "pos": "PF", "age": 27, "tier": "Mid", "salary": 13, "contractYear": 2010,
    },
    # ── Low (batch 2) ─────────────────────────────────────────────────────────
    # Pau Gasol - Bulls 2014 (2yr/$14.3M)
    {
        "id": 65, "name": "P. Gasol",      "bbref_id": "gasolpa01",
        "pos": "C",  "age": 34, "tier": "Low", "salary":  7, "contractYear": 2014,
    },
    # Lance Stephenson - Charlotte 2014 (3yr/$27.9M)
    {
        "id": 66, "name": "L. Stephenson", "bbref_id": "stephla01",
        "pos": "SG", "age": 23, "tier": "Low", "salary":  9, "contractYear": 2014,
    },
    # Marcin Gortat - Wizards 2014 (5yr/$60M)
    {
        "id": 67, "name": "M. Gortat",     "bbref_id": "gortama01",
        "pos": "C",  "age": 30, "tier": "Low", "salary": 12, "contractYear": 2014,
    },
    # Jeremy Lin - Charlotte 2014 (3yr/$36M)
    {
        "id": 68, "name": "J. Lin",        "bbref_id": "linje01",
        "pos": "PG", "age": 26, "tier": "Low", "salary": 12, "contractYear": 2014,
    },
    # ── BATCH 3 ──────────────────────────────────────────────────────────────
    # MAX
    # Steph Curry - GSW 2017 (5yr/$201M)
    {
        "id": 69, "name": "S. Curry",      "bbref_id": "curryst01",
        "pos": "PG", "age": 29, "tier": "Max", "salary": 40, "contractYear": 2017,
    },
    # Nikola Jokic - DEN 2019 (5yr/$147M)
    {
        "id": 70, "name": "N. Jokic",      "bbref_id": "jokicni01",
        "pos": "C",  "age": 24, "tier": "Max", "salary": 29, "contractYear": 2019,
    },
    # Joel Embiid - PHI 2022 (4yr/$196M)
    {
        "id": 71, "name": "J. Embiid",     "bbref_id": "embiijo01",
        "pos": "C",  "age": 28, "tier": "Max", "salary": 49, "contractYear": 2022,
    },
    # Luka Doncic - DAL 2022 (5yr/$207M)
    {
        "id": 72, "name": "L. Doncic",     "bbref_id": "doncilu01",
        "pos": "PG", "age": 23, "tier": "Max", "salary": 41, "contractYear": 2022,
    },
    # Ja Morant - MEM 2022 (5yr/$231M)
    {
        "id": 73, "name": "J. Morant",     "bbref_id": "moranja01",
        "pos": "PG", "age": 22, "tier": "Max", "salary": 46, "contractYear": 2022,
    },
    # Jayson Tatum - BOS 2023 (5yr/$195M)
    {
        "id": 74, "name": "J. Tatum",      "bbref_id": "tatumja01",
        "pos": "SF", "age": 25, "tier": "Max", "salary": 39, "contractYear": 2023,
    },
    # Kemba Walker - BOS 2019 (4yr/$141M)
    {
        "id": 75, "name": "K. Walker",     "bbref_id": "walkeke02",
        "pos": "PG", "age": 29, "tier": "Max", "salary": 35, "contractYear": 2019,
    },
    # Kyrie Irving - BKN 2019 (4yr/$136M)
    {
        "id": 76, "name": "K. Irving",     "bbref_id": "irvinky01",
        "pos": "PG", "age": 27, "tier": "Max", "salary": 34, "contractYear": 2019,
    },
    # MID
    # Nikola Vucevic - ORL 2019 (4yr/$100M)
    {
        "id": 77, "name": "N. Vucevic",    "bbref_id": "vucevni01",
        "pos": "C",  "age": 28, "tier": "Mid", "salary": 25, "contractYear": 2019,
    },
    # Victor Oladipo - IND 2018 (4yr/$85M)
    {
        "id": 78, "name": "V. Oladipo",    "bbref_id": "oladivi01",
        "pos": "SG", "age": 26, "tier": "Mid", "salary": 21, "contractYear": 2018,
    },
    # DeMar DeRozan - SAS 2019 (3yr/$82M)
    {
        "id": 79, "name": "D. DeRozan",    "bbref_id": "derozde01",
        "pos": "SG", "age": 29, "tier": "Mid", "salary": 27, "contractYear": 2019,
    },
    # Derrick Rose - CHI 2011 (5yr/$94M)
    {
        "id": 80, "name": "D. Rose",       "bbref_id": "rosede01",
        "pos": "PG", "age": 22, "tier": "Mid", "salary": 19, "contractYear": 2011,
    },
    # Ricky Rubio - MIN 2015 (5yr/$56M)
    {
        "id": 81, "name": "R. Rubio",      "bbref_id": "rubiori01",
        "pos": "PG", "age": 24, "tier": "Mid", "salary": 14, "contractYear": 2015,
    },
    # Reggie Jackson - DET 2015 (5yr/$80M)
    {
        "id": 82, "name": "R. Jackson",    "bbref_id": "jacksre01",
        "pos": "PG", "age": 25, "tier": "Mid", "salary": 16, "contractYear": 2015,
    },
    # Bradley Beal - WAS 2019 (2yr/$52M)
    {
        "id": 83, "name": "B. Beal",       "bbref_id": "bealbr01",
        "pos": "SG", "age": 26, "tier": "Mid", "salary": 26, "contractYear": 2019,
    },
    # Dirk Nowitzki - DAL 2010 (4yr/$60M)
    {
        "id": 84, "name": "D. Nowitzki",   "bbref_id": "nowitdi01",
        "pos": "PF", "age": 32, "tier": "Mid", "salary": 15, "contractYear": 2010,
    },
    # Dwyane Wade - MIA 2012 (3yr/$48M)
    {
        "id": 85, "name": "D. Wade",       "bbref_id": "wadedw01",
        "pos": "SG", "age": 30, "tier": "Mid", "salary": 16, "contractYear": 2012,
    },
    # Myles Turner - IND 2020 (2yr/$36M)
    {
        "id": 86, "name": "M. Turner",     "bbref_id": "turnemy01",
        "pos": "C",  "age": 24, "tier": "Mid", "salary": 18, "contractYear": 2020,
    },
    # LOW
    # Zach Randolph - SAC 2016 (2yr/$24M)
    {
        "id": 87, "name": "Z. Randolph",   "bbref_id": "randoza01",
        "pos": "PF", "age": 34, "tier": "Low", "salary": 11, "contractYear": 2016,
    },
    # Wayne Ellington - MIA 2017 (2yr/$12M)
    {
        "id": 88, "name": "W. Ellington",  "bbref_id": "ellinwa01",
        "pos": "SG", "age": 29, "tier": "Low", "salary":  7, "contractYear": 2017,
    },
    # Tony Allen - MEM 2014 (2yr/$10M)
    {
        "id": 89, "name": "T. Allen",      "bbref_id": "allento01",
        "pos": "SG", "age": 32, "tier": "Low", "salary":  5, "contractYear": 2014,
    },
    # Tiago Splitter - SAS 2013 (4yr/$36M)
    {
        "id": 90, "name": "T. Splitter",   "bbref_id": "splitti01",
        "pos": "C",  "age": 28, "tier": "Low", "salary":  9, "contractYear": 2013,
    },
    # Wilson Chandler - DEN 2014 (4yr/$46M)
    {
        "id": 91, "name": "W. Chandler",   "bbref_id": "chandwi01",
        "pos": "SF", "age": 27, "tier": "Low", "salary": 12, "contractYear": 2014,
    },
    # ── BATCH 4 ──────────────────────────────────────────────────────────────
    # MAX
    # Bam Adebayo - MIA 2020 (5yr/$163M)
    {
        "id": 92,  "name": "B. Adebayo",    "bbref_id": "adebaba01",
        "pos": "C",  "age": 23, "tier": "Max", "salary": 33, "contractYear": 2020,
    },
    # Rudy Gobert - UTA 2020 (5yr/$205M)
    {
        "id": 93,  "name": "R. Gobert",     "bbref_id": "goberru01",
        "pos": "C",  "age": 28, "tier": "Max", "salary": 41, "contractYear": 2020,
    },
    # D'Angelo Russell - MIN 2019 (4yr/$117M)
    {
        "id": 94,  "name": "D. Russell",    "bbref_id": "russeda01",
        "pos": "PG", "age": 23, "tier": "Max", "salary": 29, "contractYear": 2019,
    },
    # De'Aaron Fox - SAC 2021 (5yr/$163M)
    {
        "id": 95,  "name": "De'A. Fox",     "bbref_id": "foxde01",
        "pos": "PG", "age": 23, "tier": "Max", "salary": 33, "contractYear": 2021,
    },
    # Brandon Ingram - NOP 2020 (5yr/$158M)
    {
        "id": 96,  "name": "B. Ingram",     "bbref_id": "ingrabr01",
        "pos": "SF", "age": 23, "tier": "Max", "salary": 32, "contractYear": 2020,
    },
    # Shai Gilgeous-Alexander - OKC 2021 (5yr/$172M)
    {
        "id": 97,  "name": "SGA",           "bbref_id": "gilgesh01",
        "pos": "PG", "age": 23, "tier": "Max", "salary": 34, "contractYear": 2021,
    },
    # Darius Garland - CLE 2022 (5yr/$193M)
    {
        "id": 98,  "name": "D. Garland",    "bbref_id": "garlada01",
        "pos": "PG", "age": 22, "tier": "Max", "salary": 39, "contractYear": 2022,
    },
    # MID
    # Clint Capela - HOU 2018 (5yr/$90M)
    {
        "id": 99,  "name": "C. Capela",     "bbref_id": "capelca01",
        "pos": "C",  "age": 24, "tier": "Mid", "salary": 18, "contractYear": 2018,
    },
    # Marcus Smart - BOS 2019 (4yr/$52M)
    {
        "id": 100, "name": "M. Smart",      "bbref_id": "smartma01",
        "pos": "PG", "age": 25, "tier": "Mid", "salary": 13, "contractYear": 2019,
    },
    # CJ McCollum - POR 2016 (5yr/$100M)
    {
        "id": 101, "name": "CJ McCollum",   "bbref_id": "mccolcj01",
        "pos": "SG", "age": 24, "tier": "Mid", "salary": 20, "contractYear": 2016,
    },
    # Tim Hardaway Jr - DAL 2019 (4yr/$74M)
    {
        "id": 102, "name": "T. Hardaway Jr","bbref_id": "hardati02",
        "pos": "SG", "age": 27, "tier": "Mid", "salary": 19, "contractYear": 2019,
    },
    # OG Anunoby - TOR 2022 (4yr/$72M)
    {
        "id": 103, "name": "OG Anunoby",    "bbref_id": "anunoog01",
        "pos": "SF", "age": 25, "tier": "Mid", "salary": 18, "contractYear": 2022,
    },
    # Jarrett Allen - CLE 2022 (5yr/$100M)
    {
        "id": 104, "name": "J. Allen",      "bbref_id": "allenja01",
        "pos": "C",  "age": 24, "tier": "Mid", "salary": 20, "contractYear": 2022,
    },
    # Tristan Thompson - CLE 2015 (5yr/$82M)
    {
        "id": 105, "name": "T. Thompson",   "bbref_id": "thomptr01",
        "pos": "C",  "age": 24, "tier": "Mid", "salary": 16, "contractYear": 2015,
    },
    # Draymond Green - GSW 2015 (5yr/$82M)
    {
        "id": 106, "name": "D. Green",      "bbref_id": "greendr01",
        "pos": "PF", "age": 25, "tier": "Mid", "salary": 16, "contractYear": 2015,
    },
    # Dion Waiters - MIA 2017 (4yr/$52M)
    {
        "id": 107, "name": "D. Waiters",    "bbref_id": "waitedi01",
        "pos": "SG", "age": 25, "tier": "Mid", "salary": 13, "contractYear": 2017,
    },
    # LOW
    # Avery Bradley - DET 2014 (4yr/$32M)
    {
        "id": 108, "name": "A. Bradley",    "bbref_id": "bradlav01",
        "pos": "SG", "age": 23, "tier": "Low", "salary":  8, "contractYear": 2014,
    },
    # Courtney Lee - CHA 2016 (4yr/$50M)
    {
        "id": 109, "name": "C. Lee",        "bbref_id": "leeco01",
        "pos": "SG", "age": 30, "tier": "Low", "salary": 13, "contractYear": 2016,
    },
    # Patrick Patterson - TOR 2016 (3yr/$17M)
    {
        "id": 110, "name": "P. Patterson",  "bbref_id": "pattepa01",
        "pos": "PF", "age": 27, "tier": "Low", "salary":  6, "contractYear": 2016,
    },
    # Derrick Favors - UTA 2016 (2yr/$16M)
    {
        "id": 111, "name": "D. Favors",     "bbref_id": "favorde01",
        "pos": "C",  "age": 24, "tier": "Low", "salary":  8, "contractYear": 2016,
    },
    # Darren Collison - IND 2017 (3yr/$21M)
    {
        "id": 112, "name": "D. Collison",   "bbref_id": "collida01",
        "pos": "PG", "age": 29, "tier": "Low", "salary":  7, "contractYear": 2017,
    },
    # ── BATCH 5 ──────────────────────────────────────────────────────────────
    # MAX
    # Pascal Siakam - TOR 2020 (4yr/$130M)
    {
        "id": 113, "name": "P. Siakam",     "bbref_id": "siakapa01",
        "pos": "PF", "age": 26, "tier": "Max", "salary": 33, "contractYear": 2020,
    },
    # Zion Williamson - NOP 2022 (5yr/$231M)
    {
        "id": 114, "name": "Z. Williamson", "bbref_id": "willizi01",
        "pos": "PF", "age": 22, "tier": "Max", "salary": 46, "contractYear": 2022,
    },
    # Julius Randle - NYK 2021 (4yr/$117M)
    {
        "id": 115, "name": "J. Randle",     "bbref_id": "randlju01",
        "pos": "PF", "age": 26, "tier": "Max", "salary": 29, "contractYear": 2021,
    },
    # Donovan Mitchell - UTA 2021 (5yr/$163M)
    {
        "id": 116, "name": "D. Mitchell",   "bbref_id": "mitchdo01",
        "pos": "SG", "age": 25, "tier": "Max", "salary": 33, "contractYear": 2021,
    },
    # Dejounte Murray - ATL 2022 (4yr/$120M)
    {
        "id": 117, "name": "D. Murray",     "bbref_id": "murrade01",
        "pos": "PG", "age": 26, "tier": "Max", "salary": 30, "contractYear": 2022,
    },
    # MID
    # Anfernee Simons - POR 2022 (4yr/$100M)
    {
        "id": 118, "name": "A. Simons",     "bbref_id": "simonan01",
        "pos": "SG", "age": 23, "tier": "Mid", "salary": 25, "contractYear": 2022,
    },
    # Derrick White - BOS 2022 (4yr/$80M)
    {
        "id": 119, "name": "D. White",      "bbref_id": "whitede01",
        "pos": "PG", "age": 28, "tier": "Mid", "salary": 20, "contractYear": 2022,
    },
    # Kyle Kuzma - WAS 2022 (4yr/$102M)
    {
        "id": 120, "name": "K. Kuzma",      "bbref_id": "kuzmaky01",
        "pos": "SF", "age": 27, "tier": "Mid", "salary": 26, "contractYear": 2022,
    },
    # Aaron Gordon - ORL 2017 (4yr/$80M)
    {
        "id": 121, "name": "A. Gordon",     "bbref_id": "gordoaa01",
        "pos": "PF", "age": 21, "tier": "Mid", "salary": 20, "contractYear": 2017,
    },
    # Danny Green - TOR 2018 (2yr/$30M)
    {
        "id": 122, "name": "D. Green (TOR)","bbref_id": "greenda02",
        "pos": "SG", "age": 31, "tier": "Mid", "salary": 15, "contractYear": 2018,
    },
    # Josh Hart - NYK 2022 (4yr/$81M)
    {
        "id": 123, "name": "J. Hart",       "bbref_id": "hartjo01",
        "pos": "SF", "age": 27, "tier": "Mid", "salary": 20, "contractYear": 2022,
    },
    # Thaddeus Young - IND 2016 (3yr/$41M)
    {
        "id": 124, "name": "T. Young",      "bbref_id": "youngth01",
        "pos": "PF", "age": 28, "tier": "Mid", "salary": 14, "contractYear": 2016,
    },
    # Lonzo Ball - CHI 2021 (4yr/$80M)
    {
        "id": 125, "name": "L. Ball",       "bbref_id": "balllo01",
        "pos": "PG", "age": 24, "tier": "Mid", "salary": 20, "contractYear": 2021,
    },
    # Dorian Finney-Smith - DAL 2021 (4yr/$52M)
    {
        "id": 126, "name": "D. Finney-Smith","bbref_id": "finnedo01",
        "pos": "SF", "age": 27, "tier": "Mid", "salary": 13, "contractYear": 2021,
    },
    # Naz Reid - MIN 2023 (3yr/$42M)
    {
        "id": 127, "name": "N. Reid",       "bbref_id": "reidna01",
        "pos": "C",  "age": 24, "tier": "Mid", "salary": 14, "contractYear": 2023,
    },
    # LOW
    # Lou Williams - LAC 2018 (3yr/$24M)
    {
        "id": 128, "name": "L. Williams",   "bbref_id": "willilo01",
        "pos": "SG", "age": 31, "tier": "Low", "salary":  8, "contractYear": 2018,
    },
    # Marcus Morris Sr - PHX/WAS 2018 (2yr/$20M)
    {
        "id": 129, "name": "M. Morris Sr",  "bbref_id": "morrima02",
        "pos": "PF", "age": 28, "tier": "Low", "salary": 10, "contractYear": 2018,
    },
    # Al-Farouq Aminu - POR 2016 (4yr/$36M)
    {
        "id": 130, "name": "A. Aminu",      "bbref_id": "aminual01",
        "pos": "SF", "age": 25, "tier": "Low", "salary":  9, "contractYear": 2016,
    },
    # Tony Snell - MIL 2016 (4yr/$33M)
    {
        "id": 131, "name": "T. Snell",      "bbref_id": "snellto01",
        "pos": "SG", "age": 24, "tier": "Low", "salary":  8, "contractYear": 2016,
    },
    # Georges Niang - PHI 2022 (3yr/$34M)
    {
        "id": 132, "name": "G. Niang",      "bbref_id": "niangge01",
        "pos": "SF", "age": 29, "tier": "Low", "salary": 11, "contractYear": 2022,
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
    delay = DELAY + random.uniform(0, DELAY_JITTER)
    time.sleep(delay)
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

def _js_num(v) -> str:
    """Serialize a Python float/int to a JS-safe number (never 'nan' or 'inf')."""
    import math
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return "0"
    return str(v)


def fmt_stat_block(s: dict) -> str:
    return (
        f"{{ PER: {_js_num(s['PER'])}, WS: {_js_num(s['WS'])}, VORP: {_js_num(s['VORP'])}, "
        f"PTS: {_js_num(s['PTS'])}, AST: {_js_num(s['AST'])}, TRB: {_js_num(s['TRB'])}, "
        f"TS: {_js_num(s['TS'])}, TOV: {_js_num(s['TOV'])} }}"
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


def load_existing_ids() -> set:
    """Return set of player IDs already in players.csv."""
    if not CSV_PATH.exists():
        return set()
    try:
        df = pd.read_csv(CSV_PATH)
        return set(df["id"].astype(int).tolist())
    except Exception:
        return set()


def save_csv(rows: list):
    """Write/append current rows to players.csv."""
    pd.DataFrame(rows).to_csv(CSV_PATH, index=False)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    existing_ids = load_existing_ids() if SKIP_EXISTING else set()
    if existing_ids and SKIP_EXISTING:
        print(f"ℹ  Resuming — {len(existing_ids)} players already in {CSV_PATH}  (use --force to re-scrape all)")

    # Load existing rows so we can append without losing them
    if CSV_PATH.exists() and SKIP_EXISTING and existing_ids:
        csv_rows = pd.read_csv(CSV_PATH).to_dict("records")
    else:
        csv_rows = []

    js_entries_by_id = {}  # id → js string, built from all players including skipped
    errors = []

    for p in PLAYERS:
        sy = p["contractYear"]
        t_label = f"{sy - 1}-{str(sy)[2:]}"   # e.g. "2016-17"
        print(f"\n[{p['id']}/{len(PLAYERS)}]  {p['name']}  (T = {t_label}, sign_year = {sy})")

        if SKIP_EXISTING and p["id"] in existing_ids:
            print("    ↷ already scraped, skipping")
            # We still need this player's JS for the App.jsx patch.
            # Reconstruct from CSV row.
            existing_row = next((r for r in csv_rows if int(r["id"]) == p["id"]), None)
            if existing_row:
                def _s(prefix):
                    return {k: existing_row[f"{prefix}_{k}"] for k in ADV_COLS.values() | PERG_COLS.values()}
                try:
                    t1 = {k: existing_row[f"T1_{k}"] for k in list(ADV_COLS.values()) + list(PERG_COLS.values())}
                    t  = {k: existing_row[f"T_{k}"]  for k in list(ADV_COLS.values()) + list(PERG_COLS.values())}
                    t2 = {k: existing_row[f"T2_{k}"] for k in list(ADV_COLS.values()) + list(PERG_COLS.values())}
                    js_entries_by_id[p["id"]] = fmt_player_js(p, t1, t, t2)
                except Exception:
                    pass
            continue

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

            js_entries_by_id[p["id"]] = fmt_player_js(p, t1, t, t2)

            # Build flat CSV row
            row = {k: v for k, v in p.items()}
            for period, stats in [("T1", t1), ("T", t), ("T2", t2)]:
                for sk, sv in stats.items():
                    row[f"{period}_{sk}"] = sv

            # Remove any existing row for this player, then append fresh
            csv_rows = [r for r in csv_rows if int(r["id"]) != p["id"]]
            csv_rows.append(row)

            # Save incrementally after each successful scrape
            save_csv(csv_rows)
            print(f"    ✓ saved → {CSV_PATH}")

        except Exception as exc:
            msg = f"{p['name']} (id={p['id']}): {exc}"
            errors.append(msg)
            print(f"    ERROR: {exc}")

    # ── Patch src/App.jsx (preserve original player order) ───────────────────
    js_entries = [js_entries_by_id[p["id"]] for p in PLAYERS if p["id"] in js_entries_by_id]
    if js_entries:
        new_block = "const PLAYERS = [\n" + ",\n".join(js_entries) + "\n];"
        jsx_path  = Path("src/App.jsx")

        if jsx_path.exists():
            original = jsx_path.read_text()
            patched = re.sub(
                r"const PLAYERS\s*=\s*\[[\s\S]*?\];",
                new_block,
                original,
                count=1,
            )
            if patched != original:
                jsx_path.write_text(patched)
                print(f"\n✓  Patched src/App.jsx  ({len(js_entries)} players)")
            else:
                print("\n⚠   PLAYERS pattern not matched in App.jsx — printing new array below:")
                print(new_block)
        else:
            print("\n⚠   src/App.jsx not found — printing new array below:")
            print(new_block)

    # ── Error log ─────────────────────────────────────────────────────────────
    if errors:
        print(f"\n⚠   {len(errors)} error(s) during scrape:")
        for e in errors:
            print(f"    {e}")
        ERROR_LOG.write_text("\n".join(errors) + "\n")
        print(f"    Errors written to {ERROR_LOG}")
    else:
        scraped = len(PLAYERS) - len([p for p in PLAYERS if SKIP_EXISTING and p["id"] in existing_ids])
        if scraped > 0:
            print(f"\n✓  All {scraped} new players scraped successfully.")
        else:
            print(f"\n✓  Nothing to scrape — all {len(PLAYERS)} players already in CSV.")


if __name__ == "__main__":
    main()
