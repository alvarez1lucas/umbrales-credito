import numpy as np
import pandas as pd
import pytest

from ciclo import originacion as o


@pytest.fixture
def hmda():
    return pd.DataFrame({
        "grupo": ["Blanco", "Blanco", "Negro", "Negro", "Hispano", "Asiático"],
        "aprobado": [True, True, True, False, True, True],
        "dti_orden": [30.0, 49.0, 49.0, 55.0, np.nan, 33.0],
        "monto": [100.0, 200.0, 300.0, 400.0, 500.0, 600.0],
        "spread": [0.5, 1.0, np.nan, np.nan, -0.5, 0.2],
    })


def test_tope_no_afecta_a_quien_no_informa_dti(hmda):
    ap = o.aplicar_tope(hmda, 40)
    assert ap.tolist() == [True, False, False, False, True, True]


def test_impacto_adverso_es_relativo_al_grupo_de_referencia(hmda):
    v = o.impacto_adverso(hmda, hmda["aprobado"])
    assert v["Negro"] == pytest.approx(0.5) and v["Asiático"] == pytest.approx(1)


def test_simular_topes_mide_lo_perdido(hmda):
    t = o.simular_topes(hmda, [40]).iloc[0]
    assert t["aprobados_perdidos"] == 2
    assert t["monto_perdido_pct"] == pytest.approx(100 * 500 / 1700)
    assert t["spread_anual_perdido"] == pytest.approx(2.0)  # el spread nulo cuenta cero
    assert t["perdidos_Negro_pct"] == 100 and t["perdidos_Blanco_pct"] == 50


def test_rechazos_solo_dti_excluye_los_que_tienen_otro_motivo():
    df = pd.DataFrame({"resultado": ["rechazado", "rechazado", "rechazado", "otorgado"], "dti_tramo": ["50-60", "50-60", "50-60", "50-60"],
                       "motivo_rechazo_1": [1, 1, 3, pd.NA], "motivo_rechazo_2": [pd.NA, 3, pd.NA, pd.NA], "monto": [10.0, 20.0, 30.0, 40.0],
                       "aprobado": [False, False, False, True]})
    r = o.rechazos_solo_dti(df)
    assert r["solicitudes"] == 1 and r["monto"] == 10
    assert r["aprobacion_pct_si_se_aprueban"] == 50


def test_brecha_condicional_absorbe_el_perfil():
    # el rechazo depende sólo de la deuda-ingreso, pero un grupo tiene más deuda: la brecha bruta desaparece al controlar
    rng = np.random.default_rng(1)
    n = 6000
    grupo = rng.choice(["Blanco", "Negro", "Hispano", "Asiático"], n)
    dti = np.where(grupo == "Negro", rng.choice([33, 55], n, p=[.3, .7]), rng.choice([33, 55], n, p=[.8, .2]))
    df = pd.DataFrame({"grupo": grupo, "dti_orden": dti.astype(float), "ltv_tramo": "<=80", "ingreso_miles": rng.uniform(50, 150, n),
                       "monto": rng.uniform(100000, 300000, n), "producto": "Conventional", "anio": 2024,
                       "prestamista_lei": rng.choice(list("abcdefghij"), n),
                       "resultado": np.where(rng.random(n) < np.where(dti > 50, .6, .1), "rechazado", "otorgado")})
    t = o.brecha_condicional(df).set_index(["especificacion", "grupo"])
    assert t.loc[("bruta", "Negro"), "brecha_pp"] > 15
    assert abs(t.loc[("con_prestamista", "Negro"), "brecha_pp"]) < 4


def test_brecha_condicional_mantiene_solicitudes_sin_datos():
    df = pd.DataFrame({"grupo": ["Blanco", "Negro", "Hispano", "Asiático"] * 50, "dti_orden": [33.0, np.nan] * 100,
                       "ltv_tramo": ["<=80", None] * 100, "ingreso_miles": [100.0, 0.0, 80.0, np.nan] * 50, "monto": [200000.0] * 200,
                       "producto": ["Conventional", "FHA"] * 100, "anio": [2024] * 200, "prestamista_lei": list("abcdefghij") * 20,
                       "resultado": (["rechazado"] + ["otorgado"] * 3) * 50})
    assert o.brecha_condicional(df)["n"].iloc[0] == 200


def _bondora():
    return pd.DataFrame({"pais": ["Finland", "Finland", "Denmark"], "rating": ["A", "G", "G"], "monto": [1000.0, 1000.0, 1000.0],
                         "tasa": [0.20, 0.20, 0.20], "carga_pct": [5.0, 30.0, 10.0], "evento_12m": [False, True, True], "lgd": [0.5, 0.5, 0.5],
                         "fecha_otorgamiento": pd.to_datetime(["2024-01-15", "2024-02-15", "2024-08-15"])})


def test_margen_resta_costo_y_perdida():
    m = o.margen(_bondora(), costo_pp=10)
    assert m.tolist() == pytest.approx([100, -400, -400])


def test_simular_reglas_endurecer_mejora_si_lo_que_sale_pierde():
    cfg = {"topes_carga": [20], "excluir_ratings": {"G": ["G"]}, "excluir_paises": ["Denmark"], "bootstrap": 50}
    t = o.simular_reglas(_bondora(), cfg, 10).set_index("regla")
    assert t.loc["Sin cambios", "aprobados_pct"] == 100 and t.loc["Sin cambios", "cambio_resultado"] == 0
    assert t.loc["Sin ratings G", "cambio_resultado"] == pytest.approx(800)
    assert t.loc["Carga <= 20%", "aprobados_pct"] == pytest.approx(200 / 3)
    assert t.loc["Sin Denmark", "evento_12m_pct"] == pytest.approx(50)


def test_estabilidad_por_semestre():
    cfg = {"topes_carga": [], "excluir_ratings": {"G": ["G"]}, "excluir_paises": ["Denmark"]}
    t = o.estabilidad(_bondora(), cfg, 10).set_index(["regla", "semestre"])
    assert t.loc[("Sin ratings G", "2024-S1"), "margen_pct_monto"] == pytest.approx(-40)
    assert ("Sin Denmark", "2024-S2") in t.index
