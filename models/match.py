"""
Match result model — stores the outcome of a single match.
"""
from typing import List, Optional


class MatchEvent:
    """A single event in a match (goal, card, etc.)."""
    def __init__(self, minute: int, event_type: str, player_id: str,
                 team_id: str, assist_player_id: Optional[str] = None):
        self.minute = minute
        self.event_type = event_type  # "goal", "own_goal", "yellow", "red", "injury"
        self.player_id = player_id
        self.team_id = team_id
        self.assist_player_id = assist_player_id

    def to_dict(self) -> dict:
        return {
            "minute": self.minute,
            "event_type": self.event_type,
            "player_id": self.player_id,
            "team_id": self.team_id,
            "assist_player_id": self.assist_player_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MatchEvent":
        return cls(
            minute=data["minute"],
            event_type=data["event_type"],
            player_id=data["player_id"],
            team_id=data["team_id"],
            assist_player_id=data.get("assist_player_id"),
        )


class MatchResult:
    def __init__(self, home_id: str, away_id: str, home_goals: int,
                 away_goals: int, events: List[MatchEvent] = None,
                 home_formation: str = "4-4-2", away_formation: str = "4-4-2",
                 home_rating: float = 0, away_rating: float = 0):
        self.home_id = home_id
        self.away_id = away_id
        self.home_goals = home_goals
        self.away_goals = away_goals
        self.events = events or []
        self.home_formation = home_formation
        self.away_formation = away_formation
        self.home_rating = home_rating
        self.away_rating = away_rating

    @property
    def score_line(self) -> str:
        return f"{self.home_goals} - {self.away_goals}"

    def to_dict(self) -> dict:
        return {
            "home_id": self.home_id,
            "away_id": self.away_id,
            "home_goals": self.home_goals,
            "away_goals": self.away_goals,
            "events": [e.to_dict() for e in self.events],
            "home_formation": self.home_formation,
            "away_formation": self.away_formation,
            "home_rating": self.home_rating,
            "away_rating": self.away_rating,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MatchResult":
        events = [MatchEvent.from_dict(e) for e in data.get("events", [])]
        return cls(
            home_id=data["home_id"],
            away_id=data["away_id"],
            home_goals=data["home_goals"],
            away_goals=data["away_goals"],
            events=events,
            home_formation=data.get("home_formation", "4-4-2"),
            away_formation=data.get("away_formation", "4-4-2"),
            home_rating=data.get("home_rating", 0),
            away_rating=data.get("away_rating", 0),
        )
