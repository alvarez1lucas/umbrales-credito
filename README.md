# Credit thresholds

[![Tests](https://github.com/alvarez1lucas/umbrales-credito/actions/workflows/tests.yml/badge.svg)](https://github.com/alvarez1lucas/umbrales-credito/actions/workflows/tests.yml) [![Data refresh](https://github.com/alvarez1lucas/umbrales-credito/actions/workflows/actualizar-datos.yml/badge.svg)](https://github.com/alvarez1lucas/umbrales-credito/actions/workflows/actualizar-datos.yml) [![Site](https://github.com/alvarez1lucas/umbrales-credito/actions/workflows/publicar-sitio.yml/badge.svg)](https://github.com/alvarez1lucas/umbrales-credito/actions/workflows/publicar-sitio.yml) ![Python 3.11](https://img.shields.io/badge/python-3.11-blue) ![dbt](https://img.shields.io/badge/dbt-DuckDB-orange)

**[Live site](https://alvarez1lucas.github.io/umbrales-credito/)** · **[One-page memo (PDF)](https://alvarez1lucas.github.io/umbrales-credito/memo-en.pdf)** · [Power BI dashboard (.pbix)](powerbi/umbrales_credito_en.pbix) · [Policy simulator (Excel)](excel/simulador_politica_en.xlsx) · [Versión en español](README_ES.md)

A credit policy is a set of thresholds: how much debt to approve, which ratings to lend to, which day past due to call. This project asks five questions of each threshold across the full credit cycle (origination, portfolio, collections), with real data and no Kaggle datasets.

## At a glance

| Question | Finding |
|---|---|
| Where is the rule? | Conventional approval falls from 91% to 28% when debt-to-income crosses 50, and applications bunch right below |
| Does the variable separate risk? | Below 50 debt-to-income barely moves price. Days past due do: 34% go bad from 1-30 days, 84% from 61-90 |
| What does moving it cost? | A cap of 45 loses 21% of approvals. Removing two loss-making markets yields +0.53 €M giving up 3% of loans (assumed cost: 10 points) |
| Who does it affect? | Under that cap adverse impact goes from 0.77 to 0.68. The denial gap falls from 11.4 to 6.2 points with controls, which does not prove discrimination |
| Does it still hold? | Ratings F and G went from +8.3% to -9.7% of the amount in two years |

Numbers come from US and European portfolios because Argentina has no public loan-level data: what travels is the method, not the values.

**Stack:** SQL with dbt + DuckDB, Python (pandas, statsmodels), Plotly, Power BI, Excel, pytest, GitHub Actions, GitHub Pages.

## Data

- **Bondora:** 806,217 consumer loans since 2009, published by the lender. Two snapshots of the whole portfolio (Jul-25, rescued from the Wayback Machine, and Oct-26) give real transitions and recoveries; every new publication adds another.
- **HMDA:** 520,012 mortgage applications in Georgia, US, 2023-2025, with outcome and denial reason.

## Results

- [Portfolio and collections](docs/cartera_cobranzas.md) · [Origination](docs/originacion.md) · [Plan and definitions](docs/plan.md) · [Power BI guide](docs/powerbi.md)

## Reproduce

```bash
pip install -r requirements.txt && pip install -e .
python -m ciclo.ingest       # Bondora snapshots and HMDA applications
python -m ciclo.modelos      # dbt build: models and data tests
python -m ciclo.cobranzas && python -m ciclo.cartera && python -m ciclo.originacion
python -m ciclo.exportar     # marts as CSV for Power BI and the site
python -m ciclo.sitio && python -m ciclo.memo
pytest
```

Author: Lucas Alvarez · [GitHub](https://github.com/alvarez1lucas) · Related: [Credit risk models](https://github.com/alvarez1lucas/modelos-credito) ([interactive app](https://alvarez1lucas.github.io/modelos-credito/app/)), [Household loan delinquency in Argentina](https://github.com/alvarez1lucas/mora_argentina)
