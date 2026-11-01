"""Simulador de política de crédito en Excel, en español y en inglés.

`python -m ciclo.excel` escribe excel/simulador_politica.xlsx y excel/simulador_politica_en.xlsx con fórmulas
vivas sobre outputs/originacion/segmentos_politica.csv. Las fórmulas se calculan con un motor independiente
(`formulas`) y el resultado queda guardado en el archivo, así se ve igual en cualquier visor.
Usa funciones de Excel 2016 (SUMIFS, INDEX, MATCH): un banco puede tener una versión vieja.
"""

from __future__ import annotations

from pathlib import Path

import formulas
import numpy as np
import pandas as pd
import xlsxwriter

from ciclo.config import ROOT, path, settings

SALIDA = ROOT / "excel"
IDIOMAS = ("es", "en")
NOMBRES = {"es": "simulador_politica.xlsx", "en": "simulador_politica_en.xlsx"}
HOJAS = {"es": dict(guia="Guía", sup="Supuestos", dat="Datos", sim="Simulador", con="Conciliación", sen="Sensibilidad", res="Resumen"),
         "en": dict(guia="Guide", sup="Assumptions", dat="Data", sim="Simulator", con="Reconciliation", sen="Sensitivity", res="Summary")}
AZUL, VERDE, TINTA, GRIS = "#0000FF", "#008000", "#0B0B0B", "#52514E"
ENCABEZADO, LINEA, RESALTE = "#2A78D6", "#E1E0D9", "#FFFF00"
MIL = '#,##0;(#,##0);"-"'
EUR = '€#,##0;(€#,##0);"-"'
PCT = '0.0%;(0.0%);"-"'
RATINGS = ["AA", "A", "B", "C", "D", "E", "F", "G", "HR"]
ANIOS = [2023, 2024, 2025]
TOPES = {"es": ["Sin tope", "20%", "15%", "10%"], "en": ["No cap", "20%", "15%", "10%"]}
ESCENARIOS = {"es": ["Base", "Adverso", "Favorable"], "en": ["Base", "Adverse", "Favorable"]}
MULTIPLICADORES = [(1.0, 1.0), (1.3, 1.1), (0.8, 0.9)]  # SUPUESTO: mora y LGD de cada escenario
EXCLUIDOS_POR_DEFECTO = {"Denmark", "Latvia"}
REGLA_EN = {"Carga <= 20%": "Payment burden <= 20%", "Carga <= 15%": "Payment burden <= 15%", "Carga <= 10%": "Payment burden <= 10%",
            "Sin ratings F-G": "No F-G ratings", "Sin ratings E-G": "No E-G ratings", "Sin Denmark ni Latvia": "No Denmark or Latvia"}


class Libro:
    """Escribe celdas y recuerda el valor calculado de cada fórmula."""

    def __init__(self, archivo: Path, valores: dict) -> None:
        self.wb = xlsxwriter.Workbook(archivo)
        self.valores = valores
        self.cache: dict = {}
        self.wb.set_calc_mode("auto")

    def fmt(self, **k):
        clave = tuple(sorted(k.items()))
        if clave not in self.cache:
            self.cache[clave] = self.wb.add_format({"font_name": "Arial", "font_size": 10, "valign": "vcenter", **k})
        return self.cache[clave]

    def formula(self, ws, celda: str, f: str, **k) -> None:
        ws.write_formula(celda, f, self.fmt(**k), self.valores.get((ws.get_name().upper(), celda), 0))


def nueva_hoja(lb: Libro, nombre: str, titulo: str, bajada: str, color: str = ENCABEZADO):
    ws = lb.wb.add_worksheet(nombre)
    ws.hide_gridlines(2)
    ws.set_tab_color(color)
    ws.set_landscape()
    ws.set_paper(9)
    ws.fit_to_pages(1, 0)
    ws.set_footer("&L&F&C&A&R&P / &N")
    ws.set_row(0, 28)
    ws.write("A1", titulo, lb.fmt(bold=True, font_size=16))
    ws.write("A2", bajada, lb.fmt(font_color=GRIS))
    return ws


def encabezados(lb: Libro, ws, fila: int, columna: int, textos: list[str]) -> None:
    f = lb.fmt(bold=True, font_color="#FFFFFF", bg_color=ENCABEZADO, text_wrap=True, align="center", border=1, border_color=ENCABEZADO)
    for i, t in enumerate(textos):
        ws.write(fila, columna + i, t, f)


def construir(archivo: Path, L: str, df: pd.DataFrame, lgd: dict, ref: pd.DataFrame, valores: dict) -> None:
    es = L == "es"
    tr = lambda a, b: a if es else b
    H = HOJAS[L]
    si, no = tr("Sí", "Yes"), "No"
    lb = Libro(archivo, valores)
    q = lambda clave: f"'{H[clave]}'"
    n = len(df)
    p, u = 5, 4 + n  # primera y última fila de Datos
    D = lambda col: f"{q('dat')}!${col}${p}:${col}${u}"
    costo = f"{q('sup')}!$B$5"
    m_mora, m_lgd = f"{q('sup')}!$B$13", f"{q('sup')}!$B$14"
    azul = dict(font_color=AZUL, bg_color=RESALTE, border=1, border_color=LINEA)

    # --- Guía
    g = nueva_hoja(lb, H["guia"], tr("Simulador de política de crédito", "Credit policy simulator"),
                   tr("¿Qué pasa con la aprobación, la mora y el resultado si muevo una regla?", "What happens to approval, default and results if I move a rule?"))
    g.set_column("A:A", 24)
    g.set_column("B:B", 100)
    fila = 3
    bloques = [
        (tr("Cómo usarlo", "How to use it"), [
            (tr("1. Reglas", "1. Rules"), tr("En Simulador, elegí qué ratings y países se aprueban y el tope de cuota sobre ingreso.", "In Simulator, choose which ratings and countries are approved and the payment-to-income cap.")),
            (tr("2. Supuestos", "2. Assumptions"), tr("En Supuestos, cambiá el costo, el escenario o la LGD por país.", "In Assumptions, change the cost, the scenario or the LGD by country.")),
            (tr("3. Resultado", "3. Result"), tr("Leé la comparación contra la cartera actual, la sensibilidad y el costo de equilibrio.", "Read the comparison with the current book, the sensitivity and the break-even cost.")),
        ]),
        (tr("Colores", "Colors"), [
            (tr("Azul sobre amarillo", "Blue on yellow"), tr("Celdas para editar: reglas y supuestos.", "Cells to edit: rules and assumptions.")),
            (tr("Azul", "Blue"), tr("Datos fijos que vienen del proyecto.", "Fixed data from the project.")),
            (tr("Negro", "Black"), tr("Fórmulas de la misma hoja.", "Formulas on the same sheet.")),
            (tr("Verde", "Green"), tr("Fórmulas que traen datos de otra hoja.", "Formulas that bring data from another sheet.")),
        ]),
        (tr("Hojas", "Sheets"), [
            (H["sup"], tr("Costo, escenarios y LGD por país.", "Cost, scenarios and LGD by country.")),
            (H["dat"], tr(f"{n} segmentos de año, país, rating y carga, con sus cálculos.", f"{n} segments by year, country, rating and burden, with their calculations.")),
            (H["sim"], tr("Reglas, comparación contra la cartera actual y resultado por rating.", "Rules, comparison with the current book and results by rating.")),
            (H["con"], tr("Compara cada regla con Python en resultado, aprobación y mora, y corre controles internos.", "Compares each rule with Python on result, approval and default, and runs internal checks.")),
            (H["sen"], tr("Costo de equilibrio y resultado de la regla con otros costos, LGD y mora.", "Break-even cost and rule result under other costs, LGD and default.")),
            (H["res"], tr("Mora por rating y cosecha, y monto por país.", "Default by rating and vintage, and amount by country.")),
        ]),
        (tr("Fuente y alcance", "Source and scope"), [
            (tr("Datos", "Data"), tr(f"Bondora: {int(df.creditos.sum()):,} créditos con 12 meses observados, de sep-23 a oct-25.".replace(",", "."), f"Bondora: {int(df.creditos.sum()):,} loans with 12 observed months, Sep-23 to Oct-25.")),
            (tr("Resultado", "Result"), tr("Primer año: interés - costo sobre el monto - pérdida si hubo evento 90+. Usa el monto como exposición, lo que exagera un poco la pérdida.", "First year: interest - cost on amount - loss if a 90+ event occurred. Amount is used as exposure, which slightly overstates the loss.")),
            (tr("Límite", "Limit"), tr("Sólo hay créditos otorgados: sirve para endurecer una regla, no para evaluar relajarla.", "Only originated loans are included: it can test tightening a rule, not relaxing one.")),
            (tr("Supuestos", "Assumptions"), tr("El costo de 10 puntos y los escenarios son supuestos, no datos observados.", "The 10-point cost and the scenarios are assumptions, not observed data.")),
        ]),
    ]
    for titulo, filas in bloques:
        g.write(fila, 0, titulo, lb.fmt(bold=True, font_size=12, font_color=ENCABEZADO))
        fila += 1
        for a, b in filas:
            g.write(fila, 0, a, lb.fmt(bold=True, valign="top"))
            g.write(fila, 1, b, lb.fmt(text_wrap=True))
            fila += 1
        fila += 1
    g.write(fila, 0, tr("Control", "Check"), lb.fmt(bold=True, font_size=12, font_color=ENCABEZADO))
    lb.formula(g, f"B{fila + 1}", f"={q('con')}!$B$4", font_color=VERDE, bold=True)

    # --- Supuestos
    s = nueva_hoja(lb, H["sup"], tr("Supuestos", "Assumptions"), tr("Cambiá sólo las celdas en azul sobre amarillo.", "Only change the blue-on-yellow cells."), "#EDA100")
    s.set_column("A:A", 34)
    s.set_column("B:C", 14)
    s.set_column("D:D", 70)
    encabezados(lb, s, 3, 0, [tr("Parámetro", "Parameter"), tr("Valor", "Value")])
    s.write("A5", tr("Costo de fondeo y operación (% del monto)", "Funding and operating cost (% of amount)"), lb.fmt())
    s.write("B5", settings()["politica"]["costos_pp"][-1] / 100, lb.fmt(num_format="0.0%", **azul))
    s.write("D5", tr("Supuesto del proyecto (config/settings.yaml), igual para todos los países.", "Project assumption (config/settings.yaml), the same for all countries."), lb.fmt(font_color=GRIS))
    s.write("A6", tr("Escenario", "Scenario"), lb.fmt())
    s.write("B6", ESCENARIOS[L][0], lb.fmt(**azul))
    s.data_validation("B6", {"validate": "list", "source": "=$A$9:$A$11"})
    entre_0_y_1 = {"validate": "decimal", "criteria": "between", "minimum": 0, "maximum": 1, "error_title": tr("Valor fuera de rango", "Value out of range"),
                   "error_message": tr("Ingresá un porcentaje entre 0% y 100%.", "Enter a percentage between 0% and 100%.")}
    s.data_validation("B5", entre_0_y_1)
    s.data_validation("B9:C11", {"validate": "decimal", "criteria": ">", "value": 0, "error_title": tr("Valor fuera de rango", "Value out of range"),
                                 "error_message": tr("El multiplicador debe ser mayor a cero.", "The multiplier must be above zero.")})
    encabezados(lb, s, 7, 0, [tr("Escenario", "Scenario"), tr("Mult. mora", "Default mult."), tr("Mult. LGD", "LGD mult.")])
    for i, (e, (a, b)) in enumerate(zip(ESCENARIOS[L], MULTIPLICADORES)):
        s.write(8 + i, 0, e, lb.fmt())
        s.write(8 + i, 1, a, lb.fmt(num_format="0.00x", **azul))
        s.write(8 + i, 2, b, lb.fmt(num_format="0.00x", **azul))
    s.write("D9", tr("Multiplicadores supuestos: no están estimados.", "Assumed multipliers: they are not estimated."), lb.fmt(font_color=GRIS))
    s.write("A13", tr("Multiplicador de mora aplicado", "Applied default multiplier"), lb.fmt())
    lb.formula(s, "B13", "=INDEX($B$9:$B$11,MATCH($B$6,$A$9:$A$11,0))", num_format="0.00x")
    s.write("A14", tr("Multiplicador de LGD aplicado", "Applied LGD multiplier"), lb.fmt())
    lb.formula(s, "B14", "=INDEX($C$9:$C$11,MATCH($B$6,$A$9:$A$11,0))", num_format="0.00x")
    encabezados(lb, s, 15, 0, [tr("País", "Country"), "LGD"])
    paises = sorted(lgd)
    for i, c in enumerate(paises):
        s.write(16 + i, 0, c, lb.fmt())
        s.write(16 + i, 1, lgd[c], lb.fmt(num_format="0.0%", **azul))
    s.write("D17", tr("LGD por país del proyecto, o la agregada si el país no tiene eventos maduros (mart_lgd_pais).", "Project LGD by country, or the aggregate where a country has no mature events (mart_lgd_pais)."), lb.fmt(font_color=GRIS))
    fin_pais = 16 + len(paises)
    s.data_validation(f"B17:B{fin_pais}", entre_0_y_1)
    p_ini = fin_pais + 2
    encabezados(lb, s, p_ini - 1, 0, [tr("Tope de cuota sobre ingreso", "Payment-to-income cap"), tr("Tramos que quedan", "Bands kept")])
    for i, (t, o) in enumerate(zip(TOPES[L], (4, 3, 2, 1))):
        s.write(p_ini + i, 0, t, lb.fmt())
        s.write(p_ini + i, 1, o, lb.fmt(font_color=AZUL))
    LP = f"{q('sup')}!$A$17:$A${fin_pais}"
    LV = f"{q('sup')}!$B$17:$B${fin_pais}"
    TL = f"{q('sup')}!$A${p_ini + 1}:$A${p_ini + 4}"
    TV = f"{q('sup')}!$B${p_ini + 1}:$B${p_ini + 4}"

    # --- Datos
    d = nueva_hoja(lb, H["dat"], tr("Datos por segmento", "Segment data"), tr("Tabla tblSegmentos. Columnas A a J: datos del proyecto. K a Q: fórmulas.", "Table tblSegmentos. Columns A to J: project data. K to Q: formulas."), "#898781")
    titulos = [tr("Año", "Year"), tr("País", "Country"), "Rating", tr("Carga", "Burden"), tr("Orden carga", "Burden order"), tr("Créditos", "Loans"), tr("Monto", "Amount"),
               tr("Interés", "Interest"), tr("Eventos 12m", "12m events"), tr("Monto con evento", "Amount with event"), "LGD", tr("Pérdida base", "Base loss"),
               tr("Incluido", "Included"), tr("Costo", "Cost"), tr("Pérdida", "Loss"), tr("Resultado", "Result"), tr("Decisión", "Decision")]
    borde = dict(bold=True, font_color="#FFFFFF", bg_color=ENCABEZADO, text_wrap=True, align="center", border=1, border_color=ENCABEZADO)
    d.add_table(3, 0, u - 1, len(titulos) - 1, {"name": "tblSegmentos", "style": None, "columns": [{"header": t, "header_format": lb.fmt(**borde)} for t in titulos]})
    d.set_column("A:E", 9)
    d.set_column("F:Q", 13)
    d.set_row(3, 30)
    d.freeze_panes(4, 0)
    d.repeat_rows(3)
    azul_dato = lb.fmt(font_color=AZUL)
    entero = lb.fmt(font_color=AZUL, num_format=MIL)
    euro = lb.fmt(font_color=AZUL, num_format=EUR)
    sim_r, sim_p = f"{q('sim')}!$B$7:$B$15", f"{q('sim')}!$B$19:$B${18 + len(paises)}"
    sim_ri, sim_pi = f"{q('sim')}!$C$7:$C$15", f"{q('sim')}!$C$19:$C$24"
    orden_tope = f"{q('sim')}!$C$28"
    for i, r in enumerate(df.itertuples(index=False)):
        f = p + i
        for c, v in zip("ABCDE", (r.anio, r.pais, r.rating, r.carga, r.carga_orden)):
            d.write(f"{c}{f}", v, azul_dato)
        d.write(f"F{f}", r.creditos, entero)
        for c, v in zip("GHJ", (r.monto, r.interes, r.monto_evento)):
            d.write(f"{c}{f}", v, euro)
        d.write(f"I{f}", r.eventos, entero)
        lb.formula(d, f"K{f}", f"=INDEX({LV},MATCH(B{f},{LP},0))", font_color=VERDE, num_format="0.0%")
        lb.formula(d, f"L{f}", f"=J{f}*K{f}", num_format=EUR)
        lb.formula(d, f"M{f}", f'=IF(AND(INDEX({sim_ri},MATCH(C{f},{sim_r},0))="{si}",INDEX({sim_pi},MATCH(B{f},{sim_p},0))="{si}",E{f}<={orden_tope}),1,0)', font_color=VERDE)
        lb.formula(d, f"N{f}", f"=G{f}*{costo}", font_color=VERDE, num_format=EUR)
        lb.formula(d, f"O{f}", f"=L{f}*{m_mora}*{m_lgd}", font_color=VERDE, num_format=EUR)
        lb.formula(d, f"P{f}", f"=H{f}-N{f}-O{f}", num_format=EUR)
        lb.formula(d, f"Q{f}", f'=IF(M{f}=1,"{tr("Aprobado", "Approved")}","{tr("Excluido", "Excluded")}")')

    # --- Simulador
    m = nueva_hoja(lb, H["sim"], tr("Simulador", "Simulator"), tr("Por defecto muestra la regla recomendada: sacar Dinamarca y Letonia.", "By default it shows the recommended rule: removing Denmark and Latvia."), "#1BAF7A")
    m.set_column("A:A", 2)
    m.set_column("B:B", 24)
    m.set_column("C:C", 11)
    m.set_column("D:D", 3)
    m.set_column("E:E", 30)
    m.set_column("F:I", 15)
    encabezados(lb, m, 5, 1, ["Rating", tr("¿Aprobar?", "Approve?")])
    for i, r in enumerate(RATINGS):
        m.write(6 + i, 1, r, lb.fmt())
        m.write(6 + i, 2, si, lb.fmt(align="center", **azul))
    m.data_validation("C7:C15", {"validate": "list", "source": [si, no]})
    encabezados(lb, m, 17, 1, [tr("País", "Country"), tr("¿Aprobar?", "Approve?")])
    for i, c in enumerate(paises):
        m.write(18 + i, 1, c, lb.fmt())
        m.write(18 + i, 2, no if c in EXCLUIDOS_POR_DEFECTO else si, lb.fmt(align="center", **azul))
    m.data_validation("C19:C24", {"validate": "list", "source": [si, no]})
    m.conditional_format("C7:C24", {"type": "cell", "criteria": "==", "value": '"No"', "format": lb.wb.add_format({"font_color": "#9C0006", "bg_color": "#FFC7CE"})})
    encabezados(lb, m, 25, 1, [tr("Tope", "Cap"), tr("Valor", "Value")])
    m.write("B27", tr("Cuota sobre ingreso", "Payment to income"), lb.fmt())
    m.write("C27", TOPES[L][0], lb.fmt(align="center", **azul))
    m.data_validation("C27", {"validate": "list", "source": TOPES[L]})
    m.write("B28", tr("Tramos que quedan", "Bands kept"), lb.fmt(font_color=GRIS))
    lb.formula(m, "C28", f"=INDEX({TV},MATCH($C$27,{TL},0))", font_color=VERDE, align="center")

    encabezados(lb, m, 5, 4, [tr("Indicador", "Metric"), tr("Cartera actual", "Current book"), tr("Con la regla", "With the rule"), tr("Diferencia", "Difference")])
    kpis = [(tr("Créditos", "Loans"), f"=SUM({D('F')})", f"=SUMIFS({D('F')},{D('M')},1)", MIL),
            (tr("Aprobados (% del actual)", "Approved (% of current)"), "=F7/F7", "=G7/F7", PCT),
            (tr("Monto", "Amount"), f"=SUM({D('G')})", f"=SUMIFS({D('G')},{D('M')},1)", EUR),
            (tr("Mora a 12 meses", "12-month default"), f"=SUM({D('I')})*{m_mora}/F7", f"=SUMIFS({D('I')},{D('M')},1)*{m_mora}/G7", PCT),
            (tr("Interés", "Interest"), f"=SUM({D('H')})", f"=SUMIFS({D('H')},{D('M')},1)", EUR),
            (tr("Costo", "Cost"), f"=SUM({D('N')})", f"=SUMIFS({D('N')},{D('M')},1)", EUR),
            (tr("Pérdida", "Loss"), f"=SUM({D('O')})", f"=SUMIFS({D('O')},{D('M')},1)", EUR),
            (tr("Resultado", "Result"), "=F11-F12-F13", "=G11-G12-G13", EUR),
            (tr("Margen sobre monto", "Margin on amount"), "=F14/F9", "=G14/G9", PCT)]
    for i, (t, a, b, fmt) in enumerate(kpis):
        f = 7 + i
        fuerte = dict(bold=True, top=1) if i == 7 else {}
        m.write(f"E{f}", t, lb.fmt(**fuerte))
        color = VERDE if D("F")[:3] in a else TINTA
        lb.formula(m, f"F{f}", a, num_format=fmt, font_color=color, **fuerte)
        lb.formula(m, f"G{f}", b, num_format=fmt, font_color=color, **fuerte)
        lb.formula(m, f"H{f}", f"=G{f}-F{f}", num_format=fmt, **fuerte)
    lectura = (f'="{tr("Lectura", "Reading")}: "&IF($H$14>=0,"{tr("la regla suma ", "the rule adds ")}","{tr("la regla resta ", "the rule subtracts ")}")&ROUND(ABS($H$14)/1000000,2)&'
               f'" {tr("M€ y deja afuera el ", "€M and leaves out ")}"&ROUND(100*(1-$G$8),1)&"{tr("% de los créditos.", "% of loans.")}"')
    m.merge_range("E17:H17", "", lb.fmt(bold=True, font_color=ENCABEZADO))
    lb.formula(m, "E17", lectura, bold=True, font_color=ENCABEZADO)
    encabezados(lb, m, 18, 4, ["Rating", tr("Créditos", "Loans"), tr("Mora 12m", "12m default"), tr("Resultado", "Result"), tr("Margen", "Margin")])
    for i, r in enumerate(RATINGS):
        f = 20 + i
        m.write(f"E{f}", r, lb.fmt())
        lb.formula(m, f"F{f}", f"=SUMIFS({D('F')},{D('C')},$E{f})", font_color=VERDE, num_format=MIL)
        lb.formula(m, f"G{f}", f"=IF(F{f}=0,0,SUMIFS({D('I')},{D('C')},$E{f})*{m_mora}/F{f})", font_color=VERDE, num_format=PCT)
        lb.formula(m, f"H{f}", f"=SUMIFS({D('P')},{D('C')},$E{f})", font_color=VERDE, num_format=EUR)
        lb.formula(m, f"I{f}", f"=IF(F{f}=0,0,H{f}/SUMIFS({D('G')},{D('C')},$E{f}))", font_color=VERDE, num_format=PCT)
    m.conditional_format("I20:I28", {"type": "3_color_scale", "min_color": "#F8696B", "mid_color": "#FFFFFF", "max_color": "#63BE7B", "mid_type": "num", "mid_value": 0})
    graf = lb.wb.add_chart({"type": "column"})
    graf.add_series({"name": tr("Mora a 12 meses", "12-month default"), "categories": f"={q('sim')}!$E$20:$E$27", "values": f"={q('sim')}!$G$20:$G$27", "fill": {"color": ENCABEZADO}, "gap": 60,
                     "data_labels": {"value": True, "num_format": "0.0%", "font": {"name": "Arial", "size": 8}}})
    graf.set_title({"name": tr("La mora sube rating a rating", "Default rises rating by rating"), "name_font": {"name": "Arial", "size": 11}})
    graf.set_legend({"none": True})
    graf.set_y_axis({"num_format": "0%", "major_gridlines": {"visible": True, "line": {"color": LINEA}}, "num_font": {"name": "Arial", "size": 8}})
    graf.set_x_axis({"num_font": {"name": "Arial", "size": 9}})
    graf.set_size({"width": 470, "height": 300})
    m.insert_chart("K6", graf)
    m.activate()

    # --- Conciliación
    c = nueva_hoja(lb, H["con"], tr("Conciliación con el proyecto", "Reconciliation with the project"), tr("Cada regla se calcula acá con fórmulas y se compara con outputs/originacion/simulacion_reglas_bondora.csv.", "Each rule is calculated here with formulas and compared with outputs/originacion/simulacion_reglas_bondora.csv."), "#6250D6")
    c.set_column("A:A", 38)
    c.set_column("B:D", 16)
    c.set_column("E:E", 14)
    c.set_column("F:I", 13)
    filas_ref = ref[(ref.regla != "Sin cambios")]
    ini = 7
    fin = ini + len(filas_ref) - 1
    ctrl_ini = fin + 4
    ctrl_fin = ctrl_ini + 4
    c.write("A4", tr("Estado general", "Overall status"), lb.fmt(bold=True))
    base = f'AND(ROUND({costo},4)=ROUND({settings()["politica"]["costos_pp"][-1]/100},4),{q("sup")}!$B$6="{ESCENARIOS[L][0]}")'
    lb.formula(c, "B4", f'=IF(NOT({base}),"{tr("Supuestos cambiados: no aplica", "Assumptions changed: not applicable")}",IF(AND(COUNTIF($E${ini}:$E${fin},"OK")={len(filas_ref)},COUNTIF($E${ctrl_ini}:$E${ctrl_fin},"OK")=5),"{tr("Concilia con el proyecto", "Reconciles with the project")}","{tr("Revisar diferencias", "Review differences")}"))', bold=True)
    encabezados(lb, c, 5, 0, [tr("Regla", "Rule"), tr("Excel (€)", "Excel (€)"), tr("Proyecto (€)", "Project (€)"), tr("Diferencia (€)", "Difference (€)"), tr("Estado", "Status"),
                                 tr("Aprobados", "Approved"), tr("Aprobados proyecto", "Approved project"), tr("Mora 12m", "12m default"), tr("Mora proyecto", "Default project")])
    c.set_row(5, 30)
    condicion = {"Carga <= 20%": [("E", '">3"')], "Carga <= 15%": [("E", '">2"')], "Carga <= 10%": [("E", '">1"')],
                 "Sin ratings F-G": [("C", '"F"'), ("C", '"G"')], "Sin ratings E-G": [("C", '"E"'), ("C", '"F"'), ("C", '"G"')],
                 "Sin Denmark ni Latvia": [("B", '"Denmark"'), ("B", '"Latvia"')]}
    for i, r in enumerate(filas_ref.itertuples(index=False)):
        f = ini + i
        c.write(f"A{f}", r.regla if es else REGLA_EN[r.regla], lb.fmt())
        sale_regla = lambda medida: "+".join(f"SUMIFS({D(medida)},{D(col)},{crit})" for col, crit in condicion[r.regla])
        lb.formula(c, f"B{f}", f"=-({sale_regla('P')})", font_color=VERDE, num_format=EUR)
        c.write(f"C{f}", float(r.cambio_resultado), lb.fmt(font_color=AZUL, num_format=EUR))
        lb.formula(c, f"D{f}", f"=B{f}-C{f}", num_format='#,##0.00;(#,##0.00);"-"')
        lb.formula(c, f"E{f}", f'=IF(AND(ABS(D{f})<1,ABS(F{f}-G{f})<0.00005,ABS(H{f}-I{f})<0.00005),"OK","{tr("Revisar", "Review")}")', align="center")
        lb.formula(c, f"F{f}", f"=1-({sale_regla('F')})/SUM({D('F')})", font_color=VERDE, num_format="0.0%")
        c.write(f"G{f}", r.aprobados_pct / 100, lb.fmt(font_color=AZUL, num_format="0.0%"))
        lb.formula(c, f"H{f}", f"=(SUM({D('I')})-({sale_regla('I')}))*{m_mora}/(SUM({D('F')})-({sale_regla('F')}))", font_color=VERDE, num_format="0.0%")
        c.write(f"I{f}", r.evento_12m_pct / 100, lb.fmt(font_color=AZUL, num_format="0.0%"))
    c.write(f"A{ctrl_ini - 2}", tr("Controles internos", "Internal checks"), lb.fmt(bold=True, font_color=ENCABEZADO))
    encabezados(lb, c, ctrl_ini - 2, 0, [tr("Control interno", "Internal check"), tr("Valor", "Value"), tr("Debe dar", "Expected"), tr("Diferencia", "Difference"), tr("Estado", "Status")])
    controles = [(tr("Créditos por rating = total", "Loans by rating = total"), f"=SUM({q('sim')}!$F$20:$F$28)", f"=SUM({D('F')})"),
                 (tr("Monto por país = total", "Amount by country = total"), f"=SUM({q('res')}!$E$19:$E$24)", f"=SUM({D('G')})"),
                 (tr("Incluidos + excluidos = total", "Included + excluded = total"), f"=SUMIFS({D('F')},{D('M')},1)+SUMIFS({D('F')},{D('M')},0)", f"=SUM({D('F')})"),
                 (tr("Decisión coincide con Incluido", "Decision matches Included"), f'=COUNTIF({D("Q")},"{tr("Aprobado", "Approved")}")', f"=SUM({D('M')})"),
                 (tr("LGD fuera de 0% a 100%", "LGD outside 0% to 100%"), f'=COUNTIF({LV},"<0")+COUNTIF({LV},">1")', "=0")]
    for i, (t, a, b) in enumerate(controles):
        f = ctrl_ini + i
        c.write(f"A{f}", t, lb.fmt())
        lb.formula(c, f"B{f}", a, font_color=VERDE, num_format='#,##0;(#,##0);0')
        lb.formula(c, f"C{f}", b, font_color=VERDE, num_format='#,##0;(#,##0);0')
        lb.formula(c, f"D{f}", f"=B{f}-C{f}", num_format='#,##0.00;(#,##0.00);"-"')
        lb.formula(c, f"E{f}", f'=IF(ABS(D{f})<1,"OK","{tr("Revisar", "Review")}")', align="center")
    verde_ok = lb.wb.add_format({"font_color": "#006100", "bg_color": "#C6EFCE"})
    c.conditional_format(f"E{ini}:E{ctrl_fin}", {"type": "cell", "criteria": "==", "value": '"OK"', "format": verde_ok})

    # --- Sensibilidad
    e = nueva_hoja(lb, H["sen"], tr("Sensibilidad de la regla", "Rule sensitivity"), tr("Cambio de resultado de la regla activa en Simulador, con otros supuestos.", "Result change of the rule active in Simulator, under other assumptions."), "#E34948")
    e.set_column("A:A", 38)
    e.set_column("B:F", 14)
    sale = lambda col: f"SUMIFS({D(col)},{D('M')},0)"
    e.write("A4", tr("Monto que deja afuera", "Amount left out"), lb.fmt())
    lb.formula(e, "B4", f"={sale('G')}", font_color=VERDE, num_format=EUR)
    e.write("A5", tr("Costo de equilibrio", "Break-even cost"), lb.fmt(bold=True))
    lb.formula(e, "B5", f"=IF($B$4=0,0,({sale('H')}-{sale('L')}*{m_mora}*{m_lgd})/$B$4)", font_color=VERDE, num_format="0.0%", bold=True)
    e.write("C5", tr("La regla gana plata sólo si el costo real es mayor a esta cifra.", "The rule only makes money if the real cost is above this figure."), lb.fmt(font_color=GRIS))
    costos = [0.0, 0.05, 0.10, 0.15, 0.20]
    mult = [0.75, 1.0, 1.25]
    for titulo, ini_g, col_mult in ((tr("Resultado de la regla: costo contra LGD", "Rule result: cost against LGD"), 7, "lgd"),
                                    (tr("Resultado de la regla: costo contra mora", "Rule result: cost against default"), 13, "mora")):
        e.write(f"A{ini_g}", titulo, lb.fmt(bold=True, font_color=ENCABEZADO))
        encabezados(lb, e, ini_g, 0, [tr("Multiplicador", "Multiplier") + (" LGD" if col_mult == "lgd" else tr(" mora", " default"))] + [""] * len(costos))
        for j, k in enumerate(costos):
            e.write(ini_g, 1 + j, k, lb.fmt(bold=True, font_color="#FFFFFF", bg_color=ENCABEZADO, num_format='0%" ' + tr("costo", "cost") + '"', align="center"))
        for i, x in enumerate(mult):
            f = ini_g + 2 + i
            e.write(f"A{f}", x, lb.fmt(font_color=AZUL, num_format="0.00x", align="center"))
            for j in range(len(costos)):
                letra = "BCDEF"[j]
                factor = f"$A{f}*{m_mora}" if col_mult == "lgd" else f"$A{f}*{m_lgd}"
                lb.formula(e, f"{letra}{f}", f"=-({sale('H')}-{letra}${ini_g + 1}*$B$4-{sale('L')}*{factor})", font_color=VERDE, num_format=EUR)
        e.conditional_format(f"B{ini_g + 2}:F{ini_g + 4}", {"type": "3_color_scale", "min_color": "#F8696B", "mid_color": "#FFFFFF", "max_color": "#63BE7B", "mid_type": "num", "mid_value": 0})

    equilibrio = lb.wb.add_chart({"type": "line"})
    equilibrio.add_series({"name": tr("Cambio de resultado", "Result change"), "categories": f"={q('sen')}!$B$8:$F$8", "values": f"={q('sen')}!$B$10:$F$10",
                           "line": {"color": ENCABEZADO, "width": 2.25}, "marker": {"type": "circle", "size": 7, "fill": {"color": ENCABEZADO}, "border": {"color": ENCABEZADO}}})
    equilibrio.set_title({"name": tr("La regla gana plata cuando la línea supera cero", "The rule makes money when the line is above zero"), "name_font": {"name": "Arial", "size": 11}})
    equilibrio.set_legend({"none": True})
    equilibrio.set_x_axis({"name": tr("Costo sobre el monto", "Cost on amount"), "name_font": {"name": "Arial", "size": 9, "bold": False}, "num_format": "0%", "label_position": "low", "num_font": {"name": "Arial", "size": 9}})
    equilibrio.set_y_axis({"name": tr("Cambio de resultado (€)", "Result change (€)"), "name_font": {"name": "Arial", "size": 9, "bold": False}, "num_format": '#,##0.0,,"M";-#,##0.0,,"M";0',
                           "major_gridlines": {"visible": True, "line": {"color": LINEA}}, "num_font": {"name": "Arial", "size": 8}})
    equilibrio.set_size({"width": 500, "height": 300})
    e.insert_chart("H4", equilibrio)

    # --- Resumen
    r = nueva_hoja(lb, H["res"], tr("Resumen de la cartera simulada", "Simulated portfolio summary"), tr("Todos los créditos, sin aplicar las reglas: muestra de dónde sale cada resultado.", "All loans, before rules: it shows where each result comes from."), "#EB6834")
    r.set_column("A:A", 18)
    r.set_column("B:E", 13)
    r.write("A4", tr("Mora a 12 meses por rating y año", "12-month default by rating and year"), lb.fmt(bold=True, font_color=ENCABEZADO))
    encabezados(lb, r, 4, 0, ["Rating"] + [str(a) for a in ANIOS])
    for i, x in enumerate(RATINGS[:8]):
        f = 6 + i
        r.write(f"A{f}", x, lb.fmt())
        for j, a in enumerate(ANIOS):
            k = "BCD"[j]
            base_f = f"SUMIFS({D('F')},{D('C')},$A{f},{D('A')},{a})"
            lb.formula(r, f"{k}{f}", f"=IF({base_f}<200,\"\",SUMIFS({D('I')},{D('C')},$A{f},{D('A')},{a})/{base_f})", font_color=VERDE, num_format="0.0%")
    r.conditional_format("B6:D13", {"type": "2_color_scale", "min_color": "#FFFFFF", "max_color": "#E34948"})
    r.write("A15", tr("Celdas con menos de 200 créditos, en blanco.", "Cells with fewer than 200 loans are blank."), lb.fmt(font_color=GRIS, font_size=8))
    r.write("A17", tr("Monto otorgado por país y año (€)", "Amount originated by country and year (€)"), lb.fmt(bold=True, font_color=ENCABEZADO))
    encabezados(lb, r, 17, 0, [tr("País", "Country")] + [str(a) for a in ANIOS] + [tr("Total", "Total")])
    for i, x in enumerate(paises):
        f = 19 + i
        r.write(f"A{f}", x, lb.fmt())
        for j, a in enumerate(ANIOS):
            lb.formula(r, f"{'BCD'[j]}{f}", f"=SUMIFS({D('G')},{D('B')},$A{f},{D('A')},{a})", font_color=VERDE, num_format=EUR)
        lb.formula(r, f"E{f}", f"=SUM(B{f}:D{f})", bold=True, num_format=EUR)
    t = lb.wb.add_chart({"type": "bar"})
    t.add_series({"name": tr("Monto total", "Total amount"), "categories": f"={q('res')}!$A$19:$A$24", "values": f"={q('res')}!$E$19:$E$24", "fill": {"color": ENCABEZADO}, "gap": 50})
    t.set_title({"name": tr("Monto otorgado por país", "Amount originated by country"), "name_font": {"name": "Arial", "size": 11}})
    t.set_legend({"none": True})
    t.set_x_axis({"num_format": '#,##0,,"M"', "major_gridlines": {"visible": True, "line": {"color": LINEA}}, "num_font": {"name": "Arial", "size": 8}})
    t.set_y_axis({"reverse": True, "num_font": {"name": "Arial", "size": 9}})
    t.set_size({"width": 460, "height": 300})
    r.insert_chart("G4", t)

    lb.wb.set_properties({"title": tr("Simulador de política de crédito", "Credit policy simulator"), "author": "Lucas Alvarez"})
    lb.wb.close()


def calcular(archivo: Path) -> dict:
    """Calcula el libro con un motor independiente de Excel y devuelve {(HOJA, celda): valor}."""
    modelo = formulas.ExcelModel().loads(str(archivo)).finish()
    solucion = modelo.calculate()
    valores = {}
    for clave, rango in solucion.items():
        texto = str(clave)
        if ":" in texto.rsplit("!", 1)[-1] or "]" not in texto or not hasattr(rango, "value"):
            continue
        hoja = texto.split("]", 1)[1].rsplit("'!", 1)[0]
        celda = texto.rsplit("!", 1)[1]
        v = rango.value[0, 0]
        if isinstance(v, (bool, np.bool_)):
            v = bool(v)
        elif isinstance(v, np.generic):
            v = v.item()
        valores[(hoja.upper(), celda)] = v
    return valores


def insumos() -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    o = path("outputs") / "originacion"
    df = pd.read_csv(o / "segmentos_politica.csv", encoding="utf-8", keep_default_na=False)
    lgd = pd.read_csv(o / "segmentos_politica_lgd.csv", encoding="utf-8").set_index("pais")["lgd"].to_dict()
    ref = pd.read_csv(o / "simulacion_reglas_bondora.csv", encoding="utf-8")
    costo = settings()["politica"]["costos_pp"][-1]
    return df, lgd, ref[ref.costo_pp == costo]


def main() -> None:
    SALIDA.mkdir(exist_ok=True)
    df, lgd, ref = insumos()
    for L, nombre in NOMBRES.items():
        archivo = SALIDA / nombre
        construir(archivo, L, df, lgd, ref, {})
        valores = calcular(archivo)
        construir(archivo, L, df, lgd, ref, valores)
        print(f"excel {L}: {archivo.name}, {len(valores)} celdas calculadas")


if __name__ == "__main__":
    main()
