# Guaranteed Wealth Index — Project Overview

## What This Is

A data dashboard that investigates a simple question: **do NBA players perform worse after signing big contracts?**

The idea is rooted in a concept called **moral hazard** — the theory that people take fewer risks and exert less effort once they're financially secure. In the NBA context, the hypothesis is that players push harder during their contract year (the season before they become a free agent) to maximize their next deal, then relax once the money is guaranteed.

This project builds a dataset of real NBA contracts, scrapes historical player stats from Basketball Reference, runs a regression model to find which factors actually predict post-signing decline, and displays everything in an interactive dashboard.

---

## The Dataset

We collected data on **130 NBA players** who signed significant contracts between roughly 2010 and 2023, covering three salary tiers:

- **Max** — top-of-market deals, typically $28M+/year (LeBron, Giannis, Curry tier)
- **Mid** — solid starter money, $13–28M/year
- **Low** — role player contracts, under $13M/year

For each player, we pulled three seasons of stats from Basketball Reference:

| Label | What it means |
|-------|---------------|
| **T−1** | The season *before* their contract year — their baseline |
| **T** | Their **contract year** — the walk year, when they're playing for their next deal |
| **T+1** | Their **first season on the new contract** — the payday year |

The key stat we focus on is **PER (Player Efficiency Rating)** — a single number that summarizes a player's overall per-minute production. League average is 15. All-Stars typically sit around 20–23. MVPs are 25+. It's imperfect but it captures a player's overall contribution in one number, which makes it useful for comparison across eras and positions.

---

## What the Data Shows

Even before running any statistics, the averages tell a clear story:

| Tier | Avg PER Drop (T → T+1) |
|------|------------------------|
| Max  | −1.23 points |
| Mid  | −0.79 points |
| Low  | −0.15 points |

Players decline after signing across all tiers, and the decline scales with contract size. Max players drop the most. This is consistent with the moral hazard hypothesis — but averages alone don't prove causation. A player might decline simply because they were at a career peak, or because they got older, or because their role changed. That's where the regression comes in.

---

## The Regression Model

A regression model is a mathematical way of asking: *which factors are actually doing the work here, and by how much?*

We tried to predict **how many PER points a player would drop** after signing, using six potential explanatory factors:

1. **Age** at signing — older players might decline faster
2. **Salary** — bigger contract, more cushion, less motivation?
3. **T_PER** — how high their peak PER was during the contract year
4. **per_trend** — how much their PER *rose* heading into their contract year (T_PER minus T−1 PER)
5. **is_max** — whether they signed a max deal (yes/no)
6. **is_mid** — whether they signed a mid-tier deal (yes/no)

The model tests each factor and asks: does this actually predict decline, or is the relationship just noise?

### What came back statistically significant

Out of six factors, only **two** showed a reliable relationship with post-signing decline:

**1. T_PER** (coefficient: +0.142, p-value: 0.043)

A player's peak PER during their walk year predicts future decline. For every 1-point higher their PER was in the contract year, the model expects them to fall an additional 0.14 PER points the next season. This is partly **regression to the mean** — extreme performances tend to drift back toward normal over time.

**2. per_trend** (coefficient: +0.286, p-value: 0.004)

This is the stronger signal. If a player's PER *surged* heading into their contract year — say, jumped 5 points above their prior-year level — the model predicts they'll fall back by an extra 0.29 points per point of that surge. This is the clearest evidence of walk-year inflation: players who spike unusually heading into free agency tend to regress once the contract is signed.

### What didn't matter

- **Age** — not significant at this sample size
- **Salary** — once you control for actual performance, contract size adds nothing
- **Max/Mid tier dummies** — tier is basically just a proxy for high PER; once T_PER is in the model, the tier labels are redundant

---

## The Prediction Formula

The full formula the dashboard uses to generate a risk score for any player:

```
Predicted PER Drop = −3.09 + (0.142 × T_PER) + (0.286 × per_trend)
```

A **positive result** means the model expects a decline. A **negative result** means it expects improvement.

Example — V. Oladipo (2018):
```
−3.09 + (0.142 × 23.0) + (0.286 × 9.5) = +2.91 PER drop predicted
```
His walk year PER was 23. He had surged nearly 10 points above his prior-year level. The model flagged him HIGH RISK. He actually fell from 23 to 17.6 — a 5.4-point drop, worse than predicted, partly because he suffered a serious knee injury that the model couldn't foresee.

---

## How Accurate Is It?

We tested the model using **Leave-One-Out Cross-Validation (LOO-CV)** — a technique that removes one player from the dataset, trains the model on the rest, predicts that player's outcome, and repeats for every player. This gives an honest estimate of how well the model predicts players it has *never seen*.

| Metric | Value |
|--------|-------|
| Average prediction error (RMSE) | ±2.86 PER points |
| Error if you just guessed the average every time | ±2.92 PER points |
| Improvement over just guessing | 2.2% |

That 2.2% improvement is real but modest. The model is meaningfully better than random guessing, but not by a dramatic margin. The honest interpretation: the model is reasonably good at **ranking** players by risk (flagging who is likely to decline vs. improve) but its specific numerical predictions should be treated as directional, not precise.

The R² of 0.138 means the two significant features explain about **14% of the variance** in post-signing performance. The other 86% comes from things the model can't see: injuries, coaching changes, role changes, team chemistry, and plain randomness.

---

## The Dashboard

The interactive dashboard displays all of this in three sections:

**Overview** — aggregate stats across all 130 players: average PER drops by tier, the "payday dip" chart showing every player sorted by decline magnitude, and a scatter plot of scoring volume vs. efficiency changes.

**Player Profile** — click any player to see their three-season stat arc, a risk score (0–100) derived from the regression formula, the model's predicted PER direction (↓ decline or ↑ improvement), diagnostic flags (walk-year surge detected, efficiency trap, etc.), and a radar chart showing multiple risk dimensions.

**Research Findings** — tier-by-tier comparison of how PER evolves across T−1 → T → T+1, and a breakdown of the research methodology.

---

## Realistic Ceiling on Model Precision

The model's current R² of 0.138 means it explains 14% of the variance in post-signing PER drops. With significant effort it could probably reach **0.35–0.45**. It will never be a precise forecasting tool. Here's why each category of improvement hits a ceiling:

**Better features** would help the most. Adding usage rate, games played, a non-linear age curve, team/system change after signing, and minutes trends are all available from Basketball Reference. This could plausibly push R² to 0.25–0.35. These are buildable improvements.

**Better target variable** helps modestly. PER is noisy year-to-year. Using BPM or VORP, averaging T+1 and T+2 instead of just T+1, or standardizing within position would reduce noise and add maybe 0.05–0.10 R². Also realistic.

**More data** would tighten coefficient estimates. 130 players is small — 400–500 would allow interaction terms and non-linear modeling. But expanding to smaller contracts risks mixing populations with different incentive structures.

**The hard ceiling** is injury. The single biggest predictor of whether a player declines post-contract is whether they get hurt — and injury is largely unpredictable from pre-signing box score data. Players like Oladipo, Kawhi, and Embiid had their entire post-signing trajectories dominated by injury outcomes no model could have flagged. That irreducible randomness accounts for an estimated 40–50% of the unexplained variance on its own.

The right use of this model is as a **screening tool**: it identifies players with elevated *observable* risk factors (high walk-year peak, large surge into the walk year), which is genuinely useful. It is not, and realistically cannot become, a precise individual-player forecast. A well-specified version of this model would be most valuable deployed as a ranking instrument — "these 3 of your 10 candidates have the highest pre-signing red flags" — not as a source of exact PER projections.

---

## Honest Caveats

- **130 players is a small sample** for regression analysis. The coefficients will shift as more data is added.
- **PER is an imperfect stat** — it doesn't capture defense well and can be inflated by usage rate.
- **Causation vs. correlation** — we can observe that players with walk-year surges tend to decline, but we can't definitively prove it's *because* the contract was signed. Regression to the mean alone would predict some of this pattern.
- **Survivorship** — players who had terrible walk years may not have gotten big contracts at all, which means our dataset is biased toward players who performed well enough to get paid.

---

## Tech Stack

- **Data**: Python scraper pulling from Basketball Reference (curl-based, respects rate limits)
- **Model**: OLS regression via `statsmodels`, validated with `scikit-learn` LOO-CV
- **Dashboard**: React + Recharts, styled as a retro terminal interface
- **Data format**: `players.csv` for the model, auto-patched into `App.jsx` for the frontend
