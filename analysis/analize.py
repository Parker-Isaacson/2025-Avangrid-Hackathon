import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "clean_data")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "analysis_outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_clean_csvs(data_dir: str) -> dict[str, pd.DataFrame]:
    """Load all cleaned CSVs into a dict of {asset_name: DataFrame}."""
    csv_files = [f for f in os.listdir(data_dir) if f.endswith(".csv")]
    data = {}
    for f in csv_files:
        name = os.path.splitext(f)[0]
        df = pd.read_csv(os.path.join(data_dir, f))
        # try to parse timestamp
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        data[name] = df
        print(f"Loaded {name}: {len(df)} rows, columns = {list(df.columns)}")
    return data


def compute_basic_stats(df: pd.DataFrame, asset_name: str):
    """Compute capacity factor, volatility, correlations, basis, and negative price events."""
    df = df.copy()

    # Ensure numeric columns
    for col in ["gen", "rt_busbar", "rt_hub", "da_busbar", "da_hub"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    stats = {}

    # Capacity factor
    if "gen" in df.columns:
        stats["capacity_factor"] = df["gen"].mean() / df["gen"].max()

    # Hub-busbar basis (RT and DA)
    if "rt_hub" in df.columns and "rt_busbar" in df.columns:
        df["rt_basis"] = df["rt_hub"] - df["rt_busbar"]
        stats["rt_basis_mean"] = df["rt_basis"].mean()
        stats["rt_basis_std"] = df["rt_basis"].std()

    if "da_hub" in df.columns and "da_busbar" in df.columns:
        df["da_basis"] = df["da_hub"] - df["da_busbar"]
        stats["da_basis_mean"] = df["da_basis"].mean()
        stats["da_basis_std"] = df["da_basis"].std()

    # Volatility
    for price_col in ["rt_hub", "rt_busbar", "da_hub", "da_busbar"]:
        if price_col in df.columns:
            stats[f"{price_col}_std"] = df[price_col].std()

    # Correlation between gen and prices
    if "gen" in df.columns:
        for price_col in ["rt_hub", "rt_busbar", "da_hub", "da_busbar"]:
            if price_col in df.columns:
                stats[f"corr_gen_{price_col}"] = df["gen"].corr(df[price_col])

    # Negative price frequency
    for price_col in ["rt_hub", "rt_busbar", "da_hub", "da_busbar"]:
        if price_col in df.columns:
            stats[f"neg_{price_col}_pct"] = (df[price_col] < 0).mean()

    # Save stats to CSV
    out_path = os.path.join(OUTPUT_DIR, f"{asset_name}_summary_stats.csv")
    pd.DataFrame([stats]).to_csv(out_path, index=False)
    print(f"Saved summary stats for {asset_name} → {out_path}")

    return df, stats


def extract_forward_curve(df: pd.DataFrame):
    if not {"peak_date", "peak", "off_peak"}.issubset(df.columns):
        print("No forward curve columns ('peak_date', 'peak', 'off_peak') found.")
        return None

    fwd = df[["peak_date", "peak", "off_peak"]].dropna()
    fwd["peak_date"] = pd.to_datetime(fwd["peak_date"], errors="coerce")
    fwd = fwd.dropna(subset=["peak_date"]).drop_duplicates(subset=["peak_date"])

    # Melt so we have both peak and off-peak entries
    fwd_long = fwd.melt(id_vars="peak_date", value_vars=["peak", "off_peak"],
                        var_name="period", value_name="price")
    fwd_long["price"] = pd.to_numeric(fwd_long["price"], errors="coerce")

    fwd_long = fwd_long.sort_values("peak_date").reset_index(drop=True)
    return fwd_long

def simulate_forward_prices(df: pd.DataFrame, fwd: pd.DataFrame, asset_name: str, sims: int = 200):
    if fwd is None or fwd.empty:
        print(f"No forward curve found for {asset_name}")
        return None

    # --- find best available hub column ---
    hub_col = None
    for candidate in ["rt_hub", "hub", "da_hub"]:
        if candidate in df.columns:
            hub_col = candidate
            break

    if hub_col is None:
        print(f"No hub price column found for {asset_name}. Skipping.")
        return None

    # --- prepare forward data ---
    fwd["peak_date"] = pd.to_datetime(fwd["peak_date"], errors="coerce")
    fwd = fwd.dropna(subset=["peak_date"]).sort_values("peak_date")

    hist_std = df[hub_col].std()
    months = pd.date_range("2026-01-01", "2030-12-31", freq="MS")

    simulated = []
    for m in months:
        # nearest 2 forward rows (usually peak/offpeak)
        nearest = fwd.iloc[(fwd["peak_date"] - m).abs().argsort()[:2]]
        for _, row in nearest.iterrows():
            base_price = row["price"]
            label = row["period"]

            # lower volatility for off-peak (optional realism tweak)
            vol = hist_std * (0.7 if "off" in label.lower() else 1.0)

            sim_prices = np.random.normal(base_price, vol, sims)
            simulated.append({
                "month": m,
                "period": label,
                "mean": np.mean(sim_prices),
                "p25": np.percentile(sim_prices, 25),
                "p50": np.percentile(sim_prices, 50),
                "p75": np.percentile(sim_prices, 75),
                "p90": np.percentile(sim_prices, 90)
            })

    sim_df = pd.DataFrame(simulated)

    # --- save outputs ---
    sim_out = os.path.join(OUTPUT_DIR, f"{asset_name}_forward_sim.csv")
    sim_df.to_csv(sim_out, index=False)
    print(f"Saved simulated forward prices for {asset_name} → {sim_out}")

    plt.figure(figsize=(9, 5))
    for period, sub in sim_df.groupby("period"):
        plt.fill_between(sub["month"], sub["p25"], sub["p75"], alpha=0.2, label=f"{period} P25–P75")
        plt.plot(sub["month"], sub["mean"], label=f"{period} mean")

    plt.title(f"Simulated Forward Price Range ({asset_name})")
    plt.xlabel("Month")
    plt.ylabel("$/MWh")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, f"{asset_name}_forward_sim.png"))
    plt.close()

def main():
    datasets = load_clean_csvs(DATA_DIR)

    for name, df in datasets.items():
        df, stats = compute_basic_stats(df, name)
        fwd = extract_forward_curve(df)
        simulate_forward_prices(df, fwd, name)


if __name__ == "__main__":
    main()

