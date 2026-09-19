# Dynamic Market Share (MS) — DAX measures

Built for `data/cleaned/data_25_vs_26_table_cleaned.csv` loaded into Power BI as a single flat table
(columns: `Main CAT, Sub CAT, Class, Sub Class, Company, Brand, SKU Description, Year, Total Sellout`).

Replace the table name `Sales` below with whatever name Power BI gives the table on import
(Model view → rename the table to `Sales` to use these measures as-is, or find/replace `Sales[` with
`'YourTableName'[`).

## How "dynamic" works here

One measure covers every combination the request asked for — Company **or** Brand **or** SKU, at
Main CAT **or** Sub CAT **or** Class **or** Sub Class level — with no separate measure per level.

The trick: the denominator recalculates the total by removing filters from *only* the entity columns
(`Company`, `Brand`, `SKU Description`), while leaving whatever category filters are already in effect
(a slicer, or higher rows in a matrix drill-down) untouched. So:

- Put **Company** (or **Brand**, or **SKU Description**) on rows → market share of each one.
- Filter/slice by **Main CAT**, **Sub CAT**, **Class**, or **Sub Class** (or drill through a matrix
  hierarchy of all four) → the share automatically recalculates against whichever level is active,
  because that filter was never removed.
- No field parameter, no per-level measure, no manual switch needed.

## Core measures

```DAX
Total Sellout =
SUM ( Sales[Total Sellout] )
```

```DAX
Category Total Sellout =
-- Same context as [Total Sellout], but with Company/Brand/SKU filters stripped out,
-- so it always totals "everyone else in the same Main CAT / Sub CAT / Class / Sub Class".
CALCULATE (
    [Total Sellout],
    ALLSELECTED ( Sales[Company], Sales[Brand], Sales[SKU Description] )
)
```

```DAX
Market Share % =
DIVIDE ( [Total Sellout], [Category Total Sellout] )
```

Format `Market Share %` as a percentage (0.0%) in the measure's formatting pane.

### Optional: blank out subtotal/grand-total rows in a matrix

A matrix subtotal row has no Company/Brand/SKU value pinned, so numerator = denominator there and the
measure shows 100%. If you'd rather leave those cells blank:

```DAX
Market Share % (leaf only) =
IF (
    HASONEVALUE ( Sales[Company] )
        || HASONEVALUE ( Sales[Brand] )
        || HASONEVALUE ( Sales[SKU Description] ),
    [Market Share %]
)
```

## Year-over-year market share (2025 vs 2026)

Since this file's whole point is a 2025-vs-2026 comparison, these pair naturally with the measures above:

```DAX
Total Sellout 2025 =
CALCULATE ( [Total Sellout], Sales[Year] = 2025 )
```

```DAX
Total Sellout 2026 =
CALCULATE ( [Total Sellout], Sales[Year] = 2026 )
```

```DAX
Category Total Sellout 2025 =
CALCULATE ( [Category Total Sellout], Sales[Year] = 2025 )
```

```DAX
Category Total Sellout 2026 =
CALCULATE ( [Category Total Sellout], Sales[Year] = 2026 )
```

```DAX
Market Share % 2025 =
DIVIDE ( [Total Sellout 2025], [Category Total Sellout 2025] )
```

```DAX
Market Share % 2026 =
DIVIDE ( [Total Sellout 2026], [Category Total Sellout 2026] )
```

```DAX
Market Share Change (pp) =
-- Percentage-point change in share, 2025 -> 2026 (not % growth of the share itself)
[Market Share % 2026] - [Market Share % 2025]
```

## Optional: rank within the current category level

Commonly shown next to market share:

```DAX
Rank in Category =
IF (
    [Total Sellout] <> 0,
    RANKX (
        ALLSELECTED ( Sales[Company], Sales[Brand], Sales[SKU Description] ),
        [Total Sellout],
        ,
        DESC,
        DENSE
    )
)
```

## Letting the user pick Company / Brand / SKU from one slicer (optional)

The measures above already work with whichever of `Company`, `Brand`, `SKU Description` is placed on
the visual — no extra DAX needed. If you also want a single slicer that swaps which one is used, without
building three separate visuals:

1. **Modeling** ribbon → **New parameter** → **Fields**.
2. Add `Sales[Company]`, `Sales[Brand]`, `Sales[SKU Description]` as the fields, name the parameter
   e.g. `Analyze By`.
3. Put the generated `Analyze By` field on the visual's rows (instead of Company/Brand/SKU directly) and
   drop the `Analyze By` slicer on the page.
4. Use the exact same `Market Share %` measure as the value — it needs no change, since Power BI swaps
   in the real underlying column at query time.

Do the same for Main CAT / Sub CAT / Class / Sub Class if you also want one slicer to pick the
benchmarking level instead of a matrix drill-down.
