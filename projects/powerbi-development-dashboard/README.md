# Global Human Development Dashboard — Power BI Build Kit

**Author:** Aseye Amenuveve Gbagbo

## Purpose

An interactive dashboard exploring the relationship between health, education, income, and life expectancy across 193 countries (2000-2015) — deliberately mirroring the three components of the UN Human Development Index (health/life expectancy, education, income), the kind of indicator work UNDP's Digital, AI and Innovation Hub uses to track its own Digital Strategy and development outcomes.

**Status:** data modeling and measures are complete and included in this folder; the visuals themselves are built directly in Power BI Desktop (not available in this build environment), by design — see `Power BI handling` in the project notes. Screenshots are added once built.

## Dataset

WHO Global Health Observatory life expectancy data (public, via a GitHub-hosted mirror of the well-known "Life Expectancy (WHO)" dataset), enriched with UN region/sub-region classifications from the [ISO-3166 country codes dataset](https://github.com/lukes/ISO-3166-Countries-with-Regional-Codes). Covers 193 countries, 2000-2015: life expectancy, adult/infant mortality, immunization rates, health expenditure, GDP per capita, population, schooling years, and income composition of resources (a 0-1 scaled proxy for the income component of HDI).

**Known data quality note:** this is a real public health dataset with genuine gaps — several indicators (GDP, Population, Alcohol, Total expenditure) have missing values for some country-years, and a few GDP figures show implausible year-to-year swings (a documented quirk of this dataset). Rather than silently filling these, the model keeps them as blanks so Power BI's aggregate visuals handle them correctly (excluded from averages, not treated as zero) — worth mentioning if asked about data quality in an interview.

## Data model (star schema)

```
Dim_Country.csv               (193 rows)  CountryKey, Country, ISO3, Region, SubRegion, Status
Dim_Year.csv                  (16 rows)   YearKey, Year
Fact_HealthDevelopment.csv    (2,938 rows) CountryKey, YearKey, + 18 indicator columns
```

Relationships (both many-to-one, single direction, from Fact to each Dim):
- `Fact_HealthDevelopment[CountryKey]` → `Dim_Country[CountryKey]`
- `Fact_HealthDevelopment[YearKey]` → `Dim_Year[YearKey]`

This mirrors the star-schema approach from the AfiLearn data warehouse project — same modeling principle, different tool.

## Build steps (Power BI Desktop)

1. **Get Data → Text/CSV** — import all three CSVs from this folder.
2. **Model view** — confirm/create the two relationships above (Power BI usually auto-detects them from the `*Key` column names; verify cardinality is many-to-one and cross-filter direction is single, Fact → Dim).
3. **New Measure** on `Fact_HealthDevelopment` — add each DAX measure below.
4. Build the three report pages described under **Layout**.
5. **File → Export → Export to PDF** (or screenshot each page) and drop the images into this folder as `screenshot_overview.png`, `screenshot_hdi_lens.png`, `screenshot_regional.png`.

## DAX measures

```dax
Total Population =
SUM ( Fact_HealthDevelopment[Population] )

Countries Tracked =
DISTINCTCOUNT ( Fact_HealthDevelopment[CountryKey] )

Avg Life Expectancy =
AVERAGE ( Fact_HealthDevelopment[LifeExpectancy] )

Avg Schooling Years =
AVERAGE ( Fact_HealthDevelopment[SchoolingYears] )

Avg Income Composition =
AVERAGE ( Fact_HealthDevelopment[IncomeCompositionOfResources] )

Avg GDP Per Capita =
AVERAGE ( Fact_HealthDevelopment[GDPPerCapitaUSD] )

Life Expectancy YoY Change =
VAR CurrentYear = MAX ( Dim_Year[Year] )
VAR PriorYearAvg =
    CALCULATE (
        [Avg Life Expectancy],
        FILTER ( ALL ( Dim_Year ), Dim_Year[Year] = CurrentYear - 1 )
    )
RETURN
    [Avg Life Expectancy] - PriorYearAvg

Life Expectancy Rank =
RANKX ( ALL ( Dim_Country ), [Avg Life Expectancy], , DESC )
```

## Layout — 3 report pages

**Page 1 — Global Overview**
- KPI cards (top row): Countries Tracked, Avg Life Expectancy, Avg Schooling Years, Avg GDP Per Capita
- Filled map, colored by Avg Life Expectancy (use `Country` or `ISO3` as location field — ISO3 is more reliable for Power BI's geocoding)
- Line chart: Avg Life Expectancy by Year, two series split by `Status` (Developed vs Developing) — shows the development gap narrowing or persisting over time
- Slicers: Year (range slider), Region, Status

**Page 2 — Human Development Lens** *(mirrors HDI's 3 components: health, education, income)*
- Three large KPI cards: Avg Life Expectancy (health), Avg Schooling Years (education), Avg Income Composition (income)
- Scatter chart: `GDPPerCapitaUSD` (X) vs `LifeExpectancy` (Y), bubble size = `Population`, color = `Region`, with a Year slicer/play-axis if using Power BI's animated scatter — this is the classic "Gapminder" view of development
- Bar chart: Top 15 countries by Avg Income Composition of Resources

**Page 3 — Regional Comparison**
- Bar chart: Avg Life Expectancy by Region
- Table: Region | Avg Life Expectancy | Avg Schooling Years | Avg GDP Per Capita | Countries Tracked
- Line chart: Avg Life Expectancy trend by Region, 2000-2015

## Files

```
build_dataset.py              # reproduces the cleaning/star-schema build from the raw source data
Dim_Country.csv
Dim_Year.csv
Fact_HealthDevelopment.csv
README.md                     # this file
```

## Why this project

Chosen deliberately to echo UNDP's own work: tracking development indicators across countries, at scale, to inform policy — directly relevant to the Data Analytics & Insights workstream this application targets.
