import pandas as pd
import pytest

from ciclo import cobranzas


@pytest.fixture
def cartera():
    return pd.DataFrame({
        "prestamo_id": list("abcd"),
        "pais": ["Finland", "Estonia", "Denmark", "Finland"],
        "tramo": ["1-30", "1-30", "61-90", "61-90"],
        "dias": [10, 20, 80, 70],
        "saldo": [100.0, 1000.0, 500.0, 2000.0],
        "termino_mal": [False, True, True, True],
        "se_curo": [True, False, False, False],
    })


def test_mitad_es_estable():
    assert cobranzas.mitad("abc") == cobranzas.mitad("abc")


def test_segmentar_agrupa_paises_chicos(cartera):
    s = cobranzas.segmentar(cartera, [200, 800])
    assert s.loc[2, "grupo_pais"] == "Otros"
    assert s.loc[0, "segmento"] == "1-30|bajo|Finland"
    assert s.loc[3, "grupo_saldo"] == "alto"


def test_calibrar_descarta_segmentos_chicos():
    df = pd.DataFrame({"tramo": ["1-30"] * 3 + ["61-90"], "segmento": ["x"] * 3 + ["y"], "termino_mal": [True, False, False, True]})
    seg, tramo = cobranzas.calibrar(df, minimo=2)
    assert "y" not in seg.index and seg["x"] == pytest.approx(1 / 3)
    assert tramo["61-90"] == 1


def test_puntuar_usa_el_tramo_si_falta_el_segmento(cartera):
    df = cobranzas.segmentar(cartera, [200, 800])
    seg = pd.Series({df.loc[0, "segmento"]: 0.5})
    tramo = pd.Series({"1-30": 0.2, "61-90": 0.8})
    p = cobranzas.puntuar(df, seg, tramo, lgd=0.5, efecto={"1-30": 0.2, "61-90": 0.1})
    assert p.loc[0, "prob_mal"] == 0.5 and p.loc[1, "prob_mal"] == 0.2
    assert p.loc[3, "perdida_esperada"] == pytest.approx(2000 * 0.8 * 0.5)
    assert p.loc[3, "salvable"] == pytest.approx(2000 * 0.8 * 0.5 * 0.1)


def test_cobertura_mide_saldo_malo_dentro_de_la_capacidad(cartera):
    assert cobranzas.cobertura(cartera, "saldo", 0.25) == pytest.approx(100 * 2000 / 3500)
    assert cobranzas.cobertura(cartera, "dias", 0.5) == pytest.approx(100 * 2500 / 3500)
    assert cobranzas.cobertura(cartera, "saldo", 1.0) == pytest.approx(100)


def test_perdida_evitada_aplica_el_efecto_por_tramo(cartera):
    v = cobranzas.perdida_evitada(cartera, "saldo", 0.5, lgd=0.5, efecto={"1-30": 0.2, "61-90": 0.1})
    assert v == pytest.approx(2000 * 0.5 * 0.1 + 1000 * 0.5 * 0.2)


def test_canales_atenua_por_tramo():
    res = pd.DataFrame({"tramo": ["1-30", "61-90"], "saldo_medio": [1000.0, 1000.0], "prob_mal": [0.5, 0.5]})
    cfg = {"incrementalidad": 1.0, "efecto_gestion": {"1-30": 0.2, "61-90": 0.05}, "canales": {
        "llamada": {"contacto": 1.0, "promesa": 1.0, "cumplimiento": 1.0, "costo": 10.0},
        "whatsapp": {"contacto": 0.1, "promesa": 1.0, "cumplimiento": 1.0, "costo": 0.1}}}
    t = cobranzas.canales(res, cfg, lgd=0.5).set_index(["tramo", "canal"])
    assert t.loc[("1-30", "llamada"), "evitado_por_cuenta"] == pytest.approx(250)
    assert t.loc[("61-90", "llamada"), "evitado_por_cuenta"] == pytest.approx(62.5)
    assert t.loc[("1-30", "whatsapp"), "evitado_por_euro"] == pytest.approx(250)


def test_saldo_equilibrio_iguala_el_neto_de_los_canales():
    res = pd.DataFrame({"tramo": ["1-30"], "saldo_medio": [1000.0], "prob_mal": [0.5]})
    cfg = {"incrementalidad": 1.0, "efecto_gestion": {"1-30": 0.2}, "canales": {
        "llamada": {"contacto": 1.0, "promesa": 1.0, "cumplimiento": 1.0, "costo": 10.0},
        "whatsapp": {"contacto": 0.1, "promesa": 1.0, "cumplimiento": 1.0, "costo": 0.1}}}
    s = cobranzas.saldo_equilibrio(res, cfg, lgd=0.5)["1-30"]
    t = cobranzas.canales(res.assign(saldo_medio=s), cfg, lgd=0.5).set_index("canal")
    assert t.loc["llamada", "neto_por_cuenta"] == pytest.approx(t.loc["whatsapp", "neto_por_cuenta"])
