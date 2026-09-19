# Data-analysis

Sales data validation & cleaning for the 2025 vs 2026 Power BI extract.

- `data/raw/` — original, untouched source file.
- `data/cleaned/` — cleaned dataset (same rows and `Total Sellout` values as the source, text/category
  columns fixed) plus review files for items that need a human decision.
- `scripts/clean_sales_data.py` — the deterministic cleaning script (re-run with `python3 scripts/clean_sales_data.py`).
- `reports/data_validation_report.md` — full write-up of every issue found and how it was handled.
