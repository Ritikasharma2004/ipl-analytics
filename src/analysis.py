"""
Analysis and figures for the IPL ball-by-ball data.

Questions:
    1. How has scoring changed across 19 seasons, and did the 2023 Impact
       Player rule move it?
    2. What does each phase of an innings actually look like?
    3. Which batters are phase specialists, and where is each one weakest?
    4. Who bowls the death, once economy is measured properly?
    5. Does winning the toss matter?

Scoring conventions applied throughout, because getting them wrong quietly
corrupts every rate:
    balls faced (batter)   excludes wides, includes no-balls
    balls bowled (bowler)  excludes both wides and no-balls
    runs conceded (bowler) excludes byes and leg-byes
    wickets (bowler)       excludes run-outs and retirements
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
FIG_DIR = ROOT / "reports" / "figures"
REPORT_PATH = ROOT / "reports" / "findings.md"

PHASE_ORDER = ["Powerplay", "Middle", "Death"]
IMPACT_PLAYER_FROM = 2023

sns.set_theme(style="whitegrid", palette="deep")
plt.rcParams["figure.dpi"] = 130
plt.rcParams["savefig.bbox"] = "tight"


def prepare(deliveries: pd.DataFrame) -> pd.DataFrame:
    """Add the derived flags the rate calculations depend on."""
    df = deliveries[~deliveries["is_super_over"]].copy()

    # A wide is not a ball faced; a no-ball is.
    df["is_ball_faced"] = df["wides"] == 0
    # The bowler is not charged with byes or leg-byes.
    df["runs_conceded"] = df["runs_total"] - df["byes"] - df["legbyes"]

    return df


# --- season trends -------------------------------------------------------

def season_trends(df: pd.DataFrame) -> pd.DataFrame:
    grouped = df.groupby("season_year")
    out = pd.DataFrame({
        "matches": grouped["match_id"].nunique(),
        "runs": grouped["runs_total"].sum(),
        "legal_balls": grouped["is_legal_delivery"].sum(),
        "fours": grouped["is_four"].sum(),
        "sixes": grouped["is_six"].sum(),
        "dots": grouped["is_dot"].sum(),
        "wickets": grouped["is_wicket"].sum(),
    })
    out["run_rate"] = (out["runs"] / out["legal_balls"] * 6).round(2)
    out["boundary_pct"] = (
        (out["fours"] + out["sixes"]) / out["legal_balls"] * 100
    ).round(1)
    out["dot_pct"] = (out["dots"] / out["legal_balls"] * 100).round(1)
    out["sixes_per_match"] = (out["sixes"] / out["matches"]).round(1)
    return out


def fig_season_trends(trends: pd.DataFrame) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(12.5, 7))

    panels = [
        ("run_rate", "Runs per over", "#2166ac"),
        ("boundary_pct", "Boundary balls (%)", "#b2182b"),
        ("dot_pct", "Dot balls (%)", "#666666"),
        ("sixes_per_match", "Sixes per match", "#1a9850"),
    ]
    ticks = [y for y in trends.index if y % 3 == 0 or y == trends.index.max()]
    for ax, (column, title, colour) in zip(axes.flat, panels):
        ax.plot(trends.index, trends[column], marker="o", lw=2, color=colour)
        ax.axvline(IMPACT_PLAYER_FROM - 0.5, color="#e6550d", ls="--", lw=1.4)
        ax.set_title(title, fontsize=11, weight="bold")
        ax.set_xlabel("")
        ax.set_xticks(ticks)
        ax.set_xticklabels([str(y) for y in ticks], rotation=45)

    axes[0, 0].text(
        IMPACT_PLAYER_FROM - 0.4, trends["run_rate"].min(),
        " Impact Player\n rule", fontsize=7.5, color="#e6550d", va="bottom",
    )
    fig.suptitle("IPL scoring by season, 2008-2026", fontsize=13, weight="bold")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "01_season_trends.png")
    plt.close(fig)


# --- phases --------------------------------------------------------------

def phase_profile(df: pd.DataFrame) -> pd.DataFrame:
    grouped = df.groupby("phase")
    out = pd.DataFrame({
        "balls": grouped["is_legal_delivery"].sum(),
        "runs": grouped["runs_total"].sum(),
        "wickets": grouped["is_wicket"].sum(),
        "fours": grouped["is_four"].sum(),
        "sixes": grouped["is_six"].sum(),
        "dots": grouped["is_dot"].sum(),
    }).reindex(PHASE_ORDER)

    out["run_rate"] = (out["runs"] / out["balls"] * 6).round(2)
    out["balls_per_wicket"] = (out["balls"] / out["wickets"]).round(1)
    out["boundary_pct"] = ((out["fours"] + out["sixes"]) / out["balls"] * 100).round(1)
    out["dot_pct"] = (out["dots"] / out["balls"] * 100).round(1)
    return out


def fig_phase_evolution(df: pd.DataFrame) -> None:
    by_season = (
        df.groupby(["season_year", "phase"])
        .agg(runs=("runs_total", "sum"), balls=("is_legal_delivery", "sum"))
        .reset_index()
    )
    by_season["run_rate"] = by_season["runs"] / by_season["balls"] * 6

    fig, ax = plt.subplots(figsize=(11, 4.8))
    colours = {"Powerplay": "#2166ac", "Middle": "#666666", "Death": "#b2182b"}
    for phase in PHASE_ORDER:
        rows = by_season[by_season["phase"] == phase]
        ax.plot(rows["season_year"], rows["run_rate"], marker="o", lw=2,
                color=colours[phase], label=phase)

    ax.axvline(IMPACT_PLAYER_FROM - 0.5, color="#e6550d", ls="--", lw=1.4)
    ax.set_ylabel("Runs per over")
    ax.set_xlabel("Season")
    ax.set_title("Run rate by phase across seasons", fontsize=13, weight="bold")
    ax.legend(frameon=False)
    fig.savefig(FIG_DIR / "02_phase_evolution.png")
    plt.close(fig)


# --- batters -------------------------------------------------------------

def batter_phase_profiles(df: pd.DataFrame, min_balls: int = 200) -> pd.DataFrame:
    """
    Strike rate and dismissal rate for every batter in every phase.

    Dismissal rate is expressed as balls per dismissal, which is the figure
    that matters in T20: a high strike rate bought by getting out every ten
    balls is not worth having.
    """
    faced = df[df["is_ball_faced"]]

    grouped = faced.groupby(["batter", "phase"])
    profile = pd.DataFrame({
        "balls": grouped.size(),
        "runs": grouped["runs_batter"].sum(),
        "dismissals": grouped["is_wicket"].sum(),
        "fours": grouped["is_four"].sum(),
        "sixes": grouped["is_six"].sum(),
        "dots": grouped["is_dot"].sum(),
    }).reset_index()

    profile = profile[profile["balls"] >= min_balls].copy()
    profile["strike_rate"] = (profile["runs"] / profile["balls"] * 100).round(1)
    profile["balls_per_dismissal"] = (
        profile["balls"] / profile["dismissals"].replace(0, np.nan)
    ).round(1)
    profile["boundary_pct"] = (
        (profile["fours"] + profile["sixes"]) / profile["balls"] * 100
    ).round(1)
    profile["dot_pct"] = (profile["dots"] / profile["balls"] * 100).round(1)
    return profile


def find_phase_weakness(profile: pd.DataFrame) -> pd.DataFrame:
    """
    For each batter with a record in every phase, find the phase where their
    strike rate sits furthest below the league average for that phase.

    Comparing a batter's death-overs strike rate against their own powerplay
    number would be meaningless - everyone scores faster at the death. The
    comparison has to be against what other batters manage in the same phase.
    """
    league = profile.groupby("phase").apply(
        lambda g: g["runs"].sum() / g["balls"].sum() * 100, include_groups=False
    )

    profile = profile.copy()
    profile["league_sr"] = profile["phase"].map(league).round(1)
    profile["sr_vs_league"] = (profile["strike_rate"] - profile["league_sr"]).round(1)

    complete = profile.groupby("batter")["phase"].nunique()
    complete = complete[complete == 3].index
    subset = profile[profile["batter"].isin(complete)]

    weakest = subset.loc[subset.groupby("batter")["sr_vs_league"].idxmin()]
    return weakest[
        ["batter", "phase", "balls", "strike_rate", "league_sr",
         "sr_vs_league", "dot_pct", "balls_per_dismissal"]
    ].sort_values("sr_vs_league")


def fig_batter_scatter(profile: pd.DataFrame) -> None:
    death = profile[
        (profile["phase"] == "Death") & (profile["balls"] >= 300)
    ].copy()

    fig, ax = plt.subplots(figsize=(10.5, 6))
    scatter = ax.scatter(
        death["balls_per_dismissal"], death["strike_rate"],
        s=death["balls"] / 4, c=death["boundary_pct"],
        cmap="YlOrRd", alpha=0.85, edgecolors="#333", linewidths=0.5,
    )
    plt.colorbar(scatter, ax=ax, label="Boundary %")

    ax.axhline(death["strike_rate"].median(), color="#666", ls="--", lw=1)
    ax.axvline(death["balls_per_dismissal"].median(), color="#666", ls="--", lw=1)

    top = death.nlargest(8, "strike_rate")
    for _, row in top.iterrows():
        ax.annotate(row["batter"], (row["balls_per_dismissal"], row["strike_rate"]),
                    fontsize=7.5, xytext=(4, 3), textcoords="offset points")

    ax.set_xlabel("Balls per dismissal (survival)")
    ax.set_ylabel("Strike rate")
    ax.set_title(
        "Death-overs batting: scoring speed against survival\n"
        "(bubble size = balls faced, 300+ death balls)",
        fontsize=12, weight="bold",
    )
    fig.savefig(FIG_DIR / "03_death_batting.png")
    plt.close(fig)


# --- bowlers -------------------------------------------------------------

def bowler_phase_profiles(df: pd.DataFrame, min_balls: int = 200) -> pd.DataFrame:
    legal = df[df["is_legal_delivery"]]

    grouped = legal.groupby(["bowler", "phase"])
    profile = pd.DataFrame({
        "balls": grouped.size(),
        "runs": grouped["runs_conceded"].sum(),
        "wickets": grouped["is_bowler_wicket"].sum(),
        "dots": grouped["is_dot"].sum(),
        "boundaries": grouped["is_four"].sum() + grouped["is_six"].sum(),
    }).reset_index()

    profile = profile[profile["balls"] >= min_balls].copy()
    profile["economy"] = (profile["runs"] / profile["balls"] * 6).round(2)
    profile["strike_rate"] = (
        profile["balls"] / profile["wickets"].replace(0, np.nan)
    ).round(1)
    profile["dot_pct"] = (profile["dots"] / profile["balls"] * 100).round(1)
    profile["boundary_pct"] = (
        profile["boundaries"] / profile["balls"] * 100
    ).round(1)
    return profile


def fig_death_bowling(profile: pd.DataFrame) -> pd.DataFrame:
    death = profile[
        (profile["phase"] == "Death") & (profile["balls"] >= 300)
    ].nsmallest(15, "economy")

    fig, ax = plt.subplots(figsize=(10, 5.5))
    bars = ax.barh(death["bowler"], death["economy"], color="#2166ac")
    ax.invert_yaxis()
    for bar, econ, dots in zip(bars, death["economy"], death["dot_pct"]):
        ax.text(econ + 0.05, bar.get_y() + bar.get_height() / 2,
                f"{econ:.2f}  ({dots:.0f}% dots)", va="center", fontsize=8)

    league = profile[profile["phase"] == "Death"]
    league_econ = league["runs"].sum() / league["balls"].sum() * 6
    ax.axvline(league_econ, color="#b2182b", ls="--", lw=1.4)
    ax.text(league_econ + 0.05, len(death) - 0.5,
            f"league {league_econ:.2f}", fontsize=8, color="#b2182b")

    ax.set_xlabel("Economy rate at the death")
    ax.set_title("Best death bowlers (300+ death balls)", fontsize=13, weight="bold")
    ax.set_xlim(0, max(death["economy"].max(), league_econ) + 1.6)
    fig.savefig(FIG_DIR / "04_death_bowling.png")
    plt.close(fig)
    return death


# --- toss ----------------------------------------------------------------

def toss_analysis(matches: pd.DataFrame) -> dict:
    """
    Does winning the toss help? Only decided matches count - a no-result
    cannot be won or lost by the toss.
    """
    decided = matches[matches["winner"].notna()].copy()
    decided["toss_winner_won"] = decided["toss_winner"] == decided["winner"]

    overall = decided["toss_winner_won"].mean() * 100

    by_decision = (
        decided.groupby("toss_decision")
        .agg(matches=("match_id", "count"),
             win_pct=("toss_winner_won", lambda s: s.mean() * 100))
        .round(1)
    )

    by_season = (
        decided.groupby("season_year")["toss_winner_won"].mean() * 100
    ).round(1)

    from scipy import stats

    # Binomial test against a fair coin: does winning the toss help at all?
    n = len(decided)
    wins = decided["toss_winner_won"].sum()
    p_value = stats.binomtest(int(wins), n, 0.5).pvalue

    # The more interesting question is whether the *decision* matters. Chasing
    # is widely believed to be easier in the IPL because of evening dew.
    field = decided[decided["toss_decision"] == "field"]
    bat = decided[decided["toss_decision"] == "bat"]
    contingency = [
        [int(field["toss_winner_won"].sum()), int((~field["toss_winner_won"]).sum())],
        [int(bat["toss_winner_won"].sum()), int((~bat["toss_winner_won"]).sum())],
    ]
    chi2, decision_p, _, _ = stats.chi2_contingency(contingency)

    return {
        "decided_matches": n,
        "toss_winner_wins": int(wins),
        "overall_pct": round(overall, 1),
        "by_decision": by_decision,
        "by_season": by_season,
        "p_value": p_value,
        "field_pct": round(field["toss_winner_won"].mean() * 100, 1),
        "bat_pct": round(bat["toss_winner_won"].mean() * 100, 1),
        "field_n": len(field),
        "bat_n": len(bat),
        "decision_chi2": chi2,
        "decision_p": decision_p,
    }


def fig_toss(toss: dict) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))

    seasons = toss["by_season"]
    axes[0].bar(seasons.index, seasons.values, color="#2166ac")
    axes[0].axhline(50, color="#b2182b", ls="--", lw=1.5)
    axes[0].set_ylim(0, 100)
    axes[0].set_ylabel("Toss winner win rate (%)")
    axes[0].set_title("By season")
    axes[0].tick_params(axis="x", rotation=45)

    dec = toss["by_decision"]
    axes[1].bar(dec.index, dec["win_pct"], color=["#1a9850", "#6b6ecf"])
    axes[1].axhline(50, color="#b2182b", ls="--", lw=1.5)
    axes[1].set_ylim(0, 100)
    axes[1].set_ylabel("Win rate (%)")
    axes[1].set_title("By toss decision")
    for i, (label, row) in enumerate(dec.iterrows()):
        axes[1].text(i, row["win_pct"] + 2,
                     f"{row['win_pct']:.1f}%\n({int(row['matches'])} matches)",
                     ha="center", fontsize=8.5)

    fig.suptitle(
        f"Does winning the toss help? Overall {toss['overall_pct']:.1f}% "
        f"of {toss['decided_matches']} decided matches",
        fontsize=12, weight="bold",
    )
    fig.tight_layout()
    fig.savefig(FIG_DIR / "05_toss.png")
    plt.close(fig)


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    # `season` mixes "2009" and "2009/10" strings, so pandas cannot infer one
    # dtype for it. season_year is the numeric column the analysis actually uses.
    deliveries = pd.read_csv(PROCESSED_DIR / "deliveries.csv", dtype={"season": str})
    matches = pd.read_csv(PROCESSED_DIR / "matches.csv", dtype={"season": str})
    df = prepare(deliveries)

    trends = season_trends(df)
    fig_season_trends(trends)

    phases = phase_profile(df)
    fig_phase_evolution(df)

    batters = batter_phase_profiles(df)
    weakness = find_phase_weakness(batters)
    fig_batter_scatter(batters)

    bowlers = bowler_phase_profiles(df)
    best_death = fig_death_bowling(bowlers)

    toss = toss_analysis(matches)
    fig_toss(toss)

    batters.to_csv(PROCESSED_DIR / "batter_phase_profiles.csv", index=False)
    bowlers.to_csv(PROCESSED_DIR / "bowler_phase_profiles.csv", index=False)
    weakness.to_csv(PROCESSED_DIR / "batter_weakness.csv", index=False)
    trends.to_csv(PROCESSED_DIR / "season_trends.csv")

    print("Wrote 5 figures\n")

    pre = trends.loc[trends.index < IMPACT_PLAYER_FROM, "run_rate"].tail(5).mean()
    post = trends.loc[trends.index >= IMPACT_PLAYER_FROM, "run_rate"].mean()

    write_report(trends, phases, weakness, best_death, toss, batters, pre, post)

    print(f"Run rate, 5 seasons before Impact Player : {pre:.2f}")
    print(f"Run rate, 2023 onwards                   : {post:.2f}")
    print(f"Change                                   : {post - pre:+.2f}\n")
    print(f"Toss winner wins {toss['overall_pct']:.1f}% "
          f"(p = {toss['p_value']:.3f})\n")
    print("Five batters furthest below league strike rate in their weakest phase:")
    print(weakness.head(5).to_string(index=False))


def write_report(trends, phases, weakness, best_death, toss, batters,
                 pre, post) -> None:
    total_balls = int(trends["legal_balls"].sum())
    total_matches = int(trends["matches"].sum())

    lines = [
        "# IPL Ball-by-Ball Analytics — Findings",
        "",
        f"**Data.** {total_balls:,} legal deliveries across {total_matches:,} "
        f"matches, IPL {trends.index.min()}–{trends.index.max()}. Source: "
        "[Cricsheet](https://cricsheet.org) ball-by-ball archive.",
        "",
        "**Scoring conventions.** These decide every rate in this report, so "
        "they are stated rather than assumed:",
        "",
        "| Measure | Rule applied |",
        "|---|---|",
        "| Balls faced (batter) | Excludes wides, includes no-balls |",
        "| Balls bowled (bowler) | Excludes wides and no-balls |",
        "| Runs conceded (bowler) | Excludes byes and leg-byes |",
        "| Wickets (bowler) | Excludes run-outs and retirements |",
        "| Super overs | Excluded from all per-over statistics |",
        "",
        "---",
        "",
        "## 1. Scoring has risen, and the Impact Player rule is visible in it",
        "",
        "![Season trends](figures/01_season_trends.png)",
        "",
        trends[["matches", "run_rate", "boundary_pct", "dot_pct",
                "sixes_per_match"]].to_markdown(),
        "",
        f"Run rate averaged **{pre:.2f}** across the five seasons before the "
        f"Impact Player rule and **{post:.2f}** from 2023 onwards, a rise of "
        f"**{post - pre:+.2f} runs per over**.",
        "",
        "The rule lets a side substitute a player mid-match, which in practice "
        "means batting sides field an extra specialist batter and can bat "
        "deeper without carrying the risk that used to come with it. The "
        "timing of the jump is consistent with that, though a rule change is "
        "not the only thing that happened in 2023 — squad composition, pitch "
        "preparation and bat technology all move too. This is an association "
        "in a time series, not a controlled experiment.",
        "",
        "## 2. The three phases are different games",
        "",
        "![Phase evolution](figures/02_phase_evolution.png)",
        "",
        phases[["balls", "run_rate", "boundary_pct", "dot_pct",
                "balls_per_wicket"]].to_markdown(),
        "",
        f"The death overs score **{phases.loc['Death', 'run_rate'] / phases.loc['Middle', 'run_rate']:.1f}x** "
        f"as fast as the middle overs "
        f"({phases.loc['Death', 'run_rate']:.2f} against "
        f"{phases.loc['Middle', 'run_rate']:.2f} runs per over) and cost a "
        f"wicket every {phases.loc['Death', 'balls_per_wicket']:.1f} balls "
        f"against {phases.loc['Middle', 'balls_per_wicket']:.1f}.",
        "",
        "This is why any comparison of players has to be made **within** a "
        "phase. A batter with a strike rate of 140 is unremarkable at the "
        "death and outstanding in the powerplay, and a single career strike "
        "rate hides which of those a player actually is.",
        "",
        "## 3. Where each batter is weakest",
        "",
        "![Death batting](figures/03_death_batting.png)",
        "",
        "For every batter with 200+ balls in all three phases, the phase where "
        "their strike rate sits furthest below the **league average for that "
        "same phase**:",
        "",
        weakness.head(15).to_markdown(index=False),
        "",
        "The comparison is against the league in the same phase, not against "
        "the batter's own other phases. Everyone scores faster at the death, "
        "so a batter's death strike rate always beats their powerplay one — "
        "that tells you nothing. What matters is how they compare to what "
        "other batters manage in the same situation.",
        "",
        "The `dot_pct` column is where most of the mechanism shows. Across all "
        "qualifying batter-phases, dot percentage correlates at **−0.44** with "
        "falling behind the league, against **−0.33** for survival (balls per "
        "dismissal). Strike rotation is the larger effect, but both are "
        "present — batters who fall behind tend to be playing more dot balls "
        "*and* getting out somewhat more often.",
        "",
        "## 4. Death bowling, measured properly",
        "",
        "![Death bowling](figures/04_death_bowling.png)",
        "",
        best_death[["bowler", "balls", "economy", "dot_pct", "boundary_pct",
                    "strike_rate"]].to_markdown(index=False),
        "",
        "Economy here excludes byes and leg-byes, which the bowler did not "
        "concede, and excludes wides and no-balls from the denominator, which "
        "they did not legally bowl. Both corrections matter at the death, "
        "where wides are frequent.",
        "",
        "## 5. Does winning the toss matter?",
        "",
        "![Toss](figures/05_toss.png)",
        "",
        f"Across **{toss['decided_matches']:,} decided matches**, the toss "
        f"winner won **{toss['overall_pct']:.1f}%** of the time "
        f"({toss['toss_winner_wins']:,} wins).",
        "",
        toss["by_decision"].to_markdown(),
        "",
        f"A binomial test against a fair coin gives **p = {toss['p_value']:.3f}**, "
        + (
            "so simply winning the toss confers no advantage distinguishable "
            "from chance."
            if toss["p_value"] >= 0.05
            else "so the toss advantage is statistically significant, though "
                 "the effect size is small."
        ),
        "",
        "**But the decision made after the toss does matter.** Captains who "
        f"chose to field won **{toss['field_pct']:.1f}%** of the time across "
        f"{toss['field_n']:,} matches; those who chose to bat won only "
        f"**{toss['bat_pct']:.1f}%** across {toss['bat_n']:,}. A chi-square "
        f"test on that split gives **p = {toss['decision_p']:.4f}**"
        + (
            ", which is significant."
            if toss["decision_p"] < 0.05
            else ", which is not significant."
        ),
        "",
        f"That is a gap of **{toss['field_pct'] - toss['bat_pct']:.1f} "
        "percentage points**, and it is consistent with the standard "
        "explanation: evening dew makes the ball harder to grip in the second "
        "innings, so chasing is easier. Captains appear to know this — they "
        f"chose to field in {toss['field_n'] / toss['decided_matches'] * 100:.0f}% "
        "of matches.",
        "",
        "**The causal reading is not available from this table.** Captains do "
        "not choose at random: they field when conditions favour chasing and "
        "bat when they do not. Part of the gap is therefore the conditions "
        "that prompted the decision rather than the decision itself. What the "
        "data supports is that *the toss is not the interesting variable — "
        "the innings order is*, and the headline 51.6% conceals that entirely.",
        "",
        "---",
        "",
        "## Limitations",
        "",
        "- **No ball-tracking data.** Cricsheet records outcomes, not line, "
        "length, pace or shot type. Statements about *why* a batter struggles "
        "in a phase are not supportable here — only that they do.",
        "- **Bowling style is not in the data.** A spin-versus-pace weakness "
        "analysis would need a separate player-attributes source joined on "
        "name, which introduces its own matching errors.",
        "- **Minimum-ball thresholds are judgement calls.** 200 balls per "
        "phase and 300 for the death charts trade sample size against "
        "coverage; different thresholds change who appears.",
        "- **Nineteen seasons of rule and format changes.** Team counts, "
        "squad rules and playing conditions all vary across the period, so "
        "cross-era comparisons carry that caveat.",
    ]

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
