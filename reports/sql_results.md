# SQL Analysis Results

Source: `sql/analysis.sql` against `ipl.db`

## Q1. Scoring by season

|   season_year |   matches |   runs |   legal_balls |   run_rate |   six_pct |   dot_pct |
|--------------:|----------:|-------:|--------------:|-----------:|----------:|----------:|
|          2008 |        58 |  17937 |         12950 |       8.31 |      4.81 |      38   |
|          2009 |        57 |  16320 |         13085 |       7.48 |      3.87 |      39.1 |
|          2010 |        60 |  18864 |         13929 |       8.13 |      4.2  |      35.8 |
|          2011 |        73 |  21154 |         16425 |       7.73 |      3.89 |      38.2 |
|          2012 |        74 |  22453 |         17208 |       7.83 |      4.26 |      36.3 |
|          2013 |        76 |  22541 |         17613 |       7.68 |      3.83 |      38.4 |
|          2014 |        60 |  18909 |         13833 |       8.2  |      5.16 |      36.3 |
|          2015 |        59 |  18332 |         13141 |       8.37 |      5.27 |      36.3 |
|          2016 |        60 |  18862 |         13618 |       8.31 |      4.69 |      34.1 |
|          2017 |        59 |  18769 |         13390 |       8.41 |      5.27 |      34   |
|          2018 |        60 |  19901 |         13808 |       8.65 |      6.32 |      34.4 |
|          2019 |        60 |  19400 |         13837 |       8.41 |      5.67 |      35.6 |
|          2020 |        60 |  19352 |         14007 |       8.29 |      5.25 |      34.8 |
|          2021 |        60 |  18622 |         13876 |       8.05 |      4.95 |      36.2 |
|          2022 |        74 |  24395 |         17138 |       8.54 |      6.2  |      37.1 |
|          2023 |        74 |  25688 |         17137 |       8.99 |      6.56 |      33.9 |
|          2024 |        71 |  25971 |         16299 |       9.56 |      7.74 |      32.9 |
|          2025 |        74 |  26503 |         16507 |       9.63 |      7.88 |      32.3 |
|          2026 |        74 |  27450 |         16664 |       9.88 |      8.56 |      32.7 |


## Q2. The three phases compared

| phase     |   balls |   run_rate |   balls_per_wicket |   boundary_pct |
|:----------|--------:|-----------:|-------------------:|---------------:|
| Middle    |  131526 |       7.95 |               23   |           14.3 |
| Powerplay |   89153 |       8.09 |               24.9 |           20.4 |
| Death     |   63786 |      10.06 |               11.8 |           20.8 |


## Q3. Batter strike rate by phase, against the league average for that phase

| batter        | phase     |   balls_faced |   strike_rate |   league_avg_sr |   vs_league |   balls_per_dismissal |
|:--------------|:----------|--------------:|--------------:|----------------:|------------:|----------------------:|
| Kuldeep Yadav | Death     |           209 |          89.5 |           165.3 |       -75.8 |                  13.9 |
| B Kumar       | Death     |           326 |          96.9 |           165.3 |       -68.4 |                   9.1 |
| A Mishra      | Death     |           250 |         104   |           165.3 |       -61.3 |                  10.4 |
| P Kumar       | Death     |           261 |         112.6 |           165.3 |       -52.7 |                   9   |
| S Badrinath   | Powerplay |           237 |          76.8 |           128.9 |       -52.1 |                  39.5 |
| R Vinay Kumar | Death     |           226 |         115.9 |           165.3 |       -49.4 |                   9   |
| PP Chawla     | Death     |           373 |         121.4 |           165.3 |       -43.9 |                   7.8 |
| GJ Bailey     | Middle    |           229 |          89.5 |           127.3 |       -37.8 |                  14.3 |
| IK Pathan     | Middle    |           437 |          90.4 |           127.3 |       -36.9 |                  21.9 |
| DJ Bravo      | Middle    |           572 |          92.3 |           127.3 |       -35   |                  23.8 |
| CA Pujara     | Powerplay |           229 |          93.9 |           128.9 |       -35   |                  22.9 |
| GC Smith      | Powerplay |           387 |          96.6 |           128.9 |       -32.3 |                  24.2 |
| R Ashwin      | Death     |           356 |         133.7 |           165.3 |       -31.6 |                   8.9 |
| MK Tiwary     | Powerplay |           230 |          97.4 |           128.9 |       -31.5 |                  23   |
| M Manhas      | Middle    |           232 |          96.6 |           127.3 |       -30.7 |                  23.2 |
| AM Nayar      | Middle    |           307 |          96.7 |           127.3 |       -30.6 |                  20.5 |
| JP Duminy     | Powerplay |           239 |          98.3 |           128.9 |       -30.6 |                  39.8 |
| KD Karthik    | Powerplay |           402 |          98.5 |           128.9 |       -30.4 |                  40.2 |
| SC Ganguly    | Middle    |           642 |          98.1 |           127.3 |       -29.2 |                  26.8 |
| JH Kallis     | Middle    |          1012 |          98.5 |           127.3 |       -28.8 |                  32.6 |


## Q4. Death-overs bowling, ranked by economy

| bowler        |   balls |   runs_conceded |   economy |   wickets |   dot_pct |
|:--------------|--------:|----------------:|----------:|----------:|----------:|
| SP Narine     |    1105 |            1304 |      7.08 |        84 |      37.4 |
| SL Malinga    |    1117 |            1390 |      7.47 |       108 |      31.3 |
| R Ashwin      |     601 |             785 |      7.84 |        36 |      29.6 |
| JJ Bumrah     |    1423 |            1865 |      7.86 |       102 |      31.2 |
| DW Steyn      |     634 |             840 |      7.95 |        50 |      34.4 |
| B Lee         |     311 |             426 |      8.22 |        10 |      29.6 |
| M Pathirana   |     402 |             559 |      8.34 |        33 |      31.3 |
| CH Morris     |     646 |             900 |      8.36 |        58 |      28.3 |
| AR Patel      |     382 |             535 |      8.4  |        22 |      30.9 |
| Kuldeep Yadav |     370 |             521 |      8.45 |        29 |      31.4 |
| A Nehra       |     527 |             746 |      8.49 |        54 |      30.4 |
| CV Varun      |     328 |             467 |      8.54 |        19 |      35.4 |
| PP Chawla     |     444 |             632 |      8.54 |        39 |      33.8 |
| MA Starc      |     357 |             509 |      8.55 |        37 |      31.7 |
| Rashid Khan   |     630 |             900 |      8.57 |        43 |      34.3 |


## Q5. Batter versus bowler head-to-head

| batter       | bowler         |   balls |   runs |   dismissals |   strike_rate |
|:-------------|:---------------|--------:|-------:|-------------:|--------------:|
| MS Dhoni     | SP Narine      |      77 |     40 |            3 |          51.9 |
| AT Rayudu    | YS Chahal      |      83 |     63 |            4 |          75.9 |
| SV Samson    | SP Narine      |      89 |     70 |            3 |          78.7 |
| CH Gayle     | SL Malinga     |      72 |     57 |            1 |          79.2 |
| MK Pandey    | AR Patel       |      72 |     57 |            2 |          79.2 |
| S Dhawan     | R Ashwin       |      97 |     78 |            4 |          80.4 |
| AT Rayudu    | SP Narine      |      64 |     53 |            4 |          82.8 |
| CH Gayle     | R Ashwin       |      64 |     53 |            5 |          82.8 |
| RD Gaikwad   | Mohammed Shami |      84 |     73 |            0 |          86.9 |
| RG Sharma    | AR Patel       |      77 |     67 |            4 |          87   |
| AM Rahane    | B Kumar        |     124 |    109 |            7 |          87.9 |
| MK Pandey    | YS Chahal      |      60 |     53 |            4 |          88.3 |
| SR Watson    | B Kumar        |      88 |     78 |            4 |          88.6 |
| Ishan Kishan | R Ashwin       |      63 |     57 |            1 |          90.5 |
| JC Buttler   | JJ Bumrah      |      77 |     70 |            2 |          90.9 |
| G Gambhir    | SR Watson      |      65 |     60 |            3 |          92.3 |
| SA Yadav     | AR Patel       |      79 |     73 |            2 |          92.4 |
| KL Rahul     | Rashid Khan    |      70 |     65 |            3 |          92.9 |
| RG Sharma    | R Ashwin       |     128 |    119 |            4 |          93   |
| CH Gayle     | SP Narine      |      69 |     65 |            2 |          94.2 |


## Q6. Does winning the toss help?

| toss_decision   |   matches |   toss_winner_won |   win_pct |
|:----------------|----------:|------------------:|----------:|
| bat             |       408 |               185 |      45.3 |
| field           |       810 |               443 |      54.7 |
| ALL             |      1218 |               628 |      51.6 |


## Q7. Highest team totals, with the runner-up gap

|   season_year | batting_team                |   total |   gap_to_next |
|--------------:|:----------------------------|--------:|--------------:|
|          2024 | Sunrisers Hyderabad         |     287 |           nan |
|          2025 | Sunrisers Hyderabad         |     286 |            -1 |
|          2025 | Sunrisers Hyderabad         |     278 |            -8 |
|          2024 | Sunrisers Hyderabad         |     277 |            -1 |
|          2024 | Kolkata Knight Riders       |     272 |            -5 |
|          2024 | Sunrisers Hyderabad         |     266 |            -6 |
|          2026 | Punjab Kings                |     265 |            -1 |
|          2026 | Delhi Capitals              |     264 |            -1 |
|          2013 | Royal Challengers Bengaluru |     263 |            -1 |
|          2024 | Royal Challengers Bengaluru |     262 |            -1 |
|          2024 | Punjab Kings                |     262 |             0 |
|          2024 | Kolkata Knight Riders       |     261 |            -1 |
|          2023 | Lucknow Super Giants        |     257 |            -4 |
|          2024 | Delhi Capitals              |     257 |             0 |
|          2026 | Sunrisers Hyderabad         |     255 |            -2 |


## Q8. Venue scoring, first innings only

| venue                                                                 |   matches |   avg_first_innings_total |   run_rate |
|:----------------------------------------------------------------------|----------:|--------------------------:|-----------:|
| Rajiv Gandhi International Stadium, Uppal, Hyderabad                  |        26 |                     194.7 |       9.75 |
| Sawai Mansingh Stadium, Jaipur                                        |        21 |                     194.5 |       9.78 |
| Arun Jaitley Stadium, Delhi                                           |        30 |                     193.6 |       9.74 |
| M Chinnaswamy Stadium, Bengaluru                                      |        24 |                     190.4 |       9.65 |
| Eden Gardens, Kolkata                                                 |        30 |                     190.3 |       9.85 |
| Narendra Modi Stadium, Ahmedabad                                      |        41 |                     185.8 |       9.33 |
| Wankhede Stadium, Mumbai                                              |        59 |                     181.9 |       9.17 |
| Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium, Lucknow |        29 |                     174.8 |       8.79 |
| Dr DY Patil Sports Academy, Mumbai                                    |        20 |                     170.7 |       8.56 |
| MA Chidambaram Stadium, Chepauk, Chennai                              |        41 |                     168.3 |       8.44 |
| M Chinnaswamy Stadium                                                 |        65 |                     168.1 |       8.66 |
| Maharashtra Cricket Association Stadium                               |        22 |                     166.4 |       8.41 |
| Wankhede Stadium                                                      |        73 |                     166   |       8.37 |
| MA Chidambaram Stadium, Chepauk                                       |        48 |                     166   |       8.3  |
| Dubai International Cricket Stadium                                   |        46 |                     163.8 |       8.19 |
| Punjab Cricket Association Stadium, Mohali                            |        35 |                     163.3 |       8.32 |
| Feroz Shah Kotla                                                      |        60 |                     161.6 |       8.24 |
| Eden Gardens                                                          |        77 |                     160.2 |       8.14 |
| Sharjah Cricket Stadium                                               |        28 |                     159   |       7.95 |
| Sheikh Zayed Stadium                                                  |        29 |                     158.9 |       8.01 |
| Sawai Mansingh Stadium                                                |        47 |                     157.7 |       7.92 |
| Rajiv Gandhi International Stadium, Uppal                             |        49 |                     156.1 |       7.89 |

