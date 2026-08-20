# IPL Ball-by-Ball Analytics

Analysis of **295,557 deliveries** across **1,243 matches** — every IPL game
from 2008 to 2026 — from the Cricsheet ball-by-ball archive.

**Headline findings:** the 2023 Impact Player rule coincides with a **+1.13
runs per over** jump in scoring, and winning the toss is worth almost nothing
(51.6%, p = 0.289) while the *decision made after it* is worth a lot — captains
who field win 54.7% against 45.3% for those who bat (p = 0.0025).

---

## What this project does

| Stage | Script | Output |
|---|---|---|
| Ingest & parse | `src/transform.py` | Nested Cricsheet JSON → flat ball-by-ball table |
| Analyse | `src/analysis.py` | 5 figures + findings report |
| Explore | `notebooks/01_exploratory_analysis.ipynb` | EDA walkthrough |
| SQL | `src/load_db.py` | SQLite database + 8 analysis queries |
| Dashboard | `dashboard/app.py` | Interactive Streamlit app, 7 tabs |

## Key findings

1. **Scoring jumped with the Impact Player rule.** Run rate averaged 8.39 in
   the five seasons before 2023 and 9.52 after — **+1.13 runs per over**. Dot
   balls fell from ~37% to ~33% and sixes per match rose from ~14 to ~19. The
   timing fits the rule, but a rule change is not the only thing that moved in
   2023; this is an association in a time series, not a controlled experiment.
2. **The toss barely matters — the innings order does.** Across 1,218 decided
   matches the toss winner won 51.6% (p = 0.289, indistinguishable from a coin
   flip). But captains who chose to **field** won 54.7% against 45.3% for those
   who chose to **bat** — a 9.4-point gap, p = 0.0025. Consistent with evening
   dew making the chase easier. Captains appear to know: they fielded in 67% of
   matches.
3. **The three phases are different games.** The death overs score roughly
   twice as fast as the middle and cost a wicket far more often, so any player
   comparison has to be made *within* a phase. A career strike rate of 140
   hides whether a batter is outstanding in the powerplay or ordinary at the
   death.
4. **Batter weaknesses show up more in dot balls than dismissals** — though
   both matter. Dot percentage correlates at −0.44 with falling behind the
   league in a phase, against −0.33 for survival, so strike rotation is the
   larger effect without being the whole story. S Badrinath's powerplay strike
   rate sits **52 points below** the league average for that phase, with a 61%
   dot rate.
5. **Death bowling, measured properly**, is led by SP Narine (7.08 economy over
   1,105 death balls) and SL Malinga (7.47 over 1,117) against a league death
   economy well above both.

## The scoring conventions (and why they matter)

Cricket rates are easy to compute plausibly and wrongly. These are applied
consistently and pinned by tests:

| Measure | Rule |
|---|---|
| Balls faced (batter) | Excludes wides, **includes** no-balls |
| Balls bowled (bowler) | Excludes wides **and** no-balls |
| Runs conceded (bowler) | Excludes byes and leg-byes |
| Wickets (bowler) | Excludes run-outs and retirements |
| Super overs | Excluded from every per-over statistic |

Counting wides in a bowler's denominator flatters their economy. Crediting
run-outs to bowlers flatters strike bowlers. Both mistakes produce numbers that
look entirely reasonable.

**One more trap, caught during the build:** Cricsheet labels some seasons across
two years (`2007/08`, `2009/10`), and the label does **not** name the year the
cricket was played — `2007/08` was played in 2008, `2009/10` in 2010. Season
year is derived from the match date instead, which is correct for every season
including the displaced 2020 edition played in September–November.

## Tech stack

**Python** (pandas, NumPy, SciPy) · **SQL** (SQLite, portable to PostgreSQL —
CTEs, window functions, `LAG()`, `UNION ALL`) · **Streamlit** and **Plotly** ·
**matplotlib**/**seaborn** · **pytest** (26 tests)

## Quick start

Two derived files are **not committed** — `data/processed/deliveries.csv`
(57 MB) and `data/ipl.db` (68 MB) — so the repository stays small enough to
clone quickly. The 4.9 MB Cricsheet source archive they are built from **is**
committed, so running the pipeline below regenerates both.

```bash
pip install -r requirements.txt
```

Run the pipeline:

```bash
python src/transform.py && python src/analysis.py && python src/load_db.py
```

Launch the dashboard:

```bash
streamlit run dashboard/app.py
```

Run the tests:

```bash
python -m pytest tests/ -q
```

## Project structure

```
ipl-analytics/
├── data/
│   ├── raw/ipl_json.zip      Cricsheet archive as downloaded
│   ├── processed/            deliveries + matches + aggregates
│   └── ipl.db                SQLite database
├── src/
│   ├── transform.py          JSON parsing and flattening
│   ├── analysis.py           figures + findings
│   └── load_db.py            SQLite + SQL runner
├── sql/analysis.sql          8 analysis queries
├── dashboard/app.py          Streamlit dashboard
├── reports/
│   ├── findings.md           the main write-up
│   ├── sql_results.md        query output
│   └── figures/              5 PNG charts
└── tests/test_pipeline.py    26 tests
```

## Data source

[Cricsheet](https://cricsheet.org) ball-by-ball archive, all IPL matches.
Freely available under the Open Data Commons Attribution License (ODC-BY).

## Limitations

- **No ball-tracking data.** Cricsheet records outcomes, not line, length, pace
  or shot type. This project can show *that* a batter struggles in a phase, not
  *why*.
- **Bowling style is not in the data**, so a spin-versus-pace weakness analysis
  would need a separate player-attributes source joined on name, which brings
  its own matching errors.
- **Minimum-ball thresholds are judgement calls** (200 per phase, 300 for the
  death charts, 60 for matchups). Different thresholds change who appears.
- **Nineteen seasons of rule and format change.** Team counts, squad rules and
  playing conditions all vary, so cross-era comparisons carry that caveat.
- **Everything here is correlational.** The Impact Player and toss-decision
  findings in particular describe associations, not causes.

---

Built by **Ritika Sharma** — [LinkedIn](https://www.linkedin.com/in/ritikasharma04/) ·
[GitHub](https://github.com/Ritikasharma2004)
