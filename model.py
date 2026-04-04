#!/usr/bin/env python3
"""
NBA Moral Hazard Regression Model
==================================
Reads players.csv and fits an OLS regression predicting post-contract
performance change.

Target variable:
  per_drop  = T_PER  - T2_PER   (positive = player declined after signing)
  ts_drop   = T_TS   - T2_TS    (positive = efficiency declined)

Features:
  age       = player age at signing
  salary    = AAV in $M
  T_PER     = PER in the contract year (peak performance signal)
  per_trend = T_PER - T1_PER    (positive = player was rising into T)
  is_max    = 1 if Max tier, else 0
  is_mid    = 1 if Mid tier, else 0
  (Low is the baseline)

Usage:
  pip install pandas scikit-learn statsmodels
  python3 model.py
"""

import json
import sys
from pathlib import Path

import pandas as pd

try:
    import statsmodels.api as sm
    from scipy import stats as scipy_stats
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    print("⚠  statsmodels not installed — run: pip install statsmodels")
    print("   Falling back to sklearn for coefficients only.\n")

try:
    from sklearn.linear_model import LinearRegression
    from sklearn.model_selection import LeaveOneOut
    from sklearn.metrics import mean_squared_error
    import numpy as np
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("⚠  scikit-learn not installed — run: pip install scikit-learn numpy")

CSV_PATH = Path("players.csv")
OUT_PATH = Path("model_coefficients.json")

# ── Contract-type annotations ─────────────────────────────────────────────────
# UFA = unrestricted free agent  (strongest moral hazard test — full leverage)
# RFA = restricted free agent    (team had matching rights — weaker incentive)
# EXT = extension before FA      (locked in before market opened — weakest)
# UNK = unclear / complex        (excluded from UFA analysis)

CONTRACT_TYPES = {
    # MAX ── UFAs
    "jamesle01": "UFA",   # LeBron, re-signed CLE 2016
    "duranke01": "UFA",   # KD, OKC → GSW 2016
    "georgpa01": "UFA",   # Paul George, OKC → LAC 2019
    "leonaka01": "UFA",   # Kawhi, TOR → LAC 2019
    "butlejo01": "UFA",   # Butler, → MIA 2019
    "walkeke01": "UFA",   # Kemba, CHA → BOS 2019
    "irvinky01": "UFA",   # Kyrie, BOS → BKN 2019
    # MAX ── Extensions
    "curryst01": "EXT",   # Steph, GSW 2017
    "antetgi01": "EXT",   # Giannis, MIL 2016 supermax
    "townska01": "EXT",   # KAT, MIN 2019 supermax
    "embiijo01": "EXT",   # Embiid, PHI 2022 supermax
    "doncilu01": "EXT",   # Luka, DAL 2022 supermax
    "moranja01": "EXT",   # Morant, MEM 2022
    "tatumja01": "EXT",   # Tatum, BOS 2023
    "adebaed01": "EXT",   # Adebayo, MIA 2020
    "goberru01": "EXT",   # Gobert, UTA 2020
    "foxde01":   "EXT",   # Fox, SAC 2021
    "gilgesh01": "EXT",   # SGA, OKC 2021
    "garlada01": "EXT",   # Garland, CLE 2022
    "mitchdo01": "EXT",   # Mitchell, UTA 2021
    "siakapa01": "EXT",   # Siakam, TOR 2020
    "randlju01": "EXT",   # Randle, NYK 2021
    "bookede01": "EXT",   # Booker, PHX 2018
    "brownja01": "EXT",   # J. Brown, BOS 2020
    "murrade01": "EXT",   # D. Murray, ATL 2022
    # MAX ── RFAs
    "ingrabr01": "RFA",   # Ingram, NOP 2020
    "russeda01": "UNK",   # D. Russell, traded RFA rights 2019
    # MID ── UFAs
    "paulch01":  "UFA",   # CP3, HOU 2018 (player option / re-sign)
    "oladivi01": "EXT",   # Oladipo, IND 2018 extension post-trade
    "derozde01": "EXT",   # DeRozan, SAS 2019 extension post-trade
    "nowitdi01": "UFA",   # Nowitzki, DAL 2010 re-sign
    "wadedw01":  "UFA",   # Wade, MIA 2012 re-sign
    "hardati01": "UFA",   # T. Hardaway Jr, NYK → DAL 2019
    "waitedi01": "UFA",   # Waiters, → MIA 2017
    "greenda02": "UFA",   # Danny Green, SAS → TOR 2018
    "youngth01": "UFA",   # Thad Young, BKN → IND 2016
    "hartjo01":  "UFA",   # Josh Hart, NYK 2022 re-sign
    "collida01": "UFA",   # Collison, → IND 2017
    "dinwspe01": "UFA",   # Dinwiddie, BKN → WAS 2021
    # MID ── Extensions
    "conlemi01": "EXT",   # Conley, MEM 2016
    "bealbr01":  "EXT",   # Beal, WAS 2019
    "middlkh01": "EXT",   # Middleton, MIL 2019
    "harristo01": "EXT",  # Harris, PHI 2019
    "mccolcj01": "EXT",   # CJ McCollum, POR 2016
    "gordoaa01": "EXT",   # A. Gordon, ORL 2017
    "whitede01": "EXT",   # D. White, BOS 2022
    "kuzmaky01": "EXT",   # Kuzma, WAS 2022
    "simonan01": "EXT",   # Simons, POR 2022
    "allenja01": "EXT",   # J. Allen, CLE 2022
    "anunoog01": "EXT",   # OG Anunoby, TOR 2022
    "reidna01":  "EXT",   # N. Reid, MIN 2023
    "balllo01":  "EXT",   # L. Ball, CHI 2021
    "finnedo01": "EXT",   # Finney-Smith, DAL 2021
    "rosede01":  "EXT",   # D. Rose, CHI 2011 rookie ext
    "rubiori01": "EXT",   # Rubio, MIN 2015
    "jacksre01": "RFA",   # R. Jackson, DET 2015
    "vucevni01": "EXT",   # Vucevic, ORL 2019
    "thompTr01": "RFA",   # Tristan Thompson, CLE 2015
    "capelcl01": "RFA",   # Capela, HOU 2018
    "smartma01": "RFA",   # Smart, BOS 2019
    "greendr01": "RFA",   # Draymond, GSW 2015
    # LOW ── UFAs
    "leeco01":   "UFA",   # Courtney Lee, MEM → CHA 2016
    "pattepa01": "UFA",   # P. Patterson, TOR 2016 re-sign
    "collida01": "UFA",   # D. Collison (duplicate key ok, same value)
    "morrima02": "UFA",   # Marcus Morris Sr, 2018
    "aminual01": "UFA",   # Aminu, DAL → POR 2016
    "snellto01": "UFA",   # Snell, CHI → MIL 2016
    "niangge01": "UFA",   # Niang, PHI 2022 re-sign
    "chandwi01": "UFA",   # W. Chandler, 2014
    # LOW ── RFAs
    "bradlav01": "RFA",   # A. Bradley, BOS 2014
    "favorde01": "RFA",   # D. Favors, UTA 2016
    # Remaining players default to UNK if not listed
}


# ── Load data ────────────────────────────────────────────────────────────────

def load_data() -> pd.DataFrame:
    if not CSV_PATH.exists():
        sys.exit(f"ERROR: {CSV_PATH} not found. Run fetch_stats.py first.")
    df = pd.read_csv(CSV_PATH)
    print(f"Loaded {len(df)} players from {CSV_PATH}\n")
    return df


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute derived columns and return a clean modeling DataFrame."""
    df = df.copy()

    # Targets: how much did the player drop after signing?
    df["per_drop"]   = df["T_PER"]  - df["T2_PER"]   # positive = declined
    df["ts_drop"]    = df["T_TS"]   - df["T2_TS"]
    df["ws_drop"]    = df["T_WS"]   - df["T2_WS"]

    # Features
    df["per_trend"]  = df["T_PER"]  - df["T1_PER"]   # positive = rising into contract year
    df["is_max"]     = (df["tier"] == "Max").astype(int)
    df["is_mid"]     = (df["tier"] == "Mid").astype(int)

    # Drop rows where contract-year data is missing (injured during walk year)
    before = len(df)
    df = df[df["T_PER"] != 0.0].copy()
    dropped = before - len(df)
    if dropped:
        print(f"⚠  Dropped {dropped} players with missing T data (injured in walk year)")

    # Drop rows where T+1 data is missing (player retired, injury, etc.)
    before = len(df)
    df = df[df["T2_PER"] != 0.0].copy()
    dropped = before - len(df)
    if dropped:
        print(f"⚠  Dropped {dropped} players with missing T+1 data (injury/retirement)")

    # Drop any remaining rows with NaN in modelling columns
    all_cols = FEATURE_COLS + ["per_drop", "ts_drop", "ws_drop"]
    before = len(df)
    df = df.dropna(subset=all_cols).copy()
    dropped = before - len(df)
    if dropped:
        print(f"⚠  Dropped {dropped} players with NaN in feature/target columns")

    return df


# ── Regression ───────────────────────────────────────────────────────────────

FEATURE_COLS = ["age", "salary", "T_PER", "per_trend", "is_max", "is_mid"]
TARGET       = "per_drop"


def run_ols(df: pd.DataFrame):
    """OLS via statsmodels — gives p-values, R², confidence intervals."""
    X = df[FEATURE_COLS]
    y = df[TARGET]
    X_const = sm.add_constant(X)

    model = sm.OLS(y, X_const).fit()
    print("=" * 60)
    print("OLS Regression: PER Drop after Contract Signing")
    print("=" * 60)
    print(model.summary())
    print()

    return model


def run_loo_cv(df: pd.DataFrame):
    """Leave-one-out cross-validation via sklearn.

    With small samples, LOO-CV gives a better sense of out-of-sample error
    than a train/test split.
    """
    X = df[FEATURE_COLS].values
    y = df[TARGET].values

    loo  = LeaveOneOut()
    reg  = LinearRegression()
    preds = []

    for train_idx, test_idx in loo.split(X):
        reg.fit(X[train_idx], y[train_idx])
        preds.append(reg.predict(X[test_idx])[0])

    preds = np.array(preds)
    rmse  = np.sqrt(mean_squared_error(y, preds))
    mae   = np.mean(np.abs(y - preds))

    # Null model: always predict the mean
    null_rmse = np.sqrt(mean_squared_error(y, np.full_like(y, y.mean())))

    print("-" * 60)
    print("Leave-One-Out Cross-Validation (LOO-CV)")
    print("-" * 60)
    print(f"  LOO-CV RMSE : {rmse:.2f} PER points")
    print(f"  LOO-CV MAE  : {mae:.2f} PER points")
    print(f"  Null RMSE   : {null_rmse:.2f}  (predict mean for everyone)")
    print(f"  Skill ratio : {(1 - rmse/null_rmse)*100:.1f}% improvement over null")
    print()

    return rmse, mae


def export_coefficients(model, df: pd.DataFrame):
    """Write model metadata + coefficients to model_coefficients.json."""
    params = model.params.to_dict()
    pvals  = model.pvalues.to_dict()
    ci     = model.conf_int()

    coef_out = {}
    for k in params:
        coef_out[k] = {
            "coef":  round(params[k], 4),
            "pval":  round(pvals[k],  4),
            "ci_lo": round(ci.loc[k, 0], 4),
            "ci_hi": round(ci.loc[k, 1], 4),
        }

    output = {
        "n_players":    int(len(df)),
        "target":       TARGET,
        "features":     FEATURE_COLS,
        "r_squared":    round(float(model.rsquared), 4),
        "adj_r_squared":round(float(model.rsquared_adj), 4),
        "coefficients": coef_out,
        "note": (
            "Exploratory model — sample size is small. "
            "Coefficients should not be treated as definitive until n > 100."
        ),
    }

    OUT_PATH.write_text(json.dumps(output, indent=2))
    print(f"✓  Coefficients exported → {OUT_PATH}")
    return output


def print_tier_summary(df: pd.DataFrame):
    """Print average per_drop by tier — a quick sanity check."""
    print("-" * 60)
    print("Average PER drop by tier (T → T+1, positive = declined)")
    print("-" * 60)
    summary = (
        df.groupby("tier")[["per_drop", "ts_drop", "ws_drop"]]
        .agg(["mean", "count"])
    )
    print(summary.to_string())
    print()


# ── Contract-type annotation & UFA analysis ───────────────────────────────────

def annotate_contract_type(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["contract_type"] = df["bbref_id"].map(CONTRACT_TYPES).fillna("UNK")
    return df


def run_ufa_analysis(df: pd.DataFrame) -> None:
    """
    Re-run OLS and within-subject comparison on UFAs only.
    UFAs had maximum financial incentive to perform — if moral hazard is real
    the signal should be stronger here than in the full dataset.
    """
    df = annotate_contract_type(df)

    counts = df["contract_type"].value_counts()
    print("=" * 60)
    print("Contract-Type Breakdown & UFA Analysis")
    print("=" * 60)
    print("  Annotation coverage:")
    for ct in ["UFA", "RFA", "EXT", "UNK"]:
        print(f"    {ct}: {counts.get(ct, 0)}")
    print()

    ufa = df[df["contract_type"] == "UFA"].copy()
    ext = df[df["contract_type"] == "EXT"].copy()

    if len(ufa) < 15:
        print(f"  ⚠  Only {len(ufa)} confirmed UFAs — results will be noisy.")

    # Within-subject: surge vs drop for each group
    for label, sub in [("UFA", ufa), ("EXT (extension)", ext), ("Full dataset", df)]:
        if len(sub) < 5:
            continue
        surge = (sub["T_PER"] - sub["T1_PER"]).mean()
        drop  = (sub["T_PER"] - sub["T2_PER"]).mean()
        print(f"  {label:22s}  n={len(sub):3d}  surge={surge:+.2f}  drop={drop:+.2f}  excess={drop-surge:+.2f}")
    print()

    # OLS on UFAs only
    if not HAS_STATSMODELS or len(ufa) < 15:
        return

    X_ufa = sm.add_constant(ufa[FEATURE_COLS].values)
    y_ufa = ufa["per_drop"].values
    model_ufa = sm.OLS(y_ufa, X_ufa).fit()

    X_full = sm.add_constant(df[FEATURE_COLS].values)
    model_full = sm.OLS(df["per_drop"].values, X_full).fit()

    print("  Key coefficient comparison (UFA-only vs full dataset):")
    print(f"  {'Feature':12s}  {'UFA coef':>10s}  {'UFA p':>8s}  {'Full coef':>10s}  {'Full p':>8s}")
    print("  " + "-" * 55)
    labels = ["const"] + FEATURE_COLS
    for i, label in enumerate(labels):
        cu  = model_ufa.params[i]
        pu  = model_ufa.pvalues[i]
        cf  = model_full.params[i]
        pf  = model_full.pvalues[i]
        sig_u = " ✓" if pu < 0.05 else ""
        sig_f = " ✓" if pf < 0.05 else ""
        print(f"  {label:12s}  {cu:+10.3f}  {pu:8.3f}{sig_u:<2}  {cf:+10.3f}  {pf:8.3f}{sig_f}")
    print()
    print(f"  UFA R²   : {model_ufa.rsquared:.3f}  (full dataset: {model_full.rsquared:.3f})")
    print(f"  UFA n    : {len(ufa)}  (full dataset: {len(df)})")
    print()


# ── Within-subject control: pre-signing surge vs post-signing drop ────────────

def run_within_subject_control(df: pd.DataFrame) -> None:
    """
    Compare each player's pre-signing PER surge (T-1 → T) against their
    post-signing PER drop (T → T+1).

    Under pure regression to mean, the average surge and average drop should
    roughly cancel.  A systematically larger drop is evidence of excess decline
    beyond what chance would predict — the moral hazard signal.
    """
    # pre_surge: positive = player improved heading into walk year
    pre_surge  = df["T_PER"] - df["T1_PER"]
    # post_drop: positive = player declined after signing (same as per_drop)
    post_drop  = df["T_PER"] - df["T2_PER"]
    excess     = post_drop - pre_surge   # how much bigger was the drop vs the rise?

    print("=" * 60)
    print("Within-Subject Control: Pre-Signing Surge vs Post-Signing Drop")
    print("=" * 60)
    print(f"  Players analysed          : {len(df)}")
    print(f"  Avg PER surge  (T-1 → T)  : {pre_surge.mean():+.2f}  (positive = improved into walk year)")
    print(f"  Avg PER drop   (T → T+1)  : {post_drop.mean():+.2f}  (positive = declined after signing)")
    print(f"  Avg excess decline        : {excess.mean():+.2f}  (drop minus surge)")
    print()

    # Paired t-test: is the post-signing drop significantly larger than the pre-signing surge?
    if HAS_STATSMODELS:
        t_stat, p_val = scipy_stats.ttest_rel(post_drop, pre_surge)
        print(f"  Paired t-test (drop vs surge): t = {t_stat:.3f}, p = {p_val:.4f}")
        if p_val < 0.05:
            print("  ✓ Statistically significant — post-signing drop exceeds pre-signing surge")
            print("    This is evidence of excess decline beyond regression to mean alone.")
        else:
            print("  ✗ Not statistically significant at p < 0.05")
            print("    The drop is consistent with regression to mean; moral hazard signal is unclear.")

    # Break down by tier
    print()
    print("  By tier:")
    for tier in ["Max", "Mid", "Low"]:
        sub = df[df["tier"] == tier]
        s = (sub["T_PER"] - sub["T1_PER"]).mean()
        d = (sub["T_PER"] - sub["T2_PER"]).mean()
        print(f"    {tier:4s}  surge={s:+.2f}  drop={d:+.2f}  excess={d-s:+.2f}  (n={len(sub)})")
    print()


# ── Temporal holdout validation ───────────────────────────────────────────────

TEMPORAL_CUTOFF = 2019   # train on < cutoff, test on >= cutoff

def run_temporal_validation(df: pd.DataFrame) -> None:
    """
    Train OLS on contracts signed before TEMPORAL_CUTOFF, predict on contracts
    signed on or after.  This tests whether the model generalises across time —
    a stricter check than LOO-CV, which shuffles years randomly.
    """
    if not HAS_STATSMODELS:
        print("Skipping temporal validation (statsmodels not available)")
        return

    train = df[df["contractYear"] < TEMPORAL_CUTOFF].copy()
    test  = df[df["contractYear"] >= TEMPORAL_CUTOFF].copy()

    print("=" * 60)
    print(f"Temporal Holdout Validation  (cutoff: {TEMPORAL_CUTOFF})")
    print("=" * 60)
    print(f"  Train set : {len(train)} players  ({train['contractYear'].min()}–{train['contractYear'].max()})")
    print(f"  Test  set : {len(test)}  players  ({test['contractYear'].min()}–{test['contractYear'].max()})")
    print()

    if len(train) < 20 or len(test) < 10:
        print("  ⚠  Too few observations for a reliable split — skipping.")
        return

    X_train = train[FEATURE_COLS].values
    y_train = train["per_drop"].values
    X_test  = test[FEATURE_COLS].values
    y_test  = test["per_drop"].values

    X_train_c = sm.add_constant(X_train)
    X_test_c  = sm.add_constant(X_test, has_constant="add")

    model_train = sm.OLS(y_train, X_train_c).fit()

    # In-sample error on training set
    y_train_pred = model_train.predict(X_train_c)
    train_rmse   = np.sqrt(np.mean((y_train - y_train_pred) ** 2))
    train_mae    = np.mean(np.abs(y_train - y_train_pred))

    # Out-of-sample error on held-out test set
    y_test_pred  = model_train.predict(X_test_c)
    test_rmse    = np.sqrt(np.mean((y_test - y_test_pred) ** 2))
    test_mae     = np.mean(np.abs(y_test - y_test_pred))

    # Null model: predict training mean for every test player
    null_pred    = np.full_like(y_test, y_train.mean())
    null_rmse    = np.sqrt(np.mean((y_test - null_pred) ** 2))

    skill = (1 - test_rmse / null_rmse) * 100

    print(f"  Train RMSE : {train_rmse:.2f}  MAE: {train_mae:.2f}")
    print(f"  Test  RMSE : {test_rmse:.2f}  MAE: {test_mae:.2f}")
    print(f"  Null  RMSE : {null_rmse:.2f}  (predict training mean for all test players)")
    print(f"  Skill      : {skill:+.1f}% vs null")
    print()

    # Coefficient stability check — compare train-only vs full-data coefficients
    print("  Coefficient stability (train-only vs full-data):")
    full_X = sm.add_constant(df[FEATURE_COLS].values)
    model_full = sm.OLS(df["per_drop"].values, full_X).fit()
    labels = ["const"] + FEATURE_COLS
    for i, label in enumerate(labels):
        c_train = model_train.params[i]
        c_full  = model_full.params[i]
        drift   = c_train - c_full
        print(f"    {label:12s}  train={c_train:+.3f}  full={c_full:+.3f}  drift={drift:+.3f}")
    print()


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    df  = load_data()
    df  = prepare_features(df)

    print_tier_summary(df)
    run_ufa_analysis(df)
    run_within_subject_control(df)
    run_temporal_validation(df)

    if not HAS_STATSMODELS and not HAS_SKLEARN:
        sys.exit("Neither statsmodels nor sklearn available. Install one and retry.")

    if len(df) < 10:
        print(f"⚠  Only {len(df)} usable rows — regression results will be unreliable.")
        print("   Add more players via fetch_stats.py first.\n")

    if HAS_STATSMODELS:
        model = run_ols(df)
    else:
        model = None
        print("Skipping OLS (statsmodels not available)")

    if HAS_SKLEARN:
        run_loo_cv(df)
    else:
        print("Skipping LOO-CV (sklearn not available)")

    if model is not None:
        export_coefficients(model, df)
        print("\nNext steps:")
        print("  1. Expand dataset to 100+ players and re-run this script")
        print("  2. Features with p < 0.05 are statistically significant predictors")
        print("  3. Load model_coefficients.json in App.jsx to replace hardcoded weights")


if __name__ == "__main__":
    main()
