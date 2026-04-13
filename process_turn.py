#!/usr/bin/env python3
"""
process_turn.py — Process one turn of the PBM Football Manager game.

This script:
1. Loads the current game state
2. Reads all manager orders from orders/
3. Applies formation/lineup changes
4. Processes transfer bids (highest bid wins)
5. Simulates all matches for the current round
6. Updates standings, player stats, suspensions, injuries
7. Generates PDF reports for every team
8. Advances to the next round
9. Saves the updated game state
10. Handles end-of-season promotion/relegation

Run this once per turn (typically weekly).
"""
import json
import os
import sys
import glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from models.player import Player
from models.team import Team
from models.league import League
from models.match import MatchResult
from engines.match_engine import MatchEngine
from engines.transfer_engine import TransferEngine
from generators.pdf_match_report import MatchReportGenerator
from utils import save_game_state, load_game_state, load_orders, auto_select_lineup


def process_orders(teams, players):
    """Read and apply all manager orders."""
    print("\n--- PROCESSING ORDERS ---")
    all_bids = {}

    for team_id, team in teams.items():
        order = load_orders(team_id)

        if not order:
            # No order submitted — use AI auto-select
            auto_select_lineup(team, players)
            print(f"  {team.name:30s} — No orders (AI auto-select)")
            continue

        # Apply formation
        formation = order.get("formation", team.formation)
        if formation in config.VALID_FORMATIONS:
            team.formation = formation

        # Apply lineup
        lineup = order.get("lineup", [])
        if lineup:
            # Validate: all players must be in squad and available
            valid_lineup = []
            for pid in lineup:
                if pid in team.squad:
                    p = players.get(pid)
                    if p and p.is_available:
                        valid_lineup.append(pid)
            if len(valid_lineup) >= 7:  # Minimum 7 players to field a team
                team.lineup = valid_lineup[:config.LINEUP_SIZE]
            else:
                auto_select_lineup(team, players)
                print(f"  {team.name:30s} — Invalid lineup, using AI auto-select")
                continue

        # Apply subs
        subs = order.get("subs", [])
        valid_subs = [pid for pid in subs
                      if pid in team.squad and pid not in team.lineup
                      and players.get(pid, None) and players[pid].is_available]
        team.subs = valid_subs[:config.SUBS_SIZE]

        # Collect transfer listings
        for listing in order.get("transfer_list", []):
            pid = listing.get("player_id")
            min_price = listing.get("min_price", config.MIN_TRANSFER_FEE)
            if pid in team.squad and min_price >= config.MIN_TRANSFER_FEE:
                # Don't list players in the starting lineup
                if pid not in team.lineup:
                    team.transfer_listed.append({
                        "player_id": pid,
                        "min_price": min_price,
                    })

        # Collect bids
        bids = order.get("bids", [])
        if bids:
            all_bids[team_id] = bids

        print(f"  {team.name:30s} — Orders applied "
              f"(formation: {team.formation}, "
              f"{len(team.lineup)} starters, "
              f"{len(team.transfer_listed)} listed, "
              f"{len(bids)} bids)")

    return all_bids


def process_transfers(teams, players, all_bids):
    """Process all transfer bids and return completed transfers."""
    print("\n--- PROCESSING TRANSFERS ---")
    engine = TransferEngine(players, teams)

    # Show transfer list
    listings = engine.collect_transfer_list()
    print(f"  Players on transfer list: {len(listings)}")

    # Process bids
    completed = engine.process_bids(all_bids)
    for t in completed:
        print(f"  TRANSFER: {t['player_name']} ({t['position']}) — "
              f"{t['from_team_name']} -> {t['to_team_name']} "
              f"for £{t['amount']:,.0f}")

    if not completed:
        print("  No transfers completed this turn.")

    return completed, listings


def simulate_matches(teams, players, league):
    """Simulate all matches for the current round."""
    print(f"\n--- SIMULATING MATCHES (Round {league.current_round + 1}) ---")
    engine = MatchEngine(players)
    all_results = []

    for div in range(1, config.DIVISIONS + 1):
        fixtures = league.get_round_fixtures(div, league.current_round)
        div_name = {1: "Premier", 2: "Div One", 3: "Div Two", 4: "Div Three"}.get(div, f"Div {div}")

        if not fixtures:
            print(f"  {div_name}: No fixtures for this round")
            continue

        print(f"\n  {div_name}:")
        for fixture in fixtures:
            home_team = teams.get(fixture["home"])
            away_team = teams.get(fixture["away"])

            if not home_team or not away_team:
                continue

            # Ensure both teams have a lineup
            if len(home_team.lineup) < 7:
                auto_select_lineup(home_team, players)
            if len(away_team.lineup) < 7:
                auto_select_lineup(away_team, players)

            result = engine.simulate_match(home_team, away_team)

            # Update team records
            home_team.record_result(result.home_goals, result.away_goals)
            away_team.record_result(result.away_goals, result.home_goals)

            # Update player stats from events
            _update_player_stats(result, players)

            all_results.append(result)

            print(f"    {home_team.name:25s} {result.home_goals} - {result.away_goals} "
                  f"{away_team.name}")

    return all_results


def _update_player_stats(result, players):
    """Update player appearances, goals, assists, cards from match events."""
    # Record appearances for all players in both lineups
    for team_id in [result.home_id, result.away_id]:
        # We don't have direct access to the team here, but events tell us who played
        pass

    for event in result.events:
        player = players.get(event.player_id)
        if not player:
            continue

        if event.event_type == "goal":
            player.goals += 1
            if event.assist_player_id:
                assister = players.get(event.assist_player_id)
                if assister:
                    assister.assists += 1

        elif event.event_type == "yellow":
            player.yellow_cards += 1
            # 5 yellows = 1 match ban
            if player.yellow_cards % 5 == 0:
                player.suspended = 1

        elif event.event_type == "red":
            player.red_cards += 1
            player.suspended = 3  # 3-match ban

        elif event.event_type == "injury":
            import random
            player.injured = random.randint(1, 4)  # 1-4 turns out


def decrement_suspensions_and_injuries(players):
    """Reduce suspension and injury counters by 1 each turn."""
    for player in players.values():
        if player.suspended > 0:
            player.suspended -= 1
        if player.injured > 0:
            player.injured -= 1


def generate_pdfs(teams, players, league, all_results, completed_transfers, transfer_listings):
    """Generate PDF reports for every team."""
    print("\n--- GENERATING PDF REPORTS ---")
    report_gen = MatchReportGenerator(players, teams)
    output_dir = os.path.join(config.OUTPUT_DIR, "match_reports")
    os.makedirs(output_dir, exist_ok=True)

    count = 0
    for team_id, team in teams.items():
        # Find this team's match result
        team_result = None
        for r in all_results:
            if r.home_id == team_id or r.away_id == team_id:
                team_result = r
                break

        if not team_result:
            continue

        # Get standings for this team's division
        standings = league.get_standings(teams, team.division)

        # Division results only
        div_results = [r for r in all_results
                       if teams.get(r.home_id, Team("", "", "", 0)).division == team.division]

        filepath = report_gen.generate_team_report(
            team=team,
            match_result=team_result,
            standings=standings,
            round_num=league.current_round + 1,
            season=league.season,
            output_dir=output_dir,
            all_results=div_results,
            transfer_list=transfer_listings,
            completed_transfers=completed_transfers,
        )
        count += 1

    print(f"  Generated {count} PDF reports in {output_dir}")


def cleanup_orders():
    """Remove processed order files."""
    order_files = glob.glob(os.path.join(config.ORDERS_DIR, "*.json"))
    for f in order_files:
        if os.path.basename(f) != "example_order.json":
            os.remove(f)
    print(f"  Cleaned up {len(order_files)} order files")


def check_end_of_season(teams, league):
    """Check if the season is over and process promotion/relegation."""
    total_rounds = len(league.fixtures.get(1, []))
    if league.current_round >= total_rounds:
        print("\n" + "=" * 60)
        print("  END OF SEASON!")
        print("=" * 60)

        # Print final standings
        for div in range(1, config.DIVISIONS + 1):
            standings = league.get_standings(teams, div)
            div_name = {1: "Premier", 2: "Div One", 3: "Div Two", 4: "Div Three"}.get(div, "")
            print(f"\n  {div_name} Final Standings:")
            for i, t in enumerate(standings, 1):
                marker = ""
                if div > 1 and i <= config.PROMOTION_SPOTS:
                    marker = " [PROMOTED]"
                if div < config.DIVISIONS and i > len(standings) - config.RELEGATION_SPOTS:
                    marker = " [RELEGATED]"
                print(f"    {i:2d}. {t.name:28s} {t.points:3d} pts  "
                      f"GD {t.goal_difference:+3d}{marker}")

        # Process promotion/relegation
        print("\n  Processing promotions and relegations...")
        league.process_promotion_relegation(teams)

        # Reset season stats
        for team in teams.values():
            team.reset_season_stats()

        # Generate new fixtures
        teams_by_div = {}
        for team in teams.values():
            if team.division not in teams_by_div:
                teams_by_div[team.division] = []
            teams_by_div[team.division].append(team.team_id)

        league.season += 1
        league.current_round = 0
        league.generate_fixtures(teams_by_div)

        print(f"\n  Season {league.season} fixtures generated!")
        return True

    return False


def main():
    print("=" * 60)
    print("  PBM FOOTBALL MANAGER — PROCESS TURN")
    print("=" * 60)

    # Load game state
    print("\nLoading game state...")
    players, teams, league = load_game_state()
    print(f"  Loaded: {len(teams)} teams, {len(players)} players, "
          f"Season {league.season}, Round {league.current_round + 1}")

    # 1. Process orders
    all_bids = process_orders(teams, players)

    # 2. Process transfers
    completed_transfers, transfer_listings = process_transfers(teams, players, all_bids)

    # 3. Simulate matches
    all_results = simulate_matches(teams, players, league)

    # 4. Update suspensions/injuries
    decrement_suspensions_and_injuries(players)

    # 5. Generate PDFs
    generate_pdfs(teams, players, league, all_results,
                  completed_transfers, transfer_listings)

    # 6. Advance round
    league.current_round += 1

    # 7. Check end of season
    new_season = check_end_of_season(teams, league)

    # 8. Clean up orders
    cleanup_orders()

    # 9. Save state
    save_game_state(players, teams, league)

    # Summary
    print(f"\n{'=' * 60}")
    print(f"  TURN COMPLETE")
    print(f"{'=' * 60}")
    if new_season:
        print(f"  New season {league.season} has begun!")
    else:
        total_rounds = len(league.fixtures.get(1, []))
        print(f"  Season {league.season}, Round {league.current_round}/{total_rounds}")
    print(f"  Matches played: {len(all_results)}")
    print(f"  Transfers: {len(completed_transfers)}")
    print(f"  PDF reports generated in output/match_reports/")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
