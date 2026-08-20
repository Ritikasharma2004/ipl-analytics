-- ============================================================================
-- IPL Ball-by-Ball Analytics - analysis queries
--
-- SQLite (data/ipl.db); standard SQL that runs on PostgreSQL and MySQL 8+.
--
-- Tables: deliveries(match_id, season_year, venue, innings, batting_team,
--                    bowling_team, over, ball_in_over, phase, batter, bowler,
--                    runs_batter, runs_total, wides, noballs, byes, legbyes,
--                    is_legal_delivery, is_four, is_six, is_dot, is_wicket,
--                    is_bowler_wicket, dismissal_kind, player_out, ...)
--         matches(match_id, season_year, date, venue, team_1, team_2,
--                 toss_winner, toss_decision, winner, ...)
--
-- Scoring conventions, applied consistently below:
--   balls faced  = wides excluded, no-balls included
--   balls bowled = wides and no-balls both excluded
--   runs conceded = byes and leg-byes excluded
-- ============================================================================


-- Q1. Scoring by season
-- The Impact Player rule took effect in 2023; this is the series that shows it.
SELECT
    season_year,
    COUNT(DISTINCT match_id)                                   AS matches,
    SUM(runs_total)                                            AS runs,
    SUM(is_legal_delivery)                                     AS legal_balls,
    ROUND(6.0 * SUM(runs_total) / SUM(is_legal_delivery), 2)   AS run_rate,
    ROUND(100.0 * SUM(is_six) / SUM(is_legal_delivery), 2)     AS six_pct,
    ROUND(100.0 * SUM(is_dot) / SUM(is_legal_delivery), 1)     AS dot_pct
FROM deliveries
WHERE is_super_over = 0
GROUP BY season_year
ORDER BY season_year;


-- Q2. The three phases compared
SELECT
    phase,
    SUM(is_legal_delivery)                                     AS balls,
    ROUND(6.0 * SUM(runs_total) / SUM(is_legal_delivery), 2)   AS run_rate,
    ROUND(1.0 * SUM(is_legal_delivery) / SUM(is_wicket), 1)    AS balls_per_wicket,
    ROUND(100.0 * (SUM(is_four) + SUM(is_six))
          / SUM(is_legal_delivery), 1)                         AS boundary_pct
FROM deliveries
WHERE is_super_over = 0
GROUP BY phase
ORDER BY run_rate;


-- Q3. Batter strike rate by phase, against the league average for that phase
-- A window function supplies the league rate alongside each batter's own,
-- so the comparison happens in one pass.
WITH batter_phase AS (
    SELECT
        batter,
        phase,
        COUNT(*)                                    AS balls_faced,
        SUM(runs_batter)                            AS runs,
        SUM(is_wicket)                              AS dismissals,
        ROUND(100.0 * SUM(runs_batter) / COUNT(*), 1) AS strike_rate
    FROM deliveries
    WHERE is_super_over = 0
      AND wides = 0            -- a wide is not a ball faced
    GROUP BY batter, phase
    HAVING COUNT(*) >= 200
),
with_league AS (
    SELECT
        bp.*,
        ROUND(
            AVG(bp.strike_rate) OVER (PARTITION BY bp.phase), 1
        ) AS league_avg_sr
    FROM batter_phase bp
)
SELECT
    batter,
    phase,
    balls_faced,
    strike_rate,
    league_avg_sr,
    ROUND(strike_rate - league_avg_sr, 1)                        AS vs_league,
    ROUND(1.0 * balls_faced / NULLIF(dismissals, 0), 1)          AS balls_per_dismissal
FROM with_league
ORDER BY vs_league
LIMIT 20;


-- Q4. Death-overs bowling, ranked by economy
-- Byes and leg-byes removed from runs conceded; wides and no-balls removed
-- from the denominator.
SELECT
    bowler,
    SUM(is_legal_delivery)                                       AS balls,
    SUM(runs_total - byes - legbyes)                             AS runs_conceded,
    ROUND(
        6.0 * SUM(runs_total - byes - legbyes) / SUM(is_legal_delivery), 2
    )                                                            AS economy,
    SUM(is_bowler_wicket)                                        AS wickets,
    ROUND(100.0 * SUM(is_dot) / SUM(is_legal_delivery), 1)       AS dot_pct
FROM deliveries
WHERE phase = 'Death'
  AND is_super_over = 0
  AND is_legal_delivery = 1
GROUP BY bowler
HAVING SUM(is_legal_delivery) >= 300
ORDER BY economy
LIMIT 15;


-- Q5. Batter versus bowler head-to-head
-- The matchup table, restricted to pairings with a meaningful sample.
SELECT
    batter,
    bowler,
    COUNT(*)                                          AS balls,
    SUM(runs_batter)                                  AS runs,
    SUM(is_wicket)                                    AS dismissals,
    ROUND(100.0 * SUM(runs_batter) / COUNT(*), 1)     AS strike_rate
FROM deliveries
WHERE is_super_over = 0
  AND wides = 0
GROUP BY batter, bowler
HAVING COUNT(*) >= 60
ORDER BY strike_rate
LIMIT 20;


-- Q6. Does winning the toss help?
-- Only decided matches; a no-result cannot be won or lost by the toss.
SELECT
    toss_decision,
    COUNT(*)                                                     AS matches,
    SUM(CASE WHEN toss_winner = winner THEN 1 ELSE 0 END)        AS toss_winner_won,
    ROUND(
        100.0 * SUM(CASE WHEN toss_winner = winner THEN 1 ELSE 0 END)
        / COUNT(*), 1
    )                                                            AS win_pct
FROM matches
WHERE winner IS NOT NULL
  AND toss_winner IS NOT NULL
GROUP BY toss_decision

UNION ALL

SELECT
    'ALL'                                                        AS toss_decision,
    COUNT(*),
    SUM(CASE WHEN toss_winner = winner THEN 1 ELSE 0 END),
    ROUND(
        100.0 * SUM(CASE WHEN toss_winner = winner THEN 1 ELSE 0 END)
        / COUNT(*), 1
    )
FROM matches
WHERE winner IS NOT NULL
  AND toss_winner IS NOT NULL;


-- Q7. Highest team totals, with the runner-up gap
-- LAG over the ordered list shows how far clear each total is of the next.
WITH totals AS (
    SELECT
        d.match_id,
        d.season_year,
        d.batting_team,
        d.innings,
        SUM(d.runs_total) AS total
    FROM deliveries d
    WHERE d.is_super_over = 0
    GROUP BY d.match_id, d.season_year, d.batting_team, d.innings
)
SELECT
    season_year,
    batting_team,
    total,
    total - LAG(total) OVER (ORDER BY total DESC) AS gap_to_next
FROM totals
ORDER BY total DESC
LIMIT 15;


-- Q8. Venue scoring, first innings only
-- Second-innings totals are truncated by the chase, so mixing them in would
-- understate a venue's true scoring rate.
SELECT
    venue,
    COUNT(DISTINCT match_id)                                     AS matches,
    ROUND(
        1.0 * SUM(runs_total) / COUNT(DISTINCT match_id), 1
    )                                                            AS avg_first_innings_total,
    ROUND(6.0 * SUM(runs_total) / SUM(is_legal_delivery), 2)     AS run_rate
FROM deliveries
WHERE innings = 1
  AND is_super_over = 0
GROUP BY venue
HAVING COUNT(DISTINCT match_id) >= 20
ORDER BY avg_first_innings_total DESC;
