"""Memo ejecutivo de una página y READMEs, generados desde outputs/.

`python -m ciclo.memo` escribe site/memo.html, site/en/memo.html, README.md y README_ES.md.
El PDF lo imprime Chrome en el workflow de publicación.
"""

from __future__ import annotations

from ciclo.config import ROOT, settings
from ciclo.sitio import cifras, datos

CSS = """
@page{size:A4;margin:14mm 15mm}
*{box-sizing:border-box}
body{margin:0;color:#0b0b0b;font:10.2pt/1.42 system-ui,-apple-system,"Segoe UI",sans-serif;background:#fff}
main{max-width:180mm;margin:0 auto}
h1{font-size:17pt;line-height:1.2;margin:0 0 2pt}
.sub{color:#52514e;margin:0 0 9pt}
.clave{border-left:3px solid #2a78d6;background:#f6f8fb;padding:6pt 10pt;margin:0 0 9pt}
h2{font-size:10.5pt;margin:9pt 0 3pt}
ol{margin:0;padding-left:15pt}
li{margin:0 0 4pt}
table{border-collapse:collapse;width:100%;font-size:9.4pt;font-variant-numeric:tabular-nums;margin:3pt 0}
th,td{text-align:left;padding:3pt 6pt;border-bottom:1px solid #e1e0d9}
th{color:#52514e;font-weight:600}
.pie{color:#6f6e69;font-size:8.6pt;margin-top:7pt}
"""


def memo_html(d: dict, L: str) -> str:
    c = cifras(d, L)
    url = settings()["sitio"]["url"]
    if L == "es":
        titulo, cuerpo = "Memo: umbrales de la política de crédito", f"""
<h1>Umbrales de la política de crédito</h1>
<p class="sub">Qué mover, qué dejar quieto y cómo medirlo. Datos reales: {c['solicitudes']} solicitudes (HMDA) y {c['creditos']} créditos de consumo (Bondora).</p>
<div class="clave"><strong>Conclusión.</strong> Conviene actuar antes en la cobranza y en los segmentos que pierden siempre, y no tocar los topes generales sin datos de desempeño. Un umbral vale por lo que separa, lo que cuesta, a quién afecta y cuánto dura, no por lo bien que predice.</div>
<h2>Recomendaciones</h2>
<ol>
<li><strong>Concentrar la cobranza antes de los 60 días y ordenar la cola por saldo en riesgo.</strong> Terminan mal el {c['mal1']}% en 1-30 días y el {c['mal3']}% en 61-90. Con 20% de capacidad, la cobertura del saldo que termina mal pasa de {c['cob_atr']}% a {c['cob_pe']}%; ordenar sólo por saldo ya da {c['cob_saldo']}%.</li>
<li><strong>Salir primero de los segmentos que pierden siempre.</strong> Con un costo supuesto de {c['costo']} puntos, sacar dos mercados mejora el resultado {c['dl']} M€ resignando el {c['dl_sale']}% de los créditos; recortar ratings E a G da {c['eg']} M€ resignando el {c['eg_sale']}%.</li>
<li><strong>No bajar el tope de deuda-ingreso sin datos de desempeño.</strong> Por debajo de 50 casi no separa aprobación ni precio. Bajarlo a 45 pierde el {c['p45']}% de los aprobados y lleva el impacto adverso de {c['ai_n']} a {c['ai45n']} (umbral: {c['umbral']}).</li>
<li><strong>Descartar el tope de carga de la cuota.</strong> Predice mora ({c['carga_min']}% a {c['carga_max']}%), pero los topes probados empeoran el resultado: con 10%, {c['c10']} M€.</li>
<li><strong>Monitorear los umbrales por semestre.</strong> Los ratings F y G pasaron de {c['fg_ini']}% a {c['fg_fin']}% del monto en dos años. El promedio histórico no lo muestra.</li>
</ol>
<h2>Antes de aplicar cualquier regla</h2>
<table><thead><tr><th>Pregunta</th><th>Qué mirar</th><th>Ejemplo</th></tr></thead><tbody>
<tr><td>¿Dónde está?</td><td>Saltos en aprobación y amontonamientos</td><td>{c['plano']}% a {c['ap50']}% al cruzar 50</td></tr>
<tr><td>¿Separa riesgo?</td><td>Mora y precio a cada lado del corte</td><td>Spread de {c['sp20']} a {c['sp49']} hasta 49; {c['sp50']} arriba</td></tr>
<tr><td>¿Cuánto cuesta?</td><td>Volumen y resultado perdidos</td><td>{c['p45']}% de los aprobados con tope de 45</td></tr>
<tr><td>¿A quién afecta?</td><td>Impacto adverso y brecha condicional</td><td>Brecha de {c['br_n']} a {c['co_n']} puntos al controlar</td></tr>
<tr><td>¿Sigue valiendo?</td><td>Resultado por cosecha y semestre</td><td>F y G: {c['fg_ini']}% a {c['fg_fin']}%</td></tr>
</tbody></table>
<h2>Regulación</h2>
<p style="margin:0">Aplicadas como ejercicio a esta cartera, las previsiones mínimas del BCRA suman {c['bcra']} M€ contra {c['ecl_b']}-{c['ecl']} M€ de pérdida esperada: el total es parecido, la composición no. En situación 1, 1% contra {c['s1_e']}%; en situación 5, 100% contra {c['s5_e']}%.</p>
<p class="pie"><strong>Límites.</strong> Los números son de carteras de EE.UU. y Europa: se traslada el método, no los valores. El costo de {c['costo']} puntos es un supuesto: sin él, ninguna regla mejora el resultado. HMDA no tiene score ni desempeño, y la brecha condicional no prueba discriminación. Hay una sola transición de 15 meses. El backtest mide si la gestión llega a las cuentas, no si las salva. Detalle: {url}</p>"""
    else:
        titulo, cuerpo = "Memo: credit policy thresholds", f"""
<h1>Credit policy thresholds</h1>
<p class="sub">What to move, what to leave alone and how to measure it. Real data: {c['solicitudes']} applications (HMDA) and {c['creditos']} consumer loans (Bondora).</p>
<div class="clave"><strong>Bottom line.</strong> Act first on collections and on segments that always lose, and leave general caps alone until there is performance data. A threshold is worth what it separates, what it costs, who it affects and how long it lasts, not how well it predicts.</div>
<h2>Recommendations</h2>
<ol>
<li><strong>Focus collections before day 60 and sort the queue by balance at risk.</strong> {c['mal1']}% go bad from 1-30 days and {c['mal3']}% from 61-90. With 20% capacity, coverage of the balance that goes bad rises from {c['cob_atr']}% to {c['cob_pe']}%; sorting by balance alone gives {c['cob_saldo']}%.</li>
<li><strong>Leave the segments that always lose first.</strong> With an assumed cost of {c['costo']} points, removing two markets improves the result by {c['dl']} €M giving up {c['dl_sale']}% of loans; cutting ratings E to G gives {c['eg']} €M giving up {c['eg_sale']}%.</li>
<li><strong>Do not lower the debt-to-income cap without performance data.</strong> Below 50 it barely separates approval or price. Lowering it to 45 loses {c['p45']}% of approvals and takes adverse impact from {c['ai_n']} to {c['ai45n']} (threshold: {c['umbral']}).</li>
<li><strong>Drop the payment-burden cap.</strong> It predicts delinquency ({c['carga_min']}% to {c['carga_max']}%), but the caps tested worsen the result: at 10%, {c['c10']} €M.</li>
<li><strong>Monitor thresholds every half-year.</strong> Ratings F and G went from {c['fg_ini']}% to {c['fg_fin']}% of the amount in two years. The historical average does not show it.</li>
</ol>
<h2>Before applying any rule</h2>
<table><thead><tr><th>Question</th><th>What to check</th><th>Example</th></tr></thead><tbody>
<tr><td>Where is it?</td><td>Jumps in approval and bunching</td><td>{c['plano']}% to {c['ap50']}% when crossing 50</td></tr>
<tr><td>Does it separate risk?</td><td>Delinquency and price on each side</td><td>Spread {c['sp20']} to {c['sp49']} up to 49; {c['sp50']} above</td></tr>
<tr><td>What does it cost?</td><td>Volume and result lost</td><td>{c['p45']}% of approvals with a cap of 45</td></tr>
<tr><td>Who does it affect?</td><td>Adverse impact and conditional gap</td><td>Gap from {c['br_n']} to {c['co_n']} points with controls</td></tr>
<tr><td>Does it still hold?</td><td>Result by vintage and half-year</td><td>F and G: {c['fg_ini']}% to {c['fg_fin']}%</td></tr>
</tbody></table>
<h2>Regulation</h2>
<p style="margin:0">Applied as an exercise to this portfolio, the Argentine central bank's minimum provisions add up to €{c['bcra']}M against €{c['ecl_b']}-{c['ecl']}M of expected loss: the total is similar, the mix is not. In class 1, 1% against {c['s1_e']}%; in class 5, 100% against {c['s5_e']}%.</p>
<p class="pie"><strong>Limits.</strong> Numbers come from US and European portfolios: the method travels, the values do not. The {c['costo']}-point cost is an assumption: without it, no rule improves the result. HMDA has no score or performance, and the conditional gap does not prove discrimination. There is a single 15-month transition. The backtest measures whether collections reach accounts, not whether they save them. Details: {url}en/</p>"""
    return f"""<!doctype html>
<html lang="{L}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titulo}</title><style>{CSS}</style></head><body><main>{cuerpo}</main></body></html>
"""


def readme(d: dict, L: str) -> str:
    c = cifras(d, L)
    cfg = settings()["sitio"]
    url, repo = cfg["url"], cfg["repo_url"]
    wf = f"{repo}/actions/workflows"
    badges = (f"[![Tests]({wf}/tests.yml/badge.svg)]({wf}/tests.yml) "
              f"[![{'Data refresh' if L == 'en' else 'Actualizar datos'}]({wf}/actualizar-datos.yml/badge.svg)]({wf}/actualizar-datos.yml) "
              f"[![{'Site' if L == 'en' else 'Sitio'}]({wf}/publicar-sitio.yml/badge.svg)]({wf}/publicar-sitio.yml) "
              "![Python 3.11](https://img.shields.io/badge/python-3.11-blue) ![dbt](https://img.shields.io/badge/dbt-DuckDB-orange)")
    if L == "en":
        return f"""# Credit thresholds

{badges}

**[Live site]({url}en/)** · **[One-page memo (PDF)]({url}memo-en.pdf)** · [Versión en español](README_ES.md)

A credit policy is a set of thresholds: how much debt to approve, which ratings to lend to, which day past due to call. This project asks five questions of each threshold across the full credit cycle (origination, portfolio, collections), with real data and no Kaggle datasets.

## At a glance

| Question | Finding |
|---|---|
| Where is the rule? | Conventional approval falls from {c['plano']}% to {c['ap50']}% when debt-to-income crosses 50, and applications bunch right below |
| Does the variable separate risk? | Below 50 debt-to-income barely moves price. Days past due do: {c['mal1']}% go bad from 1-30 days, {c['mal3']}% from 61-90 |
| What does moving it cost? | A cap of 45 loses {c['p45']}% of approvals. Removing two loss-making markets yields {c['dl']} €M giving up {c['dl_sale']}% of loans (assumed cost: {c['costo']} points) |
| Who does it affect? | Under that cap adverse impact goes from {c['ai_n']} to {c['ai45n']}. The denial gap falls from {c['br_n']} to {c['co_n']} points with controls, which does not prove discrimination |
| Does it still hold? | Ratings F and G went from {c['fg_ini']}% to {c['fg_fin']}% of the amount in two years |

Numbers come from US and European portfolios because Argentina has no public loan-level data: what travels is the method, not the values.

**Stack:** SQL with dbt + DuckDB, Python (pandas, statsmodels), Plotly, Power BI, pytest, GitHub Actions, GitHub Pages.

## Data

- **Bondora:** {c['creditos']} consumer loans since 2009, published by the lender. Two snapshots of the whole portfolio ({c['fecha_ini']}, rescued from the Wayback Machine, and {c['fecha']}) give real transitions and recoveries; every new publication adds another.
- **HMDA:** {c['solicitudes']} mortgage applications in Georgia, US, 2023-2025, with outcome and denial reason.

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

Author: Lucas Alvarez · [GitHub](https://github.com/alvarez1lucas) · Related: [Household loan delinquency in Argentina](https://github.com/alvarez1lucas/mora_argentina)
"""
    return f"""# Umbrales de crédito

{badges}

**[Sitio]({url})** · **[Memo de una página (PDF)]({url}memo.pdf)** · [English version](README.md)

Una política de crédito es un conjunto de umbrales: hasta qué deuda aprobar, a qué rating prestar, a qué día de atraso llamar. Este proyecto le hace cinco preguntas a cada umbral a lo largo del ciclo completo del crédito (originación, cartera y cobranzas), con datos reales y sin datasets de Kaggle.

## En 30 segundos

| Pregunta | Hallazgo |
|---|---|
| ¿Dónde está la regla? | La aprobación convencional cae de {c['plano']}% a {c['ap50']}% al cruzar deuda-ingreso de 50, y las solicitudes se amontonan justo debajo |
| ¿La variable separa riesgo? | Por debajo de 50, la deuda-ingreso casi no mueve el precio. El atraso sí: terminan mal el {c['mal1']}% en 1-30 días y el {c['mal3']}% en 61-90 |
| ¿Cuánto cuesta moverla? | Un tope de 45 pierde el {c['p45']}% de los aprobados. Sacar dos mercados que pierden rinde {c['dl']} M€ resignando el {c['dl_sale']}% de los créditos (costo supuesto: {c['costo']} puntos) |
| ¿A quién afecta? | Con ese tope, el impacto adverso va de {c['ai_n']} a {c['ai45n']}. La brecha de rechazo baja de {c['br_n']} a {c['co_n']} puntos al controlar, lo que no prueba discriminación |
| ¿Sigue valiendo? | Los ratings F y G pasaron de {c['fg_ini']}% a {c['fg_fin']}% del monto en dos años |

Los números son de carteras de EE.UU. y Europa porque en Argentina no hay datos públicos de créditos individuales: se traslada el método, no los valores.

**Stack:** SQL con dbt + DuckDB, Python (pandas, statsmodels), Plotly, Power BI, pytest, GitHub Actions, GitHub Pages.

## Datos

- **Bondora:** {c['creditos']} préstamos de consumo desde 2009, publicados por la propia empresa. Dos fotos de toda la cartera ({c['fecha_ini']}, rescatada de la Wayback Machine, y {c['fecha']}) dan transiciones y recuperos reales; cada publicación nueva agrega otra.
- **HMDA:** {c['solicitudes']} solicitudes hipotecarias en Georgia, EE.UU., 2023-2025, con su resultado y el motivo del rechazo.

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

Autor: Lucas Alvarez · [GitHub](https://github.com/alvarez1lucas) · Relacionado: [Mora de los hogares en Argentina](https://github.com/alvarez1lucas/mora_argentina)
"""


def main() -> None:
    d = datos()
    destino = ROOT / settings()["sitio"]["destino"]
    for L, rel in (("es", "memo.html"), ("en", "en/memo.html")):
        f = destino / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(memo_html(d, L), encoding="utf-8")
    (ROOT / "README.md").write_text(readme(d, "en"), encoding="utf-8")
    (ROOT / "README_ES.md").write_text(readme(d, "es"), encoding="utf-8")
    print(f"memo: {destino}, README.md, README_ES.md")


if __name__ == "__main__":
    main()
