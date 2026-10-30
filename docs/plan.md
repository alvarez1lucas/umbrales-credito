# Plan del proyecto

Pregunta: **cómo se decide en cada etapa del ciclo del crédito** (a quién aprobar, dónde se deteriora la
cartera, a quién cobrar primero) con datos reales y públicos, sin datasets de Kaggle.

| Etapa | Fuente | Preguntas |
|---|---|---|
| Originación | HMDA (EE.UU., solicitudes hipotecarias con resultado y motivo de rechazo) | Embudo, motivos de rechazo, qué pasa con la aprobación si muevo el tope de deuda-ingreso, préstamo justo |
| Cartera | Bondora (préstamos de consumo en Europa, crédito por crédito, una foto por publicación) | Composición, concentración, cosechas, roll rates, cartera en riesgo, pérdida esperada |
| Cobranzas | Bondora | Recupero después del default, priorización por tramo y segmento; canales como escenario con supuestos explícitos |
| Regulación | Normas del BCRA | Situaciones 1 a 5 y previsiones mínimas vs pérdida esperada NIIF 9 |
| Comparación | Proyecto [mora_argentina](https://github.com/alvarez1lucas/mora_argentina) y fideicomisos financieros | Estrés de la pérdida esperada con los escenarios argentinos |

## Fases

1. **Ingesta y warehouse.** Bondora (foto fechada) y HMDA; modelo en dbt + DuckDB: créditos, tramos,
   evento 90+, cosechas, cartera por tramo, roll rates entre fotos. Tests de datos en dbt y de código en pytest.
2. **Cartera y cobranzas.** Pérdida esperada por segmento, situaciones del BCRA y previsiones,
   rentabilidad ajustada por riesgo, curvas de recupero, priorización de cobranza.
3. **Originación.** Embudo y motivos de rechazo, sensibilidad del tope de deuda-ingreso, análisis de préstamo justo.
4. **Tableros y publicación.** Sitio bilingüe en GitHub Pages y memo de una página, ordenados por las cinco preguntas que hay que
   hacerle a un umbral. Power BI con la [guía](powerbi.md).
5. **Automatización.** GitHub Actions mensual: baja la foto nueva de Bondora, la guarda como asset de un release,
   reconstruye el warehouse y publica.

## Definiciones

- **Evento 90+:** el crédito llega a 90 días de atraso, o Bondora lo declara en default o lo pasa a pérdida.
  Fecha: inicio del atraso + 90 días. Un atraso que se curó y se pagó sin quedar marcado no se ve en la foto.
- **Cartera viva:** créditos activos y en default todavía no castigados.
- **Excluidos:** desistimientos dentro de los 14 días, créditos devueltos o en revisión.
- **Cosechas:** en cada mes desde el otorgamiento cuentan sólo los créditos que ya tienen esa antigüedad.
