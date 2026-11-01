"""Tablero de Power BI generado desde outputs/, como proyecto de texto (TMDL y PBIR).

`python -m ciclo.powerbi` escribe el modelo, las medidas, el tema y las páginas en powerbi/, en español
(umbrales_credito.pbip) y en inglés (umbrales_credito_en.pbip). Al abrirlos, Power BI lee los CSV y dibuja el tablero.
"""

from __future__ import annotations

import json
import re
import shutil
import uuid
from pathlib import Path

import pandas as pd

from ciclo.config import ROOT, path
from ciclo.memo import hallazgos
from ciclo.originacion import SIN_TOPE
from ciclo.sitio import cifras, datos, num

NOMBRE = "umbrales_credito"
IDIOMAS = ("es", "en")
SALIDA = ROOT / "powerbi"
SEMILLA = uuid.UUID("9fd794b6-8dff-4014-b9e6-19de71ef6341")
VC = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.13.0/schema.json"
PG = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json"
PGS = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json"

# Mismos tonos que los sitios del proyecto
FONDO, SUPERFICIE, LINEA = "#f9f9f7", "#fcfcfb", "#e1e0d9"
TEXTO, SECUNDARIO, MUTED = "#0b0b0b", "#52514e", "#6f6e69"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
PAISES = ["Denmark", "Estonia", "Finland", "Latvia", "Lithuania", "Netherlands", "Spain"]
PRODUCTOS = ["Conventional", "FHA", "VA"]  # FSA/RHS queda afuera del gráfico: tan pocos casos por tramo que oscila entre 0 y 100%
ANIOS = list(range(2019, 2026))
RAMPA_ANIOS = ["#b4d0f1", "#8db8ea", "#67a0e2", "#2a78d6", "#1f61b3", "#17498a", "#0f3361"]
COLOR_TRAMO = {"Al día": "#1baf7a", "Pagado": "#2a78d6", "1-30 días": "#f3cf7c", "31-60 días": "#eda100",
               "61-90 días": "#eb6834", "90+ días": "#e34948", "Castigado": "#52514e"}
REGLAS = {"mas_atrasados": "Más atrasados", "mayor_saldo": "Mayor saldo",
          "mayor_perdida_esperada": "Mayor pérdida esperada", "mas_salvable": "Más salvable"}
RESULTADOS = {"otorgado": "Otorgado", "desistido": "Desistido", "rechazado": "Rechazado",
              "incompleto": "Incompleto", "aprobado_no_aceptado": "Aprobado, no aceptado"}
CANALES = {"llamada": "Llamada", "whatsapp": "WhatsApp", "sms": "SMS", "mail": "Mail"}
ROTULO_SIN_TOPE = {"es": "Sin tope", "en": "No cap"}
TABLA_MEDIDAS = {"es": "Medidas", "en": "Metrics"}  # "Measures" es una palabra reservada de TMDL: Power BI no abre el proyecto

TRAMOS_EN = {"Al día": "Current", "1-30 días": "1-30 days", "31-60 días": "31-60 days", "61-90 días": "61-90 days",
             "90+ días": "90+ days", "Pagado": "Paid off", "Castigado": "Written off"}
SITUACIONES_EN = {"Normal": "Normal", "Riesgo bajo (en observación)": "Low risk (watch)", "Riesgo medio": "Medium risk",
                  "Riesgo alto": "High risk", "Irrecuperable": "Unrecoverable"}
MOTIVOS_EN = {"Deuda sobre ingreso": "Debt-to-income", "Historial crediticio": "Credit history", "Garantía": "Collateral",
              "Información no verificable": "Unverifiable information", "Solicitud incompleta": "Incomplete application",
              "Otro": "Other", "Efectivo insuficiente": "Insufficient cash", "Historial laboral": "Employment history",
              "Exento de informar": "Exempt from reporting", "Seguro hipotecario rechazado": "Mortgage insurance denied"}
PLAZOS_EN = {"Hasta 24": "Up to 24", "25-36": "25-36", "37-48": "37-48", "49-60": "49-60", "Más de 60": "Over 60"}
REGLAS_POLITICA_EN = {"Sin cambios": "No change", "Carga <= 20%": "Payment burden <= 20%", "Carga <= 15%": "Payment burden <= 15%",
                      "Carga <= 10%": "Payment burden <= 10%", "Sin ratings F-G": "No F-G ratings", "Sin ratings E-G": "No E-G ratings",
                      "Sin Denmark ni Latvia": "No Denmark or Latvia"}
MEDIDAS_EN = {"Saldo composición": "Composition balance", "Participación": "Share", "PAR30 actual %": "Current PAR30 %",
              "PAR30 anterior %": "Previous PAR30 %", "Cambio PAR30": "PAR30 change", "Mora 12m %": "12m default %",
              "Pérdida evitada": "Loss avoided", "Cambio de resultado": "Result change", "Margen de lo excluido %": "Excluded margin %",
              "Evitado por euro": "Avoided per euro", "Saldo": "Balance", "Saldo previsiones": "Provisioned balance", "Previsión BCRA": "BCRA provision",
              "Pérdida esperada": "Expected loss", "Previsión BCRA %": "BCRA provision %", "Pérdida esperada %": "Expected loss %",
              "Solicitudes": "Applications", "Rechazadas": "Denied", "Con decisión": "Decided", "Tasa de rechazo": "Denial rate",
              "Aprobación %": "Approval %", "Rechazos": "Denials", "% de rechazos": "% of denials",
              "Mora cosecha %": "Vintage default %", "Roll %": "Roll %", "PD 12m % (pond.)": "12m PD % (weighted)",
              "Tasa media % (pond.)": "Average rate % (weighted)", "Saldo malo cubierto %": "Bad balance covered %",
              "Neto por cuenta": "Net per account", "PAR30 %": "PAR30 %", "PAR90 %": "PAR90 %"}
EN = {"Más atrasados": "Most overdue", "Mayor saldo": "Largest balance", "Mayor pérdida esperada": "Highest expected loss",
      "Más salvable": "Most salvageable", "Otorgado": "Originated", "Desistido": "Withdrawn", "Rechazado": "Denied",
      "Incompleto": "Incomplete", "Aprobado, no aceptado": "Approved, not accepted", "Llamada": "Call", "WhatsApp": "WhatsApp",
      "SMS": "SMS", "Mail": "Email", **TRAMOS_EN, **SITUACIONES_EN, **MOTIVOS_EN, **MEDIDAS_EN, **PLAZOS_EN, **REGLAS_POLITICA_EN}


def v(texto: str, L: str) -> str:
    """Valor visible en el idioma pedido: categorías y nombres de medidas."""
    return EN[texto] if L == "en" else texto


def carpeta(L: str) -> str:
    return NOMBRE if L == "es" else f"{NOMBRE}_en"

# nombre en el modelo: (CSV, columnas de fecha, reemplazos de valores, filas a excluir)
TABLAS = {
    "dim_pais": ("marts/dim_pais.csv", (), {}, None),
    "dim_rating": ("marts/dim_rating.csv", (), {}, None),
    "dim_situacion": ("marts/dim_situacion.csv", (), {}, None),
    "dim_tramo": ("marts/dim_tramo.csv", (), {}, None),
    "dim_tramo_desde": ("marts/dim_tramo.csv", (), {}, None),
    "dim_tramo_hasta": ("marts/dim_tramo.csv", (), {}, None),
    "mart_cartera_tramos": ("marts/mart_cartera_tramos.csv", ("fecha_foto",), {}, None),
    "mart_previsiones": ("marts/mart_previsiones.csv", ("fecha_foto",), {}, None),
    "mart_perdida_segmentos": ("marts/mart_perdida_segmentos.csv", (), {}, None),
    "mart_cosechas": ("marts/mart_cosechas.csv", ("cosecha",), {}, None),
    "mart_roll_rates": ("marts/mart_roll_rates.csv", ("fecha_desde", "fecha_hasta"), {}, None),
    "mart_embudo": ("marts/mart_embudo.csv", (), {"resultado": RESULTADOS}, None),
    "mart_motivos_rechazo": ("marts/mart_motivos_rechazo.csv", (), {}, None),
    "mart_aprobacion_dti": ("marts/mart_aprobacion_dti.csv", (), {}, "[dti_orden] <> null"),
    "simulacion_tope_dti": ("originacion/simulacion_tope_dti.csv", (), {}, None),
    "backtest_priorizacion": ("cobranzas/backtest_priorizacion.csv", (), {"regla": REGLAS}, None),
    "escenario_canales": ("cobranzas/escenario_canales.csv", (), {"canal": CANALES}, None),
    "resultado_por_tramo": ("cobranzas/resultado_por_tramo.csv", (), {}, None),
    "tasas_canales": ("cobranzas/tasas_canales.csv", (), {"canal": CANALES}, None),
    "regla_canal": ("cobranzas/regla_canal.csv", (), {}, None),
    "simulacion_reglas_bondora": ("originacion/simulacion_reglas_bondora.csv", (), {}, None),
    "estabilidad_reglas": ("originacion/estabilidad_reglas.csv", (), {}, None),
    "mart_composicion": ("marts/mart_composicion.csv", ("fecha_foto",), {}, None),
    # Eslovaquia dejó de operar antes de la primera foto: no está en dim_pais
    "mart_deterioro": ("marts/mart_deterioro.csv", (), {}, '[pais] <> "Slovakia"'),
}
RELACIONES = [
    ("mart_cartera_tramos", "tramo", "dim_tramo", "tramo"),
    ("mart_cartera_tramos", "rating", "dim_rating", "rating"),
    ("mart_cartera_tramos", "pais", "dim_pais", "pais"),
    ("mart_perdida_segmentos", "rating", "dim_rating", "rating"),
    ("mart_perdida_segmentos", "pais", "dim_pais", "pais"),
    ("mart_previsiones", "pais", "dim_pais", "pais"),
    ("mart_previsiones", "situacion", "dim_situacion", "situacion"),
    ("mart_composicion", "pais", "dim_pais", "pais"),
    ("mart_composicion", "rating", "dim_rating", "rating"),
    ("mart_deterioro", "pais", "dim_pais", "pais"),
    ("mart_deterioro", "rating", "dim_rating", "rating"),
    ("mart_roll_rates", "tramo_desde", "dim_tramo_desde", "tramo"),
    ("mart_roll_rates", "tramo_hasta", "dim_tramo_hasta", "tramo"),
]
ORDEN = {("dim_tramo", "nombre"): "orden", ("dim_tramo_desde", "nombre"): "orden", ("dim_tramo_hasta", "nombre"): "orden",
         ("dim_rating", "rating"): "orden", ("dim_situacion", "nombre"): "situacion", ("mart_aprobacion_dti", "dti"): "dti_orden",
         ("simulacion_tope_dti", "tope"): "tope_dti",
         ("mart_composicion", "plazo"): "plazo_orden"}
FORMATOS = {"simulacion_tope_dti": "0.0", "resultado_por_tramo": "0.0%", "escenario_canales": "#,0.00", "tasas_canales": "0.0",
            "simulacion_reglas_bondora": "0.0"}
FORMATO_COLUMNA = {"impacto_Negro": "0.00", "impacto_Hispano": "0.00", "costo": "0.00",
                   "cambio_ic_inf": "#,0", "cambio_ic_sup": "#,0", "cambio_resultado": "#,0"}

M = "#,0"
# Medidas: (nombre, DAX, formato). Las de cartera y previsiones miran sólo la última foto: sumar fotos duplica el saldo.
MEDIDAS = [
    ("Saldo", """VAR ultima = CALCULATE(MAX(mart_cartera_tramos[fecha_foto]), ALL(mart_cartera_tramos))
RETURN CALCULATE(SUM(mart_cartera_tramos[saldo_capital]), mart_cartera_tramos[fecha_foto] = ultima)""", "€#,0.0"),
    ("PAR30 %", """DIVIDE(
    CALCULATE([Saldo], dim_tramo[tramo] IN {"31-60", "61-90", "90+"}),
    CALCULATE([Saldo], REMOVEFILTERS(dim_tramo))
)""", "0.0%"),
    ("PAR90 %", """DIVIDE(
    CALCULATE([Saldo], dim_tramo[tramo] = "90+"),
    CALCULATE([Saldo], REMOVEFILTERS(dim_tramo))
)""", "0.0%"),
    ("Saldo previsiones", """VAR ultima = CALCULATE(MAX(mart_previsiones[fecha_foto]), ALL(mart_previsiones))
RETURN CALCULATE(SUM(mart_previsiones[saldo_capital]), mart_previsiones[fecha_foto] = ultima)""", "€#,0.0"),
    ("Previsión BCRA", """VAR ultima = CALCULATE(MAX(mart_previsiones[fecha_foto]), ALL(mart_previsiones))
RETURN CALCULATE(SUM(mart_previsiones[prevision_bcra]), mart_previsiones[fecha_foto] = ultima)""", "€#,0.0"),
    ("Pérdida esperada", """VAR ultima = CALCULATE(MAX(mart_previsiones[fecha_foto]), ALL(mart_previsiones))
RETURN CALCULATE(SUM(mart_previsiones[perdida_esperada]), mart_previsiones[fecha_foto] = ultima)""", "€#,0.0"),
    ("Previsión BCRA %", "DIVIDE([Previsión BCRA], [Saldo previsiones])", "0.0%"),
    ("Pérdida esperada %", "DIVIDE([Pérdida esperada], [Saldo previsiones])", "0.0%"),
    ("Solicitudes", "SUM(mart_embudo[solicitudes])", M),
    ("Rechazadas", """CALCULATE([Solicitudes], mart_embudo[resultado] = "Rechazado")""", M),
    ("Con decisión", """CALCULATE([Solicitudes], mart_embudo[resultado] IN {"Otorgado", "Aprobado, no aceptado", "Rechazado"})""", M),
    ("Tasa de rechazo", "DIVIDE([Rechazadas], [Con decisión])", "0.0%"),
    ("Aprobación %", "DIVIDE(SUM(mart_aprobacion_dti[aprobadas]), SUM(mart_aprobacion_dti[decisiones]))", "0.0%"),
    ("Rechazos", "SUM(mart_motivos_rechazo[rechazos])", M),
    ("% de rechazos", "DIVIDE([Rechazos], CALCULATE([Rechazos], ALL(mart_motivos_rechazo[motivo])))", "0.0%"),
    # Un año sólo se muestra en los meses observados por todos sus trimestres; si no, la mezcla deforma la curva.
    ("Mora cosecha %", """VAR observados = DISTINCTCOUNT(mart_cosechas[cosecha])
VAR total = CALCULATE(DISTINCTCOUNT(mart_cosechas[cosecha]), REMOVEFILTERS(mart_cosechas[mes]))
RETURN IF(observados = total, DIVIDE(SUM(mart_cosechas[creditos_con_evento]), SUM(mart_cosechas[creditos])))""", "0.0%"),
    ("Roll %", """DIVIDE(
    SUM(mart_roll_rates[creditos]),
    CALCULATE(SUM(mart_roll_rates[creditos]), REMOVEFILTERS(dim_tramo_hasta))
)""", "0.0%"),
    ("PD 12m % (pond.)", """DIVIDE(
    SUMX(mart_perdida_segmentos, mart_perdida_segmentos[pd_12m_pct] * mart_perdida_segmentos[creditos]),
    SUM(mart_perdida_segmentos[creditos])
) / 100""", "0.0%"),
    ("Tasa media % (pond.)", """DIVIDE(
    SUMX(mart_perdida_segmentos, mart_perdida_segmentos[tasa_media_pct] * mart_perdida_segmentos[creditos]),
    SUM(mart_perdida_segmentos[creditos])
) / 100""", "0.0%"),
    ("Saldo malo cubierto %", "AVERAGE(backtest_priorizacion[saldo_malo_cubierto_pct]) / 100", "0.0%"),
    ("Neto por cuenta", "SUM(escenario_canales[neto_por_cuenta])", "€#,0.00"),
    ("Evitado por euro", "SUM(escenario_canales[evitado_por_euro])", "€#,0.0"),
    ("Pérdida evitada", "SUM(backtest_priorizacion[perdida_evitada_escenario])", "€#,0"),
    ("Cambio de resultado", "SUM(simulacion_reglas_bondora[cambio_resultado]) / 1000000", "+0.00;-0.00;0.00"),
    ("Margen de lo excluido %", "AVERAGE(estabilidad_reglas[margen_pct_monto]) / 100", "0.0%"),
    ("Saldo composición", """VAR ultima = CALCULATE(MAX(mart_composicion[fecha_foto]), ALL(mart_composicion))
RETURN CALCULATE(SUM(mart_composicion[saldo_capital]), mart_composicion[fecha_foto] = ultima)""", "€#,0.0"),
    ("Participación", "DIVIDE([Saldo composición], CALCULATE([Saldo composición], ALL(dim_pais), ALL(mart_composicion[plazo], mart_composicion[plazo_orden])))", "0.0%"),
    ("PAR30 actual %", """VAR ultima = CALCULATE(MAX(mart_composicion[fecha_foto]), ALL(mart_composicion))
RETURN CALCULATE(DIVIDE(SUM(mart_composicion[saldo_par30]), SUM(mart_composicion[saldo_capital])), mart_composicion[fecha_foto] = ultima)""", "0.0%"),
    ("PAR30 anterior %", """VAR primera = CALCULATE(MIN(mart_composicion[fecha_foto]), ALL(mart_composicion))
RETURN CALCULATE(DIVIDE(SUM(mart_composicion[saldo_par30]), SUM(mart_composicion[saldo_capital])), mart_composicion[fecha_foto] = primera)""", "0.0%"),
    ("Cambio PAR30", "([PAR30 actual %] - [PAR30 anterior %]) * 100", "+0.0;-0.0;0.0"),
    # Con menos de 200 créditos la tasa es ruido: queda en blanco
    ("Mora 12m %", """VAR creditos = SUM(mart_deterioro[creditos])
RETURN IF(creditos >= 200, DIVIDE(SUM(mart_deterioro[eventos_12m]), creditos))""", "0.0%"),
]


def tag(*partes: object) -> str:
    return str(uuid.uuid5(SEMILLA, "|".join(map(str, partes))))


def q(nombre: str) -> str:
    """Nombre TMDL: lleva comillas si no es un identificador simple."""
    return nombre if re.fullmatch(r"[A-Za-z_]\w*", nombre, re.ASCII) else "'" + nombre.replace("'", "''") + "'"


def sangrar(texto: str, n: int) -> str:
    return "\n".join("\t" * n + linea for linea in texto.splitlines())


def reemplazos_de(nombre: str, propios: dict, L: str) -> dict:
    salida = {c: {a: v(b, L) for a, b in mapa.items()} for c, mapa in propios.items()}
    if L == "en":
        if nombre.startswith("dim_tramo"):
            salida["nombre"] = TRAMOS_EN
        elif nombre == "dim_situacion":
            salida["nombre"] = SITUACIONES_EN
        elif nombre == "mart_motivos_rechazo":
            salida["motivo"] = MOTIVOS_EN
        elif nombre == "mart_composicion":
            salida["plazo"] = PLAZOS_EN
        elif nombre in ("simulacion_reglas_bondora", "estabilidad_reglas"):
            salida["regla"] = REGLAS_POLITICA_EN
    return salida


def medidas(L: str) -> list[tuple[str, str, str]]:
    salida = []
    for nombre, dax, formato in MEDIDAS:
        for es in sorted(MEDIDAS_EN, key=len, reverse=True):
            dax = dax.replace(f"[{es}]", f"[{v(es, L)}]")
        for r in RESULTADOS.values():
            dax = dax.replace(f'"{r}"', f'"{v(r, L)}"')
        salida.append((v(nombre, L), dax, formato))
    return salida


def tipos(df: pd.DataFrame, fechas: tuple) -> dict[str, tuple[str, str]]:
    salida = {}
    for c in df.columns:
        if c in fechas:
            salida[c] = ("dateTime", "type date")
        elif pd.api.types.is_integer_dtype(df[c]):
            salida[c] = ("int64", "Int64.Type")
        elif pd.api.types.is_numeric_dtype(df[c]):
            salida[c] = ("double", "type number")
        else:
            salida[c] = ("string", "type text")
    return salida


def consulta_m(csv: str, tp: dict, reemplazos: dict, filtro: str | None, con_anio: bool, L: str) -> str:
    cols = ", ".join(f'{{"{c}", {t[1]}}}' for c, t in tp.items())
    pasos = [f'Origen = Csv.Document(File.Contents(RutaDatos & "\\{csv.replace("/", chr(92))}"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),',
             "Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars = true]),",
             f'Resultado0 = Table.TransformColumnTypes(Encabezados, {{{cols}}}, "en-US"),']
    i = 0
    for c, mapa in reemplazos.items():
        registro = ", ".join(f'[a = "{a}", b = "{b}"]' for a, b in mapa.items())
        pasos.append(f'Resultado{i + 1} = Table.TransformColumns(Resultado{i}, {{{{"{c}", (v) => List.First(List.Select({{{registro}}}, (r) => r[a] = v))[b], type text}}}}),')
        i += 1
    if filtro:
        pasos.append(f"Resultado{i + 1} = Table.SelectRows(Resultado{i}, each {filtro}),")
        i += 1
    if con_anio:
        pasos.append(f'Resultado{i + 1} = Table.AddColumn(Resultado{i}, "anio", each Date.Year([cosecha]), Int64.Type),')
        i += 1
    if "tope_dti" in tp:
        pasos.append(f'Resultado{i + 1} = Table.AddColumn(Resultado{i}, "tope", each if [tope_dti] >= {SIN_TOPE} then "{ROTULO_SIN_TOPE[L]}" else Text.From([tope_dti]), type text),')
        i += 1
    pasos[-1] = pasos[-1].rstrip(",")
    return "let\n" + "\n".join("    " + p for p in pasos) + f"\nin\n    Resultado{i}"


def tabla_tmdl(nombre: str, csv: str, fechas: tuple, reemplazos: dict, filtro: str | None, L: str) -> str:
    df = pd.read_csv(path("outputs") / csv, encoding="utf-8")
    tp = tipos(df, fechas)
    con_anio = nombre == "mart_cosechas"
    columnas = dict(tp)
    if con_anio:
        columnas["anio"] = ("int64", "Int64.Type")
    if "tope_dti" in tp:
        columnas["tope"] = ("string", "type text")
    partes = [f"table {q(nombre)}", f"\tlineageTag: {tag(nombre)}", ""]
    for c, (dt, _) in columnas.items():
        partes += [f"\tcolumn {q(c)}", f"\t\tdataType: {dt}"]
        if dt == "dateTime":
            partes.append("\t\tformatString: yyyy-mm-dd")
        elif dt == "int64" and c == "creditos":
            partes.append("\t\tformatString: #,0")
        elif dt == "double" and nombre in FORMATOS:
            partes.append(f"\t\tformatString: {FORMATO_COLUMNA.get(c, FORMATOS[nombre])}")
        partes += [f"\t\tlineageTag: {tag(nombre, c)}", "\t\tsummarizeBy: none", f"\t\tsourceColumn: {c}"]
        if (nombre, c) in ORDEN:
            partes.append(f"\t\tsortByColumn: {ORDEN[(nombre, c)]}")
        partes += ["", "\t\tannotation SummarizationSetBy = Automatic", ""]
    partes += [f"\tpartition {q(nombre)} = m", "\t\tmode: import", "\t\tsource ="]
    partes.append(sangrar(consulta_m(csv, tp, reemplazos, filtro, con_anio, L), 4))
    return "\n".join(partes) + "\n"


def medidas_tmdl(L: str) -> str:
    tm = TABLA_MEDIDAS[L]
    partes = [f"table {tm}", f"\tlineageTag: {tag('Medidas')}", ""]
    for nombre, dax, formato in medidas(L):
        partes += [f"\tmeasure {q(nombre)} =", sangrar(dax, 3), f"\t\tformatString: {formato}",
                   f"\t\tlineageTag: {tag('Medidas', nombre)}", ""]
    partes += ["\tcolumn _", "\t\tdataType: string", "\t\tisHidden", f"\t\tlineageTag: {tag('Medidas', '_')}",
               "\t\tsummarizeBy: none", "\t\tsourceColumn: _", "", "\t\tannotation SummarizationSetBy = Automatic", "",
               f"\tpartition {tm} = m", "\t\tmode: import", "\t\tsource ="]
    partes.append(sangrar('let\n    Resultado = #table(type table [_ = text], {})\nin\n    Resultado', 4))
    return "\n".join(partes) + "\n"


def escribir_modelo(raiz: Path, L: str) -> None:
    d = raiz / "definition"
    shutil.rmtree(d / "tables", ignore_errors=True)
    (d / "tables").mkdir(parents=True)
    for nombre, (csv, fechas, reemplazos, filtro) in TABLAS.items():
        (d / "tables" / f"{nombre}.tmdl").write_text(tabla_tmdl(nombre, csv, fechas, reemplazos_de(nombre, reemplazos, L), filtro, L), encoding="utf-8")
    (d / "tables" / f"{TABLA_MEDIDAS[L]}.tmdl").write_text(medidas_tmdl(L), encoding="utf-8")
    relaciones = "".join(f"relationship {tag('rel', a, b)}\n\tfromColumn: {a}.{b}\n\ttoColumn: {c}.{e}\n\n"
                         for a, b, c, e in RELACIONES)
    (d / "relationships.tmdl").write_text(relaciones, encoding="utf-8")
    ruta = str(path("outputs")).replace('"', '""')
    (d / "expressions.tmdl").write_text(
        f'expression RutaDatos = "{ruta}" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]\n'
        f"\tlineageTag: {tag('RutaDatos')}\n\n\tannotation PBI_ResultType = Text\n", encoding="utf-8")
    refs = "\n".join(f"ref table {q(t)}" for t in [*TABLAS, TABLA_MEDIDAS[L]])
    (d / "model.tmdl").write_text(f"""model Model
\tculture: en-US
\tdefaultPowerBIDataSourceVersion: powerBI_V3
\tsourceQueryCulture: en-US
\tvalueFilterBehavior: independent
\tdataAccessOptions
\t\tlegacyRedirects
\t\treturnErrorValuesAsNull

annotation __PBI_TimeIntelligenceEnabled = 0

annotation PBI_ProTooling = ["DevMode"]

{refs}

ref cultureInfo en-US
""", encoding="utf-8")


# --- Informe ---

def lit(v: object) -> dict:
    if isinstance(v, bool):
        valor = "true" if v else "false"
    elif isinstance(v, int):
        valor = f"{v}L"
    elif isinstance(v, float):
        valor = f"{v}D"
    else:
        valor = "'" + str(v).replace("'", "''") + "'"
    return {"expr": {"Literal": {"Value": valor}}}


def color(c: str) -> dict:
    return {"solid": {"color": lit(c)}}


def col(t: str, c: str, titulo: str | None = None) -> dict:
    return {"campo": {"Column": {"Expression": {"SourceRef": {"Entity": t}}, "Property": c}}, "ref": f"{t}.{c}", "corto": c, "titulo": titulo}


def med(m: str, L: str, titulo: str | None = None) -> dict:
    tm, nombre = TABLA_MEDIDAS[L], v(m, L)
    return {"campo": {"Measure": {"Expression": {"SourceRef": {"Entity": tm}}, "Property": nombre}}, "ref": f"{tm}.{nombre}", "corto": nombre, "titulo": titulo}


def proyeccion(f: dict) -> dict:
    p = {"field": f["campo"], "queryRef": f["ref"], "nativeQueryRef": f["ref"].replace(".", "_")}
    if f["titulo"]:
        p["displayName"] = f["titulo"]
    return p


def filtro_lista(nombre: str, t: str, c: str, valores: list) -> dict:
    return {"name": nombre, "field": {"Column": {"Expression": {"SourceRef": {"Entity": t}}, "Property": c}}, "type": "Categorical",
            "filter": {"Version": 2, "From": [{"Name": "t", "Entity": t, "Type": 0}],
                       "Where": [{"Condition": {"In": {
                           "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "t"}}, "Property": c}}],
                           "Values": [[{"Literal": lit(v)["expr"]["Literal"]}] for v in valores]}}}]},
            "howCreated": "User"}


def colores_serie(t: str, c: str, mapa: dict) -> list:
    return [{"properties": {"fill": color(h)},
             "selector": {"data": [{"scopeId": {"Comparison": {
                 "ComparisonKind": 0, "Left": {"Column": {"Expression": {"SourceRef": {"Entity": t}}, "Property": c}},
                 "Right": lit(v)["expr"]}}}]}} for v, h in mapa.items()]


def tabla_legible(campos: list, ancho: int, fuente: float = 11.0, aire: int = 3, primera: int | None = None) -> dict:
    util = ancho - 44
    resto = (util - primera) // (len(campos) - 1) if primera else util // len(campos)
    anchos = [primera or resto] + [resto] * (len(campos) - 1)
    return {"total": [{"properties": {"totals": lit(False)}}], "columnHeaders": [{"properties": {"fontSize": lit(fuente), "wordWrap": lit(True)}}],
            "values": [{"properties": {"fontSize": lit(fuente)}}],
            "grid": [{"properties": {"rowPadding": lit(aire), "textSize": lit(fuente)}}],
            "columnWidth": [{"properties": {"value": lit(float(a))}, "selector": {"metadata": f["ref"]}} for f, a in zip(campos, anchos)]}


LINEA_RECTA = {"lineStyles": [{"properties": {"lineChartType": lit("straight")}}]}
LINEA_CON_MARCAS = {"lineStyles": [{"properties": {"lineChartType": lit("straight"), "showMarker": lit(True)}}]}


def ejes(eje_x: str | None = None, eje_y: str | None = None, leyenda: bool = True) -> dict:
    obj: dict = {"valueAxis": [{"properties": {"show": lit(leyenda or bool(eje_x)), "showAxisTitle": lit(bool(eje_y)), "gridlineColor": color(LINEA)}}],
                 "categoryAxis": [{"properties": {"showAxisTitle": lit(bool(eje_x))}}]}
    if eje_x:
        obj["categoryAxis"][0]["properties"]["titleText"] = lit(eje_x)
    if eje_y:
        obj["valueAxis"][0]["properties"]["titleText"] = lit(eje_y)
    if leyenda:
        obj["legend"] = [{"properties": {"show": lit(True), "position": lit("Top"), "showTitle": lit(False)}}]
    return obj


class Pagina:
    def __init__(self, nombre: str, titulo: str) -> None:
        self.nombre, self.titulo, self.visuales = nombre, titulo, []

    def agregar(self, tipo: str, x: int, y: int, w: int, h: int, roles: dict | None = None, titulo: str | None = None,
                objetos: dict | None = None, filtros: list | None = None, orden: list | None = None,
                contenedor: dict | None = None) -> None:
        n = len(self.visuales)
        v: dict = {"visualType": tipo, "drillFilterOtherVisuals": True}
        if roles:
            v["query"] = {"queryState": {r: {"projections": [proyeccion(f) for f in fs]} for r, fs in roles.items()}}
            if orden:
                v["query"]["sortDefinition"] = {"sort": [{"field": f["campo"], "direction": d} for f, d in orden], "isDefaultSort": False}
        if objetos:
            v["objects"] = objetos
        cont = dict(contenedor or {})
        if tipo != "textbox":
            cont["subTitle"] = [{"properties": {"show": lit(False)}}]
        if titulo:
            cont["title"] = [{"properties": {"show": lit(True), "text": lit(titulo)}}]
        elif tipo not in ("textbox",):
            cont.setdefault("title", [{"properties": {"show": lit(False)}}])
        if cont:
            v["visualContainerObjects"] = cont
        cuerpo = {"$schema": VC, "name": f"{self.nombre}_{n:02d}",
                  "position": {"x": x, "y": y, "z": n * 100, "height": h, "width": w, "tabOrder": n * 100}, "visual": v}
        if filtros:
            cuerpo["filterConfig"] = {"filters": filtros}
        self.visuales.append(cuerpo)

    def texto(self, x: int, y: int, w: int, h: int, parrafos: list, tarjeta: bool = False) -> None:
        cont = {} if tarjeta else {"background": [{"properties": {"show": lit(False)}}], "border": [{"properties": {"show": lit(False)}}]}
        self.agregar("textbox", x, y, w, h, objetos={"general": [{"properties": {"paragraphs": parrafos}}]}, contenedor=cont)


def corrida(texto: str, pt: int, c: str = TEXTO, negrita: bool = False) -> dict:
    estilo = {"fontSize": f"{pt}pt", "color": c, "fontFamily": "Segoe UI Semibold" if negrita else "Segoe UI"}
    return {"value": texto, "textStyle": estilo}


def encabezado(p: Pagina, titulo: str, bajada: str, ancho: int = 1232) -> None:
    p.texto(24, 12, ancho, 66, [{"textRuns": [corrida(titulo, 20, negrita=True)]}, {"textRuns": [corrida(bajada, 11, SECUNDARIO)]}])


def pie(p: Pagina, nota: str) -> None:
    p.texto(24, 692, 1232, 24, [{"textRuns": [corrida(nota, 9, MUTED)]}])


def selector_pais(p: Pagina, L: str) -> None:
    p.agregar("slicer", 1036, 16, 220, 56, {"Values": [col("dim_pais", "pais", "País" if L == "es" else "Country")]},
              objetos={"data": [{"properties": {"mode": lit("Dropdown")}}],
                       "header": [{"properties": {"show": lit(True), "text": lit("País (filtra cartera)" if L == "es" else "Country (filters portfolio)")}}]},
              contenedor={"background": [{"properties": {"show": lit(False)}}], "border": [{"properties": {"show": lit(False)}}]})


def resumen(c: dict, L: str) -> Pagina:
    es = L == "es"
    p = Pagina("resumen", "Resumen" if es else "Summary")
    encabezado(p, "Una política de crédito es un conjunto de umbrales" if es else "A credit policy is a set of thresholds",
               "Cinco preguntas a cada regla del ciclo: originación, cartera y cobranzas, con datos reales" if es
               else "Five questions for each rule across the cycle: origination, portfolio and collections, on real data", 1000)
    selector_pais(p, L)
    kpis = [("Saldo", "Saldo de cartera" if es else "Portfolio balance"), ("PAR30 %", "PAR30"), ("PAR90 %", "PAR90"),
            ("Tasa de rechazo", "Rechazo sobre decisiones" if es else "Denial rate on decisions"),
            ("Pérdida esperada %", "Pérdida esperada" if es else "Expected loss")]
    for i, (m, rotulo) in enumerate(kpis):
        unidades = {"labelDisplayUnits": lit(1000000.0), "labelPrecision": lit(1)} if m == "Saldo" else {}
        p.agregar("card", 24 + i * 248, 86, 240, 96, {"Values": [med(m, L, rotulo)]},
                  objetos={"labels": [{"properties": {"fontSize": lit(26.0), "fontFamily": lit("Segoe UI Semibold"), "color": color(TEXTO), **unidades}}],
                           "categoryLabels": [{"properties": {"fontSize": lit(11.0), "color": color(SECUNDARIO)}}]})
    for i, (pregunta, hallazgo) in enumerate(hallazgos(c, L)):
        p.texto(24, 192 + i * 98, 1232, 90, [{"textRuns": [corrida(pregunta, 15, negrita=True)]},
                                              {"textRuns": [corrida(hallazgo, 14, SECUNDARIO)]}], tarjeta=True)
    pie(p, f"Bondora: {c['creditos']} créditos de consumo, foto de {c['fecha']}. HMDA: {c['solicitudes']} solicitudes hipotecarias, Georgia (EE.UU.), 2023-2025. Se traslada el método, no los valores." if es
        else f"Bondora: {c['creditos']} consumer loans, {c['fecha']} snapshot. HMDA: {c['solicitudes']} mortgage applications, Georgia (US), 2023-2025. What travels is the method, not the values.")
    return p


def originacion(c: dict, motivos: list[str], L: str) -> Pagina:
    es = L == "es"
    p = Pagina("originacion", "Originación" if es else "Origination")
    encabezado(p, "La regla está en 50 de deuda-ingreso" if es else "The rule sits at 50 debt-to-income",
               "Solicitudes hipotecarias de Georgia (EE.UU.), 2023-2025" if es else "Mortgage applications in Georgia (US), 2023-2025")
    t = "mart_aprobacion_dti"
    mapa = dict(zip(PRODUCTOS, SERIES))
    p.agregar("lineChart", 24, 84, 800, 300, {"Category": [col(t, "dti", "Deuda-ingreso" if es else "Debt-to-income")], "Y": [med("Aprobación %", L)], "Series": [col(t, "producto", "Producto" if es else "Product")]},
              f"La aprobación convencional cae de {c['plano']}% a {c['ap50']}% al cruzar 50 de deuda-ingreso" if es
              else f"Conventional approval falls from {c['plano']}% to {c['ap50']}% when debt-to-income crosses 50",
              {**ejes("Deuda-ingreso (%)" if es else "Debt-to-income (%)"), **LINEA_RECTA, "dataPoint": colores_serie(t, "producto", mapa)},
              filtros=[filtro_lista("productos", t, "producto", list(mapa))], orden=[(col(t, "dti"), "Ascending")])
    p.agregar("clusteredBarChart", 836, 84, 420, 300, {"Category": [col("mart_embudo", "resultado", "Resultado" if es else "Outcome")], "Y": [med("Solicitudes", L)]},
              f"Se otorga el {c['otorgado']}% de las solicitudes y se rechaza el {c['rechazado']}%" if es
              else f"{c['otorgado']}% of applications are originated and {c['rechazado']}% denied",
              {**ejes(leyenda=False), "labels": [{"properties": {"show": lit(True), "labelDisplayUnits": lit(1.0)}}], "dataPoint": [{"properties": {"fill": color(SERIES[0])}}]},
              orden=[(med("Solicitudes", L), "Descending")])
    p.agregar("clusteredBarChart", 24, 396, 500, 290, {"Category": [col("mart_motivos_rechazo", "motivo", "Motivo" if es else "Reason")], "Y": [med("% de rechazos", L)]},
              f"Deuda-ingreso explica el {c['mot_dti']}% de los motivos de rechazo" if es else f"Debt-to-income accounts for {c['mot_dti']}% of denial reasons",
              {**ejes(leyenda=False), "labels": [{"properties": {"show": lit(True)}}], "dataPoint": [{"properties": {"fill": color(SERIES[0])}}]},
              filtros=[filtro_lista("motivos", "mart_motivos_rechazo", "motivo", [v(m, L) for m in motivos])], orden=[(med("% de rechazos", L), "Descending")])
    t = "simulacion_tope_dti"
    campos = [col(t, "tope", "Tope" if es else "Cap"), col(t, "aprobacion_pct", "Aprobación %" if es else "Approval %"),
              col(t, "aprobados_perdidos_pct", "Aprobados perdidos %" if es else "Approvals lost %"),
              col(t, "monto_perdido_pct", "Monto perdido %" if es else "Amount lost %"),
              col(t, "impacto_Negro", "Impacto Negro" if es else "Impact, Black"), col(t, "impacto_Hispano", "Impacto Hispano" if es else "Impact, Hispanic")]
    p.agregar("tableEx", 536, 396, 720, 290, {"Values": campos},
              f"Un tope de 45 pierde el {c['p45']}% de los aprobados y baja el impacto adverso de {c['ai_n']} a {c['ai45n']}" if es
              else f"A cap of 45 loses {c['p45']}% of approvals and takes adverse impact from {c['ai_n']} to {c['ai45n']}",
              orden=[(col(t, "tope"), "Ascending")], objetos=tabla_legible(campos, 720, 10.0, 2))
    pie(p, f"Barras en vez de embudo: los resultados son excluyentes, no etapas. Impacto adverso bajo {c['umbral']} señala una regla a revisar, no prueba discriminación." if es
        else f"Bars rather than a funnel: outcomes are mutually exclusive, not stages. Adverse impact below {c['umbral']} flags a rule for review; it does not prove discrimination.")
    return p


def cartera(c: dict, m12: dict, r: pd.DataFrame, seg: pd.DataFrame, L: str) -> Pagina:
    es = L == "es"
    p = Pagina("cartera", "Cartera" if es else "Portfolio")
    encabezado(p, "La cartera se lee por cosecha, tramo y segmento" if es else "Read the portfolio by vintage, bucket and segment",
               f"Bondora, foto de {c['fecha']}" if es else f"Bondora, {c['fecha']} snapshot", 1000)
    selector_pais(p, L)
    t = "mart_cosechas"
    p.agregar("lineChart", 24, 84, 620, 300, {"Category": [col(t, "mes", "Mes" if es else "Month")], "Y": [med("Mora cosecha %", L)], "Series": [col(t, "anio", "Cosecha" if es else "Vintage")]},
              f"La mora a 12 meses pasó de {num(m12[2019], L)}% en la cosecha 2019 a {num(m12[2025], L)}% en la 2025" if es
              else f"12-month default went from {num(m12[2019], L)}% in the 2019 vintage to {num(m12[2025], L)}% in 2025",
              {**ejes("Meses desde el otorgamiento" if es else "Months since origination"), **LINEA_RECTA, "dataPoint": colores_serie(t, "anio", dict(zip(ANIOS, RAMPA_ANIOS)))},
              filtros=[filtro_lista("anios", t, "anio", ANIOS)], orden=[(col(t, "mes"), "Ascending")])
    d, h = "dim_tramo_desde", "dim_tramo_hasta"
    roll = med("Roll %", L)
    gradiente = {"properties": {"backColor": {"solid": {"color": {"expr": {"FillRule": {
        "Input": roll["campo"],
        "FillRule": {"linearGradient2": {"min": {"color": lit("#ffffff")["expr"]}, "max": {"color": lit("#2a78d6")["expr"]}}}}}}}}},
        "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": roll["ref"]}}
    queda, castigo = num(float(r.loc["90+", "quedan"]), L), num(float(r.loc["90+", "castigado"]), L)
    p.agregar("pivotTable", 656, 84, 600, 300, {"Rows": [col(d, "nombre", "Desde" if es else "From")], "Columns": [col(h, "nombre", "Hasta" if es else "To")], "Values": [roll]},
              f"El 90+ casi no vuelve: de {c['fecha_ini']} a {c['fecha']}, {queda}% sigue ahí y {castigo}% se castiga" if es
              else f"90+ rarely comes back: from {c['fecha_ini']} to {c['fecha']}, {queda}% stayed and {castigo}% was written off",
              objetos={"values": [gradiente, {"properties": {"fontSize": lit(10.0)}}],
                       "grid": [{"properties": {"rowPadding": lit(6), "textSize": lit(10.0)}}],
                       "columnHeaders": [{"properties": {"fontSize": lit(9.0), "wordWrap": lit(False), "autoSizeColumnWidth": lit(False)}}], "rowHeaders": [{"properties": {"fontSize": lit(10.0)}}],
                       "columnWidth": [{"properties": {"value": lit(69.0)}, "selector": {"metadata": roll["ref"]}}],
                       "subTotals": [{"properties": {"rowSubtotals": lit(False), "columnSubtotals": lit(False)}}]})
    malos = seg[seg.margen_ajustado_pct < 0]
    solo_dinamarca = set(malos.pais) == {"Denmark"}
    donde = (", y son de Dinamarca" if es else ", all in Denmark") if solo_dinamarca else ""
    p.agregar("scatterChart", 24, 396, 620, 290, {"Category": [col("dim_rating", "rating", "Rating")], "Series": [col("dim_pais", "pais", "País" if es else "Country")],
                                                   "X": [med("Tasa media % (pond.)", L, "Tasa media" if es else "Average rate")], "Y": [med("PD 12m % (pond.)", L, "PD a 12 meses" if es else "12-month PD")]},
              f"{len(malos)} de {len(seg)} segmentos no cubren su pérdida esperada{donde}" if es else f"{len(malos)} of {len(seg)} segments do not cover their expected loss{donde}",
              {**ejes("Tasa media" if es else "Average rate", "PD a 12 meses" if es else "12-month PD"), "dataPoint": colores_serie("dim_pais", "pais", dict(zip(PAISES, SERIES)))})
    s = "dim_situacion"
    p.agregar("clusteredColumnChart", 656, 396, 600, 290, {"Category": [col(s, "nombre", "Situación" if es else "Status")],
                                                            "Y": [med("Previsión BCRA %", L, "Norma BCRA" if es else "BCRA rule"), med("Pérdida esperada %", L, "Pérdida esperada" if es else "Expected loss")]},
              f"La norma BCRA pide {c['bcra']} M€ y la pérdida esperada, {c['ecl']} M€" if es else f"The BCRA rule requires €{c['bcra']}M and expected loss, €{c['ecl']}M",
              ejes(), orden=[(col(s, "nombre"), "Ascending")])
    pie(p, f"La norma BCRA se aplica a una cartera europea como ejercicio de comparación. LGD media supuesta: {c['lgd']}%. Las cosechas sólo se muestran en los meses observados por todos sus trimestres." if es
        else f"The BCRA rule is applied to a European portfolio as a comparison exercise. Assumed average LGD: {c['lgd']}%. Vintages only show months observed by all their quarters.")
    return p


def cobranzas(c: dict, L: str) -> Pagina:
    es = L == "es"
    p = Pagina("cobranzas", "Cobranzas" if es else "Collections")
    encabezado(p, "Con capacidad limitada, importa a quién se llama primero" if es else "With limited capacity, who gets called first matters",
               "Priorización comparada sobre créditos reales de Bondora" if es else "Prioritization rules compared on real Bondora loans")
    t = "backtest_priorizacion"
    p.agregar("lineChart", 24, 84, 660, 300, {"Category": [col(t, "capacidad_pct", "Capacidad" if es else "Capacity")], "Y": [med("Saldo malo cubierto %", L)], "Series": [col(t, "regla", "Regla" if es else "Rule")]},
              f"Con 20% de capacidad, la pérdida esperada cubre {c['cob_pe']}% del saldo malo; el atraso, {c['cob_atr']}%" if es
              else f"At 20% capacity, expected loss covers {c['cob_pe']}% of the bad balance; days past due, {c['cob_atr']}%",
              {**ejes("Capacidad de gestión (% de cuentas)" if es else "Collection capacity (% of accounts)"), **LINEA_CON_MARCAS,
               "dataPoint": colores_serie(t, "regla", {v(r, L): h for r, h in zip(REGLAS.values(), SERIES)})},
              orden=[(col(t, "capacidad_pct"), "Ascending")])
    d, h = "dim_tramo_desde", "dim_tramo_hasta"
    p.agregar("hundredPercentStackedBarChart", 696, 84, 560, 300, {"Category": [col(d, "nombre", "Desde" if es else "From")], "Y": [med("Roll %", L)], "Series": [col(h, "nombre", "Hasta" if es else "To")]},
              f"De {c['fecha_ini']} a {c['fecha']}: adónde fue cada tramo" if es else f"From {c['fecha_ini']} to {c['fecha']}: where each bucket went",
              {**ejes(leyenda=True), "dataPoint": colores_serie(h, "nombre", {v(n, L): x for n, x in COLOR_TRAMO.items()})}, orden=[(col(d, "nombre"), "Ascending")])
    t = "resultado_por_tramo"
    campos = [col(t, "tramo", "Tramo" if es else "Bucket"), col(t, "creditos", "Créditos" if es else "Loans"),
              col(t, "prob_mal", "Termina mal" if es else "Goes bad"), col(t, "prob_cura", "Se cura" if es else "Cures")]
    p.agregar("tableEx", 24, 396, 560, 290, {"Values": campos},
              f"El atraso sí separa riesgo: termina mal el {c['mal1']}% de 1-30 días y el {c['mal3']}% de 61-90" if es
              else f"Days past due do separate risk: {c['mal1']}% go bad from 1-30 days, {c['mal3']}% from 61-90",
              orden=[(col(t, "tramo"), "Ascending")], objetos=tabla_legible(campos, 560, 13.0, 7))
    t = "escenario_canales"
    neto = med("Neto por cuenta", L, "Neto por cuenta" if es else "Net per account")
    p.agregar("pivotTable", 596, 396, 660, 290, {"Rows": [col(t, "canal", "Canal" if es else "Channel")], "Columns": [col(t, "tramo", "Tramo" if es else "Bucket")], "Values": [neto]},
              "Escenario con supuestos, no datos observados: € netos evitados por cuenta" if es else "Scenario with assumptions, not observed data: net € avoided per account",
              objetos={"subTotals": [{"properties": {"rowSubtotals": lit(False), "columnSubtotals": lit(False)}}],
                       "grid": [{"properties": {"rowPadding": lit(8), "textSize": lit(13.0)}}],
                       "columnHeaders": [{"properties": {"fontSize": lit(13.0), "alignment": lit("Right")}}], "rowHeaders": [{"properties": {"fontSize": lit(13.0)}}],
                       "values": [{"properties": {"fontSize": lit(13.0)}}],
                       "columnWidth": [{"properties": {"value": lit(170.0)}, "selector": {"metadata": neto["ref"]}}]})
    pie(p, "El efecto por canal no se observa en datos públicos: el cuadro de canales es un análisis de decisión con supuestos explícitos." if es
        else "Channel effects are not observed in public data: the channel table is a decision analysis with explicit assumptions.")
    return p


def matriz_calor(medida: dict, ancho_columna: float) -> dict:
    gradiente = {"properties": {"backColor": {"solid": {"color": {"expr": {"FillRule": {
        "Input": medida["campo"],
        "FillRule": {"linearGradient2": {"min": {"color": lit("#ffffff")["expr"]}, "max": {"color": lit("#e34948")["expr"]}}}}}}}}},
        "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": medida["ref"]}}
    return {"values": [gradiente, {"properties": {"fontSize": lit(10.0)}}],
            "grid": [{"properties": {"rowPadding": lit(2), "textSize": lit(10.0)}}],
            "columnHeaders": [{"properties": {"fontSize": lit(11.0), "alignment": lit("Right"), "autoSizeColumnWidth": lit(False)}}],
            "rowHeaders": [{"properties": {"fontSize": lit(11.0)}}],
            "columnWidth": [{"properties": {"value": lit(ancho_columna)}, "selector": {"metadata": medida["ref"]}}],
            "subTotals": [{"properties": {"rowSubtotals": lit(False), "columnSubtotals": lit(False)}}]}


def politica(c: dict, L: str) -> Pagina:
    es = L == "es"
    p = Pagina("politica", "Política" if es else "Policy")
    encabezado(p, "¿Qué pasa con aprobación y resultado si muevo la regla?" if es else "What happens to approval and results if I move the rule?",
               "Reglas simuladas sobre créditos de Bondora con resultado observado" if es else "Rules simulated on Bondora loans with observed outcomes")
    t = "simulacion_reglas_bondora"
    sin_cambios = [v(r, L) for r in REGLAS_POLITICA_EN if r != "Sin cambios"]
    sin_costo = ("; sin costo, todas pierden" if es else "; with no cost, every rule loses") if c["todas_pierden_sin_costo"] else ""
    p.agregar("clusteredBarChart", 24, 84, 620, 300, {"Category": [col(t, "regla", "Regla" if es else "Rule")], "Y": [med("Cambio de resultado", L, "Cambio (M€)" if es else "Change (€M)")]},
              (f"Con {c['costo']} puntos de costo, sacar Dinamarca y Letonia rinde {c['dl']} M€{sin_costo}" if es
               else f"At {c['costo']} points of cost, removing Denmark and Latvia yields {c['dl']} €M{sin_costo}"),
              {**ejes(leyenda=False), "labels": [{"properties": {"show": lit(True)}}], "dataPoint": [{"properties": {"fill": color(SERIES[0])}}]},
              filtros=[filtro_lista("reglas", t, "regla", sin_cambios), filtro_lista("costo", t, "costo_pp", [10])], orden=[(med("Cambio de resultado", L), "Descending")])
    t = "estabilidad_reglas"
    series = {v(r, L): h for r, h in zip(("Sin ratings F-G", "Sin ratings E-G", "Sin Denmark ni Latvia"), SERIES)}
    p.agregar("lineChart", 656, 84, 600, 300, {"Category": [col(t, "semestre", "Semestre" if es else "Half-year")], "Y": [med("Margen de lo excluido %", L)], "Series": [col(t, "regla", "Regla" if es else "Rule")]},
              f"Las reglas envejecen: F y G pasaron de {c['fg_ini']}% a {c['fg_fin']}% del monto en dos años" if es
              else f"Rules age: F and G went from {c['fg_ini']}% to {c['fg_fin']}% of the amount in two years",
              {**ejes("Semestre de originación" if es else "Origination half-year"), **LINEA_CON_MARCAS, "dataPoint": colores_serie(t, "regla", series)},
              filtros=[filtro_lista("reglas", t, "regla", list(series))], orden=[(col(t, "semestre"), "Ascending")])
    t = "simulacion_reglas_bondora"
    campos = [col(t, "regla", "Regla" if es else "Rule"), col(t, "aprobados_pct", "Aprobados %" if es else "Approved %"), col(t, "monto_pct", "Monto %" if es else "Amount %"),
              col(t, "evento_12m_pct", "Mora 12m %" if es else "12m default %"), col(t, "margen_pct_monto", "Margen %" if es else "Margin %"),
              col(t, "cambio_resultado", "Cambio (€)" if es else "Change (€)"), col(t, "cambio_ic_inf", "IC inferior (€)" if es else "CI low (€)"), col(t, "cambio_ic_sup", "IC superior (€)" if es else "CI high (€)")]
    p.agregar("tableEx", 24, 396, 1232, 290, {"Values": campos},
              f"Cada regla, con {c['costo']} puntos de costo: lo que se resigna contra lo que se gana" if es else f"Each rule at {c['costo']} points of cost: what is given up against what is gained",
              objetos=tabla_legible(campos, 1232, 11.0, 2, 230), filtros=[filtro_lista("costo", t, "costo_pp", [10])], orden=[(col(t, "cambio_resultado"), "Descending")])
    pie(p, "El costo de fondeo y operación es un supuesto. Sin él, ninguna regla mejora: el margen de riesgo del segmento excluido sigue siendo positivo. IC: bootstrap al 95%." if es
        else "Funding and operating cost is an assumption. Without it, no rule improves results: the excluded segment still has a positive risk margin. CI: 95% bootstrap.")
    return p


def deterioro(c: dict, x: dict, L: str) -> Pagina:
    es = L == "es"
    p = Pagina("deterioro", "Deterioro" if es else "Deterioration")
    encabezado(p, "Dónde se deteriora la cartera y desde cuándo" if es else "Where the portfolio is deteriorating, and since when",
               "Decisión: bajar cupo en D a G y endurecer Dinamarca y Letonia, antes de que entren en la cartera madura" if es
               else "Decision: cut limits in D to G and tighten Denmark and Latvia before they reach the mature portfolio", 1000)
    selector_pais(p, L)
    t = "mart_deterioro"
    mora = med("Mora 12m %", L, "Mora a 12 meses" if es else "12-month default")
    p.agregar("pivotTable", 24, 84, 500, 300, {"Rows": [col("dim_rating", "rating", "Rating")], "Columns": [col(t, "cosecha_anio", "Cosecha" if es else "Vintage")], "Values": [mora]},
              f"Rating G: de {num(x['g_ini'], L)}% en la cosecha 2023 a {num(x['g_fin'], L)}% en la 2025" if es
              else f"Rating G: from {num(x['g_ini'], L)}% in the 2023 vintage to {num(x['g_fin'], L)}% in 2025",
              objetos=matriz_calor(mora, 110.0), filtros=[filtro_lista("anios", t, "cosecha_anio", [2023, 2024, 2025]),
                                                         filtro_lista("ratings", "dim_rating", "rating", ["AA", "A", "B", "C", "D", "E", "F", "G"])])
    p.agregar("pivotTable", 536, 84, 720, 300, {"Rows": [col("dim_pais", "pais", "País" if es else "Country")], "Columns": [col(t, "cosecha_anio", "Cosecha" if es else "Vintage")], "Values": [mora]},
              f"Los mercados nuevos arrancan peor: Dinamarca, {num(x['dk'], L)}% en 2025; Letonia, {num(x['lv'], L)}%" if es
              else f"New markets start worse: Denmark, {num(x['dk'], L)}% in 2025; Latvia, {num(x['lv'], L)}%",
              objetos=matriz_calor(mora, 84.0), filtros=[filtro_lista("anios", t, "cosecha_anio", ANIOS)])
    t = "mart_composicion"
    campos = [col("dim_pais", "pais", "País" if es else "Country"), med("Participación", L, "Saldo %" if es else "Balance %"), med("PAR30 anterior %", L, f"PAR30 {c['fecha_ini']}"),
              med("PAR30 actual %", L, f"PAR30 {c['fecha']}"), med("Cambio PAR30", L, "Cambio (pp)" if es else "Change (pp)")]
    p.agregar("tableEx", 24, 396, 620, 290, {"Values": campos},
              f"Finlandia concentra {num(x['fi'], L)}% del saldo (HHI {num(x['hhi'], L, 2)}); Dinamarca y Letonia empeoran" if es
              else f"Finland holds {num(x['fi'], L)}% of the balance (HHI {num(x['hhi'], L, 2)}); Denmark and Latvia are worsening",
              objetos=tabla_legible(campos, 620, 11.0, 2), orden=[(med("Participación", L), "Descending")])
    p.agregar("clusteredColumnChart", 656, 396, 600, 290, {"Category": [col(t, "plazo", "Plazo (meses)" if es else "Term (months)")],
                                                            "Y": [med("Participación", L, "Saldo %" if es else "Balance %"), med("PAR30 actual %", L, "PAR30")]},
              f"El plazo de 49-60 meses pesa {num(x['p60'], L)}% del saldo, con PAR30 de {num(x['par60'], L)}%" if es
              else f"The 49-60 month term is {num(x['p60'], L)}% of the balance, with a PAR30 of {num(x['par60'], L)}%",
              {**ejes("Plazo (meses)" if es else "Term (months)"), "labels": [{"properties": {"show": lit(True)}}]}, orden=[(col(t, "plazo"), "Ascending")])
    pie(p, f"Mora a 12 meses: sólo créditos con 12 meses de antigüedad; celdas con menos de 200 créditos, en blanco. El plazo mezcla antigüedad: los de más de 60 son más nuevos. {num(x['sin_rating'], L)}% del saldo no tiene rating (cartera vieja)." if es
        else f"12-month default: only loans 12 months old; cells under 200 loans are blank. Term is mixed with age: loans over 60 months are newer. {num(x['sin_rating'], L)}% of the balance has no rating (legacy book).")
    return p


def canales(c: dict, x: dict, L: str) -> Pagina:
    es = L == "es"
    p = Pagina("canales", "Canales y plan" if es else "Channels and plan")
    encabezado(p, "A quién gestionar, por qué canal y cuánto rinde" if es else "Who to work, through which channel, and what it yields",
               "Escenario con supuestos: Bondora no publica gestiones de cobranza" if es else "Scenario with assumptions: Bondora does not publish collection activity")
    t = "backtest_priorizacion"
    mejor = v(x["mejor"], L)
    p.agregar("clusteredBarChart", 24, 84, 620, 300, {"Category": [col(t, "regla", "Regla" if es else "Rule")], "Y": [med("Pérdida evitada", L, "Pérdida evitada" if es else "Loss avoided")]},
              f"Mismo equipo, {num(x['veces'], L)} veces más: «{mejor}» evita {x['evitado']} € contra {x['base']} € por antigüedad" if es
              else f"Same team, {num(x['veces'], L)} times more: '{mejor}' avoids €{x['evitado']} against €{x['base']} by age",
              {**ejes(leyenda=False), "labels": [{"properties": {"show": lit(True), "labelDisplayUnits": lit(1.0)}}], "dataPoint": [{"properties": {"fill": color(SERIES[0])}}]},
              filtros=[filtro_lista("capacidad", t, "capacidad_pct", [20.0])], orden=[(med("Pérdida evitada", L), "Descending")])
    t = "escenario_canales"
    por_euro = med("Evitado por euro", L, "€ evitados por € gastado" if es else "€ avoided per € spent")
    p.agregar("pivotTable", 656, 84, 600, 300, {"Rows": [col(t, "canal", "Canal" if es else "Channel")], "Columns": [col(t, "tramo", "Tramo" if es else "Bucket")], "Values": [por_euro]},
              "WhatsApp rinde más por euro; la llamada deja más neto por cuenta" if es else "WhatsApp yields more per euro; a call leaves more net per account",
              objetos={"subTotals": [{"properties": {"rowSubtotals": lit(False), "columnSubtotals": lit(False)}}],
                       "grid": [{"properties": {"rowPadding": lit(8), "textSize": lit(13.0)}}],
                       "columnHeaders": [{"properties": {"fontSize": lit(13.0), "alignment": lit("Right")}}], "rowHeaders": [{"properties": {"fontSize": lit(13.0)}}],
                       "values": [{"properties": {"fontSize": lit(13.0)}}],
                       "columnWidth": [{"properties": {"value": lit(150.0)}, "selector": {"metadata": por_euro["ref"]}}]})
    t = "tasas_canales"
    campos = [col(t, "canal", "Canal" if es else "Channel"), col(t, "costo", "Costo (€)" if es else "Cost (€)"), col(t, "contacto_pct", "Contacto %" if es else "Contact %"),
              col(t, "promesa_pct", "Promesa %" if es else "Promise %"), col(t, "cumplimiento_pct", "Cumple %" if es else "Kept %"), col(t, "pagos_cada_100", "Pagos cada 100" if es else "Payments per 100")]
    p.agregar("tableEx", 24, 396, 680, 290, {"Values": campos},
              "Supuestos del embudo: contacto, promesa de pago y cumplimiento" if es else "Funnel assumptions: contact, promise to pay and promise kept",
              objetos=tabla_legible(campos, 680, 12.0, 8), orden=[(col(t, "pagos_cada_100"), "Descending")])
    t = "regla_canal"
    campos = [col(t, "tramo", "Tramo" if es else "Bucket"), col(t, "base", "Caso base (€)" if es else "Base case (€)"), col(t, "contacto_mitad", "Mitad de contacto (€)" if es else "Half contact (€)"), col(t, "costo_doble", "Doble costo (€)" if es else "Double cost (€)")]
    p.agregar("tableEx", 716, 396, 540, 290, {"Values": campos},
              f"Llamar conviene desde {x['umbral']} € de saldo en 1-30 días; debajo, WhatsApp" if es else f"Calling pays from €{x['umbral']} of balance at 1-30 days; below that, WhatsApp",
              objetos=tabla_legible(campos, 540, 12.0, 8), orden=[(col(t, "tramo"), "Ascending")])
    pie(p, f"Pérdida evitada sobre {x['prueba']} créditos de prueba, gestionando el 20% de las cuentas: el costo es el mismo en todas las reglas. Tasas, costos y efecto de gestión son supuestos de config/settings.yaml." if es
        else f"Loss avoided on {x['prueba']} test loans, working 20% of accounts: cost is the same under every rule. Rates, costs and treatment effect are assumptions from config/settings.yaml.")
    return p


def tema() -> dict:
    return {
        "name": "Umbrales de crédito", "dataColors": SERIES, "background": SUPERFICIE, "foreground": TEXTO, "tableAccent": SERIES[0],
        "textClasses": {"title": {"fontFace": "Segoe UI Semibold", "fontSize": 12, "color": TEXTO},
                        "label": {"fontFace": "Segoe UI", "fontSize": 10, "color": SECUNDARIO},
                        "callout": {"fontFace": "Segoe UI Semibold", "fontSize": 26, "color": TEXTO}},
        "visualStyles": {
            "*": {"*": {"background": [{"show": True, "color": {"solid": {"color": SUPERFICIE}}, "transparency": 0}],
                        "border": [{"show": True, "color": {"solid": {"color": LINEA}}, "radius": 8}],
                        "title": [{"titleWrap": True, "alignment": "left", "fontSize": 12, "fontFamily": "Segoe UI Semibold", "fontColor": {"solid": {"color": TEXTO}}}]}},
            "page": {"*": {"background": [{"color": {"solid": {"color": FONDO}}, "transparency": 0}],
                           "outspace": [{"color": {"solid": {"color": FONDO}}, "transparency": 0}]}},
            "tableEx": {"*": {"grid": [{"gridVertical": False, "rowPadding": 4}]}},
        },
    }


def escribir_informe(raiz: Path, paginas: list[Pagina]) -> None:
    recursos = raiz / "StaticResources" / "RegisteredResources"
    recursos.mkdir(parents=True, exist_ok=True)
    (recursos / f"{NOMBRE}.json").write_text(json.dumps(tema(), ensure_ascii=False, indent=2), encoding="utf-8")

    f = raiz / "definition" / "report.json"
    rep = json.loads(f.read_text(encoding="utf-8"))
    version = rep["themeCollection"]["baseTheme"]["reportVersionAtImport"]
    rep["themeCollection"]["customTheme"] = {"name": f"{NOMBRE}.json", "reportVersionAtImport": version, "type": "RegisteredResources"}
    rep["resourcePackages"] = [r for r in rep["resourcePackages"] if r["name"] != "RegisteredResources"]
    rep["resourcePackages"].append({"name": "RegisteredResources", "type": "RegisteredResources",
                                    "items": [{"name": f"{NOMBRE}.json", "path": f"{NOMBRE}.json", "type": "CustomTheme"}]})
    f.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")

    d = raiz / "definition" / "pages"
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir()
    (d / "pages.json").write_text(json.dumps({"$schema": PGS, "pageOrder": [p.nombre for p in paginas], "activePageName": paginas[0].nombre}, indent=2), encoding="utf-8")
    for p in paginas:
        carpeta = d / p.nombre
        (carpeta / "visuals").mkdir(parents=True)
        (carpeta / "page.json").write_text(json.dumps({"$schema": PG, "name": p.nombre, "displayName": p.titulo, "displayOption": "FitToPage",
                                                       "height": 720, "width": 1280}, ensure_ascii=False, indent=2), encoding="utf-8")
        for v in p.visuales:
            (carpeta / "visuals" / v["name"]).mkdir()
            (carpeta / "visuals" / v["name"] / "visual.json").write_text(json.dumps(v, ensure_ascii=False, indent=2), encoding="utf-8")


def extras(L: str) -> dict:
    """Cifras de los títulos de deterioro y de canales, que no están en el memo."""
    o = path("outputs")
    d = pd.read_csv(o / "marts/mart_deterioro.csv", encoding="utf-8")
    mora = lambda f: 100 * d[f].eventos_12m.sum() / d[f].creditos.sum()
    co = pd.read_csv(o / "marts/mart_composicion.csv", encoding="utf-8")
    u = co[co.fecha_foto == co.fecha_foto.max()]
    total = u.saldo_capital.sum()
    p60 = u[u.plazo == "49-60"]
    res = json.loads((o / "cartera/resumen_cartera.json").read_text(encoding="utf-8"))
    cob = json.loads((o / "cobranzas/resumen_cobranzas.json").read_text(encoding="utf-8"))
    b = pd.read_csv(o / "cobranzas/backtest_priorizacion.csv", encoding="utf-8")
    b = b[b.capacidad_pct == 20].set_index("regla").perdida_evitada_escenario
    return {"g_ini": mora((d.rating == "G") & (d.cosecha_anio == 2023)), "g_fin": mora((d.rating == "G") & (d.cosecha_anio == 2025)),
            "dk": mora((d.pais == "Denmark") & (d.cosecha_anio == 2025)), "lv": mora((d.pais == "Latvia") & (d.cosecha_anio == 2025)),
            "fi": res["concentracion"]["participacion_pct"]["Finland"], "hhi": res["concentracion"]["hhi"],
            "p60": 100 * p60.saldo_capital.sum() / total, "par60": 100 * p60.saldo_par30.sum() / p60.saldo_capital.sum(),
            "sin_rating": 100 * u[u.rating == "sin_rating"].saldo_capital.sum() / total,
            "mejor": REGLAS[b.idxmax()], "veces": b.max() / b["mas_atrasados"], "evitado": num(b.max(), L, 0), "base": num(b["mas_atrasados"], L, 0),
            "umbral": cob["saldo_equilibrio_llamada"]["base"]["1-30"], "prueba": num(cob["creditos_prueba"], L, 0)}


def paginas(L: str = "es") -> list[Pagina]:
    o = path("outputs")
    c = cifras(datos(), L)
    co = pd.read_csv(o / "marts/mart_cosechas.csv")
    co["anio"] = co.cosecha.str[:4].astype(int)
    x = co[co.mes == 12].groupby("anio")[["creditos_con_evento", "creditos"]].sum()
    m12 = (x.creditos_con_evento / x.creditos * 100).to_dict()
    r = pd.read_csv(o / "marts/mart_roll_rates.csv").pivot(index="tramo_desde", columns="tramo_hasta", values="pct_del_tramo")
    r["quedan"] = r["90+"]
    seg = pd.read_csv(o / "marts/mart_perdida_segmentos.csv")
    mot = pd.read_csv(o / "marts/mart_motivos_rechazo.csv", encoding="utf-8")
    motivos = mot.groupby("motivo").rechazos.sum().nlargest(8).index.tolist()
    return [resumen(c, L), originacion(c, motivos, L), politica(c, L), cartera(c, m12, r, seg, L), deterioro(c, extras(L), L),
            cobranzas(c, L), canales(c, extras(L), L)]


def preparar_ingles() -> None:
    """Copia la estructura del proyecto en español, que Power BI creó, con nombre e identidad propios."""
    for tipo in ("Report", "SemanticModel"):
        destino = SALIDA / f"{carpeta('en')}.{tipo}"
        shutil.rmtree(destino, ignore_errors=True)
        shutil.copytree(SALIDA / f"{NOMBRE}.{tipo}", destino, ignore=shutil.ignore_patterns(".pbi"))
        f = destino / ".platform"
        plataforma = json.loads(f.read_text(encoding="utf-8"))
        plataforma["metadata"]["displayName"] = carpeta("en")
        plataforma["config"]["logicalId"] = tag("en", tipo)
        f.write_text(json.dumps(plataforma, indent=2), encoding="utf-8")
    f = SALIDA / f"{carpeta('en')}.Report" / "definition.pbir"
    f.write_text(f.read_text(encoding="utf-8").replace(f"../{NOMBRE}.SemanticModel", f"../{carpeta('en')}.SemanticModel"), encoding="utf-8")
    pbip = (SALIDA / f"{NOMBRE}.pbip").read_text(encoding="utf-8").replace(f"{NOMBRE}.Report", f"{carpeta('en')}.Report")
    (SALIDA / f"{carpeta('en')}.pbip").write_text(pbip, encoding="utf-8")


def main() -> None:
    preparar_ingles()
    for L in IDIOMAS:
        escribir_modelo(SALIDA / f"{carpeta(L)}.SemanticModel", L)
        ps = paginas(L)
        escribir_informe(SALIDA / f"{carpeta(L)}.Report", ps)
        (SALIDA / f"{carpeta(L)}.SemanticModel" / ".pbi" / "cache.abf").unlink(missing_ok=True)
        print(f"powerbi {L}: {len(TABLAS) + 1} tablas, {len(MEDIDAS)} medidas, {sum(len(p.visuales) for p in ps)} visuales")


if __name__ == "__main__":
    main()
