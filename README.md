# Ciclo del crédito con datos reales

Originación, cartera y cobranzas con datos públicos y reales, sin datasets de Kaggle:

- **Bondora:** ~840 mil préstamos de consumo en Europa desde 2009, crédito por crédito, publicados por la propia empresa. Se usan dos fotos reales de toda la cartera (jul-25, rescatada de la Wayback Machine, y oct-26), que dan transiciones y recuperos observados.
- **HMDA:** solicitudes hipotecarias de EE.UU., aprobadas y rechazadas, con el motivo del rechazo.

> En construcción. Plan y definiciones: [docs/plan.md](docs/plan.md). Resultados: [cartera y cobranzas](docs/cartera_cobranzas.md), [originación](docs/originacion.md).

## Estado

- [x] Fase 1: ingesta (Bondora con fotos fechadas, HMDA por API) y warehouse en dbt + DuckDB con tests de datos
- [x] Fase 2: cartera y cobranzas (pérdida esperada, situaciones BCRA, recupero, priorización con backtest)
- [x] Fase 3: originación (embudo, simulación de reglas con resultado real, préstamo justo)
- [ ] Fase 4: Power BI, sitio y memo ejecutivo
- [ ] Fase 5: actualización mensual con GitHub Actions

## Reproducir

```bash
python -m venv .venv && .venv/Scripts/activate   # en Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt && pip install -e .
python -m ciclo.ingest     # baja la foto vigente de Bondora y las solicitudes HMDA configuradas
python -m ciclo.modelos    # dbt build: modelos y tests de datos en data/warehouse/ciclo.duckdb
python -m ciclo.cobranzas  # priorización con backtest y escenario de canales
python -m ciclo.cartera    # resumen de cifras clave
python -m ciclo.originacion  # simulación de reglas, impacto adverso y brecha condicional
python -m ciclo.exportar   # marts en CSV para Power BI y el sitio
pytest
```

Configuración en `config/settings.yaml`; modelos SQL en `dbt_ciclo/models/` (staging → intermediate → marts).

Autor: Lucas Alvarez · [GitHub](https://github.com/alvarez1lucas)
