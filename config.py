"""
League model — manages divisions, fixtures, and promotion/relegation.
"""
import random
from typing import List, Dict
from models.team import Team
import config


class League:
    def __init__(self):
        self.season = 1
        self.current_round = 0
        self.fixtures: Dict[int, List[dict]] = {}  # division -> list of round fixtures

    def generate_fixtures(self, teams_by_division: Dict[int, List[str]]):
        """
        Generate a full season of fixtures for each division using a
        round-robin algorithm. Each team plays every other team twice
        (home and away).
        """
        self.fixtures = {}
        for div, team_ids in teams_by_division.items():
            self.fixtures[div] = self._round_robin(team_ids)

    def _round_robin(self, team_ids: List[str]) -> List[List[dict]]:
        """
        Create a double round-robin schedule.
        Returns list of rounds, each round is a list of {home, away} dicts.
        """
        teams = list(team_ids)
        n = len(teams)
        if n % 2 != 0:
            teams.append("BYE")
            n += 1

        rounds_first_half = []
        rounds_second_half = []

        fixed = teams[0]
        rotating = teams[1:]

        for round_num in range(n - 1):
            round_matches = []
            round_matches_rev = []

            # First match: fixed team vs first in rotation
            if round_num % 2 == 0:
                home, away = fixed, rotating[0]
            else:
                home, away = rotating[0], fixed

            if home != "BYE" and away != "BYE":
                round_matches.append({"home": home, "away": away})
                round_matches_rev.append({"home": away, "away": home})

            # Pair remaining teams: rotating[1] vs rotating[-1],
            # rotating[2] vs rotating[-2], etc.
            for i in range(1, n // 2):
                j = len(rotating) - i  # mirror index from end
                if i >= j:
                    break
                t1 = rotating[i]
                t2 = rotating[j]
                if t1 != "BYE" and t2 != "BYE":
                    round_matches.append({"home": t1, "away": t2})
                    round_matches_rev.append({"home": t2, "away": t1})

            rounds_first_half.append(round_matches)
            rounds_second_half.append(round_matches_rev)

            # Rotate
            rotating = [rotating[-1]] + rotating[:-1]

        all_rounds = rounds_first_half + rounds_second_half
        return all_rounds

    def get_round_fixtures(self, division: int, round_num: int) -> List[dict]:
        """Get fixtures for a specific round in a division."""
        if division not in self.fixtures:
            return []
        rounds = self.fixtures[division]
        if round_num < 0 or round_num >= len(rounds):
            return []
        return rounds[round_num]

    def get_standings(self, teams: Dict[str, Team], division: int) -> List[Team]:
        """Get sorted standings for a division."""
        div_teams = [t for t in teams.values() if t.division == division]
        div_teams.sort(key=lambda t: (-t.points, -t.goal_difference, -t.goals_for, t.name))
        return div_teams

    def process_promotion_relegation(self, teams: Dict[str, Team]):
        """
        At end of season, promote top 3 from each lower division,
        relegate bottom 3 from each upper division.
        """
        for div in range(1, config.DIVISIONS + 1):
            standings = self.get_standings(teams, div)

            if div < config.DIVISIONS:
                # Relegate bottom 3
                relegated = standings[-config.RELEGATION_SPOTS:]
                for t in relegated:
                    t.division = div + 1
                    print(f"  RELEGATED: {t.name} -> Division {div + 1}")

            if div > 1:
                # Promote top 3
                promoted = standings[:config.PROMOTION_SPOTS]
                for t in promoted:
                    t.division = div - 1
                    print(f"  PROMOTED: {t.name} -> Division {div - 1}")

    def to_dict(self) -> dict:
        # Convert fixture keys from int to str for JSON
        fixtures_str = {}
        for div, rounds in self.fixtures.items():
            fixtures_str[str(div)] = rounds
        return {
            "season": self.season,
            "current_round": self.current_round,
            "fixtures": fixtures_str,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "League":
        league = cls()
        league.season = data.get("season", 1)
        league.current_round = data.get("current_round", 0)
        # Convert keys back to int
        fixtures_raw = data.get("fixtures", {})
        league.fixtures = {int(k): v for k, v in fixtures_raw.items()}
        return league
