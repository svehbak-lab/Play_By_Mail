# PBM Football Manager

A Play-By-Mail football management game inspired by the classic PBM games of the 1980s and 1990s. Instead of sending orders by post, managers receive PDF reports and submit their decisions via simple text/JSON files.

## How It Works

1. **You (the admin)** run the game engine each "turn" (typically once per week)
2. **Players** receive a PDF with their match report, league table, squad info, and transfer list
3. **Players** submit their orders (formation, lineup, transfers) before the next deadline
4. **The engine** processes all orders, simulates matches, resolves transfers, and generates new PDFs

## League Structure

- **4 divisions** with 24 teams each (96 teams total)
- Based on the top 96 English football clubs
- Promotion/relegation: Top 3 go up, bottom 3 go down
- Each team has a squad of up to 25 players (starts with 20)
- Player names drawn from real players circa 2000

## Match Engine

The match engine considers:
- **Formation** (4-4-2, 4-3-3, 3-5-2, etc.)
- **Player stats** (attack, midfield, defense, goalkeeping)
- **Tactical matchups** (how formations counter each other)
- **Home advantage** (+8% boost)
- **Randomness** (controlled chaos — upsets happen!)

## Transfer System

- Managers can list players for sale with a minimum price
- All listed players appear on the **Transfer List PDF**
- Each player has a unique ID for bidding
- Managers submit bids (player_id + amount)
- Highest bid wins — but you don't know until the next PDF arrives
- Won players are immediately available for selection

## Project Structure

```
pbm-football/
├── README.md
├── requirements.txt
├── config.py                  # Game configuration
├── setup_game.py              # Initialize a new game (run once)
├── process_turn.py            # Process a turn (run each week)
│
├── models/
│   ├── __init__.py
│   ├── player.py              # Player model with stats
│   ├── team.py                # Team/club model
│   ├── league.py              # League & division logic
│   └── match.py               # Match result model
│
├── engines/
│   ├── __init__.py
│   ├── match_engine.py        # Match simulation engine
│   └── transfer_engine.py     # Transfer processing
│
├── generators/
│   ├── __init__.py
│   ├── player_generator.py    # Generate players with stats
│   ├── pdf_match_report.py    # Generate match report PDFs
│   ├── pdf_transfer_list.py   # Generate transfer list PDFs
│   ├── pdf_league_table.py    # Generate league table PDFs
│   └── pdf_team_sheet.py      # Generate team sheet PDFs
│
├── utils/
│   ├── __init__.py
│   └── helpers.py             # Shared utilities
│
├── data/
│   ├── teams.json             # Club definitions
│   ├── player_names.json      # Name pools for generation
│   └── game_state.json        # Persistent game state (auto-generated)
│
├── orders/                    # Managers place order files here
│   └── example_order.json     # Example order template
│
└── output/                    # Generated PDFs go here
    ├── match_reports/
    ├── transfer_lists/
    ├── league_tables/
    └── team_sheets/
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize a new game
python setup_game.py

# Process a turn (after collecting orders)
python process_turn.py

# PDFs will appear in output/
```

## Order Format

Managers submit a JSON file named `{team_id}.json` in the `orders/` folder:

```json
{
  "team_id": "arsenal",
  "formation": "4-4-2",
  "lineup": ["P001", "P002", "P003", "P004", "P005",
             "P006", "P007", "P008", "P009", "P010", "P011"],
  "subs": ["P012", "P013", "P014", "P015", "P016"],
  "transfer_list": [
    {"player_id": "P018", "min_price": 500000}
  ],
  "bids": [
    {"player_id": "P_EXT_042", "amount": 1200000}
  ]
}
```

## Manager Slots

- Each team can be claimed by a manager
- If a manager stops paying/playing, the team becomes available
- New managers inherit the team as-is (no reset)
- Unclaimed teams are run by the AI with default tactics

## License

MIT — do whatever you want with it.
