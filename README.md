# Ciclo del crédito con datos reales

Originación, cartera y cobranzas con datos públicos y reales, sin datasets de Kaggle:

- **Bondora:** ~840 mil préstamos de consumo en Europa desde 2009, crédito por crédito, publicados por la propia empresa y actualizados todos los meses.
- **HMDA:** solicitudes hipotecarias de EE.UU., aprobadas y rechazadas, con el motivo del rechazo.

> En construcción. Plan, fases y definiciones: [docs/plan.md](docs/plan.md).

## Estado

- [x] Fase 1: ingesta (Bondora con fotos fechadas, HMDA por API) y warehouse en dbt + DuckDB con tests de datos
- [ ] Fase 2: cartera y cobranzas (pérdida esperada, situaciones BCRA, recupero, priorización)
- [ ] Fase 3: originación (embudo, sensibilidad de política, préstamo justo)
- [ ] Fase 4: Power BI, sitio y memo ejecutivo
- [ ] Fase 5: actualización mensual con GitHub Actions

## Reproducir

```bash
python -m venv .venv && .venv/Scripts/activate   # en Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt && pip install -e .
python -m ciclo.ingest     # baja la foto vigente de Bondora y las solicitudes HMDA configuradas
python -m ciclo.modelos    # dbt build: modelos y tests de datos en data/warehouse/ciclo.duckdb
pytest
```

Configuración en `config/settings.yaml`; modelos SQL en `dbt_ciclo/models/` (staging → intermediate → marts).

Autor: Lucas Alvarez · [GitHub](https://github.com/alvarez1lucas)
