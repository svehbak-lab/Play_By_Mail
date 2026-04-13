#!/usr/bin/env python3
"""
manage_teams.py — Admin tool for assigning and removing managers.

Usage:
    python manage_teams.py list                    # List all teams and managers
    python manage_teams.py assign <team_id> <name> <email>
    python manage_teams.py remove <team_id>        # Remove manager (team goes to AI)
    python manage_teams.py free                     # List unmanaged teams
    python manage_teams.py info <team_id>          # Show team details
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import load_game_state, save_game_state


def list_teams(teams):
    print(f"\n{'Team':30s} {'Division':12s} {'Manager':20s} {'Budget':>12s}")
    print("-" * 78)
    for div in range(1, 5):
        div_teams = sorted(
            [t for t in teams.values() if t.division == div],
            key=lambda t: t.name
        )
        for t in div_teams:
            mgr = t.manager_name or "(AI)"
            print(f"{t.name:30s} {div:12d} {mgr:20s} £{t.budget:>11,.0f}")


def list_free(teams):
    free = [t for t in teams.values() if not t.is_managed]
    free.sort(key=lambda t: (t.division, t.name))
    print(f"\n{len(free)} unmanaged teams:\n")
    for t in free:
        print(f"  {t.team_id:20s} {t.name:30s} Division {t.division}")


def assign_manager(teams, team_id, name, email):
    if team_id not in teams:
        print(f"Error: Team '{team_id}' not found.")
        return
    team = teams[team_id]
    team.manager_name = name
    team.manager_email = email
    print(f"Assigned {name} ({email}) to {team.name}")


def remove_manager(teams, team_id):
    if team_id not in teams:
        print(f"Error: Team '{team_id}' not found.")
        return
    team = teams[team_id]
    old = team.manager_name
    team.manager_name = None
    team.manager_email = None
    print(f"Removed manager {old} from {team.name} — now AI-controlled")


def team_info(teams, players, team_id):
    if team_id not in teams:
        print(f"Error: Team '{team_id}' not found.")
        return
    t = teams[team_id]
    print(f"\n{'=' * 50}")
    print(f"  {t.name} ({t.short})")
    print(f"{'=' * 50}")
    print(f"  Division:  {t.division}")
    print(f"  Manager:   {t.manager_name or '(AI)'}")
    print(f"  Budget:    £{t.budget:,.0f}")
    print(f"  Formation: {t.formation}")
    print(f"  Record:    {t.played}P {t.won}W {t.drawn}D {t.lost}L")
    print(f"  Goals:     {t.goals_for}F {t.goals_against}A (GD {t.goal_difference:+d})")
    print(f"  Points:    {t.points}")
    print(f"\n  Squad ({len(t.squad)} players):")
    print(f"  {'ID':8s} {'Name':22s} {'Pos':4s} {'Age':4s} {'OVR':4s} {'Status':8s}")
    print(f"  {'-' * 54}")
    for pid in t.squad:
        p = players.get(pid)
        if not p:
            continue
        status = "OK"
        if pid in t.lineup:
            status = "START"
        elif pid in t.subs:
            status = "SUB"
        if p.suspended > 0:
            status = f"SUS({p.suspended})"
        if p.injured > 0:
            status = f"INJ({p.injured})"
        print(f"  {p.player_id:8s} {p.name:22s} {p.position:4s} {p.age:<4d} {p.overall:<4d} {status}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    players, teams, league = load_game_state()
    cmd = sys.argv[1].lower()

    if cmd == "list":
        list_teams(teams)
    elif cmd == "free":
        list_free(teams)
    elif cmd == "assign" and len(sys.argv) >= 5:
        assign_manager(teams, sys.argv[2], sys.argv[3], sys.argv[4])
        save_game_state(players, teams, league)
    elif cmd == "remove" and len(sys.argv) >= 3:
        remove_manager(teams, sys.argv[2])
        save_game_state(players, teams, league)
    elif cmd == "info" and len(sys.argv) >= 3:
        team_info(teams, players, sys.argv[2])
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
