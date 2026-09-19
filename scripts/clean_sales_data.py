"""
Validate and clean the Power BI sales extract (data_25_vs_26_Table.csv).

Rule #1: Total Sellout values are never modified, summed, dropped or
reordered relative to the source file. Every change made here is to
text/categorical columns (whitespace, spelling, missing labels) or is a
flag added for manual review.

Run: python3 scripts/clean_sales_data.py
"""
import re
import pandas as pd

RAW_PATH = "data/raw/data_25_vs_26_table_raw.csv"
CLEANED_PATH = "data/cleaned/data_25_vs_26_table_cleaned.csv"
FLAGS_PATH = "data/cleaned/data_quality_flags.csv"

TEXT_COLS = ["Main CAT", "Sub CAT", "Class", "Sub Class", "Company", "Brand", "SKU Description"]

# Confirmed via cross-referencing other rows in this same file (same Brand
# has exactly one non-null Company elsewhere) — not a guess.
COMPANY_FILL_BY_BRAND = {
    "Pediasure": "شركة مكتب الكمال للاستيراد المحدودة",
    "Similac": "شركة مكتب الكمال للاستيراد المحدودة",
    "Ozmo": "مؤسسات سقالة التجارية",
}

# Two spellings of the same legal entity (تاء مربوطة vs هاء) found only for
# this one company. Standardized on the more common spelling (637 vs 138 rows).
COMPANY_SPELLING_FIXES = {
    "شركة نستله العربيه السعوديه": "شركة نستله العربية السعودية",
}


def collapse_ws(x):
    if not isinstance(x, str):
        return x
    return re.sub(r"\s+", " ", x.strip())


def clean_sku(x):
    if not isinstance(x, str):
        return x
    x = collapse_ws(x)
    x = x.rstrip(".")
    return x.strip()


def main():
    df = pd.read_csv(RAW_PATH, encoding="utf-8-sig")
    original_sum = df["Total Sellout"].sum()
    original_len = len(df)
    original_values = df["Total Sellout"].copy()

    flags = pd.Series([""] * len(df), index=df.index, dtype=object)

    def add_flag(mask, text):
        flags.loc[mask] = flags.loc[mask].apply(lambda v: (v + "|" if v else "") + text)

    # 1. Whitespace cleanup on all text columns (trim + collapse internal runs).
    for col in TEXT_COLS:
        before = df[col]
        after = before.apply(collapse_ws)
        changed = (before.astype(object) != after.astype(object)) & before.notna()
        if changed.any():
            add_flag(changed, f"whitespace_cleaned:{col}")
        df[col] = after

    # 2. Strip trailing period(s) from SKU Description (confirmed formatting
    #    artifact — appears after the pack size on ~350 distinct SKU names
    #    with no semantic meaning, e.g. "...125G." / "...400G .").
    before = df["SKU Description"]
    after = before.apply(clean_sku)
    changed = (before.astype(object) != after.astype(object)) & before.notna()
    if changed.any():
        add_flag(changed, "sku_trailing_period_removed")
    df["SKU Description"] = after

    # 3. Standardize the one Company spelling variant.
    for wrong, right in COMPANY_SPELLING_FIXES.items():
        mask = df["Company"] == wrong
        if mask.any():
            add_flag(mask, "company_spelling_standardized")
            df.loc[mask, "Company"] = right

    # 4. Fill missing Company using unambiguous same-brand cross-reference.
    for brand, company in COMPANY_FILL_BY_BRAND.items():
        mask = (df["Brand"] == brand) & df["Company"].isna()
        if mask.any():
            add_flag(mask, "company_filled_from_brand")
            df.loc[mask, "Company"] = company

    # 5. Missing SKU Description cannot be recovered from other rows — flag only.
    mask = df["SKU Description"].isna()
    add_flag(mask, "missing_sku_description")

    # 6. Flag zero-sales rows (legitimate, kept as-is).
    mask = df["Total Sellout"] == 0
    add_flag(mask, "zero_sellout")

    # 7. Flag same Company+Brand+SKU(normalized)+Year appearing more than once —
    #    could be genuinely distinct source records or true duplicates; left as
    #    separate rows (never summed/merged) so no sales value is altered.
    key_cols = ["Company", "Brand", "SKU Description", "Year"]
    dup_mask = df.duplicated(subset=key_cols, keep=False)
    add_flag(dup_mask, "duplicate_key_same_year_review")

    df["Data_Quality_Flag"] = flags

    # --- Safety checks: prove Total Sellout was never touched ---
    assert len(df) == original_len, "Row count changed!"
    assert (df["Total Sellout"].values == original_values.values).all(), "A Total Sellout value changed!"
    assert abs(df["Total Sellout"].sum() - original_sum) < 1e-6, "Sum of Total Sellout changed!"

    df.to_csv(CLEANED_PATH, index=False, encoding="utf-8-sig")

    # Human-review file: exclude the purely cosmetic, auto-applied fixes
    # (whitespace, the one confirmed spelling fix) — keep only rows where a
    # judgment call was made or is still needed.
    review_tags = ["company_filled_from_brand", "missing_sku_description", "duplicate_key_same_year_review"]
    review_mask = df["Data_Quality_Flag"].apply(lambda v: any(t in v for t in review_tags))
    flagged = df[review_mask].copy()
    flagged.to_csv(FLAGS_PATH, index=False, encoding="utf-8-sig")

    print(f"Rows: {len(df)} (unchanged)")
    print(f"Total Sellout sum: {df['Total Sellout'].sum():.6f} (unchanged)")
    print(f"Rows needing manual review: {len(flagged)}")
    for tag in review_tags:
        print(f"  {tag}: {df['Data_Quality_Flag'].str.contains(tag, regex=False).sum()}")


if __name__ == "__main__":
    main()
