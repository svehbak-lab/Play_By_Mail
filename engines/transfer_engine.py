"""
Transfer Engine — Processes player sales and bids.

Flow:
1. Collect all transfer listings from teams
2. Collect all bids from managers
3. For each listed player, find highest valid bid
4. Execute transfers (move player, adjust budgets)
5. Return report of completed transfers
"""
from typing import Dict, List, Tuple, Optional
from models.player import Player
from models.team import Team


class TransferEngine:
    def __init__(self, players: Dict[str, Player], teams: Dict[str, Team]):
        self.players = players
        self.teams = teams

    def collect_transfer_list(self) -> List[dict]:
        """
        Gather all players currently listed for transfer across all teams.
        Returns list of {"player_id", "player_name", "position", "overall",
                         "age", "team_id", "team_name", "min_price"}
        """
        listings = []
        for team in self.teams.values():
            for listing in team.transfer_listed:
                pid = listing["player_id"]
                if pid in self.players:
                    p = self.players[pid]
                    listings.append({
                        "player_id": pid,
                        "player_name": p.name,
                        "position": p.position,
                        "overall": p.overall,
                        "age": p.age,
                        "stats": p.stats,
                        "team_id": team.team_id,
                        "team_name": team.name,
                        "min_price": listing["min_price"],
                        "value": p.value,
                    })
        return listings

    def process_bids(self, all_bids: Dict[str, List[dict]]) -> List[dict]:
        """
        Process all bids and execute transfers.

        all_bids: {team_id: [{"player_id": str, "amount": int}, ...]}

        Returns list of completed transfers:
        [{"player_id", "player_name", "from_team", "to_team", "amount"}, ...]
        """
        completed = []

        # Group bids by player_id
        bids_by_player: Dict[str, List[Tuple[str, int]]] = {}
        for bidder_team_id, bids in all_bids.items():
            for bid in bids:
                pid = bid["player_id"]
                amount = bid["amount"]
                if pid not in bids_by_player:
                    bids_by_player[pid] = []
                bids_by_player[pid].append((bidder_team_id, amount))

        # Process each listed player
        for team in self.teams.values():
            remaining_listings = []
            for listing in team.transfer_listed:
                pid = listing["player_id"]
                min_price = listing["min_price"]

                if pid not in bids_by_player:
                    # No bids — keep on transfer list
                    remaining_listings.append(listing)
                    continue

                # Find highest valid bid
                valid_bids = [
                    (tid, amt) for tid, amt in bids_by_player[pid]
                    if amt >= min_price and self._can_afford(tid, amt)
                    and self._has_squad_space(tid)
                ]

                if not valid_bids:
                    remaining_listings.append(listing)
                    continue

                # Highest bid wins
                valid_bids.sort(key=lambda x: -x[1])
                winner_team_id, winning_amount = valid_bids[0]

                # Execute transfer
                transfer = self._execute_transfer(
                    pid, team.team_id, winner_team_id, winning_amount
                )
                if transfer:
                    completed.append(transfer)
                else:
                    remaining_listings.append(listing)

            team.transfer_listed = remaining_listings

        return completed

    def _can_afford(self, team_id: str, amount: int) -> bool:
        team = self.teams.get(team_id)
        return team is not None and team.budget >= amount

    def _has_squad_space(self, team_id: str) -> bool:
        team = self.teams.get(team_id)
        if team is None:
            return False
        from config import MAX_SQUAD_SIZE
        return len(team.squad) < MAX_SQUAD_SIZE

    def _execute_transfer(self, player_id: str, from_team_id: str,
                          to_team_id: str, amount: int) -> Optional[dict]:
        """Move player between teams and adjust budgets."""
        player = self.players.get(player_id)
        from_team = self.teams.get(from_team_id)
        to_team = self.teams.get(to_team_id)

        if not all([player, from_team, to_team]):
            return None

        # Remove from seller
        if player_id in from_team.squad:
            from_team.squad.remove(player_id)
        if player_id in from_team.lineup:
            from_team.lineup.remove(player_id)
        if player_id in from_team.subs:
            from_team.subs.remove(player_id)
        from_team.budget += amount

        # Add to buyer
        to_team.squad.append(player_id)
        to_team.budget -= amount
        player.team_id = to_team_id

        # Update player value based on fee paid
        player.value = amount

        return {
            "player_id": player_id,
            "player_name": player.name,
            "position": player.position,
            "overall": player.overall,
            "from_team_id": from_team_id,
            "from_team_name": from_team.name,
            "to_team_id": to_team_id,
            "to_team_name": to_team.name,
            "amount": amount,
        }
