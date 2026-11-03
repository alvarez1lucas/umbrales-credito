# Umbrales de crédito

[![Tests](https://github.com/alvarez1lucas/umbrales-credito/actions/workflows/tests.yml/badge.svg)](https://github.com/alvarez1lucas/umbrales-credito/actions/workflows/tests.yml) [![Actualizar datos](https://github.com/alvarez1lucas/umbrales-credito/actions/workflows/actualizar-datos.yml/badge.svg)](https://github.com/alvarez1lucas/umbrales-credito/actions/workflows/actualizar-datos.yml) [![Sitio](https://github.com/alvarez1lucas/umbrales-credito/actions/workflows/publicar-sitio.yml/badge.svg)](https://github.com/alvarez1lucas/umbrales-credito/actions/workflows/publicar-sitio.yml) ![Python 3.11](https://img.shields.io/badge/python-3.11-blue) ![dbt](https://img.shields.io/badge/dbt-DuckDB-orange)

**[Sitio](https://alvarez1lucas.github.io/umbrales-credito/es/)** · **[Memo de una página (PDF)](https://alvarez1lucas.github.io/umbrales-credito/memo.pdf)** · [Tablero de Power BI (.pbix)](powerbi/umbrales_credito.pbix) · [Simulador de política (Excel)](excel/simulador_politica.xlsx) · [English version](README.md)

Una política de crédito es un conjunto de umbrales: hasta qué deuda aprobar, a qué rating prestar, a qué día de atraso llamar. Este proyecto le hace cinco preguntas a cada umbral a lo largo del ciclo completo del crédito (originación, cartera y cobranzas), con datos reales y sin datasets de Kaggle.

## En 30 segundos

| Pregunta | Hallazgo |
|---|---|
| ¿Dónde está la regla? | La aprobación convencional cae de 91% a 28% al cruzar deuda-ingreso de 50, y las solicitudes se amontonan justo debajo |
| ¿La variable separa riesgo? | Por debajo de 50, la deuda-ingreso casi no mueve el precio. El atraso sí: terminan mal el 34% en 1-30 días y el 84% en 61-90 |
| ¿Cuánto cuesta moverla? | Un tope de 45 pierde el 21% de los aprobados. Sacar dos mercados que pierden rinde +0,53 M€ resignando el 3% de los créditos (costo supuesto: 10 puntos) |
| ¿A quién afecta? | Con ese tope, el impacto adverso va de 0,77 a 0,68. La brecha de rechazo baja de 11,4 a 6,2 puntos al controlar, lo que no prueba discriminación |
| ¿Sigue valiendo? | Los ratings F y G pasaron de +8,3% a -9,7% del monto en dos años |

Los números son de carteras de EE.UU. y Europa porque en Argentina no hay datos públicos de créditos individuales: se traslada el método, no los valores.

**Stack:** SQL con dbt + DuckDB, Python (pandas, statsmodels), Plotly, Power BI, Excel, pytest, GitHub Actions, GitHub Pages.

## Datos

- **Bondora:** 806.217 préstamos de consumo desde 2009, publicados por la propia empresa. Dos fotos de toda la cartera (jul-25, rescatada de la Wayback Machine, y oct-26) dan transiciones y recuperos reales; cada publicación nueva agrega otra.
- **HMDA:** 520.012 solicitudes hipotecarias en Georgia, EE.UU., 2023-2025, con su resultado y el motivo del rechazo.

## Resultados

- [Cartera y cobranzas](docs/cartera_cobranzas.md) · [Originación](docs/originacion.md) · [Plan y definiciones](docs/plan.md) · [Guía de Power BI](docs/powerbi.md)

## Reproducir

```bash
pip install -r requirements.txt && pip install -e .
python -m ciclo.ingest       # fotos de Bondora y solicitudes HMDA
python -m ciclo.modelos      # dbt build: modelos y tests de datos
python -m ciclo.cobranzas && python -m ciclo.cartera && python -m ciclo.originacion
python -m ciclo.exportar     # marts en CSV para Power BI y el sitio
python -m ciclo.sitio && python -m ciclo.memo
pytest
```

Autor: Lucas Alvarez · [GitHub](https://github.com/alvarez1lucas) · Relacionado: [Modelos de riesgo de crédito](https://github.com/alvarez1lucas/modelos-credito) ([app interactiva](https://alvarez1lucas.github.io/modelos-credito/app/)), [Mora de los hogares en Argentina](https://github.com/alvarez1lucas/mora_argentina)
