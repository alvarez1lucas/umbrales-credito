import re

import pandas as pd
import pytest

from ciclo import powerbi
from ciclo.config import path


@pytest.fixture(scope="module", params=powerbi.IDIOMAS)
def idioma(request):
    return request.param


@pytest.fixture(scope="module")
def paginas(idioma):
    return powerbi.paginas(idioma)


def columnas():
    salida = {}
    for tabla, (csv, *_) in powerbi.TABLAS.items():
        salida[tabla] = set(pd.read_csv(path("outputs") / csv, nrows=1, encoding="utf-8").columns)
    salida["mart_cosechas"].add("anio")
    salida["simulacion_tope_dti"].add("tope")
    return salida


def campos(v):
    estado = v["visual"].get("query", {}).get("queryState", {})
    for rol in estado.values():
        for p in rol["projections"]:
            yield p


def test_visuales_usan_campos_que_existen(paginas, idioma):
    cols, medidas = columnas(), {m[0] for m in powerbi.medidas(idioma)}
    for p in paginas:
        for v in p.visuales:
            for proy in campos(v):
                campo = proy["field"]
                if "Measure" in campo:
                    assert campo["Measure"]["Property"] in medidas
                else:
                    assert campo["Column"]["Property"] in cols[campo["Column"]["Expression"]["SourceRef"]["Entity"]]


def test_referencias_unicas_dentro_de_cada_visual(paginas):
    for p in paginas:
        for v in p.visuales:
            nativas = [x["nativeQueryRef"] for x in campos(v)]
            assert len(nativas) == len(set(nativas)), v["name"]


def test_visuales_dentro_de_la_pagina_y_con_nombre_unico(paginas):
    nombres = [v["name"] for p in paginas for v in p.visuales]
    assert len(nombres) == len(set(nombres))
    for p in paginas:
        for v in p.visuales:
            pos = v["position"]
            assert pos["x"] + pos["width"] <= 1280 and pos["y"] + pos["height"] <= 720, v["name"]


def test_medidas_referencian_medidas_y_columnas_que_existen(idioma):
    cols, medidas = columnas(), {m[0] for m in powerbi.medidas(idioma)}
    for _, dax, _ in powerbi.medidas(idioma):
        for tabla, columna in re.findall(r"(\w+)\[([^\]]+)\]", dax):
            assert columna in cols[tabla], (tabla, columna)
        sin_columnas = re.sub(r"\w+\[[^\]]+\]", "", dax)
        for medida in re.findall(r"\[([^\]]+)\]", sin_columnas):
            assert medida in medidas, medida


@pytest.mark.parametrize("medida", ["Saldo", "Previsión BCRA", "Pérdida esperada", "Saldo previsiones"])
def test_medidas_de_stock_miran_una_sola_foto(medida):
    dax = next(m[1] for m in powerbi.MEDIDAS if m[0] == medida)
    assert "fecha_foto] = ultima" in dax


def test_relaciones_no_dejan_filas_huerfanas():
    for tabla, columna, dim, clave in powerbi.RELACIONES:
        hechos = pd.read_csv(path("outputs") / powerbi.TABLAS[tabla][0], encoding="utf-8", keep_default_na=False)
        if tabla == "mart_deterioro":
            hechos = hechos[hechos.pais != "Slovakia"]
        claves = pd.read_csv(path("outputs") / powerbi.TABLAS[dim][0], encoding="utf-8", keep_default_na=False)
        assert set(hechos[columna]) <= set(claves[clave]), (tabla, columna)


def test_ingles_traduce_todas_las_categorias():
    o = path("outputs")
    tramos = pd.read_csv(o / "marts/dim_tramo.csv", encoding="utf-8").nombre
    situaciones = pd.read_csv(o / "marts/dim_situacion.csv", encoding="utf-8").nombre
    motivos = pd.read_csv(o / "marts/mart_motivos_rechazo.csv", encoding="utf-8").motivo
    assert set(tramos) <= set(powerbi.TRAMOS_EN)
    assert set(situaciones) <= set(powerbi.SITUACIONES_EN)
    assert set(motivos) <= set(powerbi.MOTIVOS_EN)
    assert {m[0] for m in powerbi.MEDIDAS} <= set(powerbi.MEDIDAS_EN)
    assert set(pd.read_csv(o / "marts/mart_composicion.csv", encoding="utf-8").plazo) <= set(powerbi.PLAZOS_EN)
    assert set(pd.read_csv(o / "originacion/simulacion_reglas_bondora.csv", encoding="utf-8").regla) <= set(powerbi.REGLAS_POLITICA_EN)


def test_ingles_no_deja_textos_en_espanol_en_las_consultas():
    csv, fechas, reemplazos, filtro = powerbi.TABLAS["simulacion_tope_dti"]
    tmdl = powerbi.tabla_tmdl("simulacion_tope_dti", csv, fechas, reemplazos, filtro, "en")
    assert "No cap" in tmdl and "Sin tope" not in tmdl


def test_textos_sin_campos_vacios(paginas):
    for p in paginas:
        for v in p.visuales:
            assert "nan" not in str(v.get("visual", {}).get("visualContainerObjects", "")).lower().split()
