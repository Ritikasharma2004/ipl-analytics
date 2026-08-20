"""
Streamlit dashboard for the IPL ball-by-ball analysis.

Run with:
    streamlit run dashboard/app.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"

PHASE_ORDER = ["Powerplay", "Middle", "Death"]
PHASE_COLOURS = {"Powerplay": "#2166ac", "Middle": "#666666", "Death": "#b2182b"}
IMPACT_PLAYER_FROM = 2023

st.set_page_config(page_title="IPL Analytics", page_icon="IPL", layout="wide")


@st.cache_data
def load_deliveries() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED_DIR / "deliveries.csv", dtype={"season": str})
    df = df[~df["is_super_over"]].copy()
    df["is_ball_faced"] = df["wides"] == 0
    df["runs_conceded"] = df["runs_total"] - df["byes"] - df["legbyes"]
    return df


@st.cache_data
def load_matches() -> pd.DataFrame:
    return pd.read_csv(PROCESSED_DIR / "matches.csv", dtype={"season": str})


@st.cache_data
def load_trends() -> pd.DataFrame:
    return pd.read_csv(PROCESSED_DIR / "season_trends.csv", index_col="season_year")


deliveries = load_deliveries()
matches = load_matches()
trends = load_trends()

st.title("IPL Ball-by-Ball Analytics")
st.caption(
    f"{deliveries['is_legal_delivery'].sum():,} legal deliveries · "
    f"{matches['match_id'].nunique():,} matches · "
    f"IPL {matches['season_year'].min()}–{matches['season_year'].max()} · "
    "Source: Cricsheet. Built by Ritika Sharma."
)

with st.sidebar:
    st.header("Filters")
    seasons = st.slider(
        "Seasons",
        int(matches["season_year"].min()), int(matches["season_year"].max()),
        (int(matches["season_year"].min()), int(matches["season_year"].max())),
    )
    min_balls = st.number_input(
        "Minimum balls for player tables", 50, 1000, 200, step=50
    )
    st.markdown("---")
    st.caption(
        "Balls faced exclude wides but include no-balls. Balls bowled exclude "
        "both. Runs conceded exclude byes and leg-byes. Super overs are "
        "excluded throughout."
    )

df = deliveries[deliveries["season_year"].between(*seasons)]
mt = matches[matches["season_year"].between(*seasons)]

tabs = st.tabs(
    ["Scoring trends", "Phases", "Batters", "Bowlers", "Matchups", "Toss", "Method"]
)


with tabs[0]:
    c1, c2, c3, c4 = st.columns(4)
    legal = df["is_legal_delivery"].sum()
    c1.metric("Matches", f"{df['match_id'].nunique():,}")
    c2.metric("Run rate", f"{df['runs_total'].sum() / legal * 6:.2f}")
    c3.metric("Boundary %",
              f"{(df['is_four'].sum() + df['is_six'].sum()) / legal * 100:.1f}%")
    c4.metric("Dot %", f"{df['is_dot'].sum() / legal * 100:.1f}%")

    metric = st.selectbox(
        "Metric",
        ["run_rate", "boundary_pct", "dot_pct", "sixes_per_match"],
        format_func=lambda c: {
            "run_rate": "Runs per over", "boundary_pct": "Boundary balls (%)",
            "dot_pct": "Dot balls (%)", "sixes_per_match": "Sixes per match",
        }[c],
    )
    shown = trends.loc[seasons[0]:seasons[1]]
    fig = px.line(
        shown.reset_index(), x="season_year", y=metric, markers=True, height=430,
        labels={"season_year": "", metric: ""},
    )
    if seasons[0] < IMPACT_PLAYER_FROM <= seasons[1]:
        fig.add_vline(
            x=IMPACT_PLAYER_FROM - 0.5, line_dash="dash", line_color="#e6550d",
            annotation_text="Impact Player rule", annotation_font_size=10,
        )
    st.plotly_chart(fig, width="stretch")

    if seasons[0] < IMPACT_PLAYER_FROM <= seasons[1]:
        pre = trends.loc[seasons[0]:IMPACT_PLAYER_FROM - 1, "run_rate"].tail(5).mean()
        post = trends.loc[IMPACT_PLAYER_FROM:seasons[1], "run_rate"].mean()
        st.info(
            f"Run rate averaged **{pre:.2f}** in the five seasons before the "
            f"Impact Player rule and **{post:.2f}** from 2023 onwards "
            f"(**{post - pre:+.2f}** runs per over). The timing fits, but a "
            "rule change is not the only thing that moved in 2023 — this is "
            "an association in a time series, not a controlled experiment."
        )

    st.dataframe(shown.round(2), width="stretch")


with tabs[1]:
    phase = (
        df.groupby("phase")
        .agg(balls=("is_legal_delivery", "sum"), runs=("runs_total", "sum"),
             wickets=("is_wicket", "sum"), fours=("is_four", "sum"),
             sixes=("is_six", "sum"), dots=("is_dot", "sum"))
        .reindex(PHASE_ORDER)
    )
    phase["run_rate"] = (phase["runs"] / phase["balls"] * 6).round(2)
    phase["balls_per_wicket"] = (phase["balls"] / phase["wickets"]).round(1)
    phase["boundary_pct"] = (
        (phase["fours"] + phase["sixes"]) / phase["balls"] * 100
    ).round(1)
    phase["dot_pct"] = (phase["dots"] / phase["balls"] * 100).round(1)

    cols = st.columns(3)
    for col, name in zip(cols, PHASE_ORDER):
        col.metric(f"{name} run rate", f"{phase.loc[name, 'run_rate']:.2f}",
                   help=f"A wicket every {phase.loc[name, 'balls_per_wicket']:.1f} balls")

    st.dataframe(
        phase[["balls", "run_rate", "boundary_pct", "dot_pct", "balls_per_wicket"]],
        width="stretch",
    )

    by_season = (
        df.groupby(["season_year", "phase"])
        .agg(runs=("runs_total", "sum"), balls=("is_legal_delivery", "sum"))
        .reset_index()
    )
    by_season["run_rate"] = by_season["runs"] / by_season["balls"] * 6
    fig = px.line(
        by_season, x="season_year", y="run_rate", color="phase", markers=True,
        height=440, color_discrete_map=PHASE_COLOURS,
        category_orders={"phase": PHASE_ORDER},
        labels={"run_rate": "Runs per over", "season_year": ""},
    )
    st.plotly_chart(fig, width="stretch")


with tabs[2]:
    faced = df[df["is_ball_faced"]]
    grouped = faced.groupby(["batter", "phase"])
    batters = pd.DataFrame({
        "balls": grouped.size(),
        "runs": grouped["runs_batter"].sum(),
        "dismissals": grouped["is_wicket"].sum(),
        "fours": grouped["is_four"].sum(),
        "sixes": grouped["is_six"].sum(),
        "dots": grouped["is_dot"].sum(),
    }).reset_index()
    batters = batters[batters["balls"] >= min_balls].copy()
    batters["strike_rate"] = (batters["runs"] / batters["balls"] * 100).round(1)
    batters["balls_per_dismissal"] = (
        batters["balls"] / batters["dismissals"].replace(0, np.nan)
    ).round(1)
    batters["boundary_pct"] = (
        (batters["fours"] + batters["sixes"]) / batters["balls"] * 100
    ).round(1)
    batters["dot_pct"] = (batters["dots"] / batters["balls"] * 100).round(1)

    # A warning is enough here; st.stop() would halt every other tab too.
    if batters.empty:
        st.warning("No batter clears the minimum-balls threshold in this range.")
        subset = batters
        chosen_phase = PHASE_ORDER[2]
    else:
        chosen_phase = st.selectbox("Phase", PHASE_ORDER, index=2)
        subset = batters[batters["phase"] == chosen_phase]

    if not subset.empty:
        fig = px.scatter(
            subset, x="balls_per_dismissal", y="strike_rate", size="balls",
            color="boundary_pct", hover_name="batter", height=520,
            color_continuous_scale="YlOrRd",
            labels={"balls_per_dismissal": "Balls per dismissal (survival)",
                    "strike_rate": "Strike rate", "boundary_pct": "Boundary %"},
        )
        fig.add_hline(y=subset["strike_rate"].median(), line_dash="dash",
                      line_color="#888")
        fig.add_vline(x=subset["balls_per_dismissal"].median(), line_dash="dash",
                      line_color="#888")
        fig.update_layout(title=f"{chosen_phase}: scoring speed against survival")
        st.plotly_chart(fig, width="stretch")

    st.subheader("Where is each batter weakest?")
    st.markdown(
        "For batters with a record in all three phases, the phase where their "
        "strike rate sits furthest below **the league average for that same "
        "phase**. Comparing a batter's death strike rate to their own "
        "powerplay number would tell you nothing — everyone scores faster at "
        "the death."
    )

    league = batters.groupby("phase").apply(
        lambda g: g["runs"].sum() / g["balls"].sum() * 100, include_groups=False
    )
    batters["league_sr"] = batters["phase"].map(league).round(1)
    batters["vs_league"] = (batters["strike_rate"] - batters["league_sr"]).round(1)

    complete = batters.groupby("batter")["phase"].nunique()
    complete = complete[complete == 3].index
    full = batters[batters["batter"].isin(complete)]

    if full.empty:
        st.info("No batter has a qualifying record in all three phases here.")
    else:
        weakest = full.loc[full.groupby("batter")["vs_league"].idxmin()]
        st.dataframe(
            weakest[["batter", "phase", "balls", "strike_rate", "league_sr",
                     "vs_league", "dot_pct", "balls_per_dismissal"]]
            .sort_values("vs_league").head(25),
            width="stretch", hide_index=True,
        )


with tabs[3]:
    legal = df[df["is_legal_delivery"]]
    grouped = legal.groupby(["bowler", "phase"])
    bowlers = pd.DataFrame({
        "balls": grouped.size(),
        "runs": grouped["runs_conceded"].sum(),
        "wickets": grouped["is_bowler_wicket"].sum(),
        "dots": grouped["is_dot"].sum(),
    }).reset_index()
    bowlers = bowlers[bowlers["balls"] >= min_balls].copy()
    bowlers["economy"] = (bowlers["runs"] / bowlers["balls"] * 6).round(2)
    bowlers["strike_rate"] = (
        bowlers["balls"] / bowlers["wickets"].replace(0, np.nan)
    ).round(1)
    bowlers["dot_pct"] = (bowlers["dots"] / bowlers["balls"] * 100).round(1)

    if bowlers.empty:
        st.warning("No bowler clears the minimum-balls threshold in this range.")
    else:
        chosen = st.selectbox("Phase ", PHASE_ORDER, index=2, key="bowl_phase")
        subset = bowlers[bowlers["phase"] == chosen].nsmallest(20, "economy")

        fig = px.bar(
            subset.sort_values("economy", ascending=False),
            x="economy", y="bowler", orientation="h", color="dot_pct",
            color_continuous_scale="Blues", height=max(400, 26 * len(subset)),
            labels={"economy": "Economy rate", "bowler": "", "dot_pct": "Dot %"},
        )
        league_econ = (
            bowlers[bowlers["phase"] == chosen]["runs"].sum()
            / bowlers[bowlers["phase"] == chosen]["balls"].sum() * 6
        )
        fig.add_vline(x=league_econ, line_dash="dash", line_color="#b2182b",
                      annotation_text=f"league {league_econ:.2f}")
        st.plotly_chart(fig, width="stretch")

        st.dataframe(
            subset[["bowler", "balls", "economy", "wickets", "strike_rate",
                    "dot_pct"]],
            width="stretch", hide_index=True,
        )


with tabs[4]:
    st.subheader("Batter versus bowler")
    st.markdown(
        "Head-to-head records. Small samples are the trap here — a batter who "
        "faced a bowler twelve times and got out once has no meaningful "
        "record against them, so the threshold below is deliberately blunt."
    )
    min_matchup = st.slider("Minimum balls in the matchup", 20, 150, 60, step=10)

    faced = df[df["is_ball_faced"]]
    grouped = faced.groupby(["batter", "bowler"])
    matchups = pd.DataFrame({
        "balls": grouped.size(),
        "runs": grouped["runs_batter"].sum(),
        "dismissals": grouped["is_wicket"].sum(),
        "dots": grouped["is_dot"].sum(),
    }).reset_index()
    matchups = matchups[matchups["balls"] >= min_matchup].copy()

    if matchups.empty:
        st.info("No matchup reaches that threshold in this season range.")
    else:
        matchups["strike_rate"] = (
            matchups["runs"] / matchups["balls"] * 100
        ).round(1)
        matchups["balls_per_dismissal"] = (
            matchups["balls"] / matchups["dismissals"].replace(0, np.nan)
        ).round(1)
        matchups["dot_pct"] = (matchups["dots"] / matchups["balls"] * 100).round(1)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Bowler on top** (lowest strike rate conceded)")
            st.dataframe(
                matchups.nsmallest(15, "strike_rate")[
                    ["batter", "bowler", "balls", "runs", "dismissals",
                     "strike_rate"]
                ],
                width="stretch", hide_index=True,
            )
        with c2:
            st.markdown("**Batter on top** (highest strike rate)")
            st.dataframe(
                matchups.nlargest(15, "strike_rate")[
                    ["batter", "bowler", "balls", "runs", "dismissals",
                     "strike_rate"]
                ],
                width="stretch", hide_index=True,
            )

        st.markdown("---")
        player = st.selectbox(
            "Look up a batter", sorted(matchups["batter"].unique())
        )
        st.dataframe(
            matchups[matchups["batter"] == player]
            .sort_values("strike_rate")[
                ["bowler", "balls", "runs", "dismissals", "strike_rate",
                 "dot_pct", "balls_per_dismissal"]
            ],
            width="stretch", hide_index=True,
        )


with tabs[5]:
    decided = mt[mt["winner"].notna() & mt["toss_winner"].notna()].copy()
    decided["toss_winner_won"] = decided["toss_winner"] == decided["winner"]

    if decided.empty:
        st.info("No decided matches in this range.")
    else:
        overall = decided["toss_winner_won"].mean() * 100
        field = decided[decided["toss_decision"] == "field"]
        bat = decided[decided["toss_decision"] == "bat"]

        c1, c2, c3 = st.columns(3)
        c1.metric("Toss winner wins", f"{overall:.1f}%",
                  help=f"{len(decided):,} decided matches")
        if len(field):
            c2.metric("Chose to field", f"{field['toss_winner_won'].mean() * 100:.1f}%",
                      help=f"{len(field):,} matches")
        if len(bat):
            c3.metric("Chose to bat", f"{bat['toss_winner_won'].mean() * 100:.1f}%",
                      help=f"{len(bat):,} matches")

        by_season = (
            decided.groupby("season_year")["toss_winner_won"].mean() * 100
        ).reset_index()
        fig = px.bar(
            by_season, x="season_year", y="toss_winner_won", height=400,
            labels={"toss_winner_won": "Toss winner win rate (%)",
                    "season_year": ""},
        )
        fig.add_hline(y=50, line_dash="dash", line_color="#b2182b")
        fig.update_yaxes(range=[0, 100])
        st.plotly_chart(fig, width="stretch")

        st.info(
            "Winning the toss is close to a coin flip. **The decision made "
            "after it is not.** Across the full history, captains who chose "
            "to field won 54.7% and those who chose to bat won 45.3% — a "
            "9.4-point gap, consistent with evening dew making the chase "
            "easier.\n\n"
            "This is not proof that fielding causes wins. Captains choose "
            "based on conditions, so part of the gap is the conditions that "
            "prompted the choice."
        )


with tabs[6]:
    st.markdown(
        """
### Scoring conventions

These decide every rate on this dashboard, so they are stated rather than
assumed:

| Measure | Rule applied |
|---|---|
| Balls faced (batter) | Excludes wides, includes no-balls |
| Balls bowled (bowler) | Excludes wides and no-balls |
| Runs conceded (bowler) | Excludes byes and leg-byes |
| Wickets (bowler) | Excludes run-outs and retirements |
| Super overs | Excluded from every per-over statistic |

Getting these wrong is the most common way a cricket analysis goes quietly
astray: counting wides in a bowler's denominator flatters their economy,
and crediting run-outs to bowlers flatters strike bowlers.

### Phases

Powerplay is overs 1–6, middle 7–15, death 16–20. Comparisons between players
are always made **within** a phase, because the three are effectively
different games — the death overs score roughly twice as fast as the middle
and cost a wicket far more often.

### Season labelling

Cricsheet labels some seasons across two years (`2007/08`, `2009/10`), and the
label does not reliably name the year the cricket was played: `2007/08` was
played in 2008 and `2009/10` in 2010. Season year is therefore derived from
the match date, which is correct for every season including the displaced 2020
edition played in September–November.

### Data

[Cricsheet](https://cricsheet.org) ball-by-ball archive, all IPL matches.
Freely available under the Open Data Commons Attribution License.

### Limitations

- **No ball-tracking.** Cricsheet records outcomes, not line, length, pace or
  shot type. This dashboard can show *that* a batter struggles in a phase, not
  *why*.
- **Bowling style is not in the data**, so a spin-versus-pace breakdown would
  need a separate player-attributes source joined on name.
- **Minimum-ball thresholds are judgement calls** and change who appears.
        """
    )
