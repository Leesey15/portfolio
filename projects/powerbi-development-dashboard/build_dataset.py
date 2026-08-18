import pandas as pd

who = pd.read_csv("/tmp/test_life2.csv")
who.columns = [c.strip() for c in who.columns]
regions = pd.read_csv("/tmp/country_regions.csv")[["name", "alpha-3", "region", "sub-region"]]

alias = {
    "Bolivia (Plurinational State of)": "Bolivia, Plurinational State of",
    "Democratic People's Republic of Korea": "Korea, Democratic People's Republic of",
    "Democratic Republic of the Congo": "Congo, Democratic Republic of the",
    "Iran (Islamic Republic of)": "Iran, Islamic Republic of",
    "Micronesia (Federated States of)": "Micronesia, Federated States of",
    "Netherlands": "Netherlands, Kingdom of the",
    "Republic of Korea": "Korea, Republic of",
    "Republic of Moldova": "Moldova, Republic of",
    "Swaziland": "Eswatini",
    "The former Yugoslav republic of Macedonia": "North Macedonia",
    "Turkey": "Türkiye",
    "United Republic of Tanzania": "Tanzania, United Republic of",
    "Venezuela (Bolivarian Republic of)": "Venezuela, Bolivarian Republic of",
}
regions_by_name = dict(zip(regions["name"], zip(regions["alpha-3"], regions["region"], regions["sub-region"])))

def lookup(country):
    key = alias.get(country, country)
    return regions_by_name.get(key, (None, None, None))

who["ISO3"], who["Region"], who["SubRegion"] = zip(*who["Country"].map(lookup))
assert who["ISO3"].isna().sum() == 0, "unmapped countries remain"

# Rename columns to clean, Power-BI-friendly names
rename = {
    "Life expectancy": "LifeExpectancy",
    "Adult Mortality": "AdultMortality",
    "infant deaths": "InfantDeaths",
    "percentage expenditure": "HealthExpenditurePctGDP",
    "Hepatitis B": "HepatitisB_ImmunizationPct",
    "under-five deaths": "UnderFiveDeaths",
    "Total expenditure": "GovHealthExpenditurePct",
    "HIV/AIDS": "HIV_AIDS_DeathsPer1000",
    "thinness  1-19 years": "Thinness_10to19",
    "thinness 5-9 years": "Thinness_5to9",
    "Income composition of resources": "IncomeCompositionOfResources",
    "Schooling": "SchoolingYears",
    "GDP": "GDPPerCapitaUSD",
}
who = who.rename(columns=rename)

# ---- Dim_Country ----
dim_country = (
    who[["Country", "ISO3", "Region", "SubRegion", "Status"]]
    .drop_duplicates(subset=["Country"])
    .sort_values("Country")
    .reset_index(drop=True)
)
dim_country.insert(0, "CountryKey", range(1, len(dim_country) + 1))

# ---- Dim_Year ----
years = sorted(who["Year"].unique())
dim_year = pd.DataFrame({"Year": years})
dim_year.insert(0, "YearKey", range(1, len(dim_year) + 1))

# ---- Fact table ----
fact = who.merge(dim_country[["Country", "CountryKey"]], on="Country") \
          .merge(dim_year, on="Year")
fact_cols = [
    "CountryKey", "YearKey", "LifeExpectancy", "AdultMortality", "InfantDeaths",
    "Alcohol", "HealthExpenditurePctGDP", "HepatitisB_ImmunizationPct", "Measles",
    "BMI", "UnderFiveDeaths", "Polio", "GovHealthExpenditurePct", "Diphtheria",
    "HIV_AIDS_DeathsPer1000", "GDPPerCapitaUSD", "Population", "Thinness_10to19", "Thinness_5to9",
    "IncomeCompositionOfResources", "SchoolingYears",
]
fact_table = fact[fact_cols].copy()

dim_country.to_csv("Dim_Country.csv", index=False)
dim_year.to_csv("Dim_Year.csv", index=False)
fact_table.to_csv("Fact_HealthDevelopment.csv", index=False)

print("Dim_Country:", dim_country.shape)
print("Dim_Year:", dim_year.shape)
print("Fact_HealthDevelopment:", fact_table.shape)
print(dim_country.head(3).to_string())
print(fact_table.head(3).to_string())
