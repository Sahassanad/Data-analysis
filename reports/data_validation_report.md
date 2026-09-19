# Data Validation & Cleaning Report — Sales 2025 vs 2026 (Power BI extract)

**Source file:** `data_25_vs_26_Table.csv` (Power BI export)
**Rows:** 3,605 | **Columns:** 9 (`Main CAT, Sub CAT, Class, Sub Class, Company, Brand, SKU Description, Year, Total Sellout`)

**Golden rule applied throughout:** `Total Sellout` was never edited, summed, dropped, reordered or recalculated.
The script asserts row count, per-row values and the grand total are byte-identical to the source before writing
output. Only text/categorical columns were touched, and only when the fix was unambiguous.

## Files produced

| File | Description |
|---|---|
| `data/raw/data_25_vs_26_table_raw.csv` | Untouched copy of the original upload, kept for audit/reproducibility. |
| `data/cleaned/data_25_vs_26_table_cleaned.csv` | Cleaned dataset, same 3,605 rows, same `Total Sellout` values, plus a `Data_Quality_Flag` audit column. |
| `data/cleaned/data_quality_flags.csv` | The 427 rows that need a **human** decision (not auto-fixed). |
| `data/cleaned/brands_with_multiple_companies.csv` | 18 brands sold under more than one Company name — needs business confirmation. |
| `scripts/clean_sales_data.py` | The cleaning script itself (deterministic, re-runnable). |

## Issues found and how each was handled

### 1. Leading/trailing/double whitespace (auto-fixed, no risk)
- **Company**: 3,597 of 3,605 rows had a stray leading space (e.g. `" شركة تان الخليجية التجارية"`). Trimmed.
- 3 Company values also had a double internal space (e.g. `"شركة  الخير للتجارة المحدودة"`). Collapsed to one.
- **SKU Description**: 27 rows had extra/trailing whitespace. Trimmed.
- No value in any other column was affected; this is purely cosmetic.

### 2. Trailing period on SKU Description (auto-fixed — high impact for this file's purpose)
416 rows (347 distinct SKU names) had a stray period appended after the pack size, e.g.
`"HERO BABY MIXED FRUITS 125G."`, `"CERELAC WHEAT REGULAR 1000G."`. None of these look like a real abbreviation —
they're all "size + `.`" with no other examples of meaningful trailing punctuation in this column.
**This matters specifically for a 2025-vs-2026 file**: in ~46 cases the *same* SKU was recorded with the dot in
one year and without it in the other, which would make that SKU look like it "disappeared" or "launched" year over
year purely because of punctuation. The trailing period was stripped so the same product name matches across years.
No `Total Sellout` value was touched — only the label.

### 3. One Company name had two Arabic spellings (auto-fixed)
`"شركة نستله العربية السعودية"` (637 rows) and `"شركة نستله العربيه السعوديه"` (138 rows) are the same legal
entity — the only difference is تاء مربوطة (ة) vs هاء (ه) at the end of two words, a very common transliteration
inconsistency. Standardized on the more common spelling. This was checked to be the **only** company name in the
file with this kind of variant (verified programmatically across all 128 company names).

### 4. Missing Company (8 rows) — filled from unambiguous cross-reference
Rows for Brand `Pediasure` and `Similac` (7 rows) and `Ozmo` (1 row) had a blank Company. Each of these brands
appears elsewhere in the *same file* with exactly one Company value, so the fill is not a guess:
- `Pediasure`, `Similac` → `شركة مكتب الكمال للاستيراد المحدودة`
- `Ozmo` → `مؤسسات سقالة التجارية`

### 5. Missing SKU Description (3 rows) — left blank, flagged
Rows 1469, 1470 (Ferrero, Dark/Fruit&Nut Chocolate Bars, 2026) and 1503 (Bounty, Caramel Chocolate Bars, 2026)
have no SKU text and nothing else in the file identifies them. **Not guessed.** Their `Total Sellout`
(795.12, 299.80, 36,081.50 respectively) is intact — only the description is blank. Recommend pulling the SKU
name from the source system/master data.

### 6. Category hierarchy — clean
Checked `Main CAT → Sub CAT → Class → Sub Class` for any Sub Class/Class/Sub CAT mapping to more than one parent:
**zero violations**. The hierarchy is internally consistent, so no fix was needed here.

### 7. 212 groups (425 rows) share an identical Company + Brand + SKU + Year key but differ in `Total Sellout`
After the cleanup above, 212 groups (mostly pairs, one triple) turned out to have exactly the same identifying
combination within the same year, e.g.:

| Company | Brand | SKU Description | Year | Total Sellout |
|---|---|---|---|---|
| ALDurra For General Trading Co. Ltd | Durra | DURRA TOMATO PASTE 800G | 2025 | 2,731.13 |
| ALDurra For General Trading Co. Ltd | Durra | DURRA TOMATO PASTE 800G | 2025 | 29,169.56 |

These were **left as two separate rows** — merging/summing them would change what a "row" represents even
though no individual number would be altered, and it's not possible to tell from this file alone whether they are
genuinely distinct source records (different internal SKU/batch codes, different retailer channel, etc.) or a true
duplicate that should be added together. Full list in `data/cleaned/data_quality_flags.csv`. **Recommend checking
against the Power BI/source data model** — if these are true duplicates, sum them; if not, no action needed.

### 8. 18 brands are sold under more than one Company name (not changed — needs confirmation)
E.g. `Nestle` under `شركة نستله العربية السعودية` (170 rows) and `شركة سيف فود للتجارة` (1 row); `Starbucks`
under `شركة نستله العربية السعودية` and `شركة آرلا للأغذية المحدودة`. This is very plausibly legitimate
(the same brand distributed by more than one distributor), so nothing was merged. Full breakdown in
`data/cleaned/brands_with_multiple_companies.csv` — worth a quick sanity check with whoever owns the source data,
since one entry (`Haley`, 11 different companies) is worth a second look.

### 9. Zero-sales rows (6 rows) — kept as-is
6 rows have `Total Sellout = 0`. These are legitimate (a listed SKU with no sales that period) and were left
untouched, just flagged for visibility.

### 10. A short list of SKU names that look truncated/garbled (not changed — for manual review only)
No source of truth exists in this file to correct these, so nothing was rewritten. Worth checking against the
master SKU list: `ARCOR G SO`, `BOUNTY G SO`, `GALAXY G SO`, `KINDER G SO` (missing the pack size before "G SO"),
`GALAXY CHOCO 3`, `KINDER CHOCLATE 2`, `GALAXY B SMOTH MILK 18B 227`, `GALAXY CHOCO SMTH MLK CHOCO 137`,
`FERRERO HAZNUT&ALMON HAZNUT&ALMON90G` (repeated text), `NESTLE CARAM&CHOC W.CARAM&CHOC 15` (repeated text),
`NESTLE x W.CARM&CHOC7x15`, `NIDO M.FIBER POUCH BAG1800G10`.

### 11. Not an issue
- `Year` contains only `2025` / `2026`, correct type (int), no stray values.
- `Total Sellout` is a clean float column, no currency symbols/thousand separators/negatives; min 0, max ≈14.0M.
- No fully-duplicated rows (identical across all 9 columns) existed even before cleaning.

## Summary counts

| Check | Count |
|---|---|
| Rows in file | 3,605 |
| Total Sellout sum (before = after) | 849,938,100.94 |
| Rows with whitespace fixed | 3,597 (Company) + 27 (SKU Description) |
| SKU names with trailing period removed | 416 rows / 347 distinct names |
| Company spelling standardized | 138 rows |
| Missing Company filled | 8 rows |
| Missing SKU Description (unresolved) | 3 rows |
| Rows in same-year duplicate-key groups (flagged, not merged) | 425 rows / 212 groups |
| Brands under >1 Company (flagged, not merged) | 18 brands |
| Zero-sales rows | 6 rows |
