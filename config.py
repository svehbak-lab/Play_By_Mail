"""
PBM Football Manager — Game Configuration
"""
import os

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
ORDERS_DIR = os.path.join(BASE_DIR, "orders")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# League structure
DIVISIONS = 4
TEAMS_PER_DIVISION = 24
TOTAL_TEAMS = DIVISIONS * TEAMS_PER_DIVISION  # 96

# Promotion / Relegation
PROMOTION_SPOTS = 3
RELEGATION_SPOTS = 3

# Squad
MAX_SQUAD_SIZE = 25
STARTING_SQUAD_SIZE = 20
LINEUP_SIZE = 11
SUBS_SIZE = 5

# Player stats range (1-99)
STAT_MIN = 1
STAT_MAX = 99

# Player positions
POSITIONS = ["GK", "DEF", "MID", "FWD"]

# Valid formations (outfield only — GK is always 1)
VALID_FORMATIONS = [
    "4-4-2", "4-3-3", "4-5-1", "3-5-2", "3-4-3",
    "5-3-2", "5-4-1", "4-2-3-1", "4-1-4-1", "3-4-1-2",
]

# Match engine
HOME_ADVANTAGE = 0.08   # 8% boost to home team's effective rating
RANDOMNESS_FACTOR = 0.20  # How much randomness affects the result

# Formation effectiveness matrix — how formations interact
# Positive = advantage for the first formation against the second
FORMATION_MATCHUPS = {
    ("4-4-2", "4-3-3"):  0.02,
    ("4-4-2", "3-5-2"): -0.03,
    ("4-3-3", "3-5-2"):  0.04,
    ("4-3-3", "5-3-2"): -0.02,
    ("3-5-2", "4-4-2"):  0.03,
    ("3-5-2", "5-4-1"): -0.01,
    ("4-5-1", "4-3-3"):  0.03,
    ("4-5-1", "4-4-2"): -0.01,
    ("5-3-2", "4-4-2"):  0.01,
    ("5-3-2", "3-5-2"):  0.02,
    ("5-4-1", "4-3-3"):  0.03,
    ("5-4-1", "3-4-3"): -0.02,
    ("3-4-3", "5-3-2"):  0.04,
    ("3-4-3", "4-5-1"):  0.02,
    ("4-2-3-1", "4-4-2"): 0.02,
    ("4-2-3-1", "3-4-3"): -0.02,
    ("4-1-4-1", "4-3-3"): 0.01,
    ("4-1-4-1", "3-5-2"): -0.01,
    ("3-4-1-2", "4-4-2"): 0.01,
    ("3-4-1-2", "5-4-1"): -0.02,
}

# Transfer
MIN_TRANSFER_FEE = 50_000
STARTING_BUDGET = 10_000_000  # £10M per team

# Season
MATCHES_PER_SEASON = 46  # Each team plays every other team twice (23 opponents * 2)

# PDF styling
PDF_TITLE_FONT_SIZE = 18
PDF_HEADING_FONT_SIZE = 14
PDF_BODY_FONT_SIZE = 10
PDF_SMALL_FONT_SIZE = 8
