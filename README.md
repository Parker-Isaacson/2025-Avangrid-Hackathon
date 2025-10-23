# 2025 Avangrid Hackathon

This repository contains the full analysis pipeline and final results for our hackathon project on **merchant renewable energy valuation** and **risk-adjusted pricing**.

---

## Repository Overview

The project is structured into several main directories:

* **`data/`** — Contains raw and cleaned datasets.
  Includes scripts for data ingestion and preprocessing.
* **`analysis/`** — Contains analysis scripts that perform forecasting, valuation, and risk adjustment.
* **`results/`** — Contains the compiled outputs, charts, and summaries produced by the analysis.

---

## Environment Setup

To reproduce the results, you’ll need to set up a Python virtual environment and install dependencies.

### On Windows

```powershell
python -m venv Hackathon
.\Hackathon\Scripts\activate.ps1
pip install -r requirements.txt
```

### On Linux / macOS

```bash
python -m venv Hackathon
source Hackathon/bin/activate
pip install -r requirements.txt
```

---

## Pipeline Execution

Each script builds on the previous step to clean data, perform simulations, and compute risk-adjusted prices.

1. **Data Cleaning**
   Run `parse.py` (in the `data/` folder) to generate cleaned CSVs for downstream analysis.

   ```bash
   # Windows
   python data\parse.py

   # Linux / macOS
   python data/parse.py
   ```

2. **Analysis and Forecasting**
   Run `analyze.py` (in the `analysis/` folder) to create processed data, simulated forward prices, and visual diagnostics.

   ```bash
   # Windows
   python analysis\analyze.py

   # Linux / macOS
   python analysis/analyze.py
   ```

3. **Risk Adjustment and Valuation**
   Run `risk_pricing.py` (in the `analysis/` folder) to compute risk-adjusted hedge prices and generate the final comparison chart.

   ```bash
   # Windows
   python analysis\risk_pricing.py

   # Linux / macOS
   python analysis/risk_pricing.py
   ```

---

## Results

After running the full pipeline, you’ll find:

* **`analysis/risk_outputs/risk_adjusted_summary.csv`** — The final summary table containing P25, P50, and P75 price levels for each market.
* **`analysis/risk_outputs/risk_adjusted_comparison.png`** — The visualization comparing risk-adjusted hedge prices across markets.

---

## Notes

* Intermediate files (e.g., merged diagnostics or temporary simulation data) are excluded via `.gitignore` to keep the repository lightweight.
