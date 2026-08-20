"""
Flatten the Cricsheet IPL archive into two analysis tables.

    data/processed/deliveries.csv   one row per ball bowled
    data/processed/matches.csv      one row per match

Cricsheet stores each match as nested JSON. The work here is turning that into
a flat ball-by-ball table with the derived fields the analysis needs: match
phase, whether the ball was legal, whether it was a boundary, and who was
dismissed how.

Two details that are easy to get wrong and are handled explicitly:

  * Wides and no-balls are not legal deliveries. Counting them in a bowler's
    balls-bowled inflates their economy denominator and understates a batter's
    strike rate.
  * Run-outs and retirements are not credited to the bowler. Treating every
    dismissal as a bowler wicket overstates strike bowlers.
"""

import json
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_ZIP = ROOT / "data" / "raw" / "ipl_json.zip"
PROCESSED_DIR = ROOT / "data" / "processed"

# Dismissals the bowler is not credited with.
NON_BOWLER_DISMISSALS = {
    "run out",
    "retired hurt",
    "retired out",
    "retired not out",
    "obstructing the field",
}

# Team names changed over the years; the same franchise under two names would
# otherwise split its record in two.
TEAM_ALIASES = {
    "Delhi Daredevils": "Delhi Capitals",
    "Kings XI Punjab": "Punjab Kings",
    "Royal Challengers Bangalore": "Royal Challengers Bengaluru",
    "Rising Pune Supergiant": "Rising Pune Supergiants",
}


def canonical_team(name: str) -> str:
    return TEAM_ALIASES.get(name, name)


def phase_for_over(over: int) -> str:
    """Standard T20 phases. `over` is zero-indexed as Cricsheet stores it."""
    if over < 6:
        return "Powerplay"
    if over < 15:
        return "Middle"
    return "Death"


def parse_match(match_id: str, data: dict) -> tuple[dict, list[dict]]:
    info = data["info"]

    teams = [canonical_team(t) for t in info.get("teams", [])]
    outcome = info.get("outcome", {})
    toss = info.get("toss", {})

    match_row = {
        "match_id": match_id,
        "season": str(info.get("season", "")),
        "date": info.get("dates", [None])[0],
        "venue": info.get("venue"),
        "city": info.get("city"),
        "team_1": teams[0] if teams else None,
        "team_2": teams[1] if len(teams) > 1 else None,
        "toss_winner": canonical_team(toss.get("winner", "")) or None,
        "toss_decision": toss.get("decision"),
        "winner": canonical_team(outcome.get("winner", "")) or None,
        "result": outcome.get("result"),
        "win_by_runs": outcome.get("by", {}).get("runs"),
        "win_by_wickets": outcome.get("by", {}).get("wickets"),
        "player_of_match": (info.get("player_of_match") or [None])[0],
        "match_number": (info.get("event") or {}).get("match_number"),
    }

    deliveries = []
    for innings_number, innings in enumerate(data.get("innings", []), start=1):
        batting_team = canonical_team(innings.get("team", ""))
        bowling_team = next((t for t in teams if t != batting_team), None)

        # A super over is a separate mini-innings and would distort per-over
        # statistics if mixed in with the main innings.
        is_super_over = bool(innings.get("super_over", False))

        for over_block in innings.get("overs", []):
            over = over_block["over"]

            for ball_index, delivery in enumerate(over_block["deliveries"], start=1):
                runs = delivery.get("runs", {})
                extras = delivery.get("extras", {})

                wides = extras.get("wides", 0)
                noballs = extras.get("noballs", 0)
                is_legal = wides == 0 and noballs == 0

                wickets = delivery.get("wickets", []) or []
                wicket = wickets[0] if wickets else {}
                kind = wicket.get("kind")

                batter_runs = runs.get("batter", 0)

                deliveries.append({
                    "match_id": match_id,
                    "season": match_row["season"],
                    "date": match_row["date"],
                    "venue": match_row["venue"],
                    "innings": innings_number,
                    "is_super_over": is_super_over,
                    "batting_team": batting_team,
                    "bowling_team": bowling_team,
                    "over": over,
                    "ball_in_over": ball_index,
                    "phase": phase_for_over(over),
                    "batter": delivery.get("batter"),
                    "bowler": delivery.get("bowler"),
                    "non_striker": delivery.get("non_striker"),
                    "runs_batter": batter_runs,
                    "runs_extras": runs.get("extras", 0),
                    "runs_total": runs.get("total", 0),
                    "wides": wides,
                    "noballs": noballs,
                    "byes": extras.get("byes", 0),
                    "legbyes": extras.get("legbyes", 0),
                    "is_legal_delivery": is_legal,
                    "is_four": batter_runs == 4,
                    "is_six": batter_runs == 6,
                    "is_dot": runs.get("total", 0) == 0,
                    "is_wicket": bool(wickets),
                    "dismissal_kind": kind,
                    "player_out": wicket.get("player_out"),
                    "is_bowler_wicket": bool(kind) and kind not in NON_BOWLER_DISMISSALS,
                })

    return match_row, deliveries


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    match_rows = []
    delivery_rows = []

    with zipfile.ZipFile(RAW_ZIP) as archive:
        names = sorted(n for n in archive.namelist() if n.endswith(".json"))
        print(f"Parsing {len(names)} match files...")

        for name in names:
            match_id = Path(name).stem
            data = json.loads(archive.read(name))
            match_row, deliveries = parse_match(match_id, data)
            match_rows.append(match_row)
            delivery_rows.extend(deliveries)

    matches = pd.DataFrame(match_rows)
    deliveries = pd.DataFrame(delivery_rows)

    # A handful of very early matches carry no season string; drop them rather
    # than let them form an empty season bucket in every grouped result.
    matches = matches[matches["season"].str.len() > 0]
    deliveries = deliveries[deliveries["match_id"].isin(matches["match_id"])]

    # Cricsheet labels some seasons across two years ("2007/08", "2009/10"),
    # and the label does not reliably name the year the cricket was played:
    # "2007/08" was played in 2008 and "2009/10" in 2010. Deriving the season
    # year from the match date is correct for every season, including the
    # displaced 2020 edition played in September-November.
    matches["season_year"] = pd.to_datetime(matches["date"]).dt.year
    deliveries = deliveries.merge(
        matches[["match_id", "season_year"]], on="match_id", how="left"
    )

    matches.to_csv(PROCESSED_DIR / "matches.csv", index=False)
    deliveries.to_csv(PROCESSED_DIR / "deliveries.csv", index=False)

    print(f"\nMatches    : {len(matches):,}")
    print(f"Deliveries : {len(deliveries):,}")
    print(f"Seasons    : {matches['season_year'].min()}-{matches['season_year'].max()}")
    print(f"Legal balls: {deliveries['is_legal_delivery'].sum():,}")
    print(f"Wickets    : {deliveries['is_wicket'].sum():,} "
          f"({deliveries['is_bowler_wicket'].sum():,} credited to bowlers)")
    print(f"Super over deliveries: {deliveries['is_super_over'].sum():,}")


if __name__ == "__main__":
    main()
