#!/usr/bin/env python3
"""
setup_game.py — Initialize a new PBM Football Manager game.

This script:
1. Loads the 96 club definitions from data/teams.json
2. Generates 20 players per club (1920 total)
3. Auto-selects starting lineups for all teams
4. Generates the full season fixture list
5. Saves the game state to data/game_state.json
6. Creates the orders/ directory with an example order

Run this ONCE to start a new game.
"""
import json
import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from models.player import Player
from models.team import Team
from models.league import League
from generators.player_generator import PlayerGenerator
from utils import save_game_state, auto_select_lineup


def main():
    print("=" * 60)
    print("  PBM FOOTBALL MANAGER — GAME SETUP")
    print("=" * 60)

    # Load club definitions
    teams_path = os.path.join(config.DATA_DIR, "teams.json")
    with open(teams_path, "r") as f:
        teams_data = json.load(f)

    # Create teams and generate squads
    generator = PlayerGenerator()
    all_players = {}
    all_teams = {}
    teams_by_division = {}

    for div_num_str, div_data in teams_data["divisions"].items():
        div_num = int(div_num_str)
        div_name = div_data["name"]
        teams_by_division[div_num] = []

        print(f"\n--- {div_name} (Division {div_num}) ---")

        for team_def in div_data["teams"]:
            # Create team
            team = Team(
                team_id=team_def["id"],
                name=team_def["name"],
                short=team_def["short"],
                division=div_num,
            )

            # Generate squad
            tier = team_def.get("tier", div_num)
            squad = generator.generate_squad(team.team_id, tier)

            for player in squad:
                all_players[player.player_id] = player
                team.squad.append(player.player_id)

            # Auto-select starting lineup
            auto_select_lineup(team, all_players)

            all_teams[team.team_id] = team
            teams_by_division[div_num].append(team.team_id)

            print(f"  {team.name:30s} — {len(squad)} players generated "
                  f"(avg OVR: {sum(p.overall for p in squad) / len(squad):.0f})")

    # Generate fixtures
    print(f"\nGenerating fixtures...")
    league = League()
    league.generate_fixtures(teams_by_division)

    for div_num, rounds in league.fixtures.items():
        print(f"  Division {div_num}: {len(rounds)} rounds, "
              f"{sum(len(r) for r in rounds)} matches total")

    # Create orders directory
    os.makedirs(config.ORDERS_DIR, exist_ok=True)

    # Create example order
    example_team = list(all_teams.values())[0]
    example_order = {
        "team_id": example_team.team_id,
        "formation": "4-4-2",
        "lineup": example_team.lineup[:config.LINEUP_SIZE],
        "subs": example_team.subs[:config.SUBS_SIZE],
        "transfer_list": [],
        "bids": [],
    }
    example_path = os.path.join(config.ORDERS_DIR, "example_order.json")
    with open(example_path, "w") as f:
        json.dump(example_order, f, indent=2)
    print(f"\nExample order written to {example_path}")

    # Create output directories
    for subdir in ["match_reports", "transfer_lists", "league_tables", "team_sheets"]:
        os.makedirs(os.path.join(config.OUTPUT_DIR, subdir), exist_ok=True)

    # Save game state
    save_game_state(all_players, all_teams, league)

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"  SETUP COMPLETE")
    print(f"{'=' * 60}")
    print(f"  Teams:    {len(all_teams)}")
    print(f"  Players:  {len(all_players)}")
    print(f"  Divisions: {config.DIVISIONS} x {config.TEAMS_PER_DIVISION} teams")
    print(f"  Rounds per season: {len(league.fixtures.get(1, []))}")
    print(f"\n  Game state saved to: data/game_state.json")
    print(f"  Next step: Assign managers, then run process_turn.py")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
