"""
PDF Match Report Generator — Creates a detailed match report PDF
for each team after a round of matches.
"""
import os
from typing import Dict, List
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from models.player import Player
from models.team import Team
from models.match import MatchResult
import config


class MatchReportGenerator:
    def __init__(self, players: Dict[str, Player], teams: Dict[str, Team]):
        self.players = players
        self.teams = teams
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        self.styles.add(ParagraphStyle(
            "MatchTitle",
            parent=self.styles["Title"],
            fontSize=16,
            spaceAfter=6,
        ))
        self.styles.add(ParagraphStyle(
            "SectionHead",
            parent=self.styles["Heading2"],
            fontSize=12,
            spaceAfter=4,
            spaceBefore=10,
            textColor=colors.HexColor("#1a3c6e"),
        ))
        self.styles.add(ParagraphStyle(
            "SmallText",
            parent=self.styles["Normal"],
            fontSize=8,
            textColor=colors.grey,
        ))

    def generate_team_report(self, team: Team, match_result: MatchResult,
                             standings: List[Team], round_num: int,
                             season: int, output_dir: str,
                             all_results: List[MatchResult] = None,
                             transfer_list: List[dict] = None,
                             completed_transfers: List[dict] = None):
        """Generate a complete PDF report for one team."""
        filename = f"turn_{season}_{round_num:02d}_{team.team_id}.pdf"
        filepath = os.path.join(output_dir, filename)

        doc = SimpleDocTemplate(
            filepath, pagesize=A4,
            leftMargin=15 * mm, rightMargin=15 * mm,
            topMargin=15 * mm, bottomMargin=15 * mm,
        )

        story = []

        # Header
        story.append(Paragraph(
            f"PBM Football Manager — Season {season}, Round {round_num}",
            self.styles["MatchTitle"]
        ))
        story.append(Paragraph(
            f"Report for: <b>{team.name}</b> | Manager: {team.manager_name or 'AI Manager'}",
            self.styles["Normal"]
        ))
        story.append(Spacer(1, 6))

        # Match result
        story.extend(self._match_section(team, match_result))

        # Squad overview
        story.extend(self._squad_section(team))

        # League table
        story.extend(self._standings_section(standings, team))

        # All results this round
        if all_results:
            story.extend(self._all_results_section(all_results, team.division))

        # Transfer news
        if completed_transfers:
            story.extend(self._transfer_news_section(completed_transfers))

        # Transfer list (available players)
        if transfer_list:
            story.extend(self._transfer_list_section(transfer_list))

        # Budget
        story.append(Paragraph("FINANCES", self.styles["SectionHead"]))
        budget_str = f"Current Budget: <b>£{team.budget:,.0f}</b>"
        story.append(Paragraph(budget_str, self.styles["Normal"]))
        story.append(Spacer(1, 8))

        # Footer
        story.append(Spacer(1, 12))
        story.append(Paragraph(
            "Submit your orders before the next deadline. "
            "Format: JSON file with formation, lineup, subs, transfer_list, bids.",
            self.styles["SmallText"]
        ))

        doc.build(story)
        return filepath

    def _match_section(self, team: Team, result: MatchResult) -> list:
        elements = []
        elements.append(Paragraph("MATCH RESULT", self.styles["SectionHead"]))

        home_team = self.teams[result.home_id]
        away_team = self.teams[result.away_id]

        score_text = (
            f"<b>{home_team.name}</b>  {result.home_goals} - {result.away_goals}  "
            f"<b>{away_team.name}</b>"
        )
        elements.append(Paragraph(score_text, self.styles["Normal"]))

        formation_text = (
            f"Formation: {home_team.short} ({result.home_formation}) vs "
            f"{away_team.short} ({result.away_formation})"
        )
        elements.append(Paragraph(formation_text, self.styles["SmallText"]))
        elements.append(Spacer(1, 4))

        # Events
        if result.events:
            event_data = [["Min", "Event", "Player", "Team"]]
            for evt in result.events:
                player = self.players.get(evt.player_id)
                pname = player.short_name if player else "Unknown"
                evt_team = self.teams.get(evt.team_id)
                tname = evt_team.short if evt_team else "?"

                icon = {"goal": "GOAL", "yellow": "YC", "red": "RC",
                        "injury": "INJ", "own_goal": "OG"}.get(evt.event_type, evt.event_type)

                detail = icon
                if evt.event_type == "goal" and evt.assist_player_id:
                    assister = self.players.get(evt.assist_player_id)
                    if assister:
                        detail = f"GOAL (assist: {assister.short_name})"

                event_data.append([
                    str(evt.minute) + "'",
                    detail,
                    pname,
                    tname,
                ])

            t = Table(event_data, colWidths=[35, 140, 120, 50])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3c6e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            elements.append(t)

        elements.append(Spacer(1, 6))
        return elements

    def _squad_section(self, team: Team) -> list:
        elements = []
        elements.append(Paragraph("YOUR SQUAD", self.styles["SectionHead"]))

        squad_data = [["ID", "Name", "Pos", "Age", "OVR", "PAC", "SHO", "PAS", "DEF", "PHY", "GK", "Status"]]
        for pid in team.squad:
            p = self.players.get(pid)
            if not p:
                continue
            status = "OK"
            if pid in team.lineup:
                status = "START"
            elif pid in team.subs:
                status = "SUB"
            if p.suspended > 0:
                status = f"SUS({p.suspended})"
            if p.injured > 0:
                status = f"INJ({p.injured})"

            squad_data.append([
                p.player_id, p.short_name, p.position, str(p.age),
                str(p.overall),
                str(p.stats["pace"]), str(p.stats["shooting"]),
                str(p.stats["passing"]), str(p.stats["defending"]),
                str(p.stats["physical"]), str(p.stats["goalkeeping"]),
                status,
            ])

        col_widths = [40, 90, 28, 25, 28, 28, 28, 28, 28, 28, 28, 45]
        t = Table(squad_data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3c6e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
            ("ALIGN", (2, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 6))
        return elements

    def _standings_section(self, standings: List[Team], current_team: Team) -> list:
        elements = []
        div_name = {1: "Premier Division", 2: "Division One",
                    3: "Division Two", 4: "Division Three"}.get(current_team.division, "Unknown")
        elements.append(Paragraph(f"LEAGUE TABLE — {div_name}", self.styles["SectionHead"]))

        table_data = [["Pos", "Team", "P", "W", "D", "L", "GF", "GA", "GD", "Pts"]]
        for i, t in enumerate(standings, 1):
            table_data.append([
                str(i), t.name, str(t.played), str(t.won), str(t.drawn),
                str(t.lost), str(t.goals_for), str(t.goals_against),
                str(t.goal_difference), str(t.points),
            ])

        col_widths = [25, 130, 22, 22, 22, 22, 25, 25, 28, 28]
        tbl = Table(table_data, colWidths=col_widths)

        style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3c6e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
            ("ALIGN", (2, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]

        # Highlight current team's row
        for i, t in enumerate(standings, 1):
            if t.team_id == current_team.team_id:
                style_cmds.append(
                    ("BACKGROUND", (0, i), (-1, i), colors.HexColor("#e6f0ff"))
                )

        # Promotion zone (green tint for top 3)
        for i in range(1, min(4, len(standings) + 1)):
            style_cmds.append(
                ("TEXTCOLOR", (0, i), (0, i), colors.HexColor("#2d8a4e"))
            )
        # Relegation zone (red tint for bottom 3)
        for i in range(max(1, len(standings) - 2), len(standings) + 1):
            style_cmds.append(
                ("TEXTCOLOR", (0, i), (0, i), colors.HexColor("#c0392b"))
            )

        tbl.setStyle(TableStyle(style_cmds))
        elements.append(tbl)
        elements.append(Spacer(1, 6))
        return elements

    def _all_results_section(self, results: List[MatchResult], division: int) -> list:
        elements = []
        elements.append(Paragraph("ALL RESULTS THIS ROUND", self.styles["SectionHead"]))

        for r in results:
            home = self.teams.get(r.home_id)
            away = self.teams.get(r.away_id)
            if home and away and home.division == division:
                line = f"{home.name} {r.home_goals} - {r.away_goals} {away.name}"
                elements.append(Paragraph(line, self.styles["Normal"]))

        elements.append(Spacer(1, 6))
        return elements

    def _transfer_news_section(self, transfers: List[dict]) -> list:
        elements = []
        elements.append(Paragraph("TRANSFER NEWS", self.styles["SectionHead"]))

        for t in transfers:
            line = (
                f"<b>{t['player_name']}</b> ({t['position']}, OVR {t['overall']}) — "
                f"{t['from_team_name']} to {t['to_team_name']} "
                f"for <b>£{t['amount']:,.0f}</b>"
            )
            elements.append(Paragraph(line, self.styles["Normal"]))

        elements.append(Spacer(1, 6))
        return elements

    def _transfer_list_section(self, listings: List[dict]) -> list:
        elements = []
        elements.append(Paragraph("TRANSFER LIST — AVAILABLE PLAYERS", self.styles["SectionHead"]))
        elements.append(Paragraph(
            "To bid, include the Player ID and your bid amount in your order file.",
            self.styles["SmallText"]
        ))
        elements.append(Spacer(1, 4))

        if not listings:
            elements.append(Paragraph("No players currently listed.", self.styles["Normal"]))
            return elements

        tl_data = [["ID", "Name", "Pos", "Age", "OVR", "Club", "Min Price"]]
        for l in listings:
            tl_data.append([
                l["player_id"], l["player_name"], l["position"],
                str(l["age"]), str(l["overall"]), l["team_name"],
                f"£{l['min_price']:,.0f}",
            ])

        col_widths = [45, 100, 30, 28, 30, 110, 70]
        t = Table(tl_data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8b4513")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fdf5e6")]),
            ("ALIGN", (2, 0), (-1, -1), "CENTER"),
            ("ALIGN", (-1, 1), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 6))
        return elements
