"""
Player model — each player has positional stats and a unique ID.
"""
import json


class Player:
    def __init__(self, player_id: str, first_name: str, last_name: str,
                 position: str, age: int, stats: dict, value: int = 500_000):
        self.player_id = player_id
        self.first_name = first_name
        self.last_name = last_name
        self.position = position  # GK, DEF, MID, FWD
        self.age = age
        self.stats = stats  # {"pace","shooting","passing","defending","physical","goalkeeping"}
        self.value = value
        self.team_id = None
        self.goals = 0
        self.assists = 0
        self.appearances = 0
        self.yellow_cards = 0
        self.red_cards = 0
        self.suspended = 0  # turns of suspension remaining
        self.injured = 0     # turns of injury remaining

    @property
    def name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def short_name(self) -> str:
        return f"{self.first_name[0]}. {self.last_name}"

    @property
    def overall(self) -> int:
        """Weighted overall rating based on position."""
        s = self.stats
        if self.position == "GK":
            return int(s["goalkeeping"] * 0.50 + s["physical"] * 0.15 +
                       s["pace"] * 0.10 + s["defending"] * 0.15 + s["passing"] * 0.10)
        elif self.position == "DEF":
            return int(s["defending"] * 0.40 + s["physical"] * 0.20 +
                       s["pace"] * 0.15 + s["passing"] * 0.15 + s["shooting"] * 0.10)
        elif self.position == "MID":
            return int(s["passing"] * 0.35 + s["shooting"] * 0.15 +
                       s["defending"] * 0.15 + s["pace"] * 0.15 + s["physical"] * 0.20)
        else:  # FWD
            return int(s["shooting"] * 0.35 + s["pace"] * 0.25 +
                       s["passing"] * 0.15 + s["physical"] * 0.15 + s["defending"] * 0.10)

    @property
    def attack_rating(self) -> float:
        """How much this player contributes to attacking play."""
        s = self.stats
        if self.position == "FWD":
            return s["shooting"] * 0.4 + s["pace"] * 0.3 + s["passing"] * 0.2 + s["physical"] * 0.1
        elif self.position == "MID":
            return s["passing"] * 0.3 + s["shooting"] * 0.3 + s["pace"] * 0.2 + s["physical"] * 0.2
        elif self.position == "DEF":
            return s["passing"] * 0.4 + s["shooting"] * 0.2 + s["pace"] * 0.2 + s["physical"] * 0.2
        else:
            return s["passing"] * 0.5 + s["goalkeeping"] * 0.3 + s["pace"] * 0.2

    @property
    def defense_rating(self) -> float:
        """How much this player contributes to defensive play."""
        s = self.stats
        if self.position == "GK":
            return s["goalkeeping"] * 0.6 + s["physical"] * 0.2 + s["pace"] * 0.1 + s["defending"] * 0.1
        elif self.position == "DEF":
            return s["defending"] * 0.4 + s["physical"] * 0.25 + s["pace"] * 0.2 + s["passing"] * 0.15
        elif self.position == "MID":
            return s["defending"] * 0.3 + s["physical"] * 0.3 + s["pace"] * 0.2 + s["passing"] * 0.2
        else:
            return s["defending"] * 0.3 + s["physical"] * 0.3 + s["pace"] * 0.2 + s["shooting"] * 0.2

    @property
    def is_available(self) -> bool:
        return self.suspended == 0 and self.injured == 0

    def to_dict(self) -> dict:
        return {
            "player_id": self.player_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "position": self.position,
            "age": self.age,
            "stats": self.stats,
            "value": self.value,
            "team_id": self.team_id,
            "goals": self.goals,
            "assists": self.assists,
            "appearances": self.appearances,
            "yellow_cards": self.yellow_cards,
            "red_cards": self.red_cards,
            "suspended": self.suspended,
            "injured": self.injured,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        p = cls(
            player_id=data["player_id"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            position=data["position"],
            age=data["age"],
            stats=data["stats"],
            value=data.get("value", 500_000),
        )
        p.team_id = data.get("team_id")
        p.goals = data.get("goals", 0)
        p.assists = data.get("assists", 0)
        p.appearances = data.get("appearances", 0)
        p.yellow_cards = data.get("yellow_cards", 0)
        p.red_cards = data.get("red_cards", 0)
        p.suspended = data.get("suspended", 0)
        p.injured = data.get("injured", 0)
        return p
