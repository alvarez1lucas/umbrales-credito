import openpyxl
import pandas as pd
import pytest

from ciclo import excel
from ciclo.config import path


@pytest.fixture(scope="module", params=excel.IDIOMAS)
def libro(request):
    L = request.param
    return L, openpyxl.load_workbook(excel.SALIDA / excel.NOMBRES[L], data_only=True), openpyxl.load_workbook(excel.SALIDA / excel.NOMBRES[L])


def test_todas_las_formulas_tienen_valor_y_ninguna_da_error(libro):
    _, valores, formulas = libro
    total = 0
    for hoja in formulas:
        for fila in hoja.iter_rows():
            for celda in fila:
                if isinstance(celda.value, str) and celda.value.startswith("="):
                    total += 1
                    v = valores[hoja.title][celda.coordinate].value
                    assert not (isinstance(v, str) and v.startswith("#")), (hoja.title, celda.coordinate)
    assert total > 1000


def test_usa_funciones_de_excel_2016(libro):
    _, _, formulas = libro
    for hoja in formulas:
        for fila in hoja.iter_rows():
            for celda in fila:
                if isinstance(celda.value, str) and celda.value.startswith("="):
                    assert "XLOOKUP" not in celda.value and "_xlfn" not in celda.value


def test_concilia_con_las_reglas_del_proyecto(libro):
    L, valores, _ = libro
    h = valores[excel.HOJAS[L]["con"]]
    assert h["B4"].value in ("Concilia con el proyecto", "Reconciles with the project")
    for fila in range(7, 13):
        assert abs(h[f"D{fila}"].value) < 1


def test_el_escenario_por_defecto_es_la_regla_recomendada(libro):
    L, valores, _ = libro
    h = valores[excel.HOJAS[L]["sim"]]
    r = pd.read_csv(path("outputs") / "originacion/simulacion_reglas_bondora.csv", encoding="utf-8")
    esperado = r[(r.regla == "Sin Denmark ni Latvia") & (r.costo_pp == 10)].cambio_resultado.iloc[0]
    assert h["H14"].value == pytest.approx(esperado, abs=1)
    segmentos = pd.read_csv(path("outputs") / "originacion/segmentos_politica.csv", encoding="utf-8", keep_default_na=False)
    assert h["F7"].value == segmentos.creditos.sum()


def test_segmentos_conservan_el_total_de_creditos():
    d = pd.read_csv(path("outputs") / "originacion/segmentos_politica.csv", encoding="utf-8", keep_default_na=False)
    assert d.duplicated(["anio", "pais", "rating", "carga"]).sum() == 0
    assert set(d.rating) <= set(excel.RATINGS)
