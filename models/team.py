"""
Team model — represents a club with squad, budget, and manager info.
"""
from typing import List, Optional
from models.player import Player
import config


class Team:
    def __init__(self, team_id: str, name: str, short: str, division: int):
        self.team_id = team_id
        self.name = name
        self.short = short
        self.division = division
        self.manager_name: Optional[str] = None  # None = AI controlled
        self.manager_email: Optional[str] = None
        self.budget: int = config.STARTING_BUDGET
        self.formation: str = "4-4-2"
        self.lineup: List[str] = []       # player_ids for starting 11
        self.subs: List[str] = []         # player_ids for bench
        self.squad: List[str] = []        # all player_ids
        self.transfer_listed: List[dict] = []  # [{"player_id", "min_price"}]

        # Season stats
        self.played = 0
        self.won = 0
        self.drawn = 0
        self.lost = 0
        self.goals_for = 0
        self.goals_against = 0

    @property
    def points(self) -> int:
        return self.won * 3 + self.drawn

    @property
    def goal_difference(self) -> int:
        return self.goals_for - self.goals_against

    @property
    def is_managed(self) -> bool:
        return self.manager_name is not None

    def record_result(self, goals_for: int, goals_against: int):
        self.played += 1
        self.goals_for += goals_for
        self.goals_against += goals_against
        if goals_for > goals_against:
            self.won += 1
        elif goals_for == goals_against:
            self.drawn += 1
        else:
            self.lost += 1

    def reset_season_stats(self):
        self.played = 0
        self.won = 0
        self.drawn = 0
        self.lost = 0
        self.goals_for = 0
        self.goals_against = 0

    def to_dict(self) -> dict:
        return {
            "team_id": self.team_id,
            "name": self.name,
            "short": self.short,
            "division": self.division,
            "manager_name": self.manager_name,
            "manager_email": self.manager_email,
            "budget": self.budget,
            "formation": self.formation,
            "lineup": self.lineup,
            "subs": self.subs,
            "squad": self.squad,
            "transfer_listed": self.transfer_listed,
            "played": self.played,
            "won": self.won,
            "drawn": self.drawn,
            "lost": self.lost,
            "goals_for": self.goals_for,
            "goals_against": self.goals_against,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Team":
        t = cls(
            team_id=data["team_id"],
            name=data["name"],
            short=data["short"],
            division=data["division"],
        )
        t.manager_name = data.get("manager_name")
        t.manager_email = data.get("manager_email")
        t.budget = data.get("budget", config.STARTING_BUDGET)
        t.formation = data.get("formation", "4-4-2")
        t.lineup = data.get("lineup", [])
        t.subs = data.get("subs", [])
        t.squad = data.get("squad", [])
        t.transfer_listed = data.get("transfer_listed", [])
        t.played = data.get("played", 0)
        t.won = data.get("won", 0)
        t.drawn = data.get("drawn", 0)
        t.lost = data.get("lost", 0)
        t.goals_for = data.get("goals_for", 0)
        t.goals_against = data.get("goals_against", 0)
        return t
