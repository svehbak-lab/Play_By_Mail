"""
Player Generator — Creates players with realistic stats based on
team tier and position. Names are drawn from the year-2000 pool.
"""
import json
import random
import os
from typing import Dict, List
from models.player import Player
import config


class PlayerGenerator:
    _counter = 0

    def __init__(self):
        names_path = os.path.join(config.DATA_DIR, "player_names.json")
        with open(names_path, "r") as f:
            data = json.load(f)
        self.first_names = data["first_names"]
        self.last_names = data["last_names"]
        self.gk_last_names = data["goalkeeper_last_names"]
        self._used_names = set()

    def _next_id(self) -> str:
        PlayerGenerator._counter += 1
        return f"P{PlayerGenerator._counter:04d}"

    def _unique_name(self, is_gk: bool = False) -> tuple:
        for _ in range(200):
            first = random.choice(self.first_names)
            last = random.choice(self.gk_last_names if is_gk else self.last_names)
            full = f"{first} {last}"
            if full not in self._used_names:
                self._used_names.add(full)
                return first, last
        # Fallback: add number
        first = random.choice(self.first_names)
        last = random.choice(self.last_names)
        return first, f"{last} Jr."

    def generate_squad(self, team_id: str, tier: int) -> List[Player]:
        """
        Generate a starting squad of 20 players for a team.
        Tier 1 = best stats, Tier 4 = lowest stats.
        Distribution: 3 GK, 6 DEF, 6 MID, 5 FWD
        """
        squad = []
        positions = (
            [("GK", True)] * 3 +
            [("DEF", False)] * 6 +
            [("MID", False)] * 6 +
            [("FWD", False)] * 5
        )

        for position, is_gk in positions:
            first, last = self._unique_name(is_gk=is_gk)
            age = random.randint(18, 35)
            stats = self._generate_stats(position, tier, age)
            value = self._calc_value(stats, position, age, tier)

            player = Player(
                player_id=self._next_id(),
                first_name=first,
                last_name=last,
                position=position,
                age=age,
                stats=stats,
                value=value,
            )
            player.team_id = team_id
            squad.append(player)

        return squad

    def _generate_stats(self, position: str, tier: int, age: int) -> dict:
        """
        Generate stats based on position and tier.
        Tier 1: base 60-90, Tier 4: base 30-65
        Age affects: young players have potential, older have experience.
        """
        # Base range by tier
        tier_ranges = {
            1: (60, 92),
            2: (50, 82),
            3: (40, 72),
            4: (30, 65),
        }
        low, high = tier_ranges.get(tier, (40, 70))

        def rand_stat(bonus=0) -> int:
            base = random.randint(low, high) + bonus
            # Age curve: peak at 27-30
            if age < 22:
                base -= random.randint(3, 8)
            elif 27 <= age <= 30:
                base += random.randint(2, 6)
            elif age > 33:
                base -= random.randint(5, 12)
            return max(config.STAT_MIN, min(config.STAT_MAX, base))

        if position == "GK":
            return {
                "pace": rand_stat(-10),
                "shooting": rand_stat(-25),
                "passing": rand_stat(-5),
                "defending": rand_stat(5),
                "physical": rand_stat(5),
                "goalkeeping": rand_stat(20),
            }
        elif position == "DEF":
            return {
                "pace": rand_stat(0),
                "shooting": rand_stat(-10),
                "passing": rand_stat(0),
                "defending": rand_stat(15),
                "physical": rand_stat(10),
                "goalkeeping": rand_stat(-30),
            }
        elif position == "MID":
            return {
                "pace": rand_stat(5),
                "shooting": rand_stat(5),
                "passing": rand_stat(15),
                "defending": rand_stat(0),
                "physical": rand_stat(5),
                "goalkeeping": rand_stat(-30),
            }
        else:  # FWD
            return {
                "pace": rand_stat(10),
                "shooting": rand_stat(15),
                "passing": rand_stat(5),
                "defending": rand_stat(-15),
                "physical": rand_stat(5),
                "goalkeeping": rand_stat(-30),
            }

    def _calc_value(self, stats: dict, position: str, age: int, tier: int) -> int:
        """Calculate market value based on stats, age, and tier."""
        avg_stat = sum(stats.values()) / len(stats)

        # Base value from stats
        base = avg_stat * 50_000

        # Tier multiplier
        tier_mult = {1: 2.5, 2: 1.5, 3: 1.0, 4: 0.6}
        base *= tier_mult.get(tier, 1.0)

        # Age multiplier — young players worth more
        if age <= 23:
            base *= 1.4
        elif age <= 28:
            base *= 1.2
        elif age <= 31:
            base *= 1.0
        else:
            base *= 0.6

        # Position premium
        if position == "FWD":
            base *= 1.3
        elif position == "MID":
            base *= 1.1

        return max(50_000, int(base / 10_000) * 10_000)  # Round to nearest 10k
