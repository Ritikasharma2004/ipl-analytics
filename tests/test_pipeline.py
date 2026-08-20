"""
Tests for the IPL pipeline.

The tests that matter here are the scoring conventions. Cricket rates are easy
to compute plausibly and wrongly: counting wides as balls faced, charging byes
to the bowler, or crediting run-outs as bowler wickets all produce numbers that
look reasonable and are not. Each of those is pinned below.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from transform import (  # noqa: E402
    NON_BOWLER_DISMISSALS,
    canonical_team,
    parse_match,
    phase_for_over,
)

PROCESSED = ROOT / "data" / "processed"


@pytest.fixture(scope="module")
def deliveries() -> pd.DataFrame:
    return pd.read_csv(PROCESSED / "deliveries.csv", dtype={"season": str})


@pytest.fixture(scope="module")
def matches() -> pd.DataFrame:
    return pd.read_csv(PROCESSED / "matches.csv", dtype={"season": str})


# --- phases --------------------------------------------------------------

@pytest.mark.parametrize(
    "over,expected",
    [
        (0, "Powerplay"), (5, "Powerplay"),   # overs 1-6, zero-indexed
        (6, "Middle"), (14, "Middle"),        # overs 7-15
        (15, "Death"), (19, "Death"),         # overs 16-20
    ],
)
def test_phase_boundaries(over, expected):
    assert phase_for_over(over) == expected


# --- team aliasing -------------------------------------------------------

def test_renamed_franchises_map_to_one_name():
    assert canonical_team("Delhi Daredevils") == "Delhi Capitals"
    assert canonical_team("Kings XI Punjab") == "Punjab Kings"
    assert canonical_team("Chennai Super Kings") == "Chennai Super Kings"


def test_no_legacy_team_names_survive_in_the_panel(deliveries):
    legacy = {"Delhi Daredevils", "Kings XI Punjab",
              "Royal Challengers Bangalore"}
    found = set(deliveries["batting_team"].dropna().unique())
    assert not (legacy & found)


# --- parsing -------------------------------------------------------------

def make_match(deliveries: list[dict]) -> dict:
    return {
        "info": {
            "teams": ["Team A", "Team B"],
            "dates": ["2024-04-01"],
            "season": "2024",
            "venue": "Test Ground",
            "toss": {"winner": "Team A", "decision": "bat"},
            "outcome": {"winner": "Team A", "by": {"runs": 20}},
        },
        "innings": [{"team": "Team A", "overs": [{"over": 0, "deliveries": deliveries}]}],
    }


def test_wide_is_not_a_legal_delivery():
    data = make_match([
        {"batter": "X", "bowler": "Y", "non_striker": "Z",
         "runs": {"batter": 0, "extras": 1, "total": 1},
         "extras": {"wides": 1}},
    ])
    _, rows = parse_match("m1", data)
    assert rows[0]["is_legal_delivery"] is False
    assert rows[0]["wides"] == 1


def test_noball_is_not_a_legal_delivery():
    data = make_match([
        {"batter": "X", "bowler": "Y", "non_striker": "Z",
         "runs": {"batter": 4, "extras": 1, "total": 5},
         "extras": {"noballs": 1}},
    ])
    _, rows = parse_match("m1", data)
    assert rows[0]["is_legal_delivery"] is False
    assert rows[0]["is_four"] is True  # the batter still hit a four off it


def test_normal_delivery_is_legal():
    data = make_match([
        {"batter": "X", "bowler": "Y", "non_striker": "Z",
         "runs": {"batter": 1, "extras": 0, "total": 1}},
    ])
    _, rows = parse_match("m1", data)
    assert rows[0]["is_legal_delivery"] is True


def test_run_out_is_not_credited_to_the_bowler():
    data = make_match([
        {"batter": "X", "bowler": "Y", "non_striker": "Z",
         "runs": {"batter": 0, "extras": 0, "total": 0},
         "wickets": [{"player_out": "Z", "kind": "run out"}]},
    ])
    _, rows = parse_match("m1", data)
    assert rows[0]["is_wicket"] is True
    assert rows[0]["is_bowler_wicket"] is False


def test_bowled_is_credited_to_the_bowler():
    data = make_match([
        {"batter": "X", "bowler": "Y", "non_striker": "Z",
         "runs": {"batter": 0, "extras": 0, "total": 0},
         "wickets": [{"player_out": "X", "kind": "bowled"}]},
    ])
    _, rows = parse_match("m1", data)
    assert rows[0]["is_bowler_wicket"] is True


def test_every_non_bowler_dismissal_kind_is_excluded():
    for kind in NON_BOWLER_DISMISSALS:
        data = make_match([
            {"batter": "X", "bowler": "Y", "non_striker": "Z",
             "runs": {"batter": 0, "extras": 0, "total": 0},
             "wickets": [{"player_out": "X", "kind": kind}]},
        ])
        _, rows = parse_match("m1", data)
        assert rows[0]["is_bowler_wicket"] is False, kind


def test_six_is_flagged_only_for_runs_off_the_bat():
    """Six byes would not be a six for the batter."""
    data = make_match([
        {"batter": "X", "bowler": "Y", "non_striker": "Z",
         "runs": {"batter": 0, "extras": 6, "total": 6},
         "extras": {"byes": 6}},
    ])
    _, rows = parse_match("m1", data)
    assert rows[0]["is_six"] is False
    assert rows[0]["byes"] == 6


# --- the built panel -----------------------------------------------------

def test_runs_total_equals_batter_plus_extras(deliveries):
    computed = deliveries["runs_batter"] + deliveries["runs_extras"]
    assert (computed == deliveries["runs_total"]).all()


def test_extras_components_do_not_exceed_extras_total(deliveries):
    components = deliveries[["wides", "noballs", "byes", "legbyes"]].sum(axis=1)
    assert (components <= deliveries["runs_extras"]).all()


def test_bowler_wickets_are_a_subset_of_all_wickets(deliveries):
    assert deliveries["is_bowler_wicket"].sum() < deliveries["is_wicket"].sum()
    assert not (
        deliveries["is_bowler_wicket"] & ~deliveries["is_wicket"]
    ).any()


def test_every_wicket_names_the_player_out(deliveries):
    wickets = deliveries[deliveries["is_wicket"]]
    assert wickets["player_out"].notna().all()
    assert wickets["dismissal_kind"].notna().all()


def test_phase_column_matches_the_over_number(deliveries):
    expected = deliveries["over"].apply(phase_for_over)
    assert (deliveries["phase"] == expected).all()


def test_season_year_is_derived_from_the_date_not_the_label(matches):
    """
    Cricsheet labels the 2008 season "2007/08" and the 2010 season "2009/10".
    Taking the first half of the label would put IPL matches in 1994-style
    wrong years, so the year must come from the date.
    """
    from_date = pd.to_datetime(matches["date"]).dt.year
    assert (matches["season_year"] == from_date).all()
    assert matches["season_year"].min() == 2008  # the first IPL season


def test_no_season_predates_the_first_ipl(matches):
    assert (matches["season_year"] >= 2008).all()


def test_every_delivery_belongs_to_a_known_match(deliveries, matches):
    assert set(deliveries["match_id"]) <= set(matches["match_id"])


def test_innings_numbers_are_sane(deliveries):
    """Two innings normally, more only where a super over was played."""
    normal = deliveries[~deliveries["is_super_over"]]
    assert normal["innings"].max() <= 2


def test_runs_off_a_single_ball_are_plausible(deliveries):
    assert deliveries["runs_batter"].between(0, 6).all()
    assert deliveries["runs_total"].between(0, 12).all()


def test_overs_stay_within_a_twenty_over_innings(deliveries):
    normal = deliveries[~deliveries["is_super_over"]]
    assert normal["over"].between(0, 19).all()
