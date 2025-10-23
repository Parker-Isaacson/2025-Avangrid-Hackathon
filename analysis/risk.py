import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "clean_data")
ANALYSIS_DIR = os.path.join(os.path.dirname(__file__), "analysis_outputs")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "risk_outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def calc_risk_adjusted_price(asset_name: str):
    print(f"Processing {asset_name}...")

    clean_path = os.path.join(DATA_DIR, f"{asset_name}_clean.csv")
    sim_path = os.path.join(ANALYSIS_DIR, f"{asset_name}_clean_forward_sim.csv")

    # === Load generation data ===
    gen_df = pd.read_csv(clean_path, parse_dates=["timestamp"])
    gen_df["month"] = gen_df["timestamp"].dt.to_period("M").dt.to_timestamp()

    # Normalize period column
    period_col = next((c for c in gen_df.columns if c.lower().replace("_", "").replace("/", "") == "pop"), None)
    if period_col:
        gen_df["period"] = (
            gen_df[period_col].astype(str).str.strip().str.lower()
            .replace({"p": "peak", "op": "off_peak", "off": "off_peak"})
        )
    else:
        gen_df["period"] = "off_peak"

    monthly_gen = (
        gen_df.groupby(["month", "period"])["gen"]
        .sum()
        .reset_index()
        .rename(columns={"gen": "monthly_gen_mwh"})
    )

    # === Load forward simulation ===
    sim_df = pd.read_csv(sim_path, parse_dates=["month"])
    if "period" not in sim_df.columns:
        sim_df["period"] = "off_peak"
    sim_df["period"] = sim_df["period"].astype(str).str.lower().replace({"off": "off_peak"})

    # === Repeat generation pattern for all simulated years ===
    sim_years = sim_df["month"].dt.year.unique()
    gen_repeated = pd.concat([
        monthly_gen.assign(month=lambda df, y=year: df["month"].apply(lambda x: x.replace(year=y)))
        for year in sim_years
    ])
    monthly_gen = gen_repeated

    # === Merge & compute ===
    df = pd.merge(sim_df, monthly_gen, on=["month", "period"], how="left")
    df["monthly_gen_mwh"] = df["monthly_gen_mwh"].fillna(monthly_gen["monthly_gen_mwh"].mean())

    for col in ["p25", "p50", "p75"]:
        df[f"revenue_{col}"] = df[col] * df["monthly_gen_mwh"]

    total_gen = df["monthly_gen_mwh"].sum()
    if total_gen == 0:
        print(f"{asset_name}: No generation after merge.")
        return {"asset": asset_name, "p25_price": np.nan, "p50_price": np.nan, "p75_price": np.nan, "risk_premium": np.nan}

    p25_price = df["revenue_p25"].sum() / total_gen
    p50_price = df["revenue_p50"].sum() / total_gen
    p75_price = df["revenue_p75"].sum() / total_gen
    risk_premium = p75_price - p25_price

    return {
        "asset": asset_name,
        "p25_price": round(p25_price, 2),
        "p50_price": round(p50_price, 2),
        "p75_price": round(p75_price, 2),
        "risk_premium": round(risk_premium, 2),
    }


def create_comparison_chart(summary):
    """Creates final chart for P25/P50/P75 comparison."""
    plt.figure(figsize=(8, 5))
    bar_width = 0.25
    x = np.arange(len(summary))

    plt.bar(x - bar_width, summary["p25_price"], width=bar_width, label="P25", color="#ef476f")
    plt.bar(x, summary["p50_price"], width=bar_width, label="P50", color="#ffd166")
    plt.bar(x + bar_width, summary["p75_price"], width=bar_width, label="P75", color="#06d6a0")

    for i, (p25, p50, p75) in enumerate(zip(summary["p25_price"], summary["p50_price"], summary["p75_price"])):
        for j, val in enumerate([p25, p50, p75]):
            xpos = i - bar_width + j * bar_width
            plt.text(xpos, val + 2, f"{val:.0f}", ha="center", va="bottom", fontsize=8)

    plt.xticks(x, summary["asset"])
    plt.ylabel("Price ($/MWh)")
    plt.title("Risk-Adjusted Hedge Prices by Market (2026–2030)")
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    plt.tight_layout()

    chart_path = os.path.join(OUTPUT_DIR, "risk_adjusted_comparison.png")
    plt.savefig(chart_path, dpi=300)
    plt.close()
    print(f"Chart saved → {chart_path}")


if __name__ == "__main__":
    assets = ["ERCOT", "MISO", "CAISO"]
    results = [calc_risk_adjusted_price(a) for a in assets]

    summary = pd.DataFrame(results)
    summary_path = os.path.join(OUTPUT_DIR, "risk_adjusted_summary.csv")
    summary.to_csv(summary_path, index=False)

    print("\nFinal Risk-Adjusted Summary:")
    print(summary)

    create_comparison_chart(summary)
