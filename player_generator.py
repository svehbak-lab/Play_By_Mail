"""
Match Engine — Simulates football matches based on squad stats,
formation, tactics, and randomness.

The engine works in these stages:
1. Calculate team strength from lineup stats + formation
2. Apply home advantage
3. Apply formation matchup bonuses
4. Add controlled randomness
5. Convert strength differential into goals using Poisson-like distribution
6. Generate match events (goals with scorers/assisters, cards, injuries)
"""
import random
import math
from typing import Dict, List, Tuple, Optional
from models.player import Player
from models.team import Team
from models.match import MatchResult, MatchEvent
import config


class MatchEngine:
    def __init__(self, players: Dict[str, Player]):
        self.players = players

    def simulate_match(self, home_team: Team, away_team: Team) -> MatchResult:
        """Simulate a full match and return the result with events."""
        # 1. Calculate raw team ratings
        home_attack, home_defense = self._calc_team_ratings(home_team)
        away_attack, away_defense = self._calc_team_ratings(away_team)

        # 2. Apply home advantage
        home_attack *= (1 + config.HOME_ADVANTAGE)
        home_defense *= (1 + config.HOME_ADVANTAGE * 0.5)

        # 3. Apply formation matchup
        matchup_bonus = self._get_formation_matchup(
            home_team.formation, away_team.formation
        )
        home_attack *= (1 + matchup_bonus)
        home_defense *= (1 + matchup_bonus * 0.5)
        away_attack *= (1 - matchup_bonus)
        away_defense *= (1 - matchup_bonus * 0.5)

        # 4. Calculate expected goals
        # Attack vs opposing defense determines expected goals
        home_xg = self._calc_expected_goals(home_attack, away_defense)
        away_xg = self._calc_expected_goals(away_attack, home_defense)

        # 5. Add randomness — sample actual goals from Poisson distribution
        home_goals = self._poisson_sample(home_xg)
        away_goals = self._poisson_sample(away_xg)

        # 6. Generate events
        events = self._generate_events(
            home_team, away_team, home_goals, away_goals
        )

        # Store overall rating for display
        home_rating = (home_attack + home_defense) / 2
        away_rating = (away_attack + away_defense) / 2

        return MatchResult(
            home_id=home_team.team_id,
            away_id=away_team.team_id,
            home_goals=home_goals,
            away_goals=away_goals,
            events=events,
            home_formation=home_team.formation,
            away_formation=away_team.formation,
            home_rating=round(home_rating, 1),
            away_rating=round(away_rating, 1),
        )

    def _calc_team_ratings(self, team: Team) -> Tuple[float, float]:
        """
        Calculate team attack and defense ratings from the starting lineup.
        Players in wrong positions get a penalty. Formation structure matters.
        """
        lineup_players = []
        for pid in team.lineup[:config.LINEUP_SIZE]:
            if pid in self.players:
                p = self.players[pid]
                if p.is_available:
                    lineup_players.append(p)

        if not lineup_players:
            return 30.0, 30.0  # Fallback for empty lineup

        # Parse formation to know expected positional slots
        formation_slots = self._parse_formation(team.formation)

        # Sort players by position priority matching formation
        total_attack = 0.0
        total_defense = 0.0

        for player in lineup_players:
            # Position multiplier — players in their natural position are better
            pos_mult = 1.0
            total_attack += player.attack_rating * pos_mult
            total_defense += player.defense_rating * pos_mult

        # Normalize to per-player average, weighted by team size
        n = len(lineup_players)
        attack_avg = total_attack / n
        defense_avg = total_defense / n

        # Formation weighting — more forwards = higher attack, more defenders = higher defense
        atk_slots = formation_slots.get("FWD", 2)
        mid_slots = formation_slots.get("MID", 4)
        def_slots = formation_slots.get("DEF", 4)

        formation_attack_bonus = 1.0 + (atk_slots - 2) * 0.04 + (mid_slots - 4) * 0.02
        formation_defense_bonus = 1.0 + (def_slots - 4) * 0.04 + (mid_slots - 4) * 0.01

        return attack_avg * formation_attack_bonus, defense_avg * formation_defense_bonus

    def _parse_formation(self, formation: str) -> Dict[str, int]:
        """Parse '4-4-2' into {'DEF': 4, 'MID': 4, 'FWD': 2}."""
        parts = [int(x) for x in formation.split("-")]
        result = {"GK": 1}
        if len(parts) == 3:
            result["DEF"] = parts[0]
            result["MID"] = parts[1]
            result["FWD"] = parts[2]
        elif len(parts) == 4:
            result["DEF"] = parts[0]
            result["MID"] = parts[1] + parts[2]  # Combine midfield layers
            result["FWD"] = parts[3]
        return result

    def _get_formation_matchup(self, home_form: str, away_form: str) -> float:
        """
        Look up tactical matchup bonus. Returns bonus for home team
        (positive = home advantage, negative = away advantage).
        """
        key = (home_form, away_form)
        if key in config.FORMATION_MATCHUPS:
            return config.FORMATION_MATCHUPS[key]
        # Check reverse
        rev_key = (away_form, home_form)
        if rev_key in config.FORMATION_MATCHUPS:
            return -config.FORMATION_MATCHUPS[rev_key]
        return 0.0

    def _calc_expected_goals(self, attack: float, defense: float) -> float:
        """
        Convert attack/defense ratings into expected goals.
        Uses a ratio approach: higher attack vs lower defense = more goals.
        Baseline is roughly 1.3 goals (average football match).
        """
        if defense <= 0:
            defense = 1.0
        ratio = attack / defense
        # Base xG around 1.3, scaled by ratio
        xg = 1.3 * ratio

        # Apply randomness factor
        noise = random.gauss(0, config.RANDOMNESS_FACTOR)
        xg = max(0.1, xg + noise)

        # Cap at reasonable range
        return min(xg, 5.0)

    def _poisson_sample(self, xg: float) -> int:
        """Sample goals from a Poisson distribution with mean = xG."""
        # Simple Poisson sampling using Knuth's algorithm
        L = math.exp(-xg)
        k = 0
        p = 1.0
        while True:
            k += 1
            p *= random.random()
            if p < L:
                break
        return max(0, k - 1)

    def _generate_events(self, home_team: Team, away_team: Team,
                         home_goals: int, away_goals: int) -> List[MatchEvent]:
        """Generate match events: goals with scorers, cards, injuries."""
        events = []

        # Generate goal events for home team
        events.extend(self._generate_goal_events(home_team, home_goals))

        # Generate goal events for away team
        events.extend(self._generate_goal_events(away_team, away_goals))

        # Generate card events (roughly 3-4 per match total)
        num_cards = random.randint(1, 6)
        for _ in range(num_cards):
            team = random.choice([home_team, away_team])
            events.append(self._generate_card_event(team))

        # Small chance of injury (10% per match per team)
        for team in [home_team, away_team]:
            if random.random() < 0.10:
                events.append(self._generate_injury_event(team))

        # Small chance of red card (5% per match)
        if random.random() < 0.05:
            team = random.choice([home_team, away_team])
            events.append(self._generate_red_card_event(team))

        # Sort by minute
        events.sort(key=lambda e: e.minute)
        return events

    def _generate_goal_events(self, team: Team, num_goals: int) -> List[MatchEvent]:
        """Generate goal events with scorers weighted by position/stats."""
        events = []
        outfield = [
            self.players[pid] for pid in team.lineup[:config.LINEUP_SIZE]
            if pid in self.players and self.players[pid].position != "GK"
        ]
        if not outfield:
            return events

        # Weight by shooting + position
        weights = []
        for p in outfield:
            w = p.stats["shooting"]
            if p.position == "FWD":
                w *= 3.0
            elif p.position == "MID":
                w *= 1.5
            else:
                w *= 0.5
            weights.append(w)

        for _ in range(num_goals):
            minute = random.randint(1, 90)
            scorer = random.choices(outfield, weights=weights, k=1)[0]

            # 60% chance of an assist
            assist_id = None
            if random.random() < 0.60 and len(outfield) > 1:
                assisters = [p for p in outfield if p.player_id != scorer.player_id]
                assist_weights = [p.stats["passing"] for p in assisters]
                assister = random.choices(assisters, weights=assist_weights, k=1)[0]
                assist_id = assister.player_id

            events.append(MatchEvent(
                minute=minute,
                event_type="goal",
                player_id=scorer.player_id,
                team_id=team.team_id,
                assist_player_id=assist_id,
            ))

        return events

    def _generate_card_event(self, team: Team) -> MatchEvent:
        """Generate a yellow card event."""
        outfield = [
            self.players[pid] for pid in team.lineup[:config.LINEUP_SIZE]
            if pid in self.players and self.players[pid].position != "GK"
        ]
        if not outfield:
            pid = team.lineup[0] if team.lineup else "UNKNOWN"
            player = self.players.get(pid)
        else:
            # Defenders and midfielders more likely to get cards
            weights = []
            for p in outfield:
                w = p.stats["physical"]
                if p.position == "DEF":
                    w *= 2.0
                elif p.position == "MID":
                    w *= 1.5
                weights.append(w)
            player = random.choices(outfield, weights=weights, k=1)[0]

        return MatchEvent(
            minute=random.randint(1, 90),
            event_type="yellow",
            player_id=player.player_id,
            team_id=team.team_id,
        )

    def _generate_red_card_event(self, team: Team) -> MatchEvent:
        """Generate a red card event."""
        outfield = [
            self.players[pid] for pid in team.lineup[:config.LINEUP_SIZE]
            if pid in self.players
        ]
        player = random.choice(outfield) if outfield else None
        if not player:
            return MatchEvent(0, "red", "UNKNOWN", team.team_id)
        return MatchEvent(
            minute=random.randint(20, 85),
            event_type="red",
            player_id=player.player_id,
            team_id=team.team_id,
        )

    def _generate_injury_event(self, team: Team) -> MatchEvent:
        """Generate an injury event."""
        outfield = [
            self.players[pid] for pid in team.lineup[:config.LINEUP_SIZE]
            if pid in self.players
        ]
        player = random.choice(outfield) if outfield else None
        if not player:
            return MatchEvent(0, "injury", "UNKNOWN", team.team_id)
        return MatchEvent(
            minute=random.randint(1, 90),
            event_type="injury",
            player_id=player.player_id,
            team_id=team.team_id,
        )
