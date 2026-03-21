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

    # Drop rows where T+1 data is missing (player retired, injury, etc.)
    before = len(df)
    df = df[df["T2_PER"] != 0.0].copy()
    dropped = before - len(df)
    if dropped:
        print(f"⚠  Dropped {dropped} players with missing T+1 data (injury/retirement)")

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


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    df  = load_data()
    df  = prepare_features(df)

    print_tier_summary(df)

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
